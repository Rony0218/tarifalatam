import json

import mlflow
import numpy as np
import optuna
import pytest
from lightgbm import LGBMRegressor
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

from fixtures import make_train_rows
from tarifalatam.config import TARGET
from tarifalatam.data.folds import fold_indices, make_folds, reserve_hosts
from tarifalatam.models import tuning
from tarifalatam.models.train import BaselineRegressor, build_pipeline, feature_frame, usd_metrics
from tarifalatam.models.tuning import (
    SPACES,
    choose_finalist,
    starting_params,
    compare_on_reserved,
    construction_info,
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
    assert list(trials_table(study, "ridge")["state"]) == ["fallido", "completo"]


def test_trials_table_has_one_row_per_trial(tmp_path):
    _local_mlflow(tmp_path, "prueba-tabla")
    X, y, folds = _search_data()
    table = trials_table(tune("ridge", X, y, folds, n_trials=2), "ridge")
    assert list(table["trial"]) == [1, 2]
    assert {"model", "state", "alpha", "mae", "mae_std", "fit_seconds"} <= set(table.columns)


def _decision() -> dict:
    return {
        "finalista": "lightgbm",
        "parametros": {"learning_rate": 0.05},
        "origen_parametros": "partida",
        "comprobacion": {"intervalo_95": [-0.5, 0.3]},
        "regla": "Se usan los optimizados solo si todo el intervalo está por debajo de cero",
        "comparacion_finalistas": None,
        "regla_elegiria": "lightgbm",
        "decision_del_grupo": None,
        "como_se_arma": "make_model('lightgbm', parametros)",
        "parametros_fijos": {"subsample_freq": 1},
        "tracking": "local",
        "experimento": "tarifalatam-optimizacion",
        "ensayos": 30,
    }


def test_save_decision_writes_the_contract_keys(tmp_path):
    decision = _decision()
    path = tmp_path / "06_best_params.json"
    save_decision(path, decision)
    assert json.loads(path.read_text(encoding="utf-8")) == decision
    for key in ("regla", "como_se_arma", "decision_del_grupo"):
        with pytest.raises(ValueError, match=key):
            save_decision(path, {k: v for k, v in decision.items() if k != key})


# --- Revisión del 2026-10-31 (revisor-de-codigo-ia y auditor-de-fuga) -------------------------------------------


def test_save_decision_keeps_native_types_and_rejects_infinity(tmp_path):
    path = tmp_path / "06_best_params.json"
    decision = _decision() | {"ensayos": np.int64(60), "comprobacion": {"mae": np.float64(38.5), "ok": np.bool_(True)}}
    save_decision(path, decision)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["ensayos"] == 60 and isinstance(loaded["ensayos"], int)  # no 60.0
    assert loaded["comprobacion"]["ok"] is True
    with pytest.raises(ValueError):
        save_decision(path, _decision() | {"ensayos": float("inf")})  # "Infinity" no es JSON válido


def test_construction_info_matches_make_model():
    """La etapa 7 debe armar el modelo igual que la optimización: con subsample_freq=1, o LightGBM ignora subsample."""
    info = construction_info("lightgbm")
    assert "make_model" in info["como_se_arma"]
    assert info["parametros_fijos"]["subsample_freq"] == 1
    model = make_model("lightgbm", {"subsample": 0.9})
    for key, value in info["parametros_fijos"].items():
        assert model.get_params()[key] == value


def test_choose_finalist_rule():
    seconds = {"a": 5.0, "b": 2.0}
    assert choose_finalist("a", "b", -0.5, -0.1, seconds)[0] == "a"  # A se equivoca menos en todo el intervalo
    assert choose_finalist("a", "b", 0.1, 0.5, seconds)[0] == "b"  # B se equivoca menos en todo el intervalo
    winner, reason = choose_finalist("a", "b", -0.2, 0.5, seconds)
    assert winner == "b" and "empate" in reason  # cruza el cero: el más rápido de ajustar
    assert choose_finalist("a", "b", -0.2, 0.0, seconds)[0] == "b"  # tocar el cero también es empate


def test_compare_on_reserved_fails_if_hosts_are_shared():
    data = make_train_rows(n_hosts=40)
    pipeline = build_pipeline(Ridge(), "linear")
    with pytest.raises(AssertionError, match="anfitriones"):
        compare_on_reserved(pipeline, pipeline, data.iloc[:50], data.iloc[30:], n=50)


def test_compare_on_reserved_with_two_different_models():
    data = make_train_rows(n_hosts=60)
    search, reserved = reserve_hosts(data)
    ridge, base = build_pipeline(Ridge(), "linear"), build_pipeline(BaselineRegressor(), "baseline")
    result = compare_on_reserved(ridge, base, search, reserved, n=200)
    X_search, y_search = feature_frame(search), search[TARGET]
    X_reserved, y_reserved = feature_frame(reserved), reserved[TARGET]
    mae_ridge = usd_metrics(y_reserved, clone(ridge).fit(X_search, y_search).predict(X_reserved))["mae"]
    mae_base = usd_metrics(y_reserved, clone(base).fit(X_search, y_search).predict(X_reserved))["mae"]
    assert (result["mae_a"], result["mae_b"]) == pytest.approx((mae_ridge, mae_base))
    assert result["mean_difference"] == pytest.approx(mae_ridge - mae_base)  # A − B
    assert result["low"] <= result["mean_difference"] <= result["high"]
    assert result["listings"] == len(reserved)


def test_host_bootstrap_ci_is_reproducible_with_the_same_seed():
    rng = np.random.default_rng(1)
    hosts, diff = np.repeat(np.arange(20), 2), rng.normal(size=40)
    assert host_bootstrap_ci(diff, hosts, n=200, seed=3) == host_bootstrap_ci(diff, hosts, n=200, seed=3)


def test_host_bootstrap_ci_fails_with_missing_hosts():
    with pytest.raises(ValueError, match="anfitrión"):
        host_bootstrap_ci([1.0, 1.0, 100.0], [1, 2, np.nan])  # sin el error, la fila de 100 desaparecería callada


def test_tune_raises_if_every_trial_fails(tmp_path):
    _local_mlflow(tmp_path, "prueba-todo-falla")
    X, y, folds = _search_data()
    with pytest.raises(RuntimeError, match="amenities"):
        tune("ridge", X.drop(columns=["amenities"]), y, folds, n_trials=2, ideas=(2,))


@pytest.mark.parametrize("name", ["lightgbm", "random_forest"])
def test_tune_runs_each_finalist(tmp_path, name):
    _local_mlflow(tmp_path, f"prueba-{name}")
    X, y, folds = _search_data()
    study = tune(name, X, y, folds, n_trials=1)
    assert study.trials[0].state == optuna.trial.TrialState.COMPLETE


def test_tune_without_logging_registers_nothing(tmp_path):
    _local_mlflow(tmp_path, "prueba-sin-registro")
    X, y, folds = _search_data()
    tune("ridge", X, y, folds, n_trials=1, log=False)
    assert len(mlflow.search_runs(experiment_names=["prueba-sin-registro"])) == 0


def test_starting_params_are_the_tournament_configuration():
    assert starting_params("lightgbm") == {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31}
    assert starting_params("random_forest") == {"n_estimators": 200, "min_samples_leaf": 3, "max_features": 0.5}
    assert starting_params("ridge") == {"alpha": 1.0}
