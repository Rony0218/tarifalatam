"""Pruebas de las gráficas del informe técnico (scripts/report_figures.py, tarea T005 de specs/004-informe-tecnico-pdf).

Cada función de figura recibe una tabla pequeña hecha a mano y debe dejar un PNG no vacío. Las funciones que calculan
algo (participación por tamaño del anfitrión, resumen de las ideas) se comprueban con cifras fáciles de verificar.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("report_figures", ROOT / "scripts" / "report_figures.py")
rf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rf)


@pytest.fixture
def tiny_train() -> pd.DataFrame:
    """Doce anuncios de dos ciudades y cinco anfitriones, con las columnas que usan las figuras del EDA."""
    rng = np.random.default_rng(0)
    n = 12
    price = rng.uniform(20, 200, n)
    return pd.DataFrame(
        {
            "city": ["bogota"] * 6 + ["santiago"] * 6,
            "host_id": [1, 1, 1, 2, 3, 3, 4, 4, 4, 4, 5, 5],
            "room_type": ["Entire home/apt", "Private room"] * 6,
            "price_usd": price,
            "log_price_usd": np.log(price),
            "latitude": rng.uniform(4, 5, n),
            "longitude": rng.uniform(-75, -74, n),
            "accommodates": rng.integers(1, 6, n),
            "bedrooms": rng.integers(1, 4, n),
            "beds": rng.integers(1, 4, n),
            "bathrooms_count": rng.integers(1, 3, n),
            "minimum_nights": rng.integers(1, 5, n),
            "maximum_nights": rng.integers(30, 365, n),
        }
    )


def _assert_png(path: Path) -> None:
    assert path.exists() and path.stat().st_size > 1000
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_pretty_names_translate_cities_and_models():
    assert rf.pretty_city("sao-paulo") == "São Paulo"
    assert rf.pretty_city("belize") == "Belice"
    assert rf.pretty_model("linea_base") == "Línea base"
    assert rf.pretty_city("otra") == "otra"  # lo desconocido se deja igual, no se inventa


def test_host_size_shares_counts_listings_by_host_size(tiny_train):
    shares = rf.host_size_shares(tiny_train)
    # Anfitriones: 1 (3 anuncios), 2 (1), 3 (2), 4 (4), 5 (2) -> "1": 1 anuncio; "2 a 4": 11 anuncios
    assert shares.loc["1", "listings"] == 1
    assert shares.loc["2 a 4", "listings"] == 11
    assert shares["listings"].sum() == len(tiny_train)
    assert shares["share"].sum() == pytest.approx(100.0)


def test_ideas_summary_keeps_reference_and_five_ideas():
    rows = []
    for variant in ["referencia", "idea_1_distancia", "idea_2_amenidades", "final"]:
        for fold, mae in enumerate([10.0, 12.0]):
            rows.append({"variant": variant, "fold": fold, "mae": mae + (1 if variant == "final" else 0)})
    summary = rf.ideas_summary(pd.DataFrame(rows))
    assert list(summary.index) == ["referencia", "idea_1_distancia", "idea_2_amenidades"]
    assert summary.loc["referencia", "mean"] == pytest.approx(11.0)


@pytest.mark.parametrize(
    "plot",
    ["plot_listings_by_city", "plot_price_distribution", "plot_price_by_city_room", "plot_correlation",
     "plot_host_concentration"],
)
def test_eda_figures_write_a_png(plot, tiny_train, tmp_path):
    out = tmp_path / f"{plot}.png"
    getattr(rf, plot)(tiny_train, out)
    _assert_png(out)


def test_feature_ideas_figure(tmp_path):
    table = pd.DataFrame(
        [{"variant": v, "fold": f, "mae": 10 + f + i} for i, v in enumerate(["referencia", "idea_1_distancia"])
         for f in range(3)]
    )
    out = tmp_path / "f6.png"
    rf.plot_feature_ideas(table, out)
    _assert_png(out)


def test_tournament_figure(tmp_path):
    table = pd.DataFrame(
        [{"model": m, "fold": f, "mae": 40 + f + i} for i, m in enumerate(["linea_base", "lightgbm"]) for f in range(5)]
    )
    out = tmp_path / "f7.png"
    rf.plot_tournament(table, out)
    _assert_png(out)


def test_optimization_figure(tmp_path):
    table = pd.DataFrame(
        [{"model": m, "trial": t, "state": "completo", "mae": 40 - t * 0.1} for m in ["lightgbm", "random_forest"]
         for t in range(1, 6)]
    )
    out = tmp_path / "f8.png"
    rf.plot_optimization(table, out)
    _assert_png(out)


def test_city_errors_figure(tmp_path):
    rows = [{"segmento": "city", "valor": c, "modelo": m, "n": 10, "mae": mae}
            for c, base in [("bogota", 27.0), ("belize", 350.0)] for m, mae in [("final", base * 0.8),
                                                                               ("linea_base", base)]]
    rows.append({"segmento": "room_type", "valor": "Shared room", "modelo": "final", "n": 5, "mae": 15.0})
    out = tmp_path / "f9.png"
    rf.plot_city_test_errors(pd.DataFrame(rows), out)
    _assert_png(out)


def test_shap_figure(tmp_path):
    shap = pd.DataFrame({"columna": ["bedrooms", "city"], "importancia": [0.12, 0.05]})
    out = tmp_path / "f10.png"
    rf.plot_shap_importance(shap, out)
    _assert_png(out)


def test_real_vs_predicted_figure(tmp_path):
    rng = np.random.default_rng(1)
    real = rng.uniform(20, 300, 200)
    out = tmp_path / "f11.png"
    rf.plot_real_vs_predicted(real, real * rng.uniform(0.7, 1.3, 200), out)
    _assert_png(out)
