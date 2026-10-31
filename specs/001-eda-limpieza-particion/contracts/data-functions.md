# Contrato: funciones públicas de `src/tarifalatam/data` y `models/baseline.py`

Lo que cada función promete (entradas, salida y errores). No es el código: es lo que las pruebas verifican. Ninguna función
modifica la tabla que recibe: todas devuelven una nueva.

## `cleaning.py`

| Función | Entrada | Salida | Errores / garantías | Requisito |
|---|---|---|---|---|
| `load_raw(raw_dir=RAW_DIR)` | Carpeta con los siete `.csv.gz` | Una tabla con la columna `city` y sin las columnas personales ni el texto libre | Error si falta un archivo de `CITY_FILES` o si sus columnas no son las esperadas. Solo lee | FR-001, FR-002 |
| `check_currencies(df)` | Tabla con `city` y `price_quote_raw` | La misma tabla | Error que nombra la ciudad si alguna moneda no vacía difiere de `CITY_CURRENCY` | FR-003 |
| `drop_previous_scrape(df)` | Tabla con `source` | Sin las filas `"previous scrape"` | — | FR-011 |
| `parse_price(df)` | Tabla con `price` (texto) | Agrega `price_local` (número); quita `price` | Texto no numérico → vacío | FR-003 |
| `drop_missing_price(df)` | Tabla con `price_local` | Sin las filas con `price_local` vacío | — | FR-004 |
| `to_usd(df, rates=FX_RATES)` | Tabla con `city` y `price_local` | Agrega `price_usd` | Error si una ciudad presente no tiene tasa o la tasa es `None` | FR-003 |
| `drop_leakage_columns(df)` | Tabla | Sin las 6 columnas de fuga | Ignora las que ya no estén | FR-005 |
| `drop_empty_columns(df)` | Tabla | Sin las 12 columnas vacías | Ignora las que ya no estén | FR-006 |
| `parse_bathrooms_text(df)` | Tabla con `bathrooms_text` | Agrega `bathrooms_count` y `bathroom_shared` | Reglas de `data-model.md` | FR-007 |
| `drop_monthly_rentals(df)` | Tabla con `minimum_nights` | Sin las filas con `minimum_nights >= 30` | — | FR-008 |
| `mark_impossible_values(df)` | Tabla con `maximum_nights`, `bedrooms`, `accommodates` | Mismas filas, con los valores imposibles en vacío | No quita filas | FR-009 |
| `add_review_flags(df)` | Tabla con `number_of_reviews` | Agrega `has_reviews` | No imputa las notas | FR-010 |
| `fit_price_bounds(train)` | Entrenamiento con `city` y `price_usd` | `{city: (low, high)}` | Usa **solo** la tabla recibida | FR-014 |
| `drop_price_outliers(df, bounds)` | Tabla y límites | Sin las filas fuera de los límites de su ciudad | Error si una ciudad no tiene límites | FR-014 |
| `add_target(df)` | Tabla con `price_usd` | Agrega `log_price_usd` | — | FR-015 |

## `split.py`

| Función | Entrada | Salida | Garantías | Requisito |
|---|---|---|---|---|
| `split_by_host(df, test_size=0.2, seed=42)` | Tabla con `host_id` | `(train, test)` | Ningún `host_id` en ambos; `len(train) + len(test) == len(df)` | FR-013 |
| `assert_disjoint_hosts(*frames)` | Dos o más tablas | Nada | Error si un `host_id` aparece en más de una | FR-021 |
| `group_cv(n_splits=5)` | — | Un validador `GroupKFold` | Para usar con `groups=host_id` | FR-019 |

## `pipeline.py`

| Función | Entrada | Salida | Garantías | Requisito |
|---|---|---|---|---|
| `build_datasets(raw_dir=RAW_DIR, rates=FX_RATES)` | Carpeta cruda y tasas | `(train, test, exclusions, bounds)` | Aplica los pasos en el orden de `research.md` §4; registra cada paso que quita filas; en el registro, `before − removed = after` | FR-016, FR-017 |

## `models/baseline.py`

| Función / clase | Entrada | Salida | Garantías | Requisito |
|---|---|---|---|---|
| `MedianBaseline().fit(train)` / `.predict(df)` | Tablas con `city`, `room_type` y `price_usd` | Precio en USD por fila | Mediana por `city` × `room_type`; si la combinación no existe, mediana de la ciudad | FR-019 |
| `baseline_cv_mae(train, n_splits=5)` | Entrenamiento | MAE en USD por pliegue y promedio | Ajusta en cada pliegue solo con su parte de entrenamiento, con pliegues por `host_id` | FR-019 |
