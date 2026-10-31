"""Tablas de juguete para las pruebas.

Datos inventados a mano solo para pruebas: no son anuncios reales ni salen de data/raw/.
Imitan las columnas de Inside Airbnb que usan las reglas de limpieza.
"""
import json

import numpy as np
import pandas as pd

from tarifalatam.config import CITY_CURRENCY, EMPTY_COLUMNS

TOY_CITIES = ["rio-de-janeiro", "belize"]


def _quote(currency: str, price: float) -> str:
    """Imita el JSON de price_quote_raw con la moneda y el precio por noche."""
    return json.dumps({"quote": {"currency": currency, "price_per_night": str(price)}})


def make_listings(n_hosts: int = 6, per_host: int = 2, seed: int = 0, **overrides) -> pd.DataFrame:
    """Devuelve n_hosts * per_host anuncios limpios; overrides reemplaza columnas completas.

    Las ciudades se alternan fila a fila, así que un anfitrión con 2 o más anuncios tiene
    anuncios en las dos ciudades (como los 258 anfitriones reales que están en varias ciudades).
    """
    rng = np.random.default_rng(seed)
    n = n_hosts * per_host
    cities = [TOY_CITIES[i % len(TOY_CITIES)] for i in range(n)]
    prices = rng.integers(100, 900, size=n).astype(float)
    reviews = rng.integers(0, 6, size=n)
    df = pd.DataFrame(
        {
            "id": np.arange(1, n + 1),
            "host_id": np.repeat(np.arange(100, 100 + n_hosts), per_host),
            "city": cities,
            "source": [np.nan] * n,
            "price": [f"${p:,.2f}" for p in prices],
            "price_quote_raw": [_quote(CITY_CURRENCY[c], p) for c, p in zip(cities, prices)],
            "price_quote_checkin_date": ["2026-10-01"] * n,
            "price_quote_checkout_date": ["2026-10-03"] * n,
            "price_quote_total_price": prices * 2,
            "price_quote_price_per_night": prices,
            "estimated_occupancy_l365d": rng.integers(0, 255, size=n),
            "estimated_revenue_l365d": prices * 10,
            "bathrooms_text": ["1 bath"] * n,
            "minimum_nights": [2] * n,
            "maximum_nights": [365] * n,
            "bedrooms": [1.0] * n,
            "accommodates": [2] * n,
            "room_type": ["Entire home/apt"] * n,
            "number_of_reviews": reviews,
            "review_scores_rating": np.where(reviews > 0, 4.8, np.nan),
        }
    )
    for col in EMPTY_COLUMNS:
        df[col] = np.nan
    for col, values in overrides.items():
        df[col] = values
    return df
