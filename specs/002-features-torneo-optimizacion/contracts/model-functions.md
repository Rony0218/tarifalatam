# Contrato: funciones públicas nuevas de `src/tarifalatam`

Lo que cada función promete (entradas, salida y errores). No es el código: es lo que las pruebas verifican. Ninguna función
modifica la tabla que recibe. Los transformadores siguen la interfaz de scikit-learn (`fit` / `transform`) y devuelven una
tabla nueva con columnas agregadas.

## `config.py` (se amplía)

| Nombre | Contenido | Requisito |
|---|---|---|
| `TRAIN_PATH`, `FOLDS_PATH` | `data/processed/train.csv.gz`, `data/processed/folds.csv` | FR-001, FR-003 |
| `TARGET_COLUMNS` | `log_price_usd`, `price_usd`, `price_local` | FR-005 |
| `FORBIDDEN_FEATURES`, `SUSPICIOUS_FEATURES` | Listas de `data-model.md` (18 y 23) | FR-005, FR-006 |
| `REFERENCE_CATEGORICAL`, `REFERENCE_NUMERIC`, `REFERENCE_BINARY` | Referencia (4 + 8 + 1) | FR-007 |
| `HOST_PROFILE_COLUMNS` | Insumo de la idea 4 (11) | FR-009, FR-010 |
| `AMENITY_FLAGS` | `{"amenity_pool": "Pool", …}` (6 nombres exactos) | FR-010 |
| `RARE_MIN_COUNT = 30`, `N_FOLDS = 5`, `FOLD_SEED = 42` | Decisión 11 y pliegues | FR-003, FR-007 |
| `RESERVE_SIZE = 0.25`, `RESERVE_SEED = 7`, `N_TRIALS = 30`, `BOOTSTRAP_N = 1000`, `NIGHTS_SCALE = 30` | Etapas 5 y 6 | FR-018, FR-020, FR-021, FR-024 |
| `EXPERIMENT_NAME = "tarifalatam-optimizacion"` | Seguimiento | FR-023 |
| `FINAL_IDEAS`, `FINALISTS` | Ideas que conservó la etapa 4 y finalistas de la etapa 5; los anota quien cierra cada etapa, con un comentario que cita el informe | FR-012, FR-019 |

## `data/load.py`

| Función | Entrada | Salida | Errores / garantías | Requisito |
|---|---|---|---|---|
| `load_train(path=TRAIN_PATH)` | Ruta del `.csv.gz` de entrenamiento | Tabla con las 65 columnas | Error que nombra las columnas que faltan o sobran frente a las cuatro listas. Solo lee | FR-001, FR-009 |

## `data/folds.py`

| Función | Entrada | Salida | Errores / garantías | Requisito |
|---|---|---|---|---|
| `make_folds(train, n_splits=N_FOLDS, seed=FOLD_SEED)` | Tabla con `id` y `host_id` | Tabla `id`, `fold` | Cada anfitrión en un solo pliegue y cada anuncio en uno; la misma semilla da el mismo resultado; error si hay `host_id` vacíos | FR-003 |
| `save_folds(folds, path=FOLDS_PATH)` / `load_folds(path=FOLDS_PATH)` | Tabla / ruta | Archivo / tabla | `load_folds` falla si el archivo no existe, con un mensaje que dice que se ejecute el notebook 04 | FR-003 |
| `fold_indices(frame, folds, exact=True)` | Tabla con `id` y la asignación | Lista de 5 pares (índices de ajuste, índices de validación), posiciones de `frame` | `exact=True`: error si los `id` no coinciden exactamente. `exact=False`: error si algún `id` de `frame` no está en la asignación (uso: subconjunto de búsqueda) | FR-003, FR-021 |
| `reserve_hosts(train, size=RESERVE_SIZE, seed=RESERVE_SEED)` | Entrenamiento | (búsqueda, reservados) | Llama a `assert_disjoint_hosts`; ninguna fila se pierde | FR-021 |

## `features/columns.py`

| Función | Entrada | Salida | Errores / garantías | Requisito |
|---|---|---|---|---|
| `feature_columns(ideas=(), with_suspicious=False)` | Ideas activas (1–5) y si se usan sospechosas | `dict` con `categorical`, `numeric`, `binary` y `target_encoded`: las columnas que selecciona el `ColumnTransformer` | Nunca devuelve una prohibida; sin `with_suspicious`, nunca una sospechosa | FR-006, FR-007, FR-010 |
| `check_feature_columns(columns, allow_suspicious=False)` | Lista de columnas | Nada | Error que nombra cada columna prohibida (o sospechosa si no se permiten) | FR-005, FR-006 |

## `features/engineering.py`

| Transformador | Aprende en `fit` | Agrega | Requisito |
|---|---|---|---|
| `RareCategoryGrouper(columns, min_count=RARE_MIN_COUNT)` | Categorías con ≥ 30 anuncios | Reemplaza las raras, las desconocidas y los vacíos por `"Other"` | FR-007 |
| `CityCenterDistance()` | Mediana de latitud y longitud por ciudad | `distance_to_center_km` | FR-010 (idea 1) |
| `AmenityFeatures(flags=AMENITY_FLAGS)` | Nada | `amenities_count` y los 6 indicadores | FR-010 (idea 2) |
| `CapacityRatios()` | Nada | `people_per_bedroom`, `people_per_bathroom`, `beds_per_person` | FR-010 (idea 3) |
| `HostProfile()` | Nada | `host_tenure_years`, `user_tenure_years`; `t`/`f` → 1/0 | FR-010 (idea 4) |
| `SuspiciousFeatures()` | Nada | `days_since_first_review`, `days_since_last_review`; `t`/`f` → 1/0 | FR-013 |

Reglas de vacíos y divisiones por cero: `data-model.md`, sección 2.

## `models/train.py`

| Función | Entrada | Salida | Errores / garantías | Requisito |
|---|---|---|---|---|
| `BaselineRegressor()` | `fit(X, y_log)` con `city` y `room_type` | `predict` → logaritmo de la mediana de `MedianBaseline` | Reutiliza `baseline.py` sin cambiarlo; misma predicción en USD que en H1 | FR-004, FR-014 |
| `candidates(random_state=42)` | — | `{nombre: (estimador, familia)}` con los cuatro candidatos y sus parámetros aprobados | — | FR-014 |
| `build_pipeline(model, family, ideas=(), with_suspicious=False)` | Estimador, familia (`baseline`, `linear`, `forest`, `boosting`), ideas | `Pipeline` (transformadores de las ideas → `ColumnTransformer` con `remainder="drop"` → modelo) | Llama a `check_feature_columns`; error si la familia no existe | FR-007, FR-008, FR-011 |
| `feature_frame(train)` | Entrenamiento | Tabla sin `TARGET_COLUMNS` | — | FR-005 |
| `usd_metrics(y_true_log, y_pred_log)` | Dos vectores en logaritmo | `dict`: `mae`, `mape`, `rmse`, `bias` (en USD) y `r2_log` | Predicción perfecta → `mae = bias = 0`, `r2_log = 1` | FR-015 |
| `evaluate_folds(pipeline, X, y_log, folds)` | `Pipeline`, tabla, objetivo y lista de pares | (tabla con una fila por pliegue: métricas y `fit_seconds`; predicciones fuera de pliegue en logaritmo) | Usa exactamente los pliegues dados; clona el `Pipeline` en cada pliegue | FR-011, FR-014 |
| `city_errors(cities, y_true_log, oof_log, folds)` | Ciudad de cada fila, objetivo, predicciones y pliegues | Tabla `fold`, `city`, `n`, `mae`, `bias` | — | FR-016 |
| `improvement_over_noise(reference_mae, variant_mae)` | MAE por pliegue de las dos | `dict`: `improvement`, `noise` (`ddof=1` de la variante), `ratio`, `folds_won` | `noise = 0` → `ratio = inf` | FR-012 |
| `keep_idea(ratio, known_at_prediction)` | Cociente y si se conoce al predecir | `True` solo si `ratio > 1` y se conoce | — | FR-012 |
| `compare(best, other)` | MAE por pliegue de los dos | `dict`: diferencia media, pliegues que gana, diferencia / ruido (desviación de las diferencias) | — | FR-017 |
| `value_per_nights(mae_difference, nights=NIGHTS_SCALE)` | Diferencia de MAE en USD | USD por cada 30 noches | — | FR-018 |

## `models/tuning.py`

| Función | Entrada | Salida | Errores / garantías | Requisito |
|---|---|---|---|---|
| `lgbm_space(trial)`, `rf_space(trial)`, `ridge_space(trial)` | Ensayo de Optuna | `dict` de hiperparámetros dentro de los rangos aprobados | — | FR-022 |
| `make_model(name, params)` | Nombre del finalista y parámetros | Estimador con las semillas fijadas | Error si el nombre no existe | FR-022 |
| `tune(name, X, y_log, folds, n_trials=N_TRIALS, seed=42, ideas=())` | Datos de búsqueda y sus pliegues | Estudio de Optuna | Exactamente `n_trials` ensayos; cada uno registrado con `log_run` (nombre, parámetros, métricas, etiquetas); un fallo se registra con `estado=fallido` y cuenta en el presupuesto | FR-020, FR-023 |
| `trials_table(study, name)` | Estudio de Optuna y nombre del finalista | Una fila por ensayo: `model`, `trial`, `state`, hiperparámetros y métricas | Agregada en la implementación: alimenta `reports/06_optimizacion_tabla.csv` | FR-023 |
| `host_bootstrap_ci(diff_per_row, hosts, n=BOOTSTRAP_N, seed=42)` | Diferencia por anuncio y anfitrión de cada anuncio | (media, límite inferior, límite superior) | Remuestrea anfitriones completos; con una diferencia constante, los tres valores son esa constante | FR-024 |
| `paired_abs_error_difference(y_true_log, pred_a_log, pred_b_log)` | Objetivo y dos predicciones en logaritmo | \|error de A\| − \|error de B\| en USD por anuncio | Agregada en la implementación. Negativo: A se equivoca menos | FR-024 |
| `compare_on_reserved(pipeline_a, pipeline_b, search, reserved, n=BOOTSTRAP_N, seed=42)` | Dos `Pipeline`, datos de búsqueda y reservados | `dict`: `hosts`, `listings`, `mae_a`, `mae_b`, `bias_a`, `bias_b`, `mean_difference`, `low`, `high` | Agregada en la implementación. Ajusta solo con los datos de búsqueda; el intervalo remuestrea anfitriones | FR-024, FR-025 |
| `use_optimized(low, high)` | Límites del intervalo | `True` solo si `high < 0` | — | FR-024 |
| `save_decision(path, decision)` | Ruta y `dict` | Escribe `reports/06_best_params.json` | Esquema de `output-files.md` | FR-026 |

## Lo que ya existe y no cambia

`tracking/mlflow_utils.py` (`configure_mlflow`, `set_experiment`, `log_run`), `models/baseline.py` (`MedianBaseline`,
`baseline_cv_mae`) y `data/split.py` (`split_by_host`, `assert_disjoint_hosts`, `group_cv`).
