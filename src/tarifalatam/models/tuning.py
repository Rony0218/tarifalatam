"""Optimización de hiperparámetros con Optuna, con cada ensayo registrado en MLflow, y la comprobación honesta.

Reglas aprobadas antes de buscar (especificaciones/04-features-torneo-optimizacion.md, sección 6):
  - solo los finalistas del torneo, con 30 ensayos por finalista y los rangos de estos espacios de búsqueda;
  - la búsqueda usa los pliegues de folds.csv restringidos a los anfitriones de búsqueda (data/folds.py);
  - UN ENSAYO = UNA EJECUCIÓN en MLflow, registrada con log_run de tracking/mlflow_utils.py (no se reescribe);
  - la mejor puntuación de la búsqueda es optimista: la decisión se toma en el 25 % de anfitriones reservados, con un
    intervalo del 95 % que remuestrea anfitriones completos. Se usan los parámetros optimizados solo si TODO el
    intervalo está por debajo de cero;
  - entre dos finalistas, pasa el que se equivoca menos en todo el intervalo; si cruza el cero, el más rápido de ajustar
    con su configuración elegida (choose_finalist).
"""
import contextlib
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
from tarifalatam.data.split import assert_disjoint_hosts
from tarifalatam.models.train import build_pipeline, candidates, evaluate_folds, feature_frame, usd_metrics
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
FINALIST_FAMILIES = {"lightgbm": "boosting", "random_forest": "forest", "ridge": "linear"}

# Parámetros que make_model fija siempre y que NO están en los parámetros de un ensayo. La etapa 7 debe armar el modelo
# con make_model para que sean los mismos: sin subsample_freq=1, LightGBM ignora subsample (auditoría del 2026-10-31).
FIXED_PARAMS = {
    "lightgbm": {"subsample_freq": 1, "random_state": RANDOM_STATE, "n_jobs": -1, "verbose": -1},
    "random_forest": {"n_estimators": 200, "random_state": RANDOM_STATE, "n_jobs": -1},
    "ridge": {},
}
MODEL_CLASSES = {"lightgbm": LGBMRegressor, "random_forest": RandomForestRegressor, "ridge": Ridge}


def make_model(name: str, params: dict):
    """Arma el modelo de un finalista con los parámetros de un ensayo y los parámetros fijos (FIXED_PARAMS)."""
    if name not in MODEL_CLASSES:
        raise ValueError(f"No hay espacio de búsqueda para {name!r}. Opciones: {sorted(SPACES)}")
    return MODEL_CLASSES[name](**FIXED_PARAMS[name], **params)


# Parámetros de partida de cada finalista que se informan en la decisión (los que cambió el torneo respecto del valor
# por defecto de la librería)
STARTING_KEYS = {
    "lightgbm": ["n_estimators", "learning_rate", "num_leaves"],
    "random_forest": ["n_estimators", "min_samples_leaf", "max_features"],
    "ridge": ["alpha"],
}


def starting_params(name: str) -> dict:
    """Parámetros de partida (los del torneo, models/train.py:candidates) de un finalista."""
    model = candidates()[name][0]
    return {key: model.get_params()[key] for key in STARTING_KEYS[name]}


def construction_info(name: str) -> dict:
    """Cómo se vuelve a armar el modelo de un finalista (va en reports/06_best_params.json para la etapa 7)."""
    return {
        "como_se_arma": f"make_model('{name}', parametros) de src/tarifalatam/models/tuning.py, dentro de build_pipeline",
        "parametros_fijos": dict(FIXED_PARAMS[name]),
    }


def tune(name: str, X: pd.DataFrame, y_log, folds, n_trials: int = N_TRIALS, seed: int = RANDOM_STATE, ideas=(),
         log: bool = True) -> optuna.Study:
    """Busca hiperparámetros minimizando el MAE medio en USD; cada ensayo queda como una ejecución en MLflow.

    MLflow debe estar configurado antes (configure_mlflow y set_experiment); con log=False no se registra nada. Un
    ensayo que falla queda registrado con estado=fallido y cuenta en el presupuesto: nunca se hacen más de n_trials.
    Si fallan TODOS, se detiene con el error del primero (suele ser un error de programación, no de un ensayo).
    """
    if name not in SPACES:
        raise ValueError(f"No hay espacio de búsqueda para {name!r}. Opciones: {sorted(SPACES)}")
    tags = {"etapa": "06_optimizacion", "modelo": name, "variables": "sin_sospechosas", "datos": "train.csv.gz"}

    def objective(trial: optuna.Trial) -> float:
        params = SPACES[name](trial)
        run_name = f"{name}-ensayo-{trial.number + 1:02d}"
        try:
            pipeline = build_pipeline(make_model(name, params), FINALIST_FAMILIES[name], ideas=ideas)
            table, _ = evaluate_folds(pipeline, X, y_log, folds)
            metrics = {
                "mae": table["mae"].mean(),
                "mae_std": table["mae"].std(),
                "mape": table["mape"].mean(),
                "rmse": table["rmse"].mean(),
                "bias": table["bias"].mean(),
                "r2_log": table["r2_log"].mean(),
                "fit_seconds": table["fit_seconds"].mean(),
            }
            if log:
                log_run(run_name, params, metrics, tags={**tags, "estado": "completo"})
        except Exception as error:
            reason = f"{type(error).__name__}: {error}"[:250]
            trial.set_user_attr("error", reason)
            if log:
                # Registro del fallo "si se puede": si MLflow también falla, igual se propaga el error original
                with contextlib.suppress(Exception):
                    log_run(run_name, params, {}, tags={**tags, "estado": "fallido", "error": reason})
            raise
        for key, value in metrics.items():
            trial.set_user_attr(key, float(value))
        return float(metrics["mae"])

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed), study_name=f"tarifalatam-{name}"
    )
    study.optimize(objective, n_trials=n_trials, catch=(Exception,))
    if not any(t.state == optuna.trial.TrialState.COMPLETE for t in study.trials):
        first_error = study.trials[0].user_attrs.get("error", "sin detalle") if study.trials else "ningún ensayo"
        raise RuntimeError(f"Fallaron los {len(study.trials)} ensayos de {name}. Primer error: {first_error}")
    return study


def trials_table(study: optuna.Study, name: str) -> pd.DataFrame:
    """Una fila por ensayo: número, estado, hiperparámetros y métricas (lo mismo que quedó en MLflow)."""
    names = {optuna.trial.TrialState.COMPLETE: "completo", optuna.trial.TrialState.FAIL: "fallido"}
    rows = []
    for trial in study.trials:
        state = names.get(trial.state, trial.state.name.lower())
        rows.append({"model": name, "trial": trial.number + 1, "state": state, **trial.params, **trial.user_attrs})
    return pd.DataFrame(rows)


def host_bootstrap_ci(diff_per_row, hosts, n: int = BOOTSTRAP_N, seed: int = RANDOM_STATE, block: int = 100):
    """Media de una diferencia por anuncio y su intervalo del 95 %, remuestreando ANFITRIONES completos.

    Remuestrear filas sería un error: los anuncios de un mismo anfitrión no son independientes. Los remuestreos se
    calculan en bloques para no crear de una vez una matriz de n × (número de anfitriones).
    Devuelve (media, límite inferior, límite superior).
    """
    per_host = pd.DataFrame({"host": np.asarray(hosts), "diff": np.asarray(diff_per_row, dtype=float)})
    if per_host["host"].isna().any():
        raise ValueError(f"{per_host['host'].isna().sum()} anuncios sin anfitrión: se perderían al agrupar")
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
    """Regla escrita antes de mirar: los optimizados se usan solo si todo el intervalo está por debajo de cero.

    Basta mirar el límite superior: si está por debajo de cero, todo el intervalo lo está.
    """
    return bool(high < 0)


def choose_finalist(a: str, b: str, low: float, high: float, seconds: dict) -> tuple:
    """Regla entre dos finalistas, con el intervalo de la diferencia de error (A − B) en los anfitriones reservados.

    Pasa A si todo el intervalo está por debajo de cero, B si todo está por encima. Si cruza (o toca) el cero es un
    empate y pasa el más rápido de ajustar con SU configuración elegida (seconds: segundos por pliegue de cada uno).
    Devuelve (ganador, motivo).
    """
    if high < 0:
        return a, f"{a} se equivoca menos en todo el intervalo"
    if low > 0:
        return b, f"{b} se equivoca menos en todo el intervalo"
    winner = min((a, b), key=lambda name: seconds[name])
    return winner, (
        f"el intervalo cruza el cero: empate; pasa el más rápido de ajustar con su configuración elegida ({winner}: "
        f"{seconds[winner]:.2f} s por pliegue frente a {seconds[b if winner == a else a]:.2f} s)"
    )


def paired_abs_error_difference(y_true_log, pred_a_log, pred_b_log) -> np.ndarray:
    """|error de A| − |error de B| en USD, anuncio por anuncio. Negativo: A se equivoca menos que B."""
    true = np.exp(np.asarray(y_true_log, dtype=float))
    error_a = np.abs(np.exp(np.asarray(pred_a_log, dtype=float)) - true)
    error_b = np.abs(np.exp(np.asarray(pred_b_log, dtype=float)) - true)
    return error_a - error_b


def compare_on_reserved(pipeline_a, pipeline_b, search: pd.DataFrame, reserved: pd.DataFrame, n: int = BOOTSTRAP_N,
                        seed: int = RANDOM_STATE) -> dict:
    """Comprobación honesta: ajusta A y B con los datos de búsqueda y los compara en los anfitriones reservados.

    Se detiene si búsqueda y reservados comparten algún anfitrión. Devuelve el MAE y el sesgo de cada uno y la
    diferencia de MAE (A − B) con su intervalo del 95 % por anfitrión.
    """
    assert_disjoint_hosts(search, reserved)
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
    "regla_elegiria",
    "decision_del_grupo",
    "como_se_arma",
    "parametros_fijos",
    "tracking",
    "experimento",
    "ensayos",
]


def _to_native(value):
    """Convierte números de numpy a tipos de Python, para que el JSON guarde 60 y no 60.0."""
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"No se puede guardar en JSON un valor de tipo {type(value).__name__}")


def save_decision(path, decision: dict) -> None:
    """Guarda la decisión de la etapa 6 en JSON; falla si falta una clave del contrato o hay un valor infinito."""
    missing = [key for key in DECISION_KEYS if key not in decision]
    if missing:
        raise ValueError(f"A la decisión le faltan claves: {missing}")
    text = json.dumps(decision, indent=2, ensure_ascii=False, default=_to_native, allow_nan=False)
    Path(path).write_text(text, encoding="utf-8")
