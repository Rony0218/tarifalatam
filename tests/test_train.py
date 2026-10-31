import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMRegressor
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import Ridge
from sklearn.utils.validation import check_is_fitted

from fixtures import make_train_rows
from tarifalatam.config import FORBIDDEN_FEATURES, TARGET, TARGET_COLUMNS
from tarifalatam.data.folds import fold_indices, make_folds
from tarifalatam.models import train as train_module
from tarifalatam.models.baseline import MedianBaseline
from tarifalatam.models.train import (
    BaselineRegressor,
    build_pipeline,
    candidates,
    city_errors,
    compare,
    evaluate_folds,
    feature_frame,
    improvement_over_noise,
    keep_idea,
    usd_metrics,
    value_per_nights,
)

# --- Métricas y regla de decisión (T024) -----------------------------------------------------------------------


def test_usd_metrics_perfect_prediction():
    y = np.log([100.0, 200.0, 50.0])
    metrics = usd_metrics(y, y)
    assert metrics["mae"] == pytest.approx(0.0)
    assert metrics["bias"] == pytest.approx(0.0)
    assert metrics["mape"] == pytest.approx(0.0)
    assert metrics["rmse"] == pytest.approx(0.0)
    assert metrics["r2_log"] == pytest.approx(1.0)


def test_usd_metrics_hand_case():
    true = np.log([100.0, 200.0])
    under = usd_metrics(true, np.log([110.0, 180.0]))  # errores +10 y -20 USD
    assert under["mae"] == pytest.approx(15.0)
    assert under["bias"] == pytest.approx(-5.0)  # en promedio subestima
    assert under["mape"] == pytest.approx(10.0)  # (10 % + 10 %) / 2
    assert under["rmse"] == pytest.approx(np.sqrt(250.0))
    over = usd_metrics(true, np.log([110.0, 220.0]))  # errores +10 y +20 USD
    assert over["bias"] == pytest.approx(15.0)  # positivo: sobrestima, lo más caro para el inversionista


def test_improvement_over_noise_hand_case():
    result = improvement_over_noise([10, 10, 10, 10, 10], [8, 9, 8, 9, 8])
    assert result["improvement"] == pytest.approx(1.6)
    assert result["noise"] == pytest.approx(np.sqrt(0.3))  # desviación con ddof=1 de la variante
    assert result["ratio"] == pytest.approx(1.6 / np.sqrt(0.3))
    assert result["folds_won"] == 5


def test_improvement_over_noise_without_noise_is_infinite():
    assert improvement_over_noise([10, 10, 10], [9, 9, 9])["ratio"] == np.inf


def test_keep_idea_rule():
    assert keep_idea(1.3, known_at_prediction=True)
    assert not keep_idea(0.8, known_at_prediction=True)
    assert not keep_idea(1.3, known_at_prediction=False)
    assert not keep_idea(1.0, known_at_prediction=True)  # "mayor que 1", no "mayor o igual"


# --- Línea base y candidatos (T026) ----------------------------------------------------------------------------


def _baseline_train() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city": ["belize", "belize", "belize", "rio-de-janeiro", "rio-de-janeiro"],
            "room_type": ["Entire home/apt", "Entire home/apt", "Private room", "Entire home/apt", "Entire home/apt"],
            "price_usd": [100.0, 300.0, 50.0, 80.0, 120.0],
        }
    )


def test_baseline_regressor_matches_median_baseline_in_usd():
    data = _baseline_train()
    new = pd.DataFrame(
        {
            "city": ["belize", "belize", "rio-de-janeiro", "rio-de-janeiro", "santiago"],
            "room_type": ["Entire home/apt", "Private room", "Entire home/apt", "Hotel room", "Entire home/apt"],
        }
    )
    adapter = BaselineRegressor().fit(data[["city", "room_type"]], np.log(data["price_usd"]))
    expected = MedianBaseline().fit(data).predict(new)  # [200, 50, 100, 100 (ciudad), 100 (general)]
    assert np.exp(adapter.predict(new)) == pytest.approx(expected)


def test_candidates_are_the_four_approved_models():
    models = candidates()
    assert list(models) == ["linea_base", "ridge", "random_forest", "lightgbm"]
    assert [family for _, family in models.values()] == ["baseline", "linear", "forest", "boosting"]
    assert models["ridge"][0].get_params()["alpha"] == 1.0
    forest = models["random_forest"][0].get_params()
    assert (forest["n_estimators"], forest["min_samples_leaf"], forest["max_features"]) == (200, 3, 0.5)
    lgbm = models["lightgbm"][0].get_params()
    assert (lgbm["n_estimators"], lgbm["learning_rate"], lgbm["num_leaves"]) == (300, 0.05, 31)
    assert forest["random_state"] == lgbm["random_state"] == 42


# --- Pipeline (T028) -------------------------------------------------------------------------------------------

SMALL_MODELS = {
    "linear": Ridge(),
    "forest": RandomForestRegressor(n_estimators=5, random_state=0),
    "boosting": LGBMRegressor(n_estimators=10, min_child_samples=2, verbose=-1, random_state=0),
}


def test_build_pipeline_rejects_a_forbidden_column(monkeypatch):
    def with_target(ideas=(), with_suspicious=False):
        return {"categorical": ["city"], "numeric": ["accommodates", "price_usd"], "binary": [], "target_encoded": []}

    monkeypatch.setattr(train_module, "feature_columns", with_target)
    with pytest.raises(ValueError, match="price_usd"):
        build_pipeline(Ridge(), "linear")


def test_pipeline_ignores_target_and_ids():
    """Aunque la tabla traiga el precio y los identificadores (que predicen perfecto), el modelo no los usa."""
    data = make_train_rows()
    data["id"] = data["price_usd"]  # ahora también el id "contiene" el precio
    data["host_id"] = data["price_usd"].round()
    pipeline = build_pipeline(Ridge(), "linear", ideas=(1, 2, 3, 4, 5)).fit(data, data[TARGET])
    used = {name.split("__", 1)[1] for name in pipeline.named_steps["prep"].get_feature_names_out()}
    assert not used & set(FORBIDDEN_FEATURES)


@pytest.mark.parametrize("family", ["linear", "forest", "boosting"])
@pytest.mark.parametrize("ideas", [(), (1,), (2,), (3,), (4,), (5,), (1, 2, 3, 4, 5)])
def test_build_pipeline_fits_each_family_with_each_idea(family, ideas):
    data = make_train_rows()
    pipeline = build_pipeline(SMALL_MODELS[family], family, ideas=ideas).fit(feature_frame(data), data[TARGET])
    assert np.isfinite(pipeline.predict(feature_frame(data))).all()


def test_build_pipeline_with_suspicious_columns_fits():
    data = make_train_rows()
    pipeline = build_pipeline(SMALL_MODELS["boosting"], "boosting", with_suspicious=True)
    assert np.isfinite(pipeline.fit(data, data[TARGET]).predict(data)).all()


def test_build_pipeline_baseline_family():
    data = make_train_rows()
    pipeline = build_pipeline(BaselineRegressor(), "baseline").fit(feature_frame(data), data[TARGET])
    assert np.isfinite(pipeline.predict(feature_frame(data))).all()


def test_idea_5_is_a_target_encoding_inside_the_pipeline():
    data = make_train_rows()
    pipeline = build_pipeline(Ridge(), "linear", ideas=(5,)).fit(data, data[TARGET])
    names = list(pipeline.named_steps["prep"].get_feature_names_out())
    assert "neighbourhood_price_level__neighbourhood_cleansed" in names


def test_unknown_family_raises():
    with pytest.raises(ValueError, match="familia"):
        build_pipeline(Ridge(), "red_neuronal")


def test_feature_frame_drops_target_columns():
    data = make_train_rows()
    frame = feature_frame(data)
    assert not set(TARGET_COLUMNS) & set(frame.columns)
    assert {"id", "host_id"} <= set(frame.columns)  # se conservan para unir pliegues; el Pipeline no los usa
    assert len(frame.columns) == 62


# --- Evaluación por pliegue (T030) -----------------------------------------------------------------------------


def _folds(data):
    return fold_indices(data, make_folds(data))


def test_evaluate_folds_returns_one_row_per_fold():
    data = make_train_rows()
    table, oof = evaluate_folds(build_pipeline(Ridge(), "linear"), feature_frame(data), data[TARGET], _folds(data))
    assert list(table["fold"]) == [0, 1, 2, 3, 4]
    assert {"mae", "mape", "rmse", "bias", "r2_log", "fit_seconds"} <= set(table.columns)
    assert len(oof) == len(data) and np.isfinite(oof).all()


def test_evaluate_folds_uses_exactly_the_given_folds():
    data = make_train_rows()
    X, y, folds = feature_frame(data), data[TARGET].to_numpy(), _folds(data)
    pipeline = build_pipeline(Ridge(), "linear")
    _, oof = evaluate_folds(pipeline, X, y, folds)
    fit_idx, valid_idx = folds[2]
    by_hand = clone(pipeline).fit(X.iloc[fit_idx], y[fit_idx]).predict(X.iloc[valid_idx])
    assert oof[valid_idx] == pytest.approx(by_hand)  # cada predicción sale de un modelo que no vio esa fila


def test_evaluate_folds_leaves_the_original_pipeline_unfitted():
    data = make_train_rows()
    pipeline = build_pipeline(Ridge(), "linear")
    evaluate_folds(pipeline, feature_frame(data), data[TARGET], _folds(data))
    with pytest.raises(NotFittedError):
        check_is_fitted(pipeline)


# --- Funciones del torneo (T036) -------------------------------------------------------------------------------


def test_city_errors_hand_case():
    true = np.log([100.0, 100.0, 200.0, 200.0])
    oof = np.log([110.0, 90.0, 220.0, 200.0])
    folds = [(np.array([1, 3]), np.array([0, 2])), (np.array([0, 2]), np.array([1, 3]))]
    table = city_errors(["a", "a", "b", "b"], true, oof, folds).set_index(["fold", "city"])
    assert table.loc[(0, "a"), "mae"] == pytest.approx(10.0)
    assert table.loc[(0, "b"), "bias"] == pytest.approx(20.0)
    assert table.loc[(1, "a"), "bias"] == pytest.approx(-10.0)
    assert table.loc[(1, "b"), "mae"] == pytest.approx(0.0)
    assert table["n"].tolist() == [1, 1, 1, 1]


def test_compare_hand_case():
    result = compare(best=[10, 10, 10, 10, 10], other=[11, 12, 10, 13, 11])
    assert result["mean_difference"] == pytest.approx(1.4)
    assert result["folds_won"] == 4
    assert result["difference_over_noise"] == pytest.approx(1.4 / np.sqrt(1.3))


def test_value_per_nights():
    assert value_per_nights(2.5) == pytest.approx(75.0)
    assert value_per_nights(2.5, nights=10) == pytest.approx(25.0)


# --- Revisión del 2026-10-31 (revisor-de-codigo-ia y auditor-de-fuga) ------------------------------------------


def test_improvement_over_noise_without_noise_keeps_the_sign():
    worse = improvement_over_noise([10, 10, 10], [11, 11, 11])
    assert worse["ratio"] == -np.inf  # peor y sin ruido: nunca se conserva
    assert not keep_idea(worse["ratio"], known_at_prediction=True)
    assert improvement_over_noise([10, 10, 10], [10, 10, 10])["ratio"] == 0.0  # empate


def test_compare_without_noise_keeps_the_sign():
    assert compare(best=[11, 11, 11], other=[10, 10, 10])["difference_over_noise"] == -np.inf
    assert compare(best=[10, 10, 10], other=[11, 11, 11])["difference_over_noise"] == np.inf
    assert compare(best=[10, 10, 10], other=[10, 10, 10])["difference_over_noise"] == 0.0


def test_rare_categories_are_learned_inside_the_pipeline():
    data = make_train_rows(n_hosts=200)  # 399 anuncios: "Barrio Raro" tiene menos de 30
    pipeline = build_pipeline(Ridge(), "linear").fit(feature_frame(data), data[TARGET])
    rare = pipeline.named_steps["prep"].named_transformers_["categorical"].named_steps["rare"]
    assert rare.frequent_["city"] == {"rio-de-janeiro", "bogota", "belize"}
    assert {"Centro", "Norte", "Sur"} <= rare.frequent_["neighbourhood_cleansed"]
    assert "Barrio Raro" not in rare.frequent_["neighbourhood_cleansed"]


@pytest.mark.parametrize("family", ["linear", "forest", "boosting"])
def test_build_pipeline_handles_missing_values_in_the_reference(family):
    data = make_train_rows()
    for column in ("bedrooms", "beds", "bathrooms_count", "bathroom_shared"):
        data.loc[data.index[::7], column] = np.nan  # en los datos reales hay entre 0,1 % y 0,9 % de vacíos
    pipeline = build_pipeline(SMALL_MODELS[family], family, ideas=(3,)).fit(feature_frame(data), data[TARGET])
    assert np.isfinite(pipeline.predict(feature_frame(data))).all()


def test_build_pipeline_ignores_repeated_ideas():
    data = make_train_rows()
    pipeline = build_pipeline(Ridge(), "linear", ideas=(1, 1)).fit(feature_frame(data), data[TARGET])
    assert np.isfinite(pipeline.predict(feature_frame(data))).all()


def test_baseline_family_rejects_ideas_and_suspicious_columns():
    with pytest.raises(ValueError, match="línea base"):
        build_pipeline(BaselineRegressor(), "baseline", ideas=(1,))
    with pytest.raises(ValueError, match="línea base"):
        build_pipeline(BaselineRegressor(), "baseline", with_suspicious=True)
