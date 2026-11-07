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
            "source": pd.Series([np.nan] * n, dtype=object),  # texto: admite "previous scrape"
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


# Ciudades, centros aproximados y barrios inventados para la tabla de entrenamiento de juguete
TRAIN_CITIES = {
    "rio-de-janeiro": (-22.95, -43.20),
    "bogota": (4.65, -74.06),
    "belize": (17.25, -88.77),
}
# "Barrio Raro" aparece en el 3 % de los anuncios. Ojo con el umbral de 30 (RARE_MIN_COUNT): con los 60 anuncios por
# defecto TODOS los barrios quedan por debajo y pasan a "Other"; para probar el agrupador hacen falta unos 400
# (make_train_rows(n_hosts=200)), donde solo "Barrio Raro" queda por debajo
TOY_NEIGHBOURHOODS = ["Centro", "Norte", "Sur", "Barrio Raro"]
TOY_AMENITIES = [
    ["Wifi", "Kitchen", "Pool", "Air conditioning"],
    ["Wifi", "Pool table", "Elevator"],  # "Pool table" no es una piscina
    ["Wifi", "Kitchen", "Free parking on premises", "Gym", "Hot tub"],
    [],
]


def make_train_rows(n_hosts: int = 30, seed: int = 0, **overrides) -> pd.DataFrame:
    """Devuelve una tabla con las 65 columnas de data/processed/train.csv.gz (datos inventados).

    El anfitrión i tiene (i % 3) + 1 anuncios, todos en la misma ciudad: con 30 anfitriones son 60 anuncios.
    El precio depende de la capacidad y del tipo de habitación, para que un modelo tenga algo que aprender.
    overrides reemplaza columnas completas.
    """
    rng = np.random.default_rng(seed)
    host_ids = np.repeat(np.arange(500, 500 + n_hosts), [(i % 3) + 1 for i in range(n_hosts)])
    n = len(host_ids)
    city_names = list(TRAIN_CITIES)
    cities = [city_names[(h - 500) % len(city_names)] for h in host_ids]
    lat0 = np.array([TRAIN_CITIES[c][0] for c in cities])
    lon0 = np.array([TRAIN_CITIES[c][1] for c in cities])
    accommodates = rng.integers(1, 7, size=n)
    room_type = np.where(rng.random(n) < 0.7, "Entire home/apt", "Private room")
    price_usd = (30 + 20 * accommodates) * np.where(room_type == "Private room", 0.5, 1.0) * rng.uniform(0.8, 1.2, n)
    reviews = rng.integers(0, 4, size=n) * rng.integers(0, 2, size=n)  # cerca de la mitad sin reseñas
    has_reviews = reviews > 0
    review_score = np.where(has_reviews, rng.uniform(4.0, 5.0, n).round(2), np.nan)
    first_review = np.where(has_reviews, "2024-05-10", None)
    last_review = np.where(has_reviews, "2026-08-30", None)
    listings_count = pd.Series(host_ids).map(pd.Series(host_ids).value_counts()).to_numpy()
    df = pd.DataFrame(
        {
            "city": cities,
            "id": np.arange(9001, 9001 + n),
            "scrape_id": [20260900 + city_names.index(c) for c in cities],
            "last_scraped": "2026-09-22",
            "source": np.nan,
            "host_id": host_ids,
            "hosts_time_as_user_years": rng.integers(0, 12, size=n).astype(float),
            "hosts_time_as_user_months": rng.integers(0, 12, size=n).astype(float),
            "hosts_time_as_host_years": rng.integers(0, 8, size=n).astype(float),
            "hosts_time_as_host_months": rng.integers(0, 12, size=n).astype(float),
            "host_is_superhost": rng.choice(["t", "f"], size=n),
            "host_listings_count": listings_count,
            "host_has_profile_pic": rng.choice(["t", "f"], size=n, p=[0.9, 0.1]),
            "host_identity_verified": rng.choice(["t", "f"], size=n, p=[0.8, 0.2]),
            "neighbourhood_cleansed": rng.choice(TOY_NEIGHBOURHOODS, size=n, p=[0.4, 0.3, 0.27, 0.03]),
            "neighbourhood_group_cleansed": np.nan,
            "latitude": lat0 + rng.normal(0, 0.03, n),
            "longitude": lon0 + rng.normal(0, 0.03, n),
            "property_type": np.where(room_type == "Private room", "Private room in home", "Entire rental unit"),
            "room_type": room_type,
            "accommodates": accommodates,
            "bathrooms_text": "1 bath",
            "bedrooms": np.maximum(accommodates // 2, 0).astype(float),
            "beds": accommodates.astype(float),
            "amenities": [json.dumps(TOY_AMENITIES[i % len(TOY_AMENITIES)]) for i in range(n)],
            "minimum_nights": rng.integers(1, 5, size=n).astype(float),
            "maximum_nights": 365.0,
            "minimum_minimum_nights": 1.0,
            "maximum_minimum_nights": 5.0,
            "minimum_maximum_nights": 365.0,
            "maximum_maximum_nights": 365.0,
            "minimum_nights_avg_ntm": 2.0,
            "maximum_nights_avg_ntm": 365.0,
            "has_availability": rng.choice(["t", "f"], size=n, p=[0.95, 0.05]),
            "availability_30": rng.integers(0, 31, size=n),
            "availability_60": rng.integers(0, 61, size=n),
            "availability_90": rng.integers(0, 91, size=n),
            "availability_365": rng.integers(0, 366, size=n),
            "calendar_last_scraped": "2026-09-22",
            "number_of_reviews": reviews,
            "number_of_reviews_ltm": reviews,
            "number_of_reviews_l30d": np.minimum(reviews, 1),
            "availability_eoy": rng.integers(0, 101, size=n),
            "number_of_reviews_ly": reviews,
            "estimated_occupancy_l365d": rng.integers(0, 255, size=n),
            "first_review": first_review,
            "last_review": last_review,
            "review_scores_rating": review_score,
            "review_scores_accuracy": review_score,
            "review_scores_cleanliness": review_score,
            "review_scores_checkin": review_score,
            "review_scores_communication": review_score,
            "review_scores_location": review_score,
            "review_scores_value": review_score,
            "calculated_host_listings_count": listings_count,
            "calculated_host_listings_count_entire_homes": listings_count,
            "calculated_host_listings_count_private_rooms": 0,
            "calculated_host_listings_count_shared_rooms": 0,
            "reviews_per_month": np.where(has_reviews, reviews / 28.0, np.nan),
            "price_local": price_usd,
            "price_usd": price_usd,
            "bathrooms_count": 1.0,
            "bathroom_shared": 0.0,
            "has_reviews": has_reviews.astype(int),
            "log_price_usd": np.log(price_usd),
        }
    )
    for col, values in overrides.items():
        df[col] = values
    return df
