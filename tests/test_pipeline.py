import numpy as np
import pandas as pd
from fixtures import make_listings

from tarifalatam.config import CITY_CURRENCY, CITY_FILES, EMPTY_COLUMNS, FREE_TEXT_COLUMNS, LEAKAGE_COLUMNS, PII_COLUMNS
from tarifalatam.data.pipeline import build_datasets

# Tasas INVENTADAS para las pruebas: no son tasas reales y nunca van a config.py
FAKE_RATES = {
    city: {"currency": CITY_CURRENCY[city], "local_per_usd": 2.0, "date": "2026-09-01", "source": "inventada"}
    for city in CITY_FILES
}

ALWAYS = ["id", "host_id", "city", "room_type", "price_local", "price_usd", "log_price_usd",
          "bathrooms_count", "bathroom_shared", "has_reviews"]


def _write_raw_files(folder):
    """Siete archivos de juguete; cada uno con 20 anfitriones y algunas filas sucias a propósito."""
    for i, (city, filename) in enumerate(CITY_FILES.items()):
        df = make_listings(n_hosts=20, per_host=2, seed=i)
        df["host_id"] = df["host_id"] + 1000 * i  # anfitriones distintos por ciudad
        df["price_quote_raw"] = np.nan  # la moneda de juguete no importa en esta prueba
        df.loc[0, "source"] = "previous scrape"
        df.loc[1, "price"] = np.nan
        df.loc[2, "minimum_nights"] = 30
        df.loc[3, "price"] = "$999,999.00"  # extremo: más de 20 x la mediana
        df = df.drop(columns=["city"])
        for col in PII_COLUMNS + FREE_TEXT_COLUMNS:
            df[col] = "dato inventado"
        df.to_csv(folder / filename, index=False, compression="gzip")


def test_build_datasets_output_contract(tmp_path):
    _write_raw_files(tmp_path)
    train, test, _, bounds = build_datasets(tmp_path, rates=FAKE_RATES)
    for df in (train, test):
        assert set(ALWAYS) <= set(df.columns)
        forbidden = set(PII_COLUMNS + FREE_TEXT_COLUMNS + LEAKAGE_COLUMNS + EMPTY_COLUMNS + ["price"])
        assert not forbidden & set(df.columns)
        assert (df["price_usd"] > 0).all()
        assert np.isfinite(df["log_price_usd"]).all()
        assert not (df["minimum_nights"] >= 30).any()
        assert not (df["source"] == "previous scrape").any()
        assert df["price_usd"].max() < 999_999.0 / 2  # el extremo salió
    assert set(train["host_id"]).isdisjoint(test["host_id"])
    assert list(train.columns) == list(test.columns)
    assert set(bounds) == set(CITY_FILES)


# --- Registro de exclusiones (FR-017) ---


def _exclusions(tmp_path):
    _write_raw_files(tmp_path)
    _, _, exclusions, _ = build_datasets(tmp_path, rates=FAKE_RATES)
    return exclusions


def test_exclusion_log_balances(tmp_path):
    log = _exclusions(tmp_path)
    counts = log[log["step"] != "price_bounds"]
    assert (counts["before"] - counts["removed"] == counts["after"]).all()
    # dentro de una misma ciudad y conjunto, lo que queda de un paso es lo que entra al siguiente
    for _, chain in counts.groupby(["split", "city"], sort=False):
        assert (chain["after"].iloc[:-1].to_numpy() == chain["before"].iloc[1:].to_numpy()).all()


def test_exclusion_log_has_expected_steps(tmp_path):
    log = _exclusions(tmp_path)
    steps = set(zip(log["step"], log["split"]))
    for step in ("previous_scrape", "missing_price", "monthly_rental"):
        assert (step, "all") in steps
    assert ("price_outlier", "train") in steps
    assert ("price_outlier", "test") in steps
    # cada fila sucia de juguete sale por su regla: 1 por ciudad en cada paso previo a partir
    for step in ("previous_scrape", "missing_price", "monthly_rental"):
        assert (log.loc[log["step"] == step, "removed"] == 1).all()


def test_exclusion_log_includes_price_bounds(tmp_path):
    log = _exclusions(tmp_path)
    bounds = log[log["step"] == "price_bounds"]
    assert set(bounds["city"]) == set(CITY_FILES)
    assert (bounds["split"] == "train").all()  # los límites se aprenden solo en entrenamiento
    assert (bounds["low_usd"] < bounds["high_usd"]).all()


def test_price_bounds_ignore_test_prices(tmp_path):
    """Si se cambian a lo absurdo los precios de los anfitriones de prueba, los límites aprendidos no cambian."""
    _write_raw_files(tmp_path)
    train, test, _, bounds = build_datasets(tmp_path, rates=FAKE_RATES)
    test_hosts = set(test["host_id"])
    for filename in CITY_FILES.values():
        path = tmp_path / filename
        raw = pd.read_csv(path)
        is_test = raw["host_id"].isin(test_hosts) & raw["price"].notna()
        raw.loc[is_test, "price"] = "$50,000,000.00"
        raw.to_csv(path, index=False, compression="gzip")
    train_again, _, _, bounds_again = build_datasets(tmp_path, rates=FAKE_RATES)
    assert bounds_again == bounds
    pd.testing.assert_frame_equal(train_again, train)


def test_exclusion_counts_are_integers(tmp_path):
    log = _exclusions(tmp_path)
    counts = log[log["step"] != "price_bounds"]
    for col in ("before", "removed", "after"):
        assert str(counts[col].dtype) == "Int64"
