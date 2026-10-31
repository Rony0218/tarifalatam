import json

import numpy as np
import pandas as pd
import pytest
from fixtures import make_listings

from tarifalatam.config import (
    CITY_FILES,
    EMPTY_COLUMNS,
    EXCLUDED_CITIES,
    FREE_TEXT_COLUMNS,
    LEAKAGE_COLUMNS,
    PII_COLUMNS,
    UNUSED_COLUMNS,
)
from tarifalatam.data.cleaning import (
    add_review_flags,
    add_target,
    check_currencies,
    drop_empty_columns,
    drop_excluded_cities,
    drop_leakage_columns,
    drop_missing_price,
    drop_monthly_rentals,
    drop_previous_scrape,
    drop_price_outliers,
    drop_unused_columns,
    fit_price_bounds,
    load_raw,
    mark_impossible_values,
    parse_bathrooms_text,
    parse_price,
    to_usd,
)

# Tasas INVENTADAS para las pruebas: no son tasas reales y nunca van a config.py
FAKE_RATES = {
    "rio-de-janeiro": {"currency": "BRL", "local_per_usd": 5.0, "date": "2026-09-22", "source": "inventada"},
    "belize": {"currency": "USD", "local_per_usd": 1.0, "date": "2026-09-25", "source": "inventada"},
}


def _write_raw_files(folder, drop_city=None):
    """Escribe siete .csv.gz de juguete con datos personales y texto libre inventados."""
    for i, (city, filename) in enumerate(CITY_FILES.items()):
        if city == drop_city:
            continue
        df = make_listings(n_hosts=2, per_host=1, seed=i).drop(columns=["city"])
        for col in PII_COLUMNS + FREE_TEXT_COLUMNS:
            df[col] = "dato inventado"
        df.to_csv(folder / filename, index=False, compression="gzip")


# --- Carga (FR-001, FR-002, FR-022) ---


def test_load_raw_adds_city_and_drops_personal_and_free_text(tmp_path):
    _write_raw_files(tmp_path)
    df = load_raw(tmp_path)
    assert set(df["city"]) == set(CITY_FILES)
    assert len(df) == 2 * len(CITY_FILES)
    leaked = set(PII_COLUMNS + FREE_TEXT_COLUMNS) & set(df.columns)
    assert not leaked, f"columnas personales o de texto libre presentes: {leaked}"


def test_load_raw_fails_if_a_city_file_is_missing(tmp_path):
    _write_raw_files(tmp_path, drop_city="belize")
    with pytest.raises(FileNotFoundError, match="belize"):
        load_raw(tmp_path)


def test_load_raw_fails_if_columns_differ_between_files(tmp_path):
    _write_raw_files(tmp_path)
    odd = tmp_path / CITY_FILES["santiago"]
    pd.read_csv(odd).drop(columns=["bedrooms"]).to_csv(odd, index=False, compression="gzip")
    with pytest.raises(ValueError, match="santiago"):
        load_raw(tmp_path)


def test_load_raw_does_not_modify_raw_files(tmp_path):
    _write_raw_files(tmp_path)
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    load_raw(tmp_path)
    after = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    assert before == after


# --- Moneda (FR-003) ---


def test_check_currencies_passes_when_currency_matches_city():
    df = make_listings()
    assert check_currencies(df).equals(df)


def test_check_currencies_fails_and_names_the_city_on_mismatch():
    df = make_listings()
    wrong = json.dumps({"quote": {"currency": "BRL"}})
    df.loc[df["city"] == "belize", "price_quote_raw"] = wrong
    with pytest.raises(ValueError, match="belize"):
        check_currencies(df)


def test_check_currencies_ignores_empty_or_broken_quotes():
    df = make_listings()
    df.loc[0, "price_quote_raw"] = np.nan
    df.loc[1, "price_quote_raw"] = "{no es json"
    df.loc[2, "price_quote_raw"] = json.dumps({"quote": None})
    df.loc[3, "price_quote_raw"] = json.dumps({"quote": "texto en vez de diccionario"})
    df.loc[4, "price_quote_raw"] = json.dumps(["una lista"])
    check_currencies(df)


# --- Ciudades excluidas (FR-012) ---


def test_drop_excluded_cities_removes_only_listed_cities():
    out = drop_excluded_cities(make_listings(), cities=("belize",))
    assert set(out["city"]) == {"rio-de-janeiro"}


def test_drop_excluded_cities_with_empty_list_keeps_all_rows():
    df = make_listings()
    assert len(drop_excluded_cities(df, cities=())) == len(df)


def test_buenos_aires_is_the_only_excluded_city():
    assert tuple(EXCLUDED_CITIES) == ("buenos-aires",)


# --- Corte anterior (FR-011) ---


def test_drop_previous_scrape_removes_only_previous_scrape():
    df = pd.DataFrame({"source": ["previous scrape", np.nan, "city scrape"], "id": [1, 2, 3]})
    assert drop_previous_scrape(df)["id"].tolist() == [2, 3]


# --- Precio (FR-003, FR-004) ---


def test_parse_price_converts_text_to_number():
    df = pd.DataFrame({"price": ["$1,234.00", "$99.50", "$258,514,678.00"]})
    out = parse_price(df)
    assert out["price_local"].tolist() == [1234.0, 99.5, 258514678.0]
    assert "price" not in out.columns


def test_parse_price_turns_garbage_and_empty_into_missing():
    out = parse_price(pd.DataFrame({"price": ["abc", np.nan, "$"]}))
    assert out["price_local"].isna().all()


def test_drop_missing_price():
    df = pd.DataFrame({"price_local": [100.0, np.nan, 50.0], "id": [1, 2, 3]})
    assert drop_missing_price(df)["id"].tolist() == [1, 3]


def test_to_usd_divides_by_local_per_usd():
    df = pd.DataFrame({"city": ["rio-de-janeiro", "belize"], "price_local": [500.0, 120.0]})
    out = to_usd(df, rates=FAKE_RATES)
    assert out["price_usd"].tolist() == [100.0, 120.0]


def test_to_usd_fails_when_rate_is_none_and_names_the_city():
    rates = {**FAKE_RATES, "rio-de-janeiro": {**FAKE_RATES["rio-de-janeiro"], "local_per_usd": None}}
    df = pd.DataFrame({"city": ["rio-de-janeiro", "belize"], "price_local": [500.0, 120.0]})
    with pytest.raises(ValueError, match="falta la tasa de cambio de rio-de-janeiro"):
        to_usd(df, rates=rates)


def test_to_usd_fails_when_city_is_not_in_the_table():
    df = pd.DataFrame({"city": ["santiago"], "price_local": [50000.0]})
    with pytest.raises(ValueError, match="santiago"):
        to_usd(df, rates=FAKE_RATES)


@pytest.mark.parametrize("bad_rate", [0, -5.0, np.nan, np.inf])
def test_to_usd_fails_when_rate_is_not_a_positive_number(bad_rate):
    rates = {**FAKE_RATES, "rio-de-janeiro": {**FAKE_RATES["rio-de-janeiro"], "local_per_usd": bad_rate}}
    df = pd.DataFrame({"city": ["rio-de-janeiro"], "price_local": [500.0]})
    with pytest.raises(ValueError, match="rio-de-janeiro"):
        to_usd(df, rates=rates)


def test_to_usd_fails_when_rate_currency_does_not_match_city():
    rates = {**FAKE_RATES, "rio-de-janeiro": {**FAKE_RATES["rio-de-janeiro"], "currency": "MXN"}}
    df = pd.DataFrame({"city": ["rio-de-janeiro"], "price_local": [500.0]})
    with pytest.raises(ValueError, match="rio-de-janeiro"):
        to_usd(df, rates=rates)


# --- Columnas que se eliminan (FR-005, FR-006) ---


def test_drop_leakage_columns_removes_all_six():
    out = drop_leakage_columns(make_listings())
    assert not set(LEAKAGE_COLUMNS) & set(out.columns)
    assert "estimated_occupancy_l365d" in out.columns  # sospechosa: se mide en la etapa 4


def test_drop_leakage_columns_ignores_columns_already_gone():
    df = make_listings().drop(columns=["price_quote_raw"])
    drop_leakage_columns(df)


def test_drop_empty_columns_removes_all_twelve():
    out = drop_empty_columns(make_listings())
    assert not set(EMPTY_COLUMNS) & set(out.columns)
    assert "bathrooms_text" in out.columns


def test_drop_unused_columns_removes_license():
    out = drop_unused_columns(make_listings(license=["registro inventado"] * 12))
    assert not set(UNUSED_COLUMNS) & set(out.columns)
    assert "bathrooms_text" in out.columns


def test_drop_unused_columns_ignores_columns_already_gone():
    drop_unused_columns(make_listings())


# --- Baños (FR-007) ---


def test_parse_bathrooms_text_reads_number_and_shared_flag():
    df = pd.DataFrame({"bathrooms_text": ["1.5 shared baths", "2 baths", "1 private bath"]})
    out = parse_bathrooms_text(df)
    assert out["bathrooms_count"].tolist() == [1.5, 2.0, 1.0]
    assert out["bathroom_shared"].tolist() == [1.0, 0.0, 0.0]


def test_parse_bathrooms_text_handles_half_bath_no_bathroom_and_empty():
    df = pd.DataFrame(
        {
            "bathrooms_text": [
                "Half-bath",
                "Shared half-bath",
                "Private half-bath",
                "Shared half bathroom",  # 1 caso real, sin guion
                "No bathroom",
                np.nan,
            ]
        }
    )
    out = parse_bathrooms_text(df)
    assert out["bathrooms_count"].tolist()[:5] == [0.5, 0.5, 0.5, 0.5, 0.0]
    assert np.isnan(out["bathrooms_count"].iloc[5])
    assert out["bathroom_shared"].tolist()[:5] == [0.0, 1.0, 0.0, 1.0, 0.0]
    assert np.isnan(out["bathroom_shared"].iloc[5])


# --- Arriendos mensuales (FR-008) ---


def test_drop_monthly_rentals_keeps_29_drops_30_and_more():
    df = pd.DataFrame({"minimum_nights": [1, 29, 30, 365], "id": [1, 2, 3, 4]})
    assert drop_monthly_rentals(df)["id"].tolist() == [1, 2]


def test_drop_monthly_rentals_keeps_unknown_minimum_nights():
    df = pd.DataFrame({"minimum_nights": [np.nan, 2], "id": [1, 2]})
    assert drop_monthly_rentals(df)["id"].tolist() == [1, 2]


# --- Centinelas (FR-009) ---


def test_mark_impossible_values():
    df = pd.DataFrame(
        {
            "maximum_nights": [365, 1125, 2147483647, 1126],
            "bedrooms": [1.0, 14.0, 12.0, 0.0],
            "accommodates": [2, 2, 16, 1],
        }
    )
    out = mark_impossible_values(df)
    assert len(out) == len(df)
    assert out["maximum_nights"].isna().tolist() == [False, False, True, True]
    # 14 habitaciones para 2 personas es imposible; 12 para 16 personas se conserva
    assert out["bedrooms"].isna().tolist() == [False, True, False, False]


def test_mark_impossible_values_edge_cases():
    df = pd.DataFrame(
        {
            "maximum_nights": [365] * 4,
            "bedrooms": [10.0, 11.0, 12.0, 15.0],
            "accommodates": [2, 11, np.nan, 14],
        }
    )
    out = mark_impossible_values(df)
    # 10 no supera el tope; 11 = capacidad no la supera; sin capacidad no hay con qué comparar -> se conserva;
    # 15 habitaciones para 14 personas sí se marca
    assert out["bedrooms"].isna().tolist() == [False, False, False, True]


# --- Reseñas (FR-010) ---


def test_add_review_flags_marks_listings_with_reviews():
    df = pd.DataFrame({"number_of_reviews": [0, 3, np.nan], "review_scores_rating": [np.nan, 4.5, np.nan]})
    out = add_review_flags(df)
    assert out["has_reviews"].tolist() == [0, 1, 0]
    assert out["review_scores_rating"].isna().tolist() == [True, False, True]  # no se imputa aquí


# --- Precios extremos (FR-014) ---


def test_fit_price_bounds_uses_only_the_given_table():
    train = pd.DataFrame({"city": ["belize"] * 3, "price_usd": [100.0, 200.0, 300.0]})
    bounds = fit_price_bounds(train)
    assert bounds == {"belize": (20.0, 4000.0)}  # mediana 200: 0,1 x y 20 x


def test_drop_price_outliers_keeps_rows_inside_bounds():
    bounds = {"belize": (20.0, 4000.0)}
    df = pd.DataFrame({"city": ["belize"] * 4, "price_usd": [19.9, 20.0, 4000.0, 4000.1], "id": [1, 2, 3, 4]})
    assert drop_price_outliers(df, bounds)["id"].tolist() == [2, 3]


def test_drop_price_outliers_fails_for_a_city_without_bounds():
    df = pd.DataFrame({"city": ["santiago"], "price_usd": [50.0]})
    with pytest.raises(ValueError, match="santiago"):
        drop_price_outliers(df, {"belize": (20.0, 4000.0)})


# --- Objetivo (FR-015) ---


def test_add_target_is_log_of_price_usd():
    out = add_target(pd.DataFrame({"price_usd": [1.0, np.e, 100.0]}))
    assert np.allclose(out["log_price_usd"], [0.0, 1.0, np.log(100.0)])


# --- Ninguna función modifica la tabla de entrada ---


def test_functions_do_not_modify_input():
    df = make_listings()
    df["price_local"] = 100.0
    df["price_usd"] = 20.0
    snapshot = df.copy()
    for func in (
        drop_excluded_cities,
        check_currencies,
        drop_previous_scrape,
        drop_missing_price,
        drop_leakage_columns,
        drop_empty_columns,
        drop_unused_columns,
        parse_bathrooms_text,
        drop_monthly_rentals,
        mark_impossible_values,
        add_review_flags,
        add_target,
    ):
        func(df)
    parse_price(df)
    to_usd(df, rates=FAKE_RATES)
    drop_price_outliers(df, fit_price_bounds(df))
    pd.testing.assert_frame_equal(df, snapshot)
