"""Limpieza de los anuncios de Inside Airbnb (siete ciudades, septiembre de 2026).

Cada regla sale de una decisión del EDA (reports/01_eda.md, especificaciones/02-eda.md):
  1. El precio llega como texto "$1,234.00" en seis monedas: se convierte a número y a USD.
  2. Los anuncios sin precio (6,0 %) son anuncios inactivos: se excluyen, no se imputa el objetivo.
  3. Las columnas price_quote_* y estimated_revenue_l365d contienen el precio (fuga): se eliminan.
  4. Los datos personales del anfitrión y el texto libre se eliminan al cargar.
  5. La partición es por anfitrión (ver split.py).
  6. Las 12 columnas 100 % vacías se eliminan; los baños se sacan de bathrooms_text.
  7. Los arriendos mensuales (minimum_nights >= 30) se excluyen.
  8. Los precios fuera de [0,1 x, 20 x] la mediana de su ciudad (aprendida en entrenamiento) se excluyen.
  9. has_reviews marca los anuncios con reseñas; las notas vacías se imputan después, en el Pipeline.
 10. Los centinelas (maximum_nights > 1.125, habitaciones imposibles) pasan a vacío.
 11. Agrupar categorías raras va en la etapa 4, dentro del Pipeline (no aquí).
Además: los anuncios del corte anterior (source = "previous scrape") se excluyen (decisión del grupo).

Ninguna función modifica la tabla que recibe: todas devuelven una tabla nueva.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tarifalatam.config import (
    CITY_CURRENCY,
    CITY_FILES,
    EMPTY_COLUMNS,
    FREE_TEXT_COLUMNS,
    FX_RATES,
    LEAKAGE_COLUMNS,
    MAX_BEDROOMS,
    MAX_NIGHTS_CAP,
    MONTHLY_MIN_NIGHTS,
    PII_COLUMNS,
    PRICE_RATIO_BOUNDS,
    RAW_DIR,
)


def load_raw(raw_dir=RAW_DIR) -> pd.DataFrame:
    """Lee los siete archivos, agrega la ciudad y elimina los datos personales y el texto libre.

    Los datos personales se quitan archivo por archivo, antes de unir nada: nunca llegan a la
    tabla que se devuelve. Los archivos originales solo se leen.
    """
    raw_dir = Path(raw_dir)
    frames = []
    expected_columns = None
    for city, filename in CITY_FILES.items():
        path = raw_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Falta el archivo de {city}: {filename} en {raw_dir}")
        frame = pd.read_csv(path, low_memory=False)
        if expected_columns is None:
            expected_columns = set(frame.columns)
        elif set(frame.columns) != expected_columns:
            raise ValueError(f"Las columnas de {city} ({filename}) no coinciden con las de los demás archivos")
        frame = frame.drop(columns=PII_COLUMNS + FREE_TEXT_COLUMNS, errors="ignore")
        frame.insert(0, "city", city)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _quote_currency(raw) -> str | None:
    """Moneda de una cotización de price_quote_raw; None si está vacía o no es un JSON válido."""
    if not isinstance(raw, str):
        return None
    try:
        quote = (json.loads(raw) or {}).get("quote") or {}
    except (json.JSONDecodeError, AttributeError):
        return None
    return quote.get("currency")


def check_currencies(df: pd.DataFrame) -> pd.DataFrame:
    """Falla si la moneda de alguna cotización no es la esperada para su ciudad.

    El EDA descubrió que Belice publica en USD y no en BZD; si otro corte cambia una moneda,
    la conversión a USD sería incorrecta en silencio. Las cotizaciones vacías no se revisan.
    """
    found = df["price_quote_raw"].map(_quote_currency)
    expected = df["city"].map(CITY_CURRENCY)
    mismatch = found.notna() & (found != expected)
    if mismatch.any():
        cities = ", ".join(sorted(df.loc[mismatch, "city"].unique()))
        raise ValueError(f"La moneda de price_quote_raw no coincide con CITY_CURRENCY en: {cities}")
    return df


def drop_previous_scrape(df: pd.DataFrame) -> pd.DataFrame:
    """Excluye los anuncios del corte anterior (11.701; el 71,9 % sin precio): su precio puede estar desactualizado."""
    return df[~df["source"].isin(["previous scrape"])].copy()


def parse_price(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte price ("$1,234.00", el 100 % de los precios) en price_local numérico; lo que no sea número queda vacío."""
    out = df.copy()
    text = out["price"].astype("string").str.replace(r"[$,]", "", regex=True)
    out["price_local"] = pd.to_numeric(text, errors="coerce").astype(float)
    return out.drop(columns=["price"])


def drop_missing_price(df: pd.DataFrame) -> pd.DataFrame:
    """Excluye los anuncios sin precio (11.642): el 64 % tiene el calendario cerrado, son anuncios inactivos."""
    return df[df["price_local"].notna()].copy()


def to_usd(df: pd.DataFrame, rates: dict = FX_RATES) -> pd.DataFrame:
    """Agrega price_usd = price_local / (moneda local por 1 USD) con la tasa de la ciudad.

    Si a una ciudad presente le falta la tasa, se detiene: nunca se usa un valor supuesto.
    """
    missing = sorted(c for c in df["city"].unique() if (rates.get(c) or {}).get("local_per_usd") is None)
    if missing:
        raise ValueError(
            f"falta la tasa de cambio de {', '.join(missing)}: anótela en FX_RATES (config.py) con su fuente oficial"
        )
    out = df.copy()
    per_usd = out["city"].map({city: rate["local_per_usd"] for city, rate in rates.items()})
    out["price_usd"] = out["price_local"] / per_usd
    return out


def drop_leakage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina las columnas que contienen el precio (price_quote_price_per_night == price en el 100 % de los casos)."""
    return df.drop(columns=LEAKAGE_COLUMNS, errors="ignore")


def drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina las 12 columnas que vienen 100 % vacías en las siete ciudades."""
    return df.drop(columns=EMPTY_COLUMNS, errors="ignore")


def parse_bathrooms_text(df: pd.DataFrame) -> pd.DataFrame:
    """Saca de bathrooms_text el número de baños y si son compartidos (bathrooms viene 100 % vacía).

    "1.5 shared baths" -> 1,5 y compartido; "Half-bath" (1.010 casos, sin número) -> 0,5;
    "No bathroom" -> 0; texto vacío -> vacío en las dos columnas.
    """
    out = df.copy()
    text = out["bathrooms_text"].astype("string").str.lower()
    count = pd.to_numeric(text.str.extract(r"(\d+(?:\.\d+)?)")[0], errors="coerce").astype(float)
    count = count.mask(count.isna() & text.str.contains("half", na=False), 0.5)
    count = count.mask(text.str.contains("no bathroom", na=False), 0.0)
    out["bathrooms_count"] = count
    shared = text.str.contains("shared", na=False).astype(float)
    out["bathroom_shared"] = shared.mask(text.isna(), np.nan)
    return out


def drop_monthly_rentals(df: pd.DataFrame) -> pd.DataFrame:
    """Excluye los arriendos mensuales (minimum_nights >= 30: 3,1 %, y 16,9 % en Bogotá); el caso es la corta estancia.

    Los anuncios sin minimum_nights se conservan: no hay evidencia de que sean mensuales.
    """
    return df[~(df["minimum_nights"] >= MONTHLY_MIN_NIGHTS)].copy()


def mark_impossible_values(df: pd.DataFrame) -> pd.DataFrame:
    """Pasa a vacío los centinelas, sin quitar filas.

    maximum_nights > 1.125 (21 anuncios con 2.147.483.647, el máximo entero) y habitaciones > 10 que
    además superan la capacidad (124 casos: habitaciones de hotel que reportan el edificio).
    """
    out = df.copy()
    out["maximum_nights"] = out["maximum_nights"].mask(out["maximum_nights"] > MAX_NIGHTS_CAP)
    impossible = (out["bedrooms"] > MAX_BEDROOMS) & (out["bedrooms"] > out["accommodates"])
    out["bedrooms"] = out["bedrooms"].mask(impossible)
    return out


def add_review_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega has_reviews: el 15,5 % no tiene reseñas y en todos ellos las notas están vacías (anuncio nuevo).

    Las notas vacías se dejan así: se imputan dentro del Pipeline de la etapa 4.
    """
    out = df.copy()
    out["has_reviews"] = (out["number_of_reviews"].fillna(0) > 0).astype(int)
    return out


def fit_price_bounds(train: pd.DataFrame) -> dict:
    """Aprende, SOLO con el entrenamiento, el rango de precio válido de cada ciudad: [0,1 x, 20 x] su mediana en USD."""
    low, high = PRICE_RATIO_BOUNDS
    medians = train.groupby("city")["price_usd"].median()
    return {city: (float(low * m), float(high * m)) for city, m in medians.items()}


def drop_price_outliers(df: pd.DataFrame, bounds: dict) -> pd.DataFrame:
    """Excluye los precios fuera del rango de su ciudad (692 anuncios > 20 x la mediana; máximo 258.514.678 COP)."""
    missing = sorted(set(df["city"]) - set(bounds))
    if missing:
        raise ValueError(f"No hay límites de precio para: {', '.join(missing)}")
    low = df["city"].map({city: b[0] for city, b in bounds.items()})
    high = df["city"].map({city: b[1] for city, b in bounds.items()})
    return df[df["price_usd"].between(low, high)].copy()


def add_target(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega el objetivo log_price_usd: el logaritmo baja la asimetría del precio de 23-160 a 0,5-2,1."""
    out = df.copy()
    out["log_price_usd"] = np.log(out["price_usd"])
    return out
