"""Pruebas del esquema y de la predicción del precio (regresión), con un LightGBM de juguete.

La última prueba usa el modelo real (`models/model.joblib`) y una fila real del entrenamiento; se salta si no existen.
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMRegressor

from fixtures import make_train_rows
from tarifalatam.config import REFERENCE_BINARY, REFERENCE_CATEGORICAL, REFERENCE_NUMERIC, TARGET, TRAIN_PATH, VALID_RANGE
from tarifalatam.inference.predict import InputValidationError, load_model, predict_price, validate_inputs
from tarifalatam.inference.schema import build_schema, load_schema
from tarifalatam.models.train import build_pipeline, feature_frame

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = REFERENCE_CATEGORICAL + REFERENCE_NUMERIC + REFERENCE_BINARY
RATIOS = {"rio-de-janeiro": [0.8, 1.2], "bogota": [0.75, 1.25], "belize": [0.7, 1.4]}


@pytest.fixture(scope="module")
def train() -> pd.DataFrame:
    df = make_train_rows(n_hosts=90)
    # En el juguete los barrios se repiten entre ciudades; aquí cada ciudad tiene los suyos
    df["neighbourhood_cleansed"] = df["city"] + " · " + df["neighbourhood_cleansed"]
    return df


@pytest.fixture(scope="module")
def model(train):
    lgbm = LGBMRegressor(n_estimators=30, num_leaves=7, min_child_samples=3, random_state=0, verbose=-1)
    return build_pipeline(lgbm, "boosting").fit(feature_frame(train), train[TARGET].to_numpy())


def make_schema(train, **overrides):
    options = dict(
        numeric=REFERENCE_NUMERIC, categorical=REFERENCE_CATEGORICAL, binary=REFERENCE_BINARY, valid_range=VALID_RANGE,
        correction_factor=1.0, price_range_ratios=RATIOS, city_warnings={"belize": "El error en Belice es mucho mayor."},
    )
    options.update(overrides)
    return build_schema(train, **options)


def first_row(train, **changes) -> pd.DataFrame:
    row = train[COLUMNS].head(1).copy()
    for column, value in changes.items():
        row[column] = row[column].astype(object)
        row.loc[row.index[0], column] = value
    return row


# --- esquema -------------------------------------------------------------------------------------------------------

def test_build_schema_saves_and_reloads(train, tmp_path):
    schema = make_schema(train, path=tmp_path / "input_schema.json")
    assert load_schema(tmp_path / "input_schema.json") == schema
    assert schema["required"] == ["city"]
    assert schema["valid_range"]["accommodates"] == [1.0, 16.0]
    assert schema["price_range_ratios"] == RATIOS
    assert "accommodates" in schema["integer_columns"]
    assert schema["most_frequent"]["room_type"] == train["room_type"].mode().iloc[0]


def test_schema_knows_the_neighbourhoods_of_each_city(train):
    schema = make_schema(train)
    for city, group in train.groupby("city"):
        assert schema["neighbourhoods_by_city"][city] == sorted(group["neighbourhood_cleansed"].unique())
        barrio = schema["neighbourhoods_by_city"][city][0]
        lat, lon = schema["neighbourhood_coords"][city][barrio]
        assert lat == pytest.approx(group.loc[group["neighbourhood_cleansed"] == barrio, "latitude"].median())
        assert lon == pytest.approx(group.loc[group["neighbourhood_cleansed"] == barrio, "longitude"].median())


def test_build_schema_rejects_missing_column(train):
    with pytest.raises(ValueError, match="accommodates"):
        make_schema(train.drop(columns=["accommodates"]))


def test_build_schema_needs_a_range_for_each_city(train):
    with pytest.raises(ValueError, match="belize"):
        make_schema(train, price_range_ratios={"bogota": [0.8, 1.2]})


# --- validación ----------------------------------------------------------------------------------------------------

def test_valid_row_has_no_errors_or_warnings(train):
    assert validate_inputs(first_row(train), make_schema(train)) == []


def test_impossible_value_is_refused_not_predicted(train, model):
    with pytest.raises(InputValidationError, match="accommodates"):
        predict_price(first_row(train, accommodates=40), model, make_schema(train))


def test_non_numeric_value_is_an_error(train):
    with pytest.raises(InputValidationError, match="accommodates"):
        validate_inputs(first_row(train, accommodates="dos"), make_schema(train))


def test_city_is_required_and_must_be_known(train):
    schema = make_schema(train)
    with pytest.raises(InputValidationError, match="ciudad"):
        validate_inputs(first_row(train, city=np.nan), schema)
    with pytest.raises(InputValidationError, match="madrid"):
        validate_inputs(first_row(train, city="madrid"), schema)


def test_neighbourhood_of_another_city_is_an_error(train):
    row = first_row(train)
    city = row["city"].iloc[0]
    other = next(c for c in train["city"].unique() if c != city)
    barrio = train.loc[train["city"] == other, "neighbourhood_cleansed"].iloc[0]
    with pytest.raises(InputValidationError, match="no pertenece"):
        validate_inputs(first_row(train, neighbourhood_cleansed=barrio), make_schema(train))


def test_missing_column_is_an_error_naming_it(train):
    with pytest.raises(InputValidationError, match="beds"):
        validate_inputs(first_row(train).drop(columns=["beds"]), make_schema(train))


def test_unseen_category_and_out_of_observed_range_are_warnings(train):
    schema = make_schema(train)
    warnings = validate_inputs(first_row(train, property_type="Castillo", accommodates=16), schema)
    assert any("property_type" in w for w in warnings)
    assert any("accommodates" in w for w in warnings)


def test_coordinates_far_from_the_city_are_a_warning(train):
    warnings = validate_inputs(first_row(train, latitude=0.0, longitude=0.0), make_schema(train))
    assert any("coordenadas" in w for w in warnings)


# --- predicción ----------------------------------------------------------------------------------------------------

def test_predict_price_returns_whole_dollars_and_a_range(train, model):
    result = predict_price(first_row(train), model, make_schema(train))
    first = result.iloc[0]
    for column in ("price_usd", "low_usd", "high_usd"):
        assert float(first[column]).is_integer()
    assert first["low_usd"] <= first["price_usd"] <= first["high_usd"]
    assert result.attrs["warnings"] == []


def test_predict_price_uses_the_city_range(train, model):
    row = first_row(train)
    city = row["city"].iloc[0]
    exact = math.exp(model.predict(row)[0])
    result = predict_price(row, model, make_schema(train)).iloc[0]
    assert result["price_usd"] == round(exact)
    assert result["low_usd"] == round(exact * RATIOS[city][0])
    assert result["high_usd"] == round(exact * RATIOS[city][1])


def test_missing_values_are_accepted(train, model):
    row = first_row(train, bathrooms_count=np.nan, property_type=np.nan, neighbourhood_cleansed=np.nan)
    result = predict_price(row, model, make_schema(train))
    assert result.iloc[0]["price_usd"] > 0


def test_city_warning_is_added(train, model):
    row = train.loc[train["city"] == "belize", COLUMNS].head(1)
    result = predict_price(row, model, make_schema(train))
    assert any("Belice" in w for w in result.attrs["warnings"])


def test_app_module_imports_without_launching_streamlit():
    pytest.importorskip("streamlit")
    spec = importlib.util.spec_from_file_location("app_streamlit", ROOT / "app" / "streamlit_app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # no ejecuta main(): solo importa
    assert callable(module.main) and module.UNKNOWN == "(no sé)"


# --- el modelo real ------------------------------------------------------------------------------------------------

REAL_MODEL, REAL_SCHEMA = ROOT / "models" / "model.joblib", ROOT / "models" / "input_schema.json"


@pytest.mark.skipif(not (REAL_MODEL.exists() and REAL_SCHEMA.exists() and TRAIN_PATH.exists()),
                    reason="hace falta models/model.joblib, models/input_schema.json y el entrenamiento")
def test_real_model_with_a_real_row():
    from tarifalatam.data.load import load_train

    model, schema = load_model(REAL_MODEL), load_schema(REAL_SCHEMA)
    row = load_train()[COLUMNS].head(1)
    result = predict_price(row, model, schema).iloc[0]
    assert 5 <= result["price_usd"] <= 5000
    assert result["low_usd"] <= result["high_usd"]
    with pytest.raises(InputValidationError):
        predict_price(row.assign(accommodates=40), model, schema)


# --- datos del mapa (solo entrenamiento) ---------------------------------------------------------------------------

def test_schema_has_the_median_price_of_each_neighbourhood(train):
    schema = make_schema(train, min_neighbourhood_count=5, city_mae={"bogota": 22.3})
    for (city, barrio), group in train.groupby(["city", "neighbourhood_cleansed"]):
        stored = schema["neighbourhood_price"].get(city, {}).get(barrio)
        if len(group) >= 5:
            assert stored == [pytest.approx(group["price_usd"].median()), len(group)]
        else:
            assert stored is None  # con pocos anuncios la mediana no es confiable: no se muestra
    for city, group in train.groupby("city"):
        assert schema["city_price"][city] == [pytest.approx(group["price_usd"].median()), len(group)]
    assert schema["city_mae"] == {"bogota": 22.3}


def test_schema_hides_neighbourhoods_with_few_listings(train):
    schema = make_schema(train, min_neighbourhood_count=10_000)
    assert all(barrios == {} for barrios in schema["neighbourhood_price"].values())
