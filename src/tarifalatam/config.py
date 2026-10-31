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

# ---------------------------------------------------------------------------------------------------------------
# Etapas 4 a 6: variables, torneo y optimización (especificaciones/04-features-torneo-optimizacion.md, aprobada por
# el grupo el 2026-10-31). Las 65 columnas del entrenamiento están en exactamente una de estas cuatro listas.
# ---------------------------------------------------------------------------------------------------------------
TRAIN_PATH = PROCESSED_DIR / "train.csv.gz"  # la prueba (test.csv.gz) no se abre hasta la etapa 7
FOLDS_PATH = PROCESSED_DIR / "folds.csv"  # pliegues por anfitrión: se calculan una vez en el notebook 04

# El objetivo en sus tres escalas: nunca entra al modelo como variable
TARGET_COLUMNS = ["log_price_usd", "price_usd", "price_local"]

# Prohibidas (18): el objetivo, identificadores, metadatos de la descarga y columnas redundantes (sección 1.1)
FORBIDDEN_FEATURES = TARGET_COLUMNS + [
    "id",  # identifica el anuncio: solo sirve para unir los pliegues
    "host_id",  # identifica al anfitrión: solo sirve para partir (constitución, principio II)
    "scrape_id",  # metadatos de la descarga: dicen la ciudad y la fecha del corte, no el inmueble
    "last_scraped",
    "calendar_last_scraped",
    "source",  # 100 % vacía en el entrenamiento
    "bathrooms_text",  # ya convertida en bathrooms_count y bathroom_shared (decisión 6 del EDA)
    "amenities",  # texto con 15.938 nombres distintos: solo entra a través de la idea 2
    "neighbourhood_group_cleansed",  # 69,8 % vacía: solo existe en São Paulo y Belice
    "minimum_minimum_nights",  # las seis variantes del calendario repiten minimum_nights y maximum_nights
    "maximum_minimum_nights",
    "minimum_maximum_nights",
    "maximum_maximum_nights",
    "minimum_nights_avg_ntm",
    "maximum_nights_avg_ntm",
]

# Sospechosas (23): consecuencia del precio o de la demanda. Solo se miden "con y sin" (sección 1.2); nunca van al
# torneo, a la optimización ni a la app, porque el inversionista evalúa inmuebles nuevos.
SUSPICIOUS_FEATURES = [
    "estimated_occupancy_l365d",
    "availability_30",
    "availability_60",
    "availability_90",
    "availability_365",
    "availability_eoy",
    "has_availability",
    "number_of_reviews",
    "number_of_reviews_ltm",
    "number_of_reviews_l30d",
    "number_of_reviews_ly",
    "reviews_per_month",
    "first_review",
    "last_review",
    "has_reviews",
    "review_scores_rating",
    "review_scores_accuracy",
    "review_scores_cleanliness",
    "review_scores_checkin",
    "review_scores_communication",
    "review_scores_location",
    "review_scores_value",
    "host_is_superhost",  # Airbnb lo otorga por notas, estancias y cancelaciones: un anfitrión nuevo no lo tiene
]

# Referencia (13): lo que describe el inmueble, dónde está y sus reglas de estadía (sección 1.3)
REFERENCE_CATEGORICAL = ["city", "neighbourhood_cleansed", "room_type", "property_type"]
REFERENCE_NUMERIC = [
    "latitude",
    "longitude",
    "accommodates",
    "bedrooms",
    "beds",
    "bathrooms_count",
    "minimum_nights",
    "maximum_nights",
]
REFERENCE_BINARY = ["bathroom_shared"]

# Perfil del anfitrión (11): insumo de la idea 4
HOST_PROFILE_COLUMNS = [
    "host_listings_count",
    "calculated_host_listings_count",
    "calculated_host_listings_count_entire_homes",
    "calculated_host_listings_count_private_rooms",
    "calculated_host_listings_count_shared_rooms",
    "hosts_time_as_host_years",
    "hosts_time_as_host_months",
    "hosts_time_as_user_years",
    "hosts_time_as_user_months",
    "host_has_profile_pic",
    "host_identity_verified",
]

# Idea 2: indicadores por nombre EXACTO (sin variantes, decisión del grupo). En el entrenamiento: Pool 18,2 %,
# Air conditioning 40,3 %, Free parking on premises 25,8 %, Gym 12,5 %, Elevator 47,6 %, Hot tub 2,9 %.
# Buscar la palabra no sirve: "Pool table" (4.802 anuncios) es una mesa de billar.
AMENITY_FLAGS = {
    "amenity_pool": "Pool",
    "amenity_air_conditioning": "Air conditioning",
    "amenity_free_parking": "Free parking on premises",
    "amenity_gym": "Gym",
    "amenity_elevator": "Elevator",
    "amenity_hot_tub": "Hot tub",
}

# Decisión 11 del EDA: barrios y tipos de propiedad con menos de 30 anuncios pasan a "Other" (en el EDA, 146 de 371
# barrios y 73 de 123 tipos tenían menos de 30). El umbral se aplica dentro del Pipeline, con el entrenamiento
RARE_MIN_COUNT = 30

# Validación común: 5 pliegues por anfitrión, barajados con semilla 42, los mismos en las etapas 4, 5 y 6
N_FOLDS = 5
FOLD_SEED = 42

# Optimización: 25 % de los anfitriones reservados (semilla 7), 30 ensayos por finalista e intervalo del 95 %
# con 1.000 remuestreos de anfitriones completos
RESERVE_SIZE = 0.25
RESERVE_SEED = 7
N_TRIALS = 30
BOOTSTRAP_N = 1000
NIGHTS_SCALE = 30  # la diferencia de MAE se lee como "USD por cada 30 noches reservadas" (escala, no pronóstico)
EXPERIMENT_NAME = "tarifalatam-optimizacion"

# Resultado de la etapa 4 (notebooks/04_features.ipynb, 2026-10-31; detalle en reports/04_features.md): ninguna idea
# cumple mejora / ruido > 1, y el grupo decidió aplicar la regla sin excepciones. El torneo y la optimización usan la
# referencia (13 columnas). Las amenidades (idea 2) ganaron en los 5 pliegues, pero con mejora / ruido de 0,49.
FINAL_IDEAS = ()
