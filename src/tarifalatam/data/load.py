"""Carga del conjunto de entrenamiento que deja el notebook 03.

Reemplaza la lectura de train.joblib de los esqueletos: el notebook 03 guarda CSV comprimido. No hay función para
leer la prueba: test.csv.gz se abre una sola vez, en la etapa 7 (constitución, principio III).
"""
from pathlib import Path

import pandas as pd

from tarifalatam.config import (
    FORBIDDEN_FEATURES,
    HOST_PROFILE_COLUMNS,
    REFERENCE_BINARY,
    REFERENCE_CATEGORICAL,
    REFERENCE_NUMERIC,
    SUSPICIOUS_FEATURES,
    TRAIN_PATH,
)

# Las 65 columnas esperadas: cada una está en exactamente una de las cuatro listas de config.py
EXPECTED_COLUMNS = (
    FORBIDDEN_FEATURES
    + SUSPICIOUS_FEATURES
    + REFERENCE_CATEGORICAL
    + REFERENCE_NUMERIC
    + REFERENCE_BINARY
    + HOST_PROFILE_COLUMNS
)


def load_train(path=TRAIN_PATH) -> pd.DataFrame:
    """Lee el entrenamiento y comprueba que trae exactamente las 65 columnas esperadas.

    Si el notebook 03 cambia y agrega o quita columnas, se detiene con un mensaje que las nombra, en vez de
    modelar en silencio con otra tabla.
    """
    path = Path(path)
    if path.name.startswith("test"):
        raise ValueError(f"{path.name} es la prueba: se abre una sola vez, en la etapa 7, y no con esta función")
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}: ejecuta antes notebooks/03_preprocesamiento.ipynb")
    train = pd.read_csv(path, low_memory=False)
    missing = [col for col in EXPECTED_COLUMNS if col not in train.columns]
    extra = [col for col in train.columns if col not in EXPECTED_COLUMNS]
    if missing or extra:
        raise ValueError(f"Las columnas del entrenamiento no son las esperadas. Faltan: {missing}. Sobran: {extra}")
    # Los pliegues se guardan por id y se parte por anfitrión: los dos deben estar completos y el id ser único
    if train["id"].duplicated().any():
        raise ValueError(f"Hay {train['id'].duplicated().sum()} id repetidos: los pliegues se asignan por id")
    if train["host_id"].isna().any():
        raise ValueError(f"{train['host_id'].isna().sum()} anuncios no tienen host_id: no se puede partir por anfitrión")
    return train
