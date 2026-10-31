"""Constantes del proyecto TarifaLatam: rutas, partición, ciudades, monedas, tasas, columnas y umbrales.

Las cifras de los comentarios salen del EDA (reports/01_eda.md) sobre los siete archivos de Inside Airbnb.
"""
from pathlib import Path

# src/tarifalatam/config.py -> la raíz del repo está dos niveles arriba de src/
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"  # se regenera con el notebook 03; no se sube a Git
REPORTS_DIR = ROOT / "reports"

RANDOM_STATE = 42
GROUP_COL = "host_id"  # unidad para partir: el anfitrión (89.964), no el anuncio
TARGET = "log_price_usd"
TEST_SIZE = 0.2  # proporción de ANFITRIONES en prueba (no de filas)

# Un archivo por ciudad, con el nombre fijado en el README.md
CITY_FILES = {
    "rio-de-janeiro": "listings_rio-de-janeiro_2026-09-22.csv.gz",
    "sao-paulo": "listings_sao-paulo_2026-09-14.csv.gz",
    "mexico-city": "listings_mexico-city_2026-09-23.csv.gz",
    "buenos-aires": "listings_buenos-aires_2026-09-23.csv.gz",
    "bogota": "listings_bogota_2026-09-14.csv.gz",
    "santiago": "listings_santiago_2026-09-23.csv.gz",
    "belize": "listings_belize_2026-09-25.csv.gz",
}

# Moneda en que Inside Airbnb publica cada ciudad (confirmada con price_quote_raw en el EDA).
# Belice publica en USD, no en BZD.
CITY_CURRENCY = {
    "rio-de-janeiro": "BRL",
    "sao-paulo": "BRL",
    "mexico-city": "MXN",
    "buenos-aires": "ARS",
    "bogota": "COP",
    "santiago": "CLP",
    "belize": "USD",
}

# Tasas de cambio: unidades de moneda local por 1 USD, en la fecha del corte de cada ciudad.
# Las anota el grupo desde el banco central de cada país, con el enlace en "source" (tarea T014).
# None = pendiente: to_usd() se detiene con un mensaje en vez de usar un valor supuesto.
FX_RATES = {
    "rio-de-janeiro": {"currency": "BRL", "local_per_usd": None, "date": "2026-09-22", "source": None},
    "sao-paulo": {"currency": "BRL", "local_per_usd": None, "date": "2026-09-14", "source": None},
    "mexico-city": {"currency": "MXN", "local_per_usd": None, "date": "2026-09-23", "source": None},
    "buenos-aires": {"currency": "ARS", "local_per_usd": None, "date": "2026-09-23", "source": None},
    "bogota": {"currency": "COP", "local_per_usd": None, "date": "2026-09-14", "source": None},
    "santiago": {"currency": "CLP", "local_per_usd": None, "date": "2026-09-23", "source": None},
    "belize": {
        "currency": "USD",
        "local_per_usd": 1.0,
        "date": "2026-09-25",
        "source": "Inside Airbnb publica Belice en USD (price_quote_raw)",
    },
}

# Datos personales del anfitrión: se eliminan al cargar, nunca llegan al análisis
PII_COLUMNS = [
    "host_name",
    "host_about",
    "host_location",
    "host_url",
    "host_profile_url",
    "host_profile_id",
    "host_picture_url",
    "host_thumbnail_url",
    "listing_url",
    "picture_url",
]

# Texto libre: trae datos de contacto (91 descripciones con teléfonos, 9 con correos)
FREE_TEXT_COLUMNS = ["name", "description", "neighborhood_overview"]

# Columnas que contienen la respuesta: price_quote_price_per_night == price (razón 1,000 en 182.983 anuncios)
# y estimated_revenue_l365d == price * estimated_occupancy_l365d
LEAKAGE_COLUMNS = [
    "price_quote_checkin_date",
    "price_quote_checkout_date",
    "price_quote_total_price",
    "price_quote_price_per_night",
    "price_quote_raw",
    "estimated_revenue_l365d",
]

# 100 % vacías en las siete ciudades
EMPTY_COLUMNS = [
    "bathrooms",
    "host_since",
    "host_response_time",
    "host_response_rate",
    "host_acceptance_rate",
    "host_neighbourhood",
    "host_total_listings_count",
    "host_verifications",
    "instant_bookable",
    "neighbourhood",
    "neighborhood_overview",
    "calendar_updated",
]

# 6.103 anuncios (3,1 %; 16,9 % en Bogotá) piden 30 noches o más: son arriendos mensuales
MONTHLY_MIN_NIGHTS = 30
# 1.125 es el valor por defecto de Airbnb; 21 anuncios traen 2.147.483.647 (el máximo entero)
MAX_NIGHTS_CAP = 1125
# 220 anuncios con más de 10 habitaciones (129 son "habitación privada": reportan el edificio)
MAX_BEDROOMS = 10
# Precio válido: entre 0,1 y 20 veces la mediana de su ciudad (692 anuncios > 20 x, 61 < 0,1 x)
PRICE_RATIO_BOUNDS = (0.1, 20.0)
