"""Línea base: la mediana del precio por ciudad y tipo de habitación.

Es la regla simple que el modelo debe superar (especificacion-proyecto.md, sección 4). Si una combinación
ciudad × tipo no se vio al ajustar (por ejemplo, hay solo 21 habitaciones de hotel en Río), usa la mediana
de la ciudad; si tampoco se vio la ciudad (un pliegue sin Belice, por ejemplo), usa la mediana general.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

from tarifalatam.config import GROUP_COL
from tarifalatam.data.split import group_cv


class MedianBaseline:
    """Predice el precio en USD con la mediana de su ciudad × room_type aprendida al ajustar."""

    def fit(self, train: pd.DataFrame) -> "MedianBaseline":
        self.cell_medians_ = train.groupby(["city", "room_type"])["price_usd"].median()
        self.city_medians_ = train.groupby("city")["price_usd"].median()
        self.overall_median_ = float(train["price_usd"].median())
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        keys = pd.MultiIndex.from_frame(df[["city", "room_type"]])
        by_cell = self.cell_medians_.reindex(keys).to_numpy(dtype=float)
        by_city = df["city"].map(self.city_medians_).to_numpy(dtype=float)
        prediction = np.where(np.isnan(by_cell), by_city, by_cell)
        return np.where(np.isnan(prediction), self.overall_median_, prediction)


def baseline_cv_mae(train: pd.DataFrame, n_splits: int = 5) -> dict:
    """MAE en USD de la línea base con validación cruzada por anfitrión, usando solo el entrenamiento.

    En cada pliegue la mediana se aprende con su parte de entrenamiento y se evalúa en anfitriones que no vio.
    """
    maes = []
    for fit_idx, valid_idx in group_cv(n_splits).split(train, groups=train[GROUP_COL]):
        fit_part, valid_part = train.iloc[fit_idx], train.iloc[valid_idx]
        prediction = MedianBaseline().fit(fit_part).predict(valid_part)
        maes.append(float(mean_absolute_error(valid_part["price_usd"], prediction)))
    return {"per_fold": maes, "mean": float(np.mean(maes)), "std": float(np.std(maes))}
