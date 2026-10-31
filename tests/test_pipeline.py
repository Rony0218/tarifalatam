import numpy as np
from fixtures import make_listings

from tarifalatam.config import CITY_FILES, EMPTY_COLUMNS, FREE_TEXT_COLUMNS, LEAKAGE_COLUMNS, PII_COLUMNS
from tarifalatam.data.pipeline import build_datasets

# Tasas INVENTADAS para las pruebas: no son tasas reales y nunca van a config.py
FAKE_RATES = {
    city: {"currency": "X", "local_per_usd": 2.0, "date": "2026-09-01", "source": "inventada"} for city in CITY_FILES
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
    train, test, bounds = build_datasets(tmp_path, rates=FAKE_RATES)
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
