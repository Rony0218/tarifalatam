"""Qué columnas puede usar el modelo en cada variante, y la barrera que impide que entre una prohibida.

Hay dos barreras contra la fuga: esta lista revisada (check_feature_columns) y el ColumnTransformer con
remainder="drop" de models/train.py, que descarta cualquier columna que nadie pidió.
"""
from tarifalatam.config import (
    AMENITY_FLAGS,
    FORBIDDEN_FEATURES,
    REFERENCE_BINARY,
    REFERENCE_CATEGORICAL,
    REFERENCE_NUMERIC,
    SUSPICIOUS_FEATURES,
)

# Columnas calculadas a partir de las sospechosas (SuspiciousFeatures): se tratan igual que ellas
SUSPICIOUS_DERIVED = ["days_since_first_review", "days_since_last_review"]

# Nombre de cada idea en las tablas de resultados (reports/04_features_tabla.csv)
IDEA_NAMES = {
    1: "idea_1_distancia",
    2: "idea_2_amenidades",
    3: "idea_3_capacidad",
    4: "idea_4_anfitrion",
    5: "idea_5_barrio",
}

# Columnas que agrega cada idea, por tipo (las calculan los transformadores de engineering.py)
IDEA_NUMERIC = {
    1: ["distance_to_center_km"],
    2: ["amenities_count"],
    3: ["people_per_bedroom", "people_per_bathroom", "beds_per_person"],
    4: [
        "host_listings_count",
        "calculated_host_listings_count",
        "calculated_host_listings_count_entire_homes",
        "calculated_host_listings_count_private_rooms",
        "calculated_host_listings_count_shared_rooms",
        "host_tenure_years",
        "user_tenure_years",
    ],
}
IDEA_BINARY = {2: list(AMENITY_FLAGS), 4: ["host_has_profile_pic", "host_identity_verified"]}

# Sospechosas por tipo: las dos fechas entran convertidas en días (SUSPICIOUS_DERIVED)
SUSPICIOUS_BINARY = ["has_availability", "has_reviews", "host_is_superhost"]
SUSPICIOUS_NUMERIC = [
    col for col in SUSPICIOUS_FEATURES if col not in SUSPICIOUS_BINARY + ["first_review", "last_review"]
] + SUSPICIOUS_DERIVED


def feature_columns(ideas=(), with_suspicious: bool = False) -> dict:
    """Columnas que selecciona el ColumnTransformer para una variante, por tipo.

    Devuelve {"categorical", "numeric", "binary", "target_encoded"}. Sin ideas es la referencia (13 columnas). La
    idea 5 no agrega una columna cruda: codifica neighbourhood_cleansed con el promedio del objetivo.
    """
    ideas = sorted(set(ideas))  # una idea repetida cuenta una sola vez
    unknown = set(ideas) - set(IDEA_NAMES)
    if unknown:
        raise ValueError(f"Ideas desconocidas: {sorted(unknown)}. Las ideas van de 1 a 5")
    numeric = list(REFERENCE_NUMERIC)
    binary = list(REFERENCE_BINARY)
    for idea in ideas:
        numeric += IDEA_NUMERIC.get(idea, [])
        binary += IDEA_BINARY.get(idea, [])
    if with_suspicious:
        numeric += SUSPICIOUS_NUMERIC
        binary += SUSPICIOUS_BINARY
    return {
        "categorical": list(REFERENCE_CATEGORICAL),
        "numeric": numeric,
        "binary": binary,
        "target_encoded": ["neighbourhood_cleansed"] if 5 in ideas else [],
    }


def check_feature_columns(columns, allow_suspicious: bool = False) -> None:
    """Falla si alguna columna está prohibida, o si es sospechosa y no se permiten sospechosas.

    El mensaje nombra cada columna, para que se sepa cuál quitar.
    """
    forbidden = [col for col in columns if col in FORBIDDEN_FEATURES]
    if forbidden:
        raise ValueError(f"Columnas prohibidas como variables (objetivo, identificadores o redundantes): {forbidden}")
    if not allow_suspicious:
        suspicious = [col for col in columns if col in SUSPICIOUS_FEATURES or col in SUSPICIOUS_DERIVED]
        if suspicious:
            raise ValueError(
                "Columnas sospechosas (consecuencia del precio o de la demanda) fuera de la medición con "
                f"sospechosas: {suspicious}"
            )
