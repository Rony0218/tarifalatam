"""Optimización de hiperparámetros con Optuna, con cada ensayo registrado en MLflow, y la comprobación honesta.

Reglas aprobadas antes de buscar (especificaciones/04-features-torneo-optimizacion.md, sección 6):
  - solo los finalistas del torneo, con 30 ensayos por finalista y los rangos de estos espacios de búsqueda;
  - la búsqueda usa los pliegues de folds.csv restringidos a los anfitriones de búsqueda (data/folds.py);
  - UN ENSAYO = UNA EJECUCIÓN en MLflow, registrada con log_run de tracking/mlflow_utils.py (no se reescribe);
  - la mejor puntuación de la búsqueda es optimista: la decisión se toma en el 25 % de anfitriones reservados, con un
    intervalo del 95 % que remuestrea anfitriones completos. Se usan los parámetros optimizados solo si TODO el
    intervalo está por debajo de cero.
"""
import json
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

from tarifalatam.config import BOOTSTRAP_N, GROUP_COL, N_TRIALS, RANDOM_STATE, TARGET
from tarifalatam.models.train import build_pipeline, evaluate_folds, feature_frame, usd_metrics
from tarifalatam.tracking.mlflow_utils import log_run


def lgbm_space(trial: optuna.Trial) -> dict:
    """Espacio de LightGBM: los rangos salen del conocimiento del algoritmo (guía, sección 3.2), no del azar."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 200, 1000),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 255),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 200),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
    }


def rf_space(trial: optuna.Trial) -> dict:
    """Espacio del bosque aleatorio. Los árboles se fijan en 200: lo que se afina es su forma."""
    return {
        "max_depth": trial.suggest_int("max_depth", 8, 40),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 20),
        "max_features": trial.suggest_float("max_features", 0.2, 1.0),
    }


def ridge_space(trial: optuna.Trial) -> dict:
    """Espacio de Ridge: solo la fuerza de la regularización, en escala logarítmica."""
    return {"alpha": trial.suggest_float("alpha", 1e-3, 1e3, log=True)}


SPACES = {"lightgbm": lgbm_space, "random_forest": rf_space, "ridge": ridge_space}
FAMILIES = {"lightgbm": "boosting", "random_forest": "forest", "ridge": "linear"}


def make_model(name: str, params: dict, random_state: int = RANDOM_STATE):
    """Arma el modelo de un finalista con los parámetros de un ensayo, con las semillas fijadas."""
    if name == "lightgbm":
        return LGBMRegressor(subsample_freq=1, random_state=random_state, n_jobs=-1, verbose=-1, **params)
    if name == "random_forest":
        return RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=random_state, **params)
    if name == "ridge":
        return Ridge(**params)
    raise ValueError(f"No hay espacio de búsqueda para {name!r}. Opciones: {sorted(SPACES)}")


def tune(name: str, X: pd.DataFrame, y_log, folds, n_trials: int = N_TRIALS, seed: int = RANDOM_STATE, ideas=(),
         log: bool = True) -> optuna.Study:
    """Busca hiperparámetros minimizando el MAE medio en USD; cada ensayo queda como una ejecución en MLflow.

    MLflow debe estar configurado antes (configure_mlflow y set_experiment). Un ensayo que falla queda registrado con
    estado=fallido y cuenta en el presupuesto: nunca se hacen más de n_trials.
    """
    if name not in SPACES:
        raise ValueError(f"No hay espacio de búsqueda para {name!r}. Opciones: {sorted(SPACES)}")
    tags = {"etapa": "06_optimizacion", "modelo": name, "variables": "sin_sospechosas", "datos": "train.csv.gz"}

    def objective(trial: optuna.Trial) -> float:
        params = SPACES[name](trial)
        run_name = f"{name}-ensayo-{trial.number + 1:02d}"
        try:
            pipeline = build_pipeline(make_model(name, params), FAMILIES[name], ideas=ideas)
            table, _ = evaluate_folds(pipeline, X, y_log, folds)
        except Exception as error:
            if log:
                reason = f"{type(error).__name__}: {error}"[:250]
                log_run(run_name, params, {}, tags={**tags, "estado": "fallido", "error": reason})
            raise
        metrics = {
            "mae": table["mae"].mean(),
            "mae_std": table["mae"].std(),
            "mape": table["mape"].mean(),
            "rmse": table["rmse"].mean(),
            "bias": table["bias"].mean(),
            "r2_log": table["r2_log"].mean(),
            "fit_seconds": table["fit_seconds"].mean(),
        }
        for key, value in metrics.items():
            trial.set_user_attr(key, float(value))
        if log:
            log_run(run_name, params, metrics, tags={**tags, "estado": "completo"})
        return float(metrics["mae"])

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed), study_name=f"tarifalatam-{name}"
    )
    study.optimize(objective, n_trials=n_trials, catch=(Exception,))
    return study


def trials_table(study: optuna.Study, name: str) -> pd.DataFrame:
    """Una fila por ensayo: número, estado, hiperparámetros y métricas (lo mismo que quedó en MLflow)."""
    rows = []
    for trial in study.trials:
        state = "completo" if trial.state == optuna.trial.TrialState.COMPLETE else "fallido"
        rows.append({"model": name, "trial": trial.number + 1, "state": state, **trial.params, **trial.user_attrs})
    return pd.DataFrame(rows)


def host_bootstrap_ci(diff_per_row, hosts, n: int = BOOTSTRAP_N, seed: int = RANDOM_STATE, block: int = 100):
    """Media de una diferencia por anuncio y su intervalo del 95 %, remuestreando ANFITRIONES completos.

    Remuestrear filas sería un error: los anuncios de un mismo anfitrión no son independientes. Los remuestreos se
    calculan en bloques para no crear de una vez una matriz de n × (número de anfitriones).
    Devuelve (media, límite inferior, límite superior).
    """
    per_host = pd.DataFrame({"host": np.asarray(hosts), "diff": np.asarray(diff_per_row, dtype=float)})
    per_host = per_host.groupby("host")["diff"].agg(["sum", "count"])
    sums, counts = per_host["sum"].to_numpy(), per_host["count"].to_numpy()
    rng = np.random.default_rng(seed)
    means = []
    for start in range(0, n, block):
        idx = rng.integers(0, len(sums), size=(min(block, n - start), len(sums)))
        means.append(sums[idx].sum(axis=1) / counts[idx].sum(axis=1))
    means = np.concatenate(means)
    return float(sums.sum() / counts.sum()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def use_optimized(low: float, high: float) -> bool:
    """Regla escrita antes de mirar: los optimizados se usan solo si todo el intervalo está por debajo de cero."""
    return bool(high < 0)


def paired_abs_error_difference(y_true_log, pred_a_log, pred_b_log) -> np.ndarray:
    """|error de A| − |error de B| en USD, anuncio por anuncio. Negativo: A se equivoca menos que B."""
    true = np.exp(np.asarray(y_true_log, dtype=float))
    error_a = np.abs(np.exp(np.asarray(pred_a_log, dtype=float)) - true)
    error_b = np.abs(np.exp(np.asarray(pred_b_log, dtype=float)) - true)
    return error_a - error_b


def compare_on_reserved(pipeline_a, pipeline_b, search: pd.DataFrame, reserved: pd.DataFrame, n: int = BOOTSTRAP_N,
                        seed: int = RANDOM_STATE) -> dict:
    """Comprobación honesta: ajusta A y B con los datos de búsqueda y los compara en los anfitriones reservados.

    Devuelve el MAE y el sesgo de cada uno y la diferencia de MAE (A − B) con su intervalo del 95 % por anfitrión.
    """
    X_search, y_search = feature_frame(search), search[TARGET].to_numpy()
    X_reserved, y_reserved = feature_frame(reserved), reserved[TARGET].to_numpy()
    pred_a = clone(pipeline_a).fit(X_search, y_search).predict(X_reserved)
    pred_b = clone(pipeline_b).fit(X_search, y_search).predict(X_reserved)
    diff = paired_abs_error_difference(y_reserved, pred_a, pred_b)
    mean, low, high = host_bootstrap_ci(diff, reserved[GROUP_COL], n=n, seed=seed)
    metrics_a, metrics_b = usd_metrics(y_reserved, pred_a), usd_metrics(y_reserved, pred_b)
    return {
        "hosts": int(reserved[GROUP_COL].nunique()),
        "listings": int(len(reserved)),
        "mae_a": metrics_a["mae"],
        "mae_b": metrics_b["mae"],
        "bias_a": metrics_a["bias"],
        "bias_b": metrics_b["bias"],
        "mean_difference": mean,
        "low": low,
        "high": high,
    }


# Claves de reports/06_best_params.json (specs/002-features-torneo-optimizacion/contracts/output-files.md)
DECISION_KEYS = [
    "finalista",
    "parametros",
    "origen_parametros",
    "comprobacion",
    "regla",
    "comparacion_finalistas",
    "tracking",
    "experimento",
    "ensayos",
]


def save_decision(path, decision: dict) -> None:
    """Guarda la decisión de la etapa 6 en JSON; falla si falta alguna clave del contrato."""
    missing = [key for key in DECISION_KEYS if key not in decision]
    if missing:
        raise ValueError(f"A la decisión le faltan claves: {missing}")
    Path(path).write_text(json.dumps(decision, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
