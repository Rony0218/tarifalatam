"""Pliegues por anfitrión que comparten las etapas 4, 5 y 6, y anfitriones reservados para la optimización.

Los pliegues se calculan UNA vez (notebook 04) y se guardan por id de anuncio en data/processed/folds.csv. Así las
tres etapas comparan ideas, modelos y ensayos con exactamente la misma validación (guía de modelado, sección 1.2).
Todas las particiones mantienen a cada anfitrión completo de un solo lado.

split.py no se modifica: group_cv() (sin barajar) es la que midió la línea base de H1 y queda como registro.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from tarifalatam.config import FOLD_SEED, FOLDS_PATH, GROUP_COL, N_FOLDS, RESERVE_SEED, RESERVE_SIZE
from tarifalatam.data.split import assert_disjoint_hosts


def make_folds(train: pd.DataFrame, n_splits: int = N_FOLDS, seed: int = FOLD_SEED) -> pd.DataFrame:
    """Asigna cada anuncio a un pliegue de validación (0 a n_splits - 1), con cada anfitrión entero en un pliegue.

    Devuelve una tabla id -> fold. Se ordena por id antes de partir, así el orden de las filas no cambia el resultado.
    """
    if train[GROUP_COL].isna().any():
        raise ValueError(f"{train[GROUP_COL].isna().sum()} anuncios no tienen {GROUP_COL}: no se puede partir por anfitrión")
    ordered = train[["id", GROUP_COL]].sort_values("id").reset_index(drop=True)
    fold = np.full(len(ordered), -1)
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for k, (_, valid_idx) in enumerate(splitter.split(ordered, groups=ordered[GROUP_COL])):
        fold[valid_idx] = k
    assert_disjoint_hosts(*[ordered.loc[fold == k] for k in range(n_splits)])
    return pd.DataFrame({"id": ordered["id"].to_numpy(), "fold": fold})


def save_folds(folds: pd.DataFrame, path=FOLDS_PATH) -> None:
    """Guarda la asignación id -> fold (data/processed/ no se sube a Git)."""
    folds.to_csv(path, index=False)


def load_folds(path=FOLDS_PATH) -> pd.DataFrame:
    """Lee la asignación que guardó el notebook 04."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}: ejecuta antes notebooks/04_features.ipynb, que calcula los pliegues")
    return pd.read_csv(path)


def fold_indices(frame: pd.DataFrame, folds: pd.DataFrame, exact: bool = True) -> list:
    """Convierte la asignación en pares (posiciones de ajuste, posiciones de validación) para las filas de frame.

    exact=True (entrenamiento completo): los id de frame y de la asignación deben coincidir exactamente.
    exact=False (subconjunto de búsqueda de la etapa 6): todos los id de frame deben estar en la asignación, y cada
    anuncio conserva su pliegue.
    """
    known = set(folds["id"])
    ids = set(frame["id"])
    if exact and ids != known:
        raise ValueError(
            f"Los anuncios no coinciden con la asignación de pliegues ({len(ids - known)} sin pliegue, "
            f"{len(known - ids)} de más): vuelve a ejecutar el notebook 04"
        )
    if not exact and not ids <= known:
        raise ValueError(f"{len(ids - known)} anuncios no están en la asignación de pliegues")
    fold = frame[["id"]].merge(folds, on="id", how="left")["fold"].to_numpy()
    missing = sorted(set(range(int(folds["fold"].max()) + 1)) - set(fold))
    if missing:
        raise ValueError(f"No hay anuncios del pliegue {missing} en esta tabla: no se pueden usar los 5 pliegues")
    positions = np.arange(len(frame))
    return [(positions[fold != k], positions[fold == k]) for k in sorted(set(fold))]


def reserve_hosts(train: pd.DataFrame, size: float = RESERVE_SIZE, seed: int = RESERVE_SEED):
    """Separa, dentro del entrenamiento, el 25 % de los ANFITRIONES que la búsqueda nunca verá.

    Devuelve (búsqueda, reservados). Sirven para la comprobación honesta de la etapa 6 (guía, sección 3.4).
    """
    if train[GROUP_COL].isna().any():
        raise ValueError(f"{train[GROUP_COL].isna().sum()} anuncios no tienen {GROUP_COL}: no se puede reservar por anfitrión")
    splitter = GroupShuffleSplit(n_splits=1, test_size=size, random_state=seed)
    search_idx, reserved_idx = next(splitter.split(train, groups=train[GROUP_COL]))
    search = train.iloc[search_idx].reset_index(drop=True)
    reserved = train.iloc[reserved_idx].reset_index(drop=True)
    assert_disjoint_hosts(search, reserved)
    return search, reserved
