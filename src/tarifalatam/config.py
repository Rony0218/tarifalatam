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

# Ciudades que se cargan (el EDA las describe) pero se excluyen del modelo. Decisión del grupo del 2026-10-31:
# en Buenos Aires (29.753 anuncios) el 38,6 % de los precios son múltiplos de 764,41 ARS, una tasa sin explicación
# verificable, y la inflación de Argentina hace dudosa la conversión a USD.
EXCLUDED_CITIES = ("buenos-aires",)

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

# Tasas de cambio: unidades de moneda local por 1 USD, en la fecha del corte de cada ciudad (tarea T014).
# Criterio: la tasa oficial publicada por el banco central PARA esa fecha. Consultadas el 2026-10-30 en las
# fuentes oficiales del campo "source". ESTADO: APROBADAS POR EL GRUPO el 2026-10-31 (registro en la
# sección 7 de especificacion-proyecto.md).
# None = pendiente: to_usd() se detiene con un mensaje en vez de usar un valor supuesto.
FX_RATES = {
    "rio-de-janeiro": {
        "currency": "BRL",
        "local_per_usd": 5.1161,
        "date": "2026-09-22",
        "source": "Banco Central do Brasil, PTAX venta del 2026-09-22 (API olinda.bcb.gov.br, CotacaoDolarDia)",
    },
    "sao-paulo": {
        "currency": "BRL",
        "local_per_usd": 5.1696,
        "date": "2026-09-14",
        "source": "Banco Central do Brasil, PTAX venta del 2026-09-14 (API olinda.bcb.gov.br, CotacaoDolarDia)",
    },
    "mexico-city": {
        "currency": "MXN",
        "local_per_usd": 17.3015,
        "date": "2026-09-23",
        # El FIX determinado el mismo 23-09 se publicó en el DOF del 24-09: 17,5030 (1,2 % más)
        "source": "Banxico, tipo de cambio FIX publicado en el DOF el 2026-09-23 (sidof.segob.gob.mx, indicador 158)",
    },
    "buenos-aires": {
        "currency": "ARS",
        "local_per_usd": 1516.2964,
        "date": "2026-09-23",
        # No se usa: Buenos Aires se excluye antes de convertir (EXCLUDED_CITIES). Se conserva como registro.
        "source": "BCRA, tipo de cambio de referencia Com. A 3500 del 2026-09-23 (api.bcra.gob.ar, variable 5)",
    },
    "bogota": {
        "currency": "COP",
        "local_per_usd": 3072.27,
        "date": "2026-09-14",
        "source": "Superfinanciera, TRM vigente del 2026-09-12 al 2026-09-14 (datos.gov.co, conjunto 32sa-8pi3)",
    },
    "santiago": {
        "currency": "CLP",
        "local_per_usd": 945.87,
        "date": "2026-09-23",
        "source": "Banco Central de Chile, dólar observado al 2026-09-23 (Diario Oficial Núm. 44.556, CVE 2876853)",
    },
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

# Columnas con datos que no se usan. license solo existe en Bogotá (84,9 % llena, vacía en las demás ciudades):
# delata la ciudad en vez de describir el inmueble y es un número de registro (decisión del grupo, 2026-10-31)
UNUSED_COLUMNS = ["license"]

# 6.103 anuncios (3,1 %; 16,9 % en Bogotá) piden 30 noches o más: son arriendos mensuales
MONTHLY_MIN_NIGHTS = 30
# 1.125 es el valor por defecto de Airbnb; 21 anuncios traen 2.147.483.647 (el máximo entero)
MAX_NIGHTS_CAP = 1125
# 220 anuncios con más de 10 habitaciones (129 son "habitación privada": reportan el edificio)
MAX_BEDROOMS = 10
# Precio válido: entre 0,1 y 20 veces la mediana de su ciudad (692 anuncios > 20 x, 61 < 0,1 x)
PRICE_RATIO_BOUNDS = (0.1, 20.0)
