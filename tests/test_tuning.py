import json

import mlflow
import numpy as np
import optuna
import pytest
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

from fixtures import make_train_rows
from tarifalatam.config import TARGET
from tarifalatam.data.folds import fold_indices, make_folds, reserve_hosts
from tarifalatam.models import tuning
from tarifalatam.models.train import build_pipeline, feature_frame, usd_metrics
from tarifalatam.models.tuning import (
    SPACES,
    compare_on_reserved,
    host_bootstrap_ci,
    make_model,
    paired_abs_error_difference,
    save_decision,
    trials_table,
    tune,
    use_optimized,
)
from tarifalatam.tracking import mlflow_utils as mu

# Rangos aprobados (especificaciones/04-features-torneo-optimizacion.md, sección 6)
RANGES = {
    "lightgbm": {
        "n_estimators": (200, 1000),
        "learning_rate": (0.01, 0.2),
        "num_leaves": (15, 255),
        "min_child_samples": (10, 200),
        "subsample": (0.6, 1.0),
        "colsample_bytree": (0.5, 1.0),
        "reg_lambda": (0.001, 10.0),
    },
    "random_forest": {"max_depth": (8, 40), "min_samples_leaf": (1, 20), "max_features": (0.2, 1.0)},
    "ridge": {"alpha": (0.001, 1000.0)},
}


@pytest.mark.parametrize("name", list(RANGES))
def test_spaces_stay_within_approved_ranges(name):
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=0))
    for _ in range(50):
        trial = study.ask()
        params = SPACES[name](trial)
        assert set(params) == set(RANGES[name])
        for key, (low, high) in RANGES[name].items():
            assert low <= params[key] <= high
        study.tell(trial, 0.0)


def test_make_model_fixes_seeds_and_the_number_of_trees():
    lgbm = make_model("lightgbm", {"learning_rate": 0.1})
    assert isinstance(lgbm, LGBMRegressor)
    assert (lgbm.get_params()["random_state"], lgbm.get_params()["subsample_freq"]) == (42, 1)
    forest = make_model("random_forest", {"max_depth": 10})
    assert isinstance(forest, RandomForestRegressor)
    assert (forest.get_params()["n_estimators"], forest.get_params()["random_state"]) == (200, 42)
    assert isinstance(make_model("ridge", {"alpha": 3.0}), Ridge)


def test_make_model_unknown_name_raises():
    with pytest.raises(ValueError, match="xgboost"):
        make_model("xgboost", {})


# --- Comprobación honesta ---------------------------------------------------------------------------------------


def test_host_bootstrap_ci_constant_difference():
    mean, low, high = host_bootstrap_ci(np.full(20, 2.0), np.repeat(np.arange(5), 4), n=200)
    assert (mean, low, high) == pytest.approx((2.0, 2.0, 2.0))


def test_host_bootstrap_ci_resamples_hosts_not_rows():
    """Repetir 10 veces las filas de cada anfitrión no estrecha el intervalo: la unidad es el anfitrión."""
    rng = np.random.default_rng(0)
    hosts = np.repeat(np.arange(30), 3)
    diff = rng.normal(0, 1, size=len(hosts))
    once = host_bootstrap_ci(diff, hosts, n=300)
    tenfold = host_bootstrap_ci(np.repeat(diff, 10), np.repeat(hosts, 10), n=300)
    assert tenfold == pytest.approx(once)


def test_use_optimized_rule():
    assert use_optimized(-1.2, -0.3)
    assert not use_optimized(-0.8, 0.4)
    assert not use_optimized(-0.5, 0.0)  # tocar el cero no cuenta como mejora


def test_paired_abs_error_difference_hand_case():
    true = np.log([100.0, 200.0])
    a = np.log([110.0, 200.0])  # errores 10 y 0
    b = np.log([95.0, 230.0])  # errores 5 y 30
    assert paired_abs_error_difference(true, a, b) == pytest.approx([5.0, -30.0])  # negativo: A se equivoca menos


def test_compare_on_reserved_identical_pipelines_give_zero():
    data = make_train_rows(n_hosts=40)
    search, reserved = reserve_hosts(data)
    pipeline = build_pipeline(Ridge(), "linear")
    result = compare_on_reserved(pipeline, pipeline, search, reserved, n=100)
    assert (result["mean_difference"], result["low"], result["high"]) == pytest.approx((0.0, 0.0, 0.0))
    expected = pipeline.fit(feature_frame(search), search[TARGET]).predict(feature_frame(reserved))
    assert result["mae_a"] == pytest.approx(usd_metrics(reserved[TARGET], expected)["mae"])  # ajusta solo con búsqueda
    assert result["hosts"] == reserved["host_id"].nunique()


# --- Búsqueda con registro en MLflow local ----------------------------------------------------------------------


def _search_data():
    data = make_train_rows()
    return feature_frame(data), data[TARGET].to_numpy(), fold_indices(data, make_folds(data))


def _local_mlflow(tmp_path, experiment: str):
    mu.configure_mlflow(force_local=True, local_db=tmp_path / "mlflow.db", env_file=tmp_path / "no_existe.env")
    mu.set_experiment(experiment)


def test_tune_logs_one_run_per_trial(tmp_path):
    _local_mlflow(tmp_path, "prueba-busqueda")
    X, y, folds = _search_data()
    study = tune("ridge", X, y, folds, n_trials=2)
    runs = mlflow.search_runs(experiment_names=["prueba-busqueda"])
    assert len(runs) == len(study.trials) == 2
    assert sorted(runs["tags.mlflow.runName"]) == ["ridge-ensayo-01", "ridge-ensayo-02"]
    assert set(runs["tags.etapa"]) == {"06_optimizacion"}
    assert set(runs["tags.modelo"]) == {"ridge"}
    assert set(runs["tags.variables"]) == {"sin_sospechosas"}
    assert set(runs["tags.datos"]) == {"train.csv.gz"}
    assert set(runs["tags.estado"]) == {"completo"}
    assert runs["params.alpha"].notna().all()
    for metric in ("mae", "mae_std", "mape", "rmse", "bias", "r2_log", "fit_seconds"):
        assert runs[f"metrics.{metric}"].notna().all()


def test_tune_records_failed_trials(tmp_path, monkeypatch):
    _local_mlflow(tmp_path, "prueba-fallo")
    X, y, folds = _search_data()
    original, calls = tuning.evaluate_folds, []

    def fails_once(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise MemoryError("sin memoria (simulado)")
        return original(*args, **kwargs)

    monkeypatch.setattr(tuning, "evaluate_folds", fails_once)
    study = tune("ridge", X, y, folds, n_trials=2)
    assert len(study.trials) == 2  # el ensayo fallido cuenta en el presupuesto
    assert [t.state for t in study.trials] == [optuna.trial.TrialState.FAIL, optuna.trial.TrialState.COMPLETE]
    runs = mlflow.search_runs(experiment_names=["prueba-fallo"])
    assert sorted(runs["tags.estado"]) == ["completo", "fallido"]


def test_trials_table_has_one_row_per_trial(tmp_path):
    _local_mlflow(tmp_path, "prueba-tabla")
    X, y, folds = _search_data()
    table = trials_table(tune("ridge", X, y, folds, n_trials=2), "ridge")
    assert list(table["trial"]) == [1, 2]
    assert {"model", "state", "alpha", "mae", "mae_std", "fit_seconds"} <= set(table.columns)


def test_save_decision_writes_the_contract_keys(tmp_path):
    decision = {
        "finalista": "lightgbm",
        "parametros": {"learning_rate": 0.05},
        "origen_parametros": "partida",
        "comprobacion": {"intervalo_95": [-0.5, 0.3]},
        "regla": "Se usan los optimizados solo si todo el intervalo está por debajo de cero",
        "comparacion_finalistas": None,
        "tracking": "local",
        "experimento": "tarifalatam-optimizacion",
        "ensayos": 30,
    }
    path = tmp_path / "06_best_params.json"
    save_decision(path, decision)
    assert json.loads(path.read_text(encoding="utf-8")) == decision
    with pytest.raises(ValueError, match="regla"):
        save_decision(path, {k: v for k, v in decision.items() if k != "regla"})
