"""Etapa 7: por qué el modelo sugiere el precio que sugiere (valores SHAP sobre el Pipeline de LightGBM).

Límites que se escriben en el informe: los aportes explican al MODELO, no al mundo (no dicen si acertó); las variables
correlacionadas (latitud, longitud, barrio, ciudad) se reparten el crédito; una importancia alta no es causa.
Los aportes están en la escala del modelo (logaritmo del precio): un aporte de +0,10 sube el precio cerca de un 10 %.
"""
import numpy as np
import pandas as pd
import shap


def _output_columns(prep) -> list:
    """Nombre original de cada columna que sale del ColumnTransformer (en LightGBM cada entrada da una salida)."""
    names = []
    for name, _, columns in prep.transformers_:
        if name != "remainder":
            names.extend(columns)
    return names


def shap_values(pipeline, X: pd.DataFrame) -> pd.DataFrame:
    """Aportes SHAP (en logaritmo) de cada columna original para cada anuncio de X.

    El valor base queda en `resultado.attrs["base_value"]`: base + suma de aportes = predicción del modelo.
    """
    prep, model = pipeline[:-1], pipeline[-1]
    transformed = np.asarray(prep.transform(X), dtype=float)
    columns = _output_columns(prep[-1])
    if len(columns) != transformed.shape[1]:
        raise ValueError(f"Se esperaban {len(columns)} columnas transformadas y hay {transformed.shape[1]}")
    explainer = shap.TreeExplainer(model)
    values = np.asarray(explainer.shap_values(transformed), dtype=float)
    contributions = pd.DataFrame(values, columns=columns, index=X.index)
    contributions.attrs["base_value"] = float(np.ravel(explainer.expected_value)[0])
    return contributions


def global_importance(contributions: pd.DataFrame) -> pd.DataFrame:
    """Importancia global: promedio del aporte absoluto de cada columna, de mayor a menor."""
    importance = contributions.abs().mean().sort_values(ascending=False)
    return pd.DataFrame({"columna": importance.index, "importancia": importance.to_numpy()})


def top_contributions(contributions: pd.DataFrame, row: int, k: int = 5) -> pd.DataFrame:
    """Los k aportes más grandes (en valor absoluto) de un anuncio, por su posición en la tabla."""
    values = contributions.iloc[row]
    order = values.abs().sort_values(ascending=False).index[:k]
    return pd.DataFrame({"columna": order, "aporte": values[order].to_numpy()})
