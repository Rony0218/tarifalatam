"""Pruebas de la etapa 7 (src/tarifalatam/models/validation.py), con datos de juguete: ninguna lee la prueba real."""
import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMRegressor
from sklearn.base import BaseEstimator, RegressorMixin

from fixtures import make_train_rows
from tarifalatam.config import GROUP_COL
from tarifalatam.data.folds import reserve_hosts
from tarifalatam.models.train import build_pipeline, feature_frame
from tarifalatam.models.validation import (
    asymmetric_cost,
    check_log_correction,
    mae_with_ci,
    oof_log_predictions,
    open_test,
    paired_mae_difference,
    price_range_ratios,
    segment_errors,
    smearing_factor,
    success_goal,
    test_metrics,
    to_usd_price,
)

# pytest no debe tratar a la función test_metrics como una prueba
test_metrics.__test__ = False


# --- open_test y to_usd_price ------------------------------------------------------------------------------------

def _toy_test_file(folder):
    path = folder / "test.csv.gz"
    pd.DataFrame({"id": [1, 2], "host_id": [10, 11]}).to_csv(path, index=False)
    return path


def test_open_test_first_read_writes_the_mark(tmp_path):
    mark = tmp_path / "prueba_abierta.txt"
    frame = open_test(_toy_test_file(tmp_path), mark_path=mark, purpose="evaluación única")
    assert len(frame) == 2
    lines = mark.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("Primera apertura:") and "evaluación única" in lines[0]


def test_open_test_second_read_appends_and_warns(tmp_path):
    mark = tmp_path / "prueba_abierta.txt"
    path = _toy_test_file(tmp_path)
    open_test(path, mark_path=mark, purpose="evaluación única")
    with pytest.warns(UserWarning, match="ya se había abierto"):
        open_test(path, mark_path=mark, purpose="comprobar el modelo exportado")
    lines = mark.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("Primera apertura:")
    assert lines[1].startswith("Nueva lectura:") and "comprobar el modelo exportado" in lines[1]


def test_open_test_rejects_a_file_that_is_not_the_test_set(tmp_path):
    path = tmp_path / "train.csv.gz"
    pd.DataFrame({"id": [1]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="no es la prueba"):
        open_test(path, mark_path=tmp_path / "marca.txt", purpose="x")
    assert not (tmp_path / "marca.txt").exists()


def test_open_test_requires_a_purpose(tmp_path):
    with pytest.raises(ValueError, match="propósito"):
        open_test(_toy_test_file(tmp_path), mark_path=tmp_path / "marca.txt", purpose="  ")


def test_to_usd_price_applies_exp_and_factor():
    assert to_usd_price(np.log([100.0]), 1.1)[0] == pytest.approx(110.0)
    assert to_usd_price(np.log([50.0]))[0] == pytest.approx(50.0)


# --- factor del logaritmo ------------------------------------------------------------------------------------------

def test_smearing_factor_is_one_with_zero_residuals():
    assert smearing_factor(np.zeros(5)) == pytest.approx(1.0)


def test_smearing_factor_hand_case():
    assert smearing_factor([np.log(2.0), 0.0]) == pytest.approx(1.5)


class _HostMemorizer(RegressorMixin, BaseEstimator):
    """Predice 1 si vio al anfitrión de la fila al ajustar y 0 si no (para comprobar que no hay fuga)."""

    def fit(self, X, y):
        self.hosts_ = set(X[GROUP_COL])
        return self

    def predict(self, X):
        return np.array([1.0 if host in self.hosts_ else 0.0 for host in X[GROUP_COL]])


def test_oof_predictions_never_come_from_a_model_that_saw_the_host():
    train = make_train_rows(n_hosts=30)
    X = feature_frame(train)
    oof = oof_log_predictions(_HostMemorizer(), X, train["log_price_usd"], train[GROUP_COL])
    assert len(oof) == len(train)
    assert np.all(oof == 0.0)


@pytest.fixture(scope="module")
def small_lgbm():
    model = LGBMRegressor(n_estimators=30, num_leaves=7, min_child_samples=3, random_state=0, verbose=-1)
    return build_pipeline(model, "boosting")


def test_check_log_correction_applies_the_written_rule(small_lgbm):
    search, reserved = reserve_hosts(make_train_rows(n_hosts=120))
    result = check_log_correction(small_lgbm, search, reserved, n=200)
    assert result["factor"] > 0
    assert result["low"] <= result["media"] <= result["high"]
    assert result["se_usa"] == (result["high"] < 0)
    assert len(result["pred_reserved_log"]) == len(reserved)


# --- rango típico y costo asimétrico -------------------------------------------------------------------------------

def test_price_range_ratios_by_city():
    ratios = np.array([0.8, 0.9, 1.0, 1.1, 1.2])
    cities = ["bogota"] * 5 + ["belize"] * 5
    pred = np.full(10, 100.0)
    true = np.concatenate([100 * ratios, 100 * ratios * 2])
    result = price_range_ratios(cities, true, pred)
    assert result["bogota"] == pytest.approx([0.9, 1.1])
    assert result["belize"] == pytest.approx([1.8, 2.2])
    low, high = result["bogota"]
    assert low * 100 <= 100 <= high * 100  # con mediana de la razón 1, el sugerido queda dentro del rango


def test_asymmetric_cost_hand_case():
    # sobrestimar 10 USD cuesta 20; subestimar 10 USD cuesta 10
    assert asymmetric_cost([100.0, 100.0], [110.0, 90.0], over=2.0, under=1.0) == pytest.approx(15.0)
    assert asymmetric_cost([100.0], [110.0], over=3.0, under=1.0) == pytest.approx(30.0)


# --- métricas, intervalos, segmentos y meta -----------------------------------------------------------------------

def test_test_metrics_includes_the_three_costs():
    true_log = np.log([100.0, 100.0])
    pred_log = np.log([110.0, 90.0])
    metrics = test_metrics(true_log, pred_log)
    assert metrics["mae"] == pytest.approx(10.0)
    assert metrics["cost_2_1"] == pytest.approx(15.0)
    assert metrics["cost_1.5_1"] == pytest.approx(12.5)
    assert metrics["cost_3_1"] == pytest.approx(20.0)


def test_test_metrics_uses_the_factor():
    metrics = test_metrics(np.log([110.0]), np.log([100.0]), factor=1.1)
    assert metrics["mae"] == pytest.approx(0.0, abs=1e-9)


def test_mae_with_ci_and_constant_difference():
    true_log = np.log(np.full(40, 100.0))
    hosts = np.repeat(np.arange(20), 2)
    worse = np.log(np.full(40, 115.0))  # error 15
    better = np.log(np.full(40, 110.0))  # error 10
    ci = mae_with_ci(true_log, worse, hosts, n=200)
    assert ci["mae"] == pytest.approx(15.0) and ci["low"] == pytest.approx(15.0) and ci["high"] == pytest.approx(15.0)
    diff = paired_mae_difference(true_log, worse, better, hosts, n=200)
    assert diff["mean"] == pytest.approx(5.0) and diff["low"] == pytest.approx(5.0) and diff["high"] == pytest.approx(5.0)


def test_segment_errors_hand_case():
    frame = pd.DataFrame({"city": ["a", "a", "b"], "price_usd": [100.0, 100.0, 50.0], "pred_usd": [110.0, 40.0, 50.0]})
    table = segment_errors(frame, "city").set_index("city")
    a = table.loc["a"]
    assert a["n"] == 2
    assert a["mae"] == pytest.approx(35.0)
    assert a["mape"] == pytest.approx(35.0)
    assert a["bias"] == pytest.approx(-25.0)
    assert a["pct_over"] == pytest.approx(50.0)
    assert a["n_error_over_half"] == 1
    assert table.loc["b", "mae"] == pytest.approx(0.0)


def _cities(model_maes, baseline_maes):
    return pd.DataFrame({"city": ["x", "y"], "mae_model": model_maes, "mae_baseline": baseline_maes})


def test_success_goal_passes_with_the_three_conditions():
    goal = success_goal(80.0, 100.0, -1.0, _cities([30.0, 60.0], [40.0, 60.0]))
    assert goal["a_20pct"] and goal["b_intervalo"] and goal["c_ciudades"] and goal["cumple"]
    assert goal["ciudades_peores"] == []
    assert goal["mejora_pct"] == pytest.approx(20.0)


@pytest.mark.parametrize(
    "model_mae, diff_high, model_cities, failed",
    [
        (81.0, -1.0, [30.0, 60.0], "a_20pct"),  # 19 % de mejora
        (70.0, 0.0, [30.0, 60.0], "b_intervalo"),  # el intervalo toca el cero
        (70.0, -1.0, [30.0, 61.0], "c_ciudades"),  # una ciudad peor que la línea base
    ],
)
def test_success_goal_fails_each_condition(model_mae, diff_high, model_cities, failed):
    goal = success_goal(model_mae, 100.0, diff_high, _cities(model_cities, [40.0, 60.0]))
    assert not goal[failed]
    assert not goal["cumple"]
    if failed == "c_ciudades":
        assert goal["ciudades_peores"] == ["y"]


def test_segment_errors_leaves_non_positive_prices_out_of_the_mape():
    frame = pd.DataFrame({"city": ["a", "a"], "price_usd": [0.0, 100.0], "pred_usd": [10.0, 110.0]})
    row = segment_errors(frame, "city").iloc[0]
    assert row["mae"] == pytest.approx(10.0)
    assert row["mape"] == pytest.approx(10.0)  # solo el anuncio con precio positivo


def test_success_goal_needs_a_positive_baseline():
    with pytest.raises(ValueError, match="positivo"):
        success_goal(10.0, 0.0, -1.0, _cities([1.0, 1.0], [1.0, 1.0]))
