"""Gráficas del informe técnico (specs/004-informe-tecnico-pdf, figuras F1 a F11).

Uso, desde la raíz del repositorio y con el entorno activado:

    python scripts/report_figures.py

Deja los PNG en reports/figuras/ y las cifras de la figura F11 en reports/figuras/F11_metricas.json.

De dónde sale cada figura:
- F1 a F5 (EDA): solo del entrenamiento procesado (data/processed/train.csv.gz).
- F6 a F8 (variables, torneo, optimización): de las tablas ya guardadas en reports/.
- F9 y F10 (resultados en la prueba): de reports/07_segmentos.csv y reports/07_shap_global.csv. La prueba NO se vuelve a
  abrir (constitución, principio III).
- F11 (real contra predicho): predicciones fuera de pliegue en el entrenamiento, con pliegues por anfitrión, del mismo
  LightGBM optimizado de la etapa 7 (decisión del grupo del 2026-11-11, opción A).
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventana: solo se guardan archivos
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401  (ejes logarítmicos con números normales)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figuras"

# Colores fijos para todo el informe: el modelo siempre en azul, la línea base siempre en gris
MODEL_COLOR = "#1f6f8b"
BASELINE_COLOR = "#a0a7b0"
ACCENT_COLOR = "#d9822b"
DPI = 150
# Cada modelo con el mismo color en todas las figuras (LightGBM, el elegido, siempre en azul)
MODEL_COLORS = {"linea_base": BASELINE_COLOR, "ridge": "#7b5ea7", "random_forest": ACCENT_COLOR, "lightgbm": MODEL_COLOR}
LOG_TICKS = [10, 20, 50, 100, 200, 500, 1000]

CITY_NAMES = {
    "belize": "Belice",
    "bogota": "Bogotá",
    "mexico-city": "Ciudad de México",
    "rio-de-janeiro": "Río de Janeiro",
    "santiago": "Santiago",
    "sao-paulo": "São Paulo",
}
MODEL_NAMES = {
    "linea_base": "Línea base",
    "ridge": "Ridge",
    "random_forest": "Bosque aleatorio",
    "lightgbm": "LightGBM",
}
ROOM_NAMES = {
    "Entire home/apt": "Vivienda entera",
    "Private room": "Habitación privada",
    "Hotel room": "Habitación de hotel",
    "Shared room": "Habitación compartida",
}
IDEA_NAMES = {
    "referencia": "Referencia (13 columnas)",
    "idea_1_distancia": "1. Distancia al centro",
    "idea_2_amenidades": "2. Amenidades",
    "idea_3_capacidad": "3. Capacidad relativa",
    "idea_4_anfitrion": "4. Perfil del anfitrión",
    "idea_5_barrio": "5. Nivel de precio del barrio",
}
# Las 8 numéricas del modelo (config.REFERENCE_NUMERIC) y el objetivo
CORRELATION_COLUMNS = {
    "accommodates": "huéspedes",
    "bedrooms": "habitaciones",
    "beds": "camas",
    "bathrooms_count": "baños",
    "minimum_nights": "noches mín.",
    "maximum_nights": "noches máx.",
    "latitude": "latitud",
    "longitude": "longitud",
    "log_price_usd": "log(precio USD)",
}
# Nombre en español de las 13 columnas del modelo (se muestra junto al nombre técnico)
SHAP_LABELS = {
    "bedrooms": "habitaciones",
    "accommodates": "huéspedes",
    "longitude": "longitud",
    "bathrooms_count": "baños",
    "latitude": "latitud",
    "neighbourhood_cleansed": "barrio",
    "city": "ciudad",
    "property_type": "tipo de propiedad",
    "room_type": "tipo de habitación",
    "minimum_nights": "noches mínimas",
    "bathroom_shared": "baño compartido",
    "maximum_nights": "noches máximas",
    "beds": "camas",
}
HOST_SIZE_BINS = [0, 1, 4, 9, np.inf]
HOST_SIZE_LABELS = ["1", "2 a 4", "5 a 9", "10 o más"]


def pretty_city(code: str) -> str:
    """Nombre en español de una ciudad; si no se conoce, se deja como viene."""
    return CITY_NAMES.get(code, code)


def pretty_model(code: str) -> str:
    """Nombre en español de un modelo; si no se conoce, se deja como viene."""
    return MODEL_NAMES.get(code, code)


def _save(fig, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def _style() -> None:
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
    plt.rcParams["axes.titleweight"] = "bold"


def _plain_log_axis(axis, low: float, high: float) -> None:
    """Eje logarítmico con números normales (20, 50, 100…) en vez de 2×10¹, y sin marcas menores con texto."""
    ticks = [t for t in LOG_TICKS if low <= t <= high]
    axis.set_major_locator(matplotlib.ticker.FixedLocator(ticks))
    axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    axis.set_minor_formatter(matplotlib.ticker.NullFormatter())


# --- Cálculos pequeños (con prueba) -------------------------------------------------------------------------------

def host_size_shares(train: pd.DataFrame) -> pd.DataFrame:
    """Cuántos anuncios (y qué % del total) son de anfitriones con 1, 2 a 4, 5 a 9 o 10 o más anuncios."""
    size = train.groupby("host_id")["host_id"].transform("size")
    bucket = pd.cut(size, bins=HOST_SIZE_BINS, labels=HOST_SIZE_LABELS)
    listings = bucket.value_counts().reindex(HOST_SIZE_LABELS, fill_value=0)
    out = pd.DataFrame({"listings": listings})
    out["share"] = out["listings"] / out["listings"].sum() * 100
    out.index = out.index.astype(str)
    return out


def ideas_summary(table: pd.DataFrame) -> pd.DataFrame:
    """MAE medio y desviación entre pliegues de la referencia y de las cinco ideas (sin las variantes finales)."""
    keep = [v for v in IDEA_NAMES if v in set(table["variant"])]
    summary = table[table["variant"].isin(keep)].groupby("variant")["mae"].agg(["mean", "std"])
    return summary.reindex(keep)


# --- F1 a F5: EDA, solo con el entrenamiento ----------------------------------------------------------------------

def plot_listings_by_city(train: pd.DataFrame, path) -> Path:
    """F1. Anuncios y anfitriones por ciudad."""
    _style()
    counts = train.groupby("city").agg(anuncios=("city", "size"), anfitriones=("host_id", "nunique"))
    counts = counts.sort_values("anuncios")
    counts.index = [pretty_city(c) for c in counts.index]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = np.arange(len(counts))
    ax.barh(y + 0.2, counts["anuncios"], height=0.4, color=MODEL_COLOR, label="Anuncios")
    ax.barh(y - 0.2, counts["anfitriones"], height=0.4, color=BASELINE_COLOR, label="Anfitriones")
    for i, (a, h) in enumerate(zip(counts["anuncios"], counts["anfitriones"])):
        ax.text(a, i + 0.2, f" {a:,}".replace(",", "."), va="center", fontsize=8)
        ax.text(h, i - 0.2, f" {h:,}".replace(",", "."), va="center", fontsize=8)
    ax.set_yticks(y, counts.index)
    ax.set_xlabel("Cantidad en el entrenamiento")
    ax.set_title("Anuncios y anfitriones por ciudad (entrenamiento)")
    ax.legend(loc="lower right")
    ax.set_xlim(0, counts["anuncios"].max() * 1.15)
    return _save(fig, path)


def plot_price_distribution(train: pd.DataFrame, path) -> Path:
    """F2. El precio en USD es muy asimétrico; su logaritmo es casi simétrico (por eso se modela log(precio))."""
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4))
    cap = train["price_usd"].quantile(0.99)
    axes[0].hist(train["price_usd"].clip(upper=cap), bins=60, color=BASELINE_COLOR)
    axes[0].set_title("Precio por noche (USD)")
    axes[0].set_xlabel(f"USD (cortado en el percentil 99 = {cap:,.0f})".replace(",", "."))
    axes[0].set_ylabel("Anuncios")
    axes[1].hist(train["log_price_usd"], bins=60, color=MODEL_COLOR)
    axes[1].set_title("Logaritmo del precio")
    axes[1].set_xlabel("log(precio USD): lo que predice el modelo")
    skew_raw, skew_log = train["price_usd"].skew(), train["log_price_usd"].skew()
    axes[0].text(0.95, 0.9, f"asimetría {skew_raw:.1f}", transform=axes[0].transAxes, ha="right")
    axes[1].text(0.95, 0.9, f"asimetría {skew_log:.1f}", transform=axes[1].transAxes, ha="right")
    return _save(fig, path)


def plot_price_by_city_room(train: pd.DataFrame, path) -> Path:
    """F3. Precio por ciudad y tipo de habitación (cajas en escala logarítmica, sin puntos extremos)."""
    _style()
    data = train.assign(
        ciudad=train["city"].map(pretty_city),
        tipo=train["room_type"].map(lambda r: ROOM_NAMES.get(r, r)),
    )
    order = data.groupby("ciudad")["price_usd"].median().sort_values().index
    hue_order = [r for r in ROOM_NAMES.values() if r in set(data["tipo"])]
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.boxplot(data=data, x="ciudad", y="price_usd", hue="tipo", order=order, hue_order=hue_order, showfliers=False,
                palette="Blues_r", ax=ax, linewidth=0.8)
    ax.set_yscale("log")
    _plain_log_axis(ax.yaxis, 1, 5000)
    ax.set_xlabel("")
    ax.set_ylabel("Precio por noche (USD, escala log)")
    ax.set_title("Precio por ciudad y tipo de habitación (entrenamiento)")
    ax.legend(title="", fontsize=8, loc="upper left")
    ax.tick_params(axis="x", labelsize=9)
    return _save(fig, path)


def plot_correlation(train: pd.DataFrame, path) -> Path:
    """F4. Matriz de correlación de Spearman (por rangos: no la dominan los precios extremos)."""
    _style()
    cols = [c for c in CORRELATION_COLUMNS if c in train.columns]
    corr = train[cols].corr(method="spearman").rename(index=CORRELATION_COLUMNS, columns=CORRELATION_COLUMNS)
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    fig, ax = plt.subplots(figsize=(7, 5.6))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, square=True,
                cbar_kws={"shrink": 0.7, "label": "Correlación de Spearman"}, annot_kws={"size": 8}, ax=ax)
    ax.set_title("Correlación entre las variables numéricas del modelo y el precio")
    return _save(fig, path)


def plot_host_concentration(train: pd.DataFrame, path) -> Path:
    """F5. Parte de los anuncios que es de anfitriones con varios anuncios: por eso se parte por anfitrión."""
    _style()
    shares = host_size_shares(train)
    fig, ax = plt.subplots(figsize=(8, 3))
    bars = ax.bar(shares.index, shares["share"], color=[BASELINE_COLOR, BASELINE_COLOR, MODEL_COLOR, MODEL_COLOR])
    for bar, share, n in zip(bars, shares["share"], shares["listings"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{share:.1f} %\n({n:,} anuncios)".replace(",", "."),
                ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, shares["share"].max() * 1.35)
    ax.set_xlabel("Anuncios que tiene el anfitrión en el entrenamiento")
    ax.set_ylabel("% de los anuncios")
    ax.set_title("¿De quién son los anuncios? Concentración por anfitrión")
    return _save(fig, path)


# --- F6 a F8: variables, torneo y optimización (tablas guardadas) -------------------------------------------------

def plot_feature_ideas(table: pd.DataFrame, path) -> Path:
    """F6. MAE (media ± desviación entre pliegues) de la referencia y de las cinco ideas de variables."""
    _style()
    summary = ideas_summary(table)
    labels = [IDEA_NAMES.get(v, v) for v in summary.index]
    colors = [MODEL_COLOR if v == "referencia" else BASELINE_COLOR for v in summary.index]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    y = np.arange(len(summary))[::-1]
    ax.barh(y, summary["mean"], xerr=summary["std"], color=colors, capsize=3, error_kw={"lw": 0.8})
    x_low = summary["mean"].min() - 4
    for yi, m in zip(y, summary["mean"]):
        ax.text(x_low + 0.15, yi, f"{m:.2f}".replace(".", ","), ha="left", va="center", fontsize=8, color="white",
                fontweight="bold")
    ax.set_yticks(y, labels)
    ax.set_xlim(x_low, summary["mean"].max() + 3)
    ax.set_xlabel("MAE en validación cruzada (USD por noche; barra = ± desviación entre pliegues)")
    ax.set_title("Ideas de variables frente a la referencia (LightGBM fijo)")
    return _save(fig, path)


def plot_tournament(table: pd.DataFrame, path) -> Path:
    """F7. MAE de cada candidato en los mismos 5 pliegues por anfitrión."""
    _style()
    order = table.groupby("model")["mae"].mean().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for model in order:
        part = table[table["model"] == model].sort_values("fold")
        color = MODEL_COLORS.get(model)
        ax.plot(part["fold"] + 1, part["mae"], marker="o", label=f"{pretty_model(model)} ({part['mae'].mean():.2f})"
                .replace(".", ","), color=color)
    ax.set_xticks(sorted(table["fold"].unique() + 1))
    ax.set_xlabel("Pliegue (por anfitrión)")
    ax.set_ylabel("MAE (USD por noche)")
    ax.set_title("Torneo de modelos: error en cada pliegue (media entre paréntesis)")
    ax.legend(fontsize=8, ncol=2)
    return _save(fig, path)


def plot_optimization(table: pd.DataFrame, path) -> Path:
    """F8. MAE de cada ensayo de Optuna y el mejor acumulado, por finalista."""
    _style()
    done = table[table["state"] == "completo"]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for model in ["lightgbm", "random_forest"]:
        color = MODEL_COLORS[model]
        part = done[done["model"] == model].sort_values("trial")
        if part.empty:
            continue
        ax.scatter(part["trial"], part["mae"], s=14, alpha=0.5, color=color)
        ax.plot(part["trial"], part["mae"].cummin(), color=color, label=f"{pretty_model(model)}: mejor hasta ese ensayo")
    ax.set_xlabel("Ensayo de Optuna")
    ax.set_ylabel("MAE medio en 5 pliegues (USD)")
    ax.set_title("Optimización de hiperparámetros (30 ensayos por finalista)")
    ax.legend(fontsize=8)
    return _save(fig, path)


# --- F9 a F11: resultados ---------------------------------------------------------------------------------------

def plot_city_test_errors(segments: pd.DataFrame, path) -> Path:
    """F9. MAE por ciudad en la prueba, modelo contra línea base (cifras de reports/07_segmentos.csv)."""
    _style()
    cities = segments[segments["segmento"] == "city"].pivot(index="valor", columns="modelo", values="mae")
    cities = cities.sort_values("final")
    labels = [pretty_city(c) for c in cities.index]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = np.arange(len(cities))
    ax.barh(y - 0.2, cities["final"], height=0.4, color=MODEL_COLOR, label="Modelo (LightGBM)")
    ax.barh(y + 0.2, cities["linea_base"], height=0.4, color=BASELINE_COLOR, label="Línea base")
    for i, (m, b) in enumerate(zip(cities["final"], cities["linea_base"])):
        ax.text(m, i - 0.2, f" {m:.1f}".replace(".", ","), va="center", fontsize=8)
        ax.text(b, i + 0.2, f" {b:.1f}".replace(".", ","), va="center", fontsize=8)
    ax.set_yticks(y, labels)
    ax.set_xscale("log")
    ax.set_xlim(10, cities.to_numpy().max() * 2)
    _plain_log_axis(ax.xaxis, 10, cities.to_numpy().max() * 2)
    ax.set_xlabel("MAE en la prueba (USD por noche, escala log)")
    ax.set_title("Error por ciudad en la prueba: el modelo mejora en las seis")
    ax.legend(loc="lower right", fontsize=8)
    return _save(fig, path)


def plot_shap_importance(shap: pd.DataFrame, path) -> Path:
    """F10. Importancia global de cada columna (media del valor SHAP absoluto, reports/07_shap_global.csv)."""
    _style()
    data = shap.sort_values("importancia")
    labels = [f"{SHAP_LABELS[c]} ({c})" if c in SHAP_LABELS else c for c in data["columna"]]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.barh(labels, data["importancia"], color=MODEL_COLOR)
    ax.set_xlabel("Media del |valor SHAP| (en logaritmo del precio)")
    ax.set_title("¿Qué columnas pesan más en el modelo? (SHAP)")
    return _save(fig, path)


def plot_real_vs_predicted(real_usd, pred_usd, path) -> Path:
    """F11. Precio real contra predicho (izquierda) y distribución del error relativo (derecha)."""
    _style()
    real_usd, pred_usd = np.asarray(real_usd, float), np.asarray(pred_usd, float)
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.8))
    hb = axes[0].hexbin(real_usd, pred_usd, gridsize=45, xscale="log", yscale="log", bins="log", cmap="Blues",
                        mincnt=1)
    low, high = np.percentile(np.r_[real_usd, pred_usd], [0.5, 99.5])
    axes[0].plot([low, high], [low, high], color=ACCENT_COLOR, lw=1.2, label="predicho = real")
    axes[0].set_xlim(low, high)
    axes[0].set_ylim(low, high)
    _plain_log_axis(axes[0].xaxis, low, high)
    _plain_log_axis(axes[0].yaxis, low, high)
    axes[0].set_xlabel("Precio real (USD, log)")
    axes[0].set_ylabel("Precio predicho (USD, log)")
    axes[0].set_title("Real contra predicho")
    axes[0].legend(fontsize=8, loc="upper left")
    fig.colorbar(hb, ax=axes[0], label="anuncios (log)")
    relative = (pred_usd - real_usd) / real_usd * 100
    axes[1].hist(np.clip(relative, -100, 200), bins=60, color=BASELINE_COLOR)
    axes[1].axvline(0, color=ACCENT_COLOR, lw=1.2)
    axes[1].set_xlabel("Error relativo (%): (predicho − real) / real")
    axes[1].set_ylabel("Anuncios")
    axes[1].set_title("Residuos (cortados en −100 % y 200 %)")
    return _save(fig, path)


def compute_oof_predictions(train: pd.DataFrame) -> pd.DataFrame:
    """Predicciones fuera de pliegue del LightGBM optimizado (parámetros de reports/06_best_params.json).

    Cada anuncio lo predice un modelo que no vio a su anfitrión (pliegues por anfitrión). No toca la prueba.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from tarifalatam.config import GROUP_COL, TARGET
    from tarifalatam.models.train import build_pipeline, feature_frame
    from tarifalatam.models.tuning import make_model
    from tarifalatam.models.validation import oof_log_predictions

    params = json.loads((REPORTS / "06_best_params.json").read_text(encoding="utf-8"))["parametros"]
    pipeline = build_pipeline(make_model("lightgbm", params), "boosting")
    oof_log = oof_log_predictions(pipeline, feature_frame(train), train[TARGET], train[GROUP_COL])
    return pd.DataFrame({"city": train["city"], "price_usd": np.exp(train[TARGET]), "pred_usd": np.exp(oof_log)})


def main() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from tarifalatam.data.load import load_train
    from tarifalatam.models.train import usd_metrics

    FIGURES.mkdir(parents=True, exist_ok=True)
    train = load_train()
    print(f"Entrenamiento: {len(train):,} anuncios, {train['host_id'].nunique():,} anfitriones")

    plot_listings_by_city(train, FIGURES / "F01_anuncios_por_ciudad.png")
    plot_price_distribution(train, FIGURES / "F02_distribucion_precio.png")
    plot_price_by_city_room(train, FIGURES / "F03_precio_ciudad_tipo.png")
    plot_correlation(train, FIGURES / "F04_matriz_correlacion.png")
    plot_host_concentration(train, FIGURES / "F05_concentracion_anfitrion.png")
    plot_feature_ideas(pd.read_csv(REPORTS / "04_features_tabla.csv"), FIGURES / "F06_ideas_variables.png")
    plot_tournament(pd.read_csv(REPORTS / "05_torneo_tabla.csv"), FIGURES / "F07_torneo.png")
    plot_optimization(pd.read_csv(REPORTS / "06_optimizacion_tabla.csv"), FIGURES / "F08_optimizacion.png")
    plot_city_test_errors(pd.read_csv(REPORTS / "07_segmentos.csv"), FIGURES / "F09_error_ciudad_prueba.png")
    plot_shap_importance(pd.read_csv(REPORTS / "07_shap_global.csv"), FIGURES / "F10_importancia_shap.png")

    print("F11: predicciones fuera de pliegue (5 modelos LightGBM, puede tardar unos minutos)...")
    oof = compute_oof_predictions(train)
    plot_real_vs_predicted(oof["price_usd"], oof["pred_usd"], FIGURES / "F11_real_vs_predicho.png")
    relative = (oof["pred_usd"] - oof["price_usd"]).abs() / oof["price_usd"]
    metrics = usd_metrics(np.log(oof["price_usd"]), np.log(oof["pred_usd"]))
    metrics.update(
        n=int(len(oof)),
        pct_error_over_half=float((relative > 0.5).mean() * 100),
        fuente="predicciones fuera de pliegue en el entrenamiento, 5 pliegues por anfitrión; la prueba no se abre",
    )
    (FIGURES / "F11_metricas.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print("F11:", {k: round(v, 2) if isinstance(v, float) else v for k, v in metrics.items()})
    print(f"Listo: {len(list(FIGURES.glob('F*.png')))} figuras en {FIGURES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
