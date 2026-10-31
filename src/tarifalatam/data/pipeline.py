"""Encadena las reglas de limpieza y la partición en el orden fijado en specs/001-eda-limpieza-particion/research.md (§4).

Primero van las reglas que no aprenden de los datos; después la partición por anfitrión; al final lo único que
aprende de los datos (los límites de precio por ciudad), ajustado SOLO con el entrenamiento.
"""
from tarifalatam.config import FX_RATES, RAW_DIR
from tarifalatam.data.cleaning import (
    add_review_flags,
    add_target,
    check_currencies,
    drop_empty_columns,
    drop_leakage_columns,
    drop_missing_price,
    drop_monthly_rentals,
    drop_previous_scrape,
    drop_price_outliers,
    fit_price_bounds,
    load_raw,
    mark_impossible_values,
    parse_bathrooms_text,
    parse_price,
    to_usd,
)
from tarifalatam.data.split import split_by_host


def build_datasets(raw_dir=RAW_DIR, rates: dict = FX_RATES):
    """Genera entrenamiento y prueba desde los archivos crudos.

    Devuelve (train, test, bounds): bounds son los límites de precio por ciudad aprendidos en entrenamiento.
    Se detiene si falta una tasa de cambio (nunca usa un valor supuesto).
    """
    df = load_raw(raw_dir)  # 1: carga sin datos personales ni texto libre
    df = check_currencies(df)  # 2
    df = drop_previous_scrape(df)  # 3
    df = parse_price(df)  # 4
    df = drop_missing_price(df)  # 5
    df = to_usd(df, rates)  # 6
    df = drop_leakage_columns(df)  # 7 (después de check_currencies, que usa price_quote_raw)
    df = drop_empty_columns(df)  # 8
    df = parse_bathrooms_text(df)  # 9
    df = drop_monthly_rentals(df)  # 10
    df = mark_impossible_values(df)  # 11
    df = add_review_flags(df)  # 12

    train, test = split_by_host(df)  # 13: nada de lo anterior aprende de los datos

    bounds = fit_price_bounds(train)  # 14: solo con entrenamiento
    train = add_target(drop_price_outliers(train, bounds))  # 15
    test = add_target(drop_price_outliers(test, bounds))
    return train.reset_index(drop=True), test.reset_index(drop=True), bounds
