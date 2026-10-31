"""Qué columnas puede usar el modelo en cada variante, y la barrera que impide que entre una prohibida.

Hay dos barreras contra la fuga: esta lista revisada (check_feature_columns) y el ColumnTransformer con
remainder="drop" de models/train.py, que descarta cualquier columna que nadie pidió.
"""
from tarifalatam.config import FORBIDDEN_FEATURES, SUSPICIOUS_FEATURES

# Columnas calculadas a partir de las sospechosas (SuspiciousFeatures): se tratan igual que ellas
SUSPICIOUS_DERIVED = ["days_since_first_review", "days_since_last_review"]


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
