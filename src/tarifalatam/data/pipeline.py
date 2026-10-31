"""Encadena las reglas de limpieza y la partición en el orden fijado en specs/001-eda-limpieza-particion/research.md (§4).

Primero van las reglas que no aprenden de los datos; después la partición por anfitrión; al final lo único que
aprende de los datos (los límites de precio por ciudad), ajustado SOLO con el entrenamiento. Cada paso que quita
filas queda en un registro de exclusiones por ciudad y conjunto (reports/03_exclusiones.csv).
"""
import pandas as pd

from tarifalatam.config import FX_RATES, RAW_DIR
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
from tarifalatam.data.split import split_by_host


def log_step(log: list, step: str, split: str, before_df: pd.DataFrame, after_df: pd.DataFrame) -> None:
    """Agrega al registro una fila por ciudad: filas antes del paso, quitadas y después."""
    before = before_df.groupby("city").size()
    after = after_df.groupby("city").size().reindex(before.index, fill_value=0)
    for city in before.index:
        log.append(
            {
                "step": step,
                "split": split,
                "city": city,
                "before": int(before[city]),
                "removed": int(before[city] - after[city]),
                "after": int(after[city]),
            }
        )


def build_datasets(raw_dir=RAW_DIR, rates: dict = FX_RATES):
    """Genera entrenamiento y prueba desde los archivos crudos.

    Devuelve (train, test, exclusions, bounds): exclusions es el registro de filas quitadas por cada regla y
    bounds son los límites de precio por ciudad aprendidos en entrenamiento. Se detiene si falta una tasa de
    cambio (nunca usa un valor supuesto).
    """
    log: list = []
    df = load_raw(raw_dir)  # 1: carga sin datos personales ni texto libre
    df = _logged(log, "excluded_city", df, drop_excluded_cities)  # 2: Buenos Aires (decisión del 2026-10-31)
    df = check_currencies(df)  # 3
    df = _logged(log, "previous_scrape", df, drop_previous_scrape)  # 4
    df = parse_price(df)  # 5
    df = _logged(log, "missing_price", df, drop_missing_price)  # 6
    df = to_usd(df, rates)  # 7
    df = drop_leakage_columns(df)  # 8 (después de check_currencies, que usa price_quote_raw)
    df = drop_empty_columns(df)  # 9
    df = drop_unused_columns(df)  # 10: license
    df = parse_bathrooms_text(df)  # 11
    df = _logged(log, "monthly_rental", df, drop_monthly_rentals)  # 12
    df = mark_impossible_values(df)  # 13
    df = add_review_flags(df)  # 14

    train, test = split_by_host(df)  # 15: nada de lo anterior aprende de los datos

    bounds = fit_price_bounds(train)  # 16: solo con entrenamiento
    cleaned = {}
    for split, part in (("train", train), ("test", test)):
        kept = drop_price_outliers(part, bounds)
        log_step(log, "price_outlier", split, part, kept)
        cleaned[split] = add_target(kept).reset_index(drop=True)  # 17

    for city, (low, high) in bounds.items():
        log.append({"step": "price_bounds", "split": "train", "city": city, "low_usd": low, "high_usd": high})
    exclusions = pd.DataFrame(log, columns=["step", "split", "city", "before", "removed", "after", "low_usd", "high_usd"])
    exclusions = exclusions.astype({"before": "Int64", "removed": "Int64", "after": "Int64"})  # enteros con vacíos
    return cleaned["train"], cleaned["test"], exclusions, bounds


def _logged(log: list, step: str, df: pd.DataFrame, rule) -> pd.DataFrame:
    """Aplica una regla que quita filas (antes de partir) y anota cuántas quitó en cada ciudad."""
    result = rule(df)
    log_step(log, step, "all", df, result)
    return result
