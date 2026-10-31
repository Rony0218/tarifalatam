"""Candidatos, Pipeline completo, métricas en USD y evaluación con los pliegues por anfitrión.

Todos los modelos aprenden log(price_usd); las métricas se calculan en USD con la exponencial de la predicción,
sin corrección de retransformación: exp de la predicción en logaritmo se acerca a la mediana del precio, que es lo
que premia el MAE (especificaciones/04-features-torneo-optimizacion.md, sección 0).

Las reglas de decisión que el grupo aprobó antes de medir también están aquí, como funciones probadas:
improvement_over_noise y keep_idea (etapa 4) y compare (etapa 5).
"""
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler, TargetEncoder

from tarifalatam.config import NIGHTS_SCALE, RANDOM_STATE, TARGET_COLUMNS
from tarifalatam.features.columns import check_feature_columns, feature_columns
from tarifalatam.features.engineering import (
    AmenityFeatures,
    CapacityRatios,
    CityCenterDistance,
    HostProfile,
    RareCategoryGrouper,
    SuspiciousFeatures,
)
from tarifalatam.models.baseline import MedianBaseline

# Familias de preprocesamiento (research.md, punto 5): mismas columnas de entrada, distinta preparación
FAMILIES = ("baseline", "linear", "forest", "boosting")

# Transformadores de las ideas 1 a 4 (la 5 es el TargetEncoder del ColumnTransformer)
IDEA_TRANSFORMERS = {1: CityCenterDistance, 2: AmenityFeatures, 3: CapacityRatios, 4: HostProfile}


class BaselineRegressor(RegressorMixin, BaseEstimator):
    """La línea base de H1 (mediana por ciudad × room_type) con la interfaz de los demás modelos.

    Recibe el objetivo en logaritmo y devuelve el logaritmo de la mediana en USD. Usa MedianBaseline sin cambiarlo:
    la predicción en USD es la misma que en H1.
    """

    def fit(self, X: pd.DataFrame, y):
        frame = X[["city", "room_type"]].copy()
        frame["price_usd"] = np.exp(np.asarray(y, dtype=float))
        self.baseline_ = MedianBaseline().fit(frame)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.log(self.baseline_.predict(X))


def candidates(random_state: int = RANDOM_STATE) -> dict:
    """Los cuatro candidatos del torneo con su configuración de partida, sin optimizar (sección 5.1 de la etapa).

    Devuelve {nombre: (estimador, familia)}. El LightGBM es también el modelo fijo con que se miden las variables.
    """
    return {
        "linea_base": (BaselineRegressor(), "baseline"),
        "ridge": (Ridge(alpha=1.0), "linear"),
        "random_forest": (
            RandomForestRegressor(
                n_estimators=200, min_samples_leaf=3, max_features=0.5, n_jobs=-1, random_state=random_state
            ),
            "forest",
        ),
        "lightgbm": (
            LGBMRegressor(
                n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=random_state, n_jobs=-1, verbose=-1
            ),
            "boosting",
        ),
    }


def _ordinal() -> OrdinalEncoder:
    return OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)


def _preprocessor(columns: dict, family: str) -> ColumnTransformer:
    """Prepara cada tipo de columna según la familia del modelo (data-model.md, sección 3).

    remainder="drop": cualquier columna que no esté en la lista (el precio, los id) se descarta.
    """
    if family == "linear":
        encode = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
        binary = SimpleImputer(strategy="most_frequent")
    elif family == "forest":
        encode = _ordinal()
        numeric = SimpleImputer(strategy="median")
        binary = SimpleImputer(strategy="most_frequent")
    else:  # boosting: LightGBM maneja los vacíos, no se imputa
        encode = _ordinal()
        numeric = "passthrough"
        binary = "passthrough"
    transformers = [
        ("categorical", Pipeline([("rare", RareCategoryGrouper()), ("encode", encode)]), columns["categorical"]),
        ("numeric", numeric, columns["numeric"]),
        ("binary", binary, columns["binary"]),
    ]
    if columns["target_encoded"]:
        # Idea 5. La validación cruzada interna hace que, al ajustar, ninguna fila vea su propio precio. En
        # scikit-learn 1.9 shuffle y random_state de TargetEncoder están obsoletos: se pasa un KFold en cv
        encoder = TargetEncoder(target_type="continuous", cv=KFold(5, shuffle=True, random_state=RANDOM_STATE))
        if family == "linear":
            encoder = Pipeline([("encode", encoder), ("scale", StandardScaler())])
        transformers.append(("neighbourhood_price_level", encoder, columns["target_encoded"]))
    return ColumnTransformer(transformers, remainder="drop")


def build_pipeline(model, family: str, ideas=(), with_suspicious: bool = False) -> Pipeline:
    """Pipeline completo: variables de las ideas -> preprocesamiento -> modelo. Se ajusta y se guarda entero.

    Revisa que ninguna columna pedida esté prohibida (ni sospechosa, salvo with_suspicious=True). La familia
    "baseline" no usa preprocesamiento: la línea base solo mira city y room_type.
    """
    if family not in FAMILIES:
        raise ValueError(f"No existe la familia de modelo {family!r}. Opciones: {FAMILIES}")
    if family == "baseline":
        return Pipeline([("model", clone(model))])
    columns = feature_columns(ideas, with_suspicious)
    check_feature_columns([col for group in columns.values() for col in group], allow_suspicious=with_suspicious)
    steps = [(f"idea_{idea}", IDEA_TRANSFORMERS[idea]()) for idea in sorted(ideas) if idea in IDEA_TRANSFORMERS]
    if with_suspicious:
        steps.append(("suspicious", SuspiciousFeatures()))
    steps += [("prep", _preprocessor(columns, family)), ("model", clone(model))]
    return Pipeline(steps)


def feature_frame(train: pd.DataFrame) -> pd.DataFrame:
    """Quita el objetivo en sus tres escalas. Conserva id y host_id (para unir pliegues), que el Pipeline descarta."""
    return train.drop(columns=TARGET_COLUMNS)


def usd_metrics(y_true_log, y_pred_log) -> dict:
    """MAE, MAPE (%), RMSE y sesgo en USD por noche, y R² sobre el logaritmo.

    Sesgo = promedio de (predicho − real): positivo significa que sobrestima, el error más caro para el inversionista.
    """
    y_true_log = np.asarray(y_true_log, dtype=float)
    y_pred_log = np.asarray(y_pred_log, dtype=float)
    true, error = np.exp(y_true_log), np.exp(y_pred_log) - np.exp(y_true_log)
    return {
        "mae": float(np.mean(np.abs(error))),
        "mape": float(np.mean(np.abs(error) / true) * 100),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "bias": float(np.mean(error)),
        "r2_log": float(r2_score(y_true_log, y_pred_log)),
    }


def evaluate_folds(pipeline, X: pd.DataFrame, y_log, folds) -> tuple:
    """Ajusta una copia del Pipeline en cada pliegue dado y mide en sus anuncios de validación.

    Devuelve (tabla con una fila por pliegue: métricas y segundos de ajuste, predicciones fuera de pliegue en
    logaritmo). Con las predicciones se calcula el error por ciudad sin volver a ajustar.
    """
    y_log = np.asarray(y_log, dtype=float)
    oof = np.full(len(X), np.nan)
    rows = []
    for fold, (fit_idx, valid_idx) in enumerate(folds):
        model = clone(pipeline)
        start = time.perf_counter()
        model.fit(X.iloc[fit_idx], y_log[fit_idx])
        seconds = time.perf_counter() - start
        oof[valid_idx] = model.predict(X.iloc[valid_idx])
        rows.append({"fold": fold, **usd_metrics(y_log[valid_idx], oof[valid_idx]), "fit_seconds": seconds})
    return pd.DataFrame(rows), oof


def city_errors(cities, y_true_log, oof_log, folds) -> pd.DataFrame:
    """MAE y sesgo en USD de cada ciudad en cada pliegue de validación, con el número de anuncios."""
    cities = np.asarray(cities)
    error = np.exp(np.asarray(oof_log, dtype=float)) - np.exp(np.asarray(y_true_log, dtype=float))
    rows = []
    for fold, (_, valid_idx) in enumerate(folds):
        frame = pd.DataFrame({"city": cities[valid_idx], "error": error[valid_idx]})
        for city, group in frame.groupby("city"):
            rows.append(
                {"fold": fold, "city": city, "n": len(group), "mae": group["error"].abs().mean(), "bias": group["error"].mean()}
            )
    return pd.DataFrame(rows)


def improvement_over_noise(reference_mae, variant_mae) -> dict:
    """Mejora de una variante frente a la referencia, dividida por el ruido entre pliegues (guía, sección 1.3).

    mejora = MAE medio de la referencia − MAE medio de la variante (positivo: la variante es mejor);
    ruido = desviación estándar (ddof=1) del MAE de la variante entre pliegues. Cuenta también los pliegues que gana.
    """
    reference = np.asarray(reference_mae, dtype=float)
    variant = np.asarray(variant_mae, dtype=float)
    improvement = reference.mean() - variant.mean()
    noise = variant.std(ddof=1)
    return {
        "improvement": float(improvement),
        "noise": float(noise),
        "ratio": float(improvement / noise) if noise > 0 else np.inf,
        "folds_won": int((variant < reference).sum()),
    }


def keep_idea(ratio: float, known_at_prediction: bool) -> bool:
    """Regla escrita antes de medir: se conserva la idea solo si mejora / ruido > 1 y se conoce al predecir."""
    return bool(known_at_prediction and ratio > 1)


def compare(best, other) -> dict:
    """Comparación pliegue a pliegue entre dos modelos (guía, sección 2.4). Diferencia positiva: 'best' gana.

    El ruido es la desviación (ddof=1) de las diferencias pliegue a pliegue.
    """
    difference = np.asarray(other, dtype=float) - np.asarray(best, dtype=float)
    noise = difference.std(ddof=1)
    return {
        "mean_difference": float(difference.mean()),
        "folds_won": int((difference > 0).sum()),
        "difference_over_noise": float(difference.mean() / noise) if noise > 0 else np.inf,
    }


def value_per_nights(mae_difference: float, nights: int = NIGHTS_SCALE) -> float:
    """Diferencia de MAE (USD por noche) expresada en USD por cada 30 noches: una escala, no un pronóstico."""
    return float(mae_difference * nights)
