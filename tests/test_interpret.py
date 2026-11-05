"""Pruebas de la interpretación con SHAP (src/tarifalatam/models/interpret.py), con un LightGBM de juguete."""
import numpy as np
import pytest
from lightgbm import LGBMRegressor

from fixtures import make_train_rows
from tarifalatam.config import REFERENCE_BINARY, REFERENCE_CATEGORICAL, REFERENCE_NUMERIC, TARGET
from tarifalatam.models.interpret import global_importance, shap_values, top_contributions
from tarifalatam.models.train import build_pipeline, feature_frame

REFERENCE = REFERENCE_CATEGORICAL + REFERENCE_NUMERIC + REFERENCE_BINARY


@pytest.fixture(scope="module")
def fitted():
    train = make_train_rows(n_hosts=60)
    X, y = feature_frame(train), train[TARGET].to_numpy()
    model = LGBMRegressor(n_estimators=40, num_leaves=7, min_child_samples=3, random_state=0, verbose=-1)
    return build_pipeline(model, "boosting").fit(X, y), X


def test_one_column_per_original_column(fitted):
    pipeline, X = fitted
    contributions = shap_values(pipeline, X.head(20))
    assert sorted(contributions.columns) == sorted(REFERENCE)
    assert len(contributions) == 20


def test_contributions_add_up_to_the_prediction(fitted):
    pipeline, X = fitted
    sample = X.head(20)
    contributions = shap_values(pipeline, sample)
    rebuilt = contributions.sum(axis=1).to_numpy() + contributions.attrs["base_value"]
    np.testing.assert_allclose(rebuilt, pipeline.predict(sample), atol=1e-6)


def test_global_importance_is_sorted(fitted):
    pipeline, X = fitted
    table = global_importance(shap_values(pipeline, X))
    assert list(table.columns) == ["columna", "importancia"]
    assert len(table) == len(REFERENCE)
    assert table["importancia"].is_monotonic_decreasing
    assert (table["importancia"] >= 0).all()


def test_top_contributions_returns_k_rows(fitted):
    pipeline, X = fitted
    contributions = shap_values(pipeline, X.head(10))
    top = top_contributions(contributions, row=3, k=5)
    assert len(top) == 5
    assert top["aporte"].abs().is_monotonic_decreasing
