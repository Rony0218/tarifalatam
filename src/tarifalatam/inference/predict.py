"""Inferencia: validar las entradas y sugerir el precio por noche en USD, con su rango típico.

Contrato (specs/003-validacion-registro-app/data-model.md, secciones 4 y 5):
  - Entrada: una tabla con las 13 columnas CRUDAS que una persona conoce (las del esquema). La ciudad es obligatoria; lo
    demás puede venir vacío («No sé»): el Pipeline del modelo trata los vacíos y las categorías desconocidas.
  - Salida: `price_usd` (redondeado al dólar), `low_usd` y `high_usd` (el rango típico de su ciudad) y `city`.
    Las advertencias quedan en `resultado.attrs["warnings"]`.
  - Nunca devuelve un precio con datos imposibles: lanza `InputValidationError` con un mensaje que dice qué corregir.

Uso:

    from tarifalatam.inference.predict import load_model, predict_price
    from tarifalatam.inference.schema import load_schema
    model, schema = load_model("models/model.joblib"), load_schema("models/input_schema.json")
    resultado = predict_price(filas_nuevas, model, schema)
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from tarifalatam.models.price import to_usd_price


class InputValidationError(ValueError):
    """Los datos de entrada no son válidos; el mensaje dice qué corregir."""


def load_model(path: str | Path):
    """Carga el modelo exportado (un Pipeline completo, con el preprocesamiento adentro)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}. Ejecuta antes el notebook 09_inferencia para exportarlo.")
    return joblib.load(path)


def _label(schema: dict, column: str) -> str:
    return f"{schema.get('labels', {}).get(column, column)} ({column})"


def _unique(messages: list[str]) -> list[str]:
    return list(dict.fromkeys(messages))


def validate_inputs(df: pd.DataFrame, schema: dict) -> list[str]:
    """Valida columnas, ciudad, números, rangos posibles y barrio. Lanza InputValidationError si hay errores; devuelve
    advertencias (categoría no vista, fuera de lo observado, coordenadas lejos de la ciudad)."""
    numbers = schema["numeric"] + schema["binary"]
    missing = [c for c in schema["categorical"] + numbers if c not in df.columns]
    if missing:
        raise InputValidationError(f"Faltan columnas: {', '.join(missing)}")

    errors, warnings = [], []
    known_cities = set(schema["categories"]["city"])
    if df["city"].isna().any():
        errors.append("Falta la ciudad (city): es obligatoria")
    unknown_cities = sorted(set(df["city"].dropna().astype(str)) - known_cities)
    if unknown_cities:
        errors.append(f"Ciudad desconocida (city): {', '.join(unknown_cities)}. El modelo solo conoce: {', '.join(sorted(known_cities))}")

    values = {}
    for col in numbers:
        values[col] = pd.to_numeric(df[col], errors="coerce")
        if (values[col].isna() & df[col].notna()).any():
            errors.append(f"{_label(schema, col)}: hay valores que no son números")
        if col in schema.get("valid_range", {}):
            low, high = schema["valid_range"][col]
            if (values[col].notna() & ~values[col].between(low, high)).any():
                errors.append(f"{_label(schema, col)}: debe estar entre {low:g} y {high:g}")

    by_city = schema["neighbourhoods_by_city"]
    all_barrios = {b for barrios in by_city.values() for b in barrios}
    for city, barrio in zip(df["city"], df["neighbourhood_cleansed"]):
        if pd.isna(city) or pd.isna(barrio) or str(city) not in by_city:
            continue
        if str(barrio) not in by_city[str(city)] and str(barrio) in all_barrios:
            city_name = schema.get("city_labels", {}).get(str(city), str(city))
            errors.append(f"El barrio '{barrio}' no pertenece a {city_name} (neighbourhood_cleansed)")
    if errors:
        raise InputValidationError("; ".join(_unique(errors)))

    for col, known in schema.get("categories", {}).items():
        if col == "city":
            continue
        unseen = sorted(set(df[col].dropna().astype(str)) - set(known))
        if unseen:
            warnings.append(f"{_label(schema, col)}: categoría no vista en el entrenamiento ({', '.join(unseen)})")
    for col, (low, high) in schema.get("observed_range", {}).items():
        if ((values[col] < low) | (values[col] > high)).any():
            warnings.append(f"{_label(schema, col)}: fuera de lo visto en el entrenamiento ({low:g} a {high:g})")
    for city, lat, lon in zip(df["city"], values["latitude"], values["longitude"]):
        box = schema.get("city_box", {}).get(str(city))
        if box is None or pd.isna(lat) or pd.isna(lon):
            continue
        if not (box[0] <= lat <= box[1] and box[2] <= lon <= box[3]):
            city_name = schema.get("city_labels", {}).get(str(city), str(city))
            warnings.append(f"Las coordenadas quedan fuera de la zona de {city_name} vista en los datos")
    return _unique(warnings)


def predict_price(df: pd.DataFrame, model, schema: dict) -> pd.DataFrame:
    """Sugiere el precio por noche. Una fila de salida por fila de entrada: price_usd, low_usd, high_usd y city."""
    warnings = validate_inputs(df, schema)
    numbers = schema["numeric"] + schema["binary"]
    X = df[schema["categorical"] + numbers].copy()
    for col in numbers:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    for col in schema["categorical"]:
        X[col] = X[col].astype(object).where(X[col].notna(), np.nan)

    exact = to_usd_price(model.predict(X), schema.get("correction_factor", 1.0))
    ratios = np.array([schema["price_range_ratios"][str(city)] for city in df["city"]], dtype=float)
    out = pd.DataFrame(
        {
            "city": df["city"].astype(str).to_numpy(),
            "price_usd": np.round(exact).astype(int),
            "low_usd": np.round(exact * ratios[:, 0]).astype(int),
            "high_usd": np.round(exact * ratios[:, 1]).astype(int),
        },
        index=df.index,
    )
    for city in out["city"].unique():
        if city in schema.get("city_warnings", {}):
            warnings.append(schema["city_warnings"][city])
    out.attrs["warnings"] = _unique(warnings)
    return out
