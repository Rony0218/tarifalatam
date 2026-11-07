"""Conversión de la predicción del modelo (logaritmo) a precio en USD por noche.

Va en un módulo aparte y liviano porque la usan dos lugares que deben dar exactamente lo mismo: la validación de la
etapa 7 (`models/validation.py`) y la app (`inference/predict.py`). Así el modelo exportado da el mismo MAE que el evaluado.
"""
import numpy as np


def to_usd_price(pred_log, factor: float = 1.0) -> np.ndarray:
    """Precio sugerido en USD: exp de la predicción en logaritmo, multiplicado por el factor de corrección (1 = sin)."""
    return np.exp(np.asarray(pred_log, dtype=float)) * float(factor)
