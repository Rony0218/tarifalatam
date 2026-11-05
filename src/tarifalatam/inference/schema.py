"""Esquema de entrada del modelo de precio: qué columnas espera, qué es posible, qué conoce y cómo se entrega el precio.

El esquema es un archivo (`models/input_schema.json`) que viaja con el modelo. Lo usan `predict.py` (para validar y para
convertir la predicción en un precio con su rango) y la app (para construir el formulario). Se arma una vez, en el
notebook 09, con el ENTRENAMIENTO y con lo que se decidió en la etapa 7 (factor del logaritmo y rango típico por ciudad).
Claves y reglas: specs/003-validacion-registro-app/data-model.md, sección 4.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tarifalatam.config import TARGET

DEFAULT_LABELS = {
    "city": "Ciudad",
    "neighbourhood_cleansed": "Barrio",
    "room_type": "Tipo de alojamiento",
    "property_type": "Tipo de propiedad",
    "latitude": "Latitud",
    "longitude": "Longitud",
    "accommodates": "Huéspedes",
    "bedrooms": "Habitaciones",
    "beds": "Camas",
    "bathrooms_count": "Baños",
    "minimum_nights": "Noches mínimas",
    "maximum_nights": "Noches máximas",
    "bathroom_shared": "¿El baño es compartido? (1 = sí, 0 = no)",
}
DEFAULT_CITY_LABELS = {
    "rio-de-janeiro": "Río de Janeiro",
    "sao-paulo": "São Paulo",
    "mexico-city": "Ciudad de México",
    "bogota": "Bogotá",
    "santiago": "Santiago",
    "belize": "Belice",
}
DEFAULT_TITLE = "TarifaLatam · precio sugerido por noche"
DEFAULT_RESPONSIBLE_USE = (
    "- Es un **precio de referencia**: la tarifa la fija el anfitrión.\n"
    "- Para el inversionista es un insumo más: el modelo **no dice si un inmueble se paga** (no conoce la ocupación, los "
    "costos ni el valor de compra).\n"
    "- Se entrenó con anuncios de Inside Airbnb de septiembre de 2026 en seis ciudades. Predice el precio **publicado**, "
    "no el que se cobra, y no ve la temporada.\n"
    "- El rango muestra dónde quedó la mitad de los precios reales en anfitriones que el modelo no vio.\n"
    "- Revisa los límites del modelo en `models/ficha_modelo.md` antes de usarlo."
)


def _is_integer_column(values: pd.Series) -> bool:
    """True si todos los valores no vacíos son enteros (la app usará un campo entero)."""
    clean = values.dropna()
    return bool(len(clean)) and bool((clean == np.round(clean)).all())


def build_schema(
    df: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
    binary: list[str],
    valid_range: dict,
    price_range_ratios: dict,
    correction_factor: float = 1.0,
    city_warnings: dict | None = None,
    labels: dict | None = None,
    city_labels: dict | None = None,
    app_title: str = DEFAULT_TITLE,
    responsible_use: str = DEFAULT_RESPONSIBLE_USE,
    path: str | Path | None = None,
) -> dict:
    """Construye (y opcionalmente guarda) el esquema a partir del ENTRENAMIENTO.

    - `numeric`, `categorical`, `binary`: las columnas que el modelo necesita, tal como llegan en una fila nueva.
    - `valid_range`: {columna: (mínimo, máximo)} de lo POSIBLE (conocimiento del grupo). Fuera de él, la predicción se niega.
    - `price_range_ratios`: {ciudad: [p25, p75]} de precio real / sugerido en los anfitriones reservados (etapa 7).
    - `correction_factor`: el factor al volver del logaritmo (1 = sin corrección, lo decidido en la etapa 7).
    - `city_warnings`: {ciudad: texto} que la app muestra junto al precio (p. ej. Belice).
    """
    numbers = list(numeric) + list(binary)
    missing = [c for c in list(categorical) + numbers if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en los datos: {', '.join(missing)}")
    if "city" not in categorical or "neighbourhood_cleansed" not in categorical:
        raise ValueError("El esquema necesita las columnas city y neighbourhood_cleansed")
    cities = sorted(df["city"].dropna().astype(str).unique())
    without_range = [c for c in cities if c not in price_range_ratios]
    if without_range:
        raise ValueError(f"Falta el rango típico de: {', '.join(without_range)}")

    by_city = df.dropna(subset=["city"]).groupby("city")
    coords = (
        df.dropna(subset=["city", "neighbourhood_cleansed", "latitude", "longitude"])
        .groupby(["city", "neighbourhood_cleansed"])[["latitude", "longitude"]]
        .median()
    )
    schema = {
        "target": TARGET,
        "numeric": list(numeric),
        "categorical": list(categorical),
        "binary": list(binary),
        "required": ["city"],
        "categories": {c: sorted(df[c].dropna().astype(str).unique().tolist()) for c in categorical},
        # la categoría más frecuente: la que el formulario muestra por defecto
        "most_frequent": {c: str(df[c].dropna().astype(str).mode().iloc[0]) for c in categorical},
        "neighbourhoods_by_city": {
            str(city): sorted(group["neighbourhood_cleansed"].dropna().astype(str).unique().tolist())
            for city, group in by_city
        },
        "neighbourhood_coords": {},
        "city_box": {
            str(city): [float(group["latitude"].min()), float(group["latitude"].max()),
                        float(group["longitude"].min()), float(group["longitude"].max())]
            for city, group in by_city
        },
        "valid_range": {k: [float(v[0]), float(v[1])] for k, v in valid_range.items() if k in numbers},
        "observed_range": {},
        "median": {},
        "integer_columns": [],
        "correction_factor": float(correction_factor),
        "price_range_ratios": {str(c): [float(v[0]), float(v[1])] for c, v in price_range_ratios.items()},
        "city_warnings": dict(city_warnings or {}),
        "labels": {**DEFAULT_LABELS, **(labels or {})},
        "city_labels": {**DEFAULT_CITY_LABELS, **(city_labels or {})},
        "app_title": app_title,
        "responsible_use": responsible_use,
    }
    for (city, barrio), row in coords.iterrows():
        schema["neighbourhood_coords"].setdefault(str(city), {})[str(barrio)] = [float(row["latitude"]), float(row["longitude"])]
    for col in numbers:
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        if values.empty:
            raise ValueError(f"La columna numérica '{col}' no tiene ningún valor numérico")
        schema["observed_range"][col] = [float(values.min()), float(values.max())]
        schema["median"][col] = float(values.median())
        if _is_integer_column(values):
            schema["integer_columns"].append(col)
    if path is not None:
        save_schema(schema, path)
    return schema


def save_schema(schema: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def load_schema(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
