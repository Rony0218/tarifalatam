"""Variables nuevas y agrupación de categorías raras, como transformadores de scikit-learn.

Cada idea es una hipótesis que se mide en el notebook 04 (especificaciones/04-features-torneo-optimizacion.md,
sección 2):
  1. CityCenterDistance: distancia en km al "centro" de la ciudad (mediana de las coordenadas, aprendida en fit).
  2. AmenityFeatures: número de amenidades e indicadores de seis amenidades por nombre exacto.
  3. CapacityRatios: personas por habitación y por baño, y camas por persona.
  4. HostProfile: antigüedad del anfitrión y de su cuenta, y sus indicadores t/f como 1/0.
  5. Precio típico del barrio: no está aquí; es el TargetEncoder de scikit-learn dentro del ColumnTransformer
     (models/train.py), porque aprende del objetivo.
Además: RareCategoryGrouper (decisión 11 del EDA) y SuspiciousFeatures (solo para medir las columnas sospechosas).

Todos van DENTRO del Pipeline: el modelo guardado recibe las columnas crudas y la app no repite cálculos. Los que
aprenden algo (RareCategoryGrouper y CityCenterDistance) lo hacen solo en fit, con la parte de entrenamiento de cada
pliegue. Ninguno modifica la tabla que recibe: devuelven una copia con columnas nuevas.
"""
import json

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from tarifalatam.config import AMENITY_FLAGS, RARE_MIN_COUNT

OTHER = "Other"
EARTH_RADIUS_KM = 6371.0


def true_false(values: pd.Series) -> pd.Series:
    """Convierte "t"/"f" de Inside Airbnb en 1/0; cualquier otro valor queda vacío."""
    return values.map({"t": 1.0, "f": 0.0}).astype(float)


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Distancia en km sobre la superficie de la Tierra entre dos puntos (vacío si falta una coordenada)."""
    lat1, lon1, lat2, lon2 = (np.radians(np.asarray(v, dtype=float)) for v in (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


class RareCategoryGrouper(TransformerMixin, BaseEstimator):
    """Cambia por "Other" las categorías con menos de min_count anuncios en el entrenamiento (decisión 11 del EDA).

    En fit aprende qué categorías son frecuentes. En transform, las raras, las que no vio (un barrio nuevo en la app) y
    los vacíos pasan a "Other": el modelo no falla con una categoría desconocida.
    """

    def __init__(self, columns=None, min_count: int = RARE_MIN_COUNT):
        self.columns = columns
        self.min_count = min_count

    def fit(self, X: pd.DataFrame, y=None):
        columns = self.columns if self.columns is not None else list(X.columns)
        self.frequent_ = {}
        for col in columns:
            counts = X[col].value_counts()
            self.frequent_[col] = set(counts[counts >= self.min_count].index)
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        for col, frequent in self.frequent_.items():
            out[col] = X[col].where(X[col].isin(frequent), OTHER)
        return out

    def get_feature_names_out(self, input_features=None):
        return self.feature_names_in_


class CityCenterDistance(TransformerMixin, BaseEstimator):
    """Idea 1: distancia en km (haversine) al centro de la ciudad del anuncio.

    El centro es la mediana de la latitud y de la longitud de los anuncios de esa ciudad, aprendida en fit. Una ciudad
    que no se vio al ajustar deja la distancia vacía. Ojo: Belice es un país entero; allí un único centro dice poco.
    """

    def fit(self, X: pd.DataFrame, y=None):
        self.centers_ = X.groupby("city")[["latitude", "longitude"]].median()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        center_lat = X["city"].map(self.centers_["latitude"])
        center_lon = X["city"].map(self.centers_["longitude"])
        out["distance_to_center_km"] = haversine_km(X["latitude"], X["longitude"], center_lat, center_lon)
        return out


def _parse_list(text):
    """Lee la lista JSON de amenidades; devuelve None si el texto no es una lista."""
    if not isinstance(text, str):
        return None
    try:
        value = json.loads(text)
    except ValueError:
        return None
    return value if isinstance(value, list) else None


class AmenityFeatures(TransformerMixin, BaseEstimator):
    """Idea 2: número de amenidades e indicadores 0/1 por nombre EXACTO (config.AMENITY_FLAGS).

    Solo cuenta el nombre exacto: "Pool table" (una mesa de billar) no activa amenity_pool. Una lista vacía da 0; un
    texto que no es una lista deja el conteo y los indicadores vacíos (se imputan dentro del modelo).
    """

    def __init__(self, flags=None):
        self.flags = flags

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        flags = self.flags if self.flags is not None else AMENITY_FLAGS
        lists = X["amenities"].map(_parse_list)
        out = X.copy()
        out["amenities_count"] = lists.map(lambda items: np.nan if items is None else len(items)).astype(float)
        for column, name in flags.items():
            out[column] = lists.map(lambda items: np.nan if items is None else float(name in items)).astype(float)
        return out


class CapacityRatios(TransformerMixin, BaseEstimator):
    """Idea 3: personas por habitación, personas por baño y camas por persona.

    0 habitaciones es un estudio y cuenta como 1; 0 baños o 0 de capacidad dejan la razón vacía (no se divide por 0).
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        people = X["accommodates"].astype(float)
        bathrooms = X["bathrooms_count"].astype(float)
        out["people_per_bedroom"] = people / np.maximum(X["bedrooms"].astype(float), 1)
        out["people_per_bathroom"] = people / bathrooms.where(bathrooms > 0)
        out["beds_per_person"] = X["beds"].astype(float) / people.where(people > 0)
        return out


class HostProfile(TransformerMixin, BaseEstimator):
    """Idea 4: antigüedad del anfitrión y de su cuenta en años (años + meses / 12) e indicadores t/f como 1/0.

    Los cinco conteos de anuncios del anfitrión se usan tal cual (no necesitan cálculo).
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        out["host_tenure_years"] = X["hosts_time_as_host_years"] + X["hosts_time_as_host_months"] / 12
        out["user_tenure_years"] = X["hosts_time_as_user_years"] + X["hosts_time_as_user_months"] / 12
        for column in ("host_has_profile_pic", "host_identity_verified"):
            out[column] = true_false(X[column])
        return out


class SuspiciousFeatures(TransformerMixin, BaseEstimator):
    """Solo para la medición "con sospechosas": nunca va al torneo, a la optimización ni a la app.

    Convierte las fechas de reseñas en días hasta el corte de la ciudad (last_scraped se usa como fecha de referencia,
    no como variable) y los t/f de has_availability y host_is_superhost en 1/0.
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        cut = pd.to_datetime(X["last_scraped"])
        for column, source in (("days_since_first_review", "first_review"), ("days_since_last_review", "last_review")):
            out[column] = (cut - pd.to_datetime(X[source])).dt.days.astype(float)
        for column in ("has_availability", "host_is_superhost"):
            out[column] = true_false(X[column])
        return out
