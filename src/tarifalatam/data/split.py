"""Partición de datos por anfitrión.

Un anfitrión puede tener muchos anuncios (89.964 anfitriones; el 31 % de los anuncios es de anfitriones con
10 o más, y uno llega a 699). Sus anuncios se parecen: mismo estilo de precio y de descripción. Si se parte
por fila, el modelo "reconoce" al anfitrión en la prueba y la métrica sale inflada (fuga de información).
Aquí **todas** las particiones mantienen a cada anfitrión completo de un solo lado, aunque tenga anuncios
en varias ciudades.
"""
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from tarifalatam.config import GROUP_COL, RANDOM_STATE, TEST_SIZE


def split_by_host(df: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = RANDOM_STATE):
    """Separa entrenamiento y prueba sin repartir a ningún anfitrión entre los dos.

    test_size es la proporción de ANFITRIONES en prueba: la de filas queda cerca, no exacta.
    Falla si algún host_id está vacío: un anuncio sin anfitrión no se puede agrupar con seguridad.
    """
    if df[GROUP_COL].isna().any():
        raise ValueError(f"{df[GROUP_COL].isna().sum()} anuncios no tienen {GROUP_COL}: no se puede partir por anfitrión")
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(df, groups=df[GROUP_COL]))
    train = df.iloc[train_idx].reset_index(drop=True)
    test = df.iloc[test_idx].reset_index(drop=True)
    assert_disjoint_hosts(train, test)
    return train, test


def assert_disjoint_hosts(*frames: pd.DataFrame) -> None:
    """Falla si algún anfitrión aparece en más de una partición."""
    seen: set = set()
    for i, frame in enumerate(frames):
        hosts = set(frame[GROUP_COL])
        overlap = seen & hosts
        if overlap:
            raise AssertionError(f"{len(overlap)} anfitriones aparecen en más de una partición (partición {i})")
        seen |= hosts


def group_cv(n_splits: int = 5) -> GroupKFold:
    """Validación cruzada que mantiene a cada anfitrión completo en un solo pliegue (usar con groups=host_id)."""
    return GroupKFold(n_splits=n_splits)
