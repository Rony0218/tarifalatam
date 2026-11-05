"""Etapa 7: validación del modelo final. La prueba se abre UNA sola vez, con las decisiones ya congeladas.

Qué hay aquí (especificaciones/07-validacion-registro-app.md y specs/003-validacion-registro-app/research.md):

- `open_test`: la única puerta a la prueba. Deja constancia de cada lectura, con su propósito, en
  reports/prueba_abierta.txt. La ruta del archivo la pasan los notebooks 07 y 09: ninguna función de src/ la conoce.
- Antes de abrir la prueba, con los anfitriones reservados de la etapa 6: el factor de corrección al volver del
  logaritmo (`check_log_correction`) y el rango típico de cada ciudad (`price_range_ratios`).
- Con la prueba: métricas en USD con los costos asimétricos (`test_metrics`), intervalos por anfitrión (`mae_with_ci`,
  `paired_mae_difference`), errores por segmento (`segment_errors`) y la meta escrita antes de mirar (`success_goal`).
"""
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GroupKFold

from tarifalatam.config import (
    BOOTSTRAP_N,
    COST_RATIOS,
    GOAL_IMPROVEMENT,
    GROUP_COL,
    RANDOM_STATE,
    RANGE_QUANTILES,
    TARGET,
    TEST_MARK_PATH,
)
from tarifalatam.data.split import assert_disjoint_hosts
from tarifalatam.models.price import to_usd_price  # la misma conversión que usa la app
from tarifalatam.models.train import feature_frame, usd_metrics
from tarifalatam.models.tuning import host_bootstrap_ci, paired_abs_error_difference, use_optimized


# --- La prueba -----------------------------------------------------------------------------------------------------

def open_test(path, mark_path=TEST_MARK_PATH, purpose: str = "") -> pd.DataFrame:
    """Lee la prueba y anota la lectura en la marca: 'Primera apertura' la primera vez, 'Nueva lectura' después.

    `purpose` es obligatorio: dice para qué se lee (p. ej. "evaluación única de la etapa 7"). Si la prueba ya se había
    abierto, avisa: cualquier decisión tomada después de verla ya no la puede juzgar la prueba.
    """
    path, mark_path = Path(path), Path(mark_path)
    if not path.name.startswith("test"):
        raise ValueError(f"{path.name} no es la prueba: open_test solo lee el archivo de prueba de data/processed/")
    if not purpose.strip():
        raise ValueError("Falta el propósito de la lectura: queda escrito en la marca de la prueba")
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}: se genera en notebooks/03_preprocesamiento.ipynb")
    stamp = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    if mark_path.exists():
        warnings.warn(
            f"La prueba ya se había abierto (ver {mark_path.name}). Esta lectura queda anotada; no la uses para decidir.",
            UserWarning,
            stacklevel=2,
        )
        line = f"Nueva lectura: {stamp} · propósito: {purpose.strip()}"
    else:
        line = f"Primera apertura: {stamp} · propósito: {purpose.strip()}"
    mark_path.parent.mkdir(parents=True, exist_ok=True)
    with mark_path.open("a", encoding="utf-8") as mark:
        mark.write(line + "\n")
    return pd.read_csv(path, low_memory=False)


# --- Antes de abrir la prueba: factor del logaritmo y rango típico (anfitriones reservados) -----------------------

def oof_log_predictions(pipeline, X: pd.DataFrame, y_log, groups, n_splits: int = 5, seed: int = RANDOM_STATE) -> np.ndarray:
    """Predicciones fuera de pliegue, con pliegues por anfitrión: ningún anuncio es predicho por un modelo que vio a su
    anfitrión."""
    y_log = np.asarray(y_log, dtype=float)
    oof = np.full(len(X), np.nan)
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for fit_idx, valid_idx in splitter.split(X, y_log, groups=np.asarray(groups)):
        model = clone(pipeline).fit(X.iloc[fit_idx], y_log[fit_idx])
        oof[valid_idx] = model.predict(X.iloc[valid_idx])
    return oof


def smearing_factor(residuals_log) -> float:
    """Factor de Duan: promedio de exp(residuo). Con residuos nulos vale 1 (no hay nada que corregir)."""
    return float(np.mean(np.exp(np.asarray(residuals_log, dtype=float))))


def check_log_correction(pipeline, search: pd.DataFrame, reserved: pd.DataFrame, n: int = BOOTSTRAP_N,
                         seed: int = RANDOM_STATE) -> dict:
    """Comprobación con los anfitriones reservados (nunca con la prueba) de si conviene el factor de Duan.

    El factor sale de residuos fuera de pliegue en la búsqueda; el modelo se ajusta con toda la búsqueda y se compara en
    los reservados el error con y sin factor. Regla aprobada: se usa solo si todo el intervalo de
    |error con factor| − |error sin factor| queda por debajo de cero. Devuelve también las predicciones (en logaritmo)
    de los reservados, que sirven para el rango típico sin volver a ajustar.
    """
    assert_disjoint_hosts(search, reserved)
    X_search, y_search = feature_frame(search), search[TARGET].to_numpy()
    X_reserved, y_reserved = feature_frame(reserved), reserved[TARGET].to_numpy()
    oof = oof_log_predictions(pipeline, X_search, y_search, search[GROUP_COL], seed=seed)
    factor = smearing_factor(y_search - oof)
    pred_reserved = clone(pipeline).fit(X_search, y_search).predict(X_reserved)
    with_factor = pred_reserved + np.log(factor)
    diff = paired_abs_error_difference(y_reserved, with_factor, pred_reserved)
    mean, low, high = host_bootstrap_ci(diff, reserved[GROUP_COL], n=n, seed=seed)
    return {
        "factor": factor,
        "mae_sin": usd_metrics(y_reserved, pred_reserved)["mae"],
        "mae_con": usd_metrics(y_reserved, with_factor)["mae"],
        "media": mean,
        "low": low,
        "high": high,
        "se_usa": use_optimized(low, high),
        "anfitriones_reservados": int(reserved[GROUP_COL].nunique()),
        "anuncios_reservados": int(len(reserved)),
        "pred_reserved_log": pred_reserved,
    }


def price_range_ratios(cities, y_true_usd, y_pred_usd, quantiles=RANGE_QUANTILES) -> dict:
    """Rango típico por ciudad: percentiles de la razón precio real / precio sugerido.

    El rango que ve el usuario es [sugerido × p25, sugerido × p75]: en anfitriones que el modelo no vio, la mitad de
    los anuncios de esa ciudad quedó dentro de él.
    """
    frame = pd.DataFrame({
        "city": np.asarray(cities),
        "ratio": np.asarray(y_true_usd, dtype=float) / np.asarray(y_pred_usd, dtype=float),
    })
    return {
        str(city): [float(np.quantile(group["ratio"], q)) for q in quantiles]
        for city, group in frame.groupby("city")
    }


def asymmetric_cost(y_true_usd, y_pred_usd, over: float = 2.0, under: float = 1.0) -> float:
    """Promedio de [over × máx(sugerido − real, 0) + under × máx(real − sugerido, 0)], en USD por noche.

    Con over=2 y under=1, sobrestimar 10 USD cuesta 20 y subestimar 10 USD cuesta 10 (PR #5; un supuesto, no una medición).
    """
    error = np.asarray(y_pred_usd, dtype=float) - np.asarray(y_true_usd, dtype=float)
    return float(np.mean(over * np.maximum(error, 0) + under * np.maximum(-error, 0)))


# --- Con la prueba -------------------------------------------------------------------------------------------------

def _cost_key(over: float, under: float) -> str:
    return f"cost_{over:g}_{under:g}"


def test_metrics(y_true_log, y_pred_log, factor: float = 1.0) -> dict:
    """Las métricas del torneo (MAE, MAPE, RMSE, sesgo en USD y R² en logaritmo) más los costos de COST_RATIOS."""
    y_true_log = np.asarray(y_true_log, dtype=float)
    pred_log = np.asarray(y_pred_log, dtype=float) + np.log(float(factor))
    metrics = usd_metrics(y_true_log, pred_log)
    true_usd, pred_usd = np.exp(y_true_log), np.exp(pred_log)
    for over, under in COST_RATIOS:
        metrics[_cost_key(over, under)] = asymmetric_cost(true_usd, pred_usd, over, under)
    return metrics


def mae_with_ci(y_true_log, y_pred_log, hosts, factor: float = 1.0, n: int = BOOTSTRAP_N, seed: int = RANDOM_STATE) -> dict:
    """MAE en USD con su intervalo del 95 %, remuestreando anfitriones completos."""
    abs_error = np.abs(to_usd_price(y_pred_log, factor) - np.exp(np.asarray(y_true_log, dtype=float)))
    mae, low, high = host_bootstrap_ci(abs_error, hosts, n=n, seed=seed)
    return {"mae": mae, "low": low, "high": high}


def paired_mae_difference(y_true_log, pred_a_log, pred_b_log, hosts, factor_a: float = 1.0, factor_b: float = 1.0,
                          n: int = BOOTSTRAP_N, seed: int = RANDOM_STATE) -> dict:
    """MAE de A − MAE de B (anuncio por anuncio) con su intervalo del 95 % por anfitrión. Negativo: A se equivoca menos."""
    a = np.asarray(pred_a_log, dtype=float) + np.log(float(factor_a))
    b = np.asarray(pred_b_log, dtype=float) + np.log(float(factor_b))
    diff = paired_abs_error_difference(y_true_log, a, b)
    mean, low, high = host_bootstrap_ci(diff, hosts, n=n, seed=seed)
    return {"mean": mean, "low": low, "high": high}


def segment_errors(frame: pd.DataFrame, by: str, true_col: str = "price_usd", pred_col: str = "pred_usd") -> pd.DataFrame:
    """Error por segmento: anuncios, MAE, MAPE (%), sesgo, % de anuncios sobrestimados y cuántos tienen un error mayor a
    la mitad de su precio real."""
    error = frame[pred_col].astype(float) - frame[true_col].astype(float)
    work = pd.DataFrame({
        by: frame[by].to_numpy(),
        "abs_error": error.abs().to_numpy(),
        # un precio real de 0 o menos no tiene error porcentual: queda fuera del MAPE (revisión de código, 2026-11-05)
        "pct_error": (error.abs() / frame[true_col].astype(float).where(frame[true_col] > 0) * 100).to_numpy(),
        "error": error.to_numpy(),
        "over": (error > 0).to_numpy(),
        "over_half": (error.abs() > 0.5 * frame[true_col].astype(float)).to_numpy(),
    })
    grouped = work.groupby(by)
    return pd.DataFrame({
        "n": grouped.size(),
        "mae": grouped["abs_error"].mean(),
        "mape": grouped["pct_error"].mean(),
        "bias": grouped["error"].mean(),
        "pct_over": grouped["over"].mean() * 100,
        "n_error_over_half": grouped["over_half"].sum().astype(int),
    }).reset_index()


def success_goal(model_mae: float, baseline_mae: float, diff_high: float, city_mae: pd.DataFrame) -> dict:
    """La meta escrita antes de abrir la prueba (PR #5). Se cumple solo con las tres condiciones:

    (a) MAE del modelo al menos GOAL_IMPROVEMENT (20 %) menor que el de la línea base;
    (b) el intervalo del 95 % de la diferencia (modelo − línea base) entero bajo cero (`diff_high` < 0);
    (c) en ninguna ciudad el MAE del modelo es mayor que el de la línea base (`city_mae`: city, mae_model, mae_baseline).
    """
    if baseline_mae <= 0:
        raise ValueError("El MAE de la línea base debe ser positivo para medir la mejora")
    improvement = 1 - model_mae / baseline_mae
    worse = city_mae.loc[city_mae["mae_model"] > city_mae["mae_baseline"], "city"].astype(str).tolist()
    goal = {
        "mejora_pct": float(improvement * 100),
        "a_20pct": bool(improvement >= GOAL_IMPROVEMENT - 1e-12),
        "b_intervalo": bool(diff_high < 0),
        "c_ciudades": not worse,
        "ciudades_peores": worse,
    }
    goal["cumple"] = goal["a_20pct"] and goal["b_intervalo"] and goal["c_ciudades"]
    return goal
