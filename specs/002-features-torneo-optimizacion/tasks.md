---

description: "Lista de tareas del hito H2 (etapas 4 a 6): variables, torneo de modelos y optimización con seguimiento"
---

# Tasks: Variables, torneo de modelos y optimización con seguimiento (hito H2, etapas 4 a 6)

**Input**: Documentos de diseño en `specs/002-features-torneo-optimizacion/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: **Sí se piden** (FR-029, FR-030 y la regla 9 de `CLAUDE.md`). En cada tarea de código, la prueba se escribe
**antes** que la función y debe **fallar primero**.

**Organization**: tareas agrupadas por historia de usuario (US1 = variables decididas con evidencia, US2 = torneo con
finalistas, US3 = optimización registrada y comprobada) y, dentro de cada una, por paquete del plan (P1 a P5).

**Reglas del proyecto**:

- Una tarea se marca `[X]` **solo cuando su prueba pasa** (para notebooks e informes: cuando se cumple su comprobación).
- **Responsable**: lo asigna el grupo al aprobar esta lista. Cada integrante hace los commits de sus tareas con su propia
  cuenta de GitHub.
- Las tareas marcadas **(GRUPO)** son decisiones o revisiones del grupo, no código.

## Reparto por paquete (lo llena el grupo)

| Paquete | Tareas | Responsable |
|---|---|---|
| P1 · Columnas, carga y pliegues | T003–T009, T022–T023 | |
| P2 · Variables | T010–T021 | |
| P3 · Pipeline, métricas y evaluación | T024–T031, T036–T037 | |
| P4 · Optimización | T042–T043 | |
| P5 · Notebooks e informes | T001–T002, T032–T034, T038–T040, T044–T046 | |
| Decisiones del grupo | T035, T041, T047 | Todo el grupo |
| Cierre | T048–T053 | |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas pendientes)
- **[Story]**: historia a la que pertenece (US1, US2, US3)
- Cada tarea termina con su paquete y un campo `Responsable:` vacío
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

- Paquete: `src/tarifalatam/` · Pruebas: `tests/` · Notebooks: `notebooks/` · Informes: `reports/`
- Código con nombres en inglés y docstrings y comentarios en español, al estilo de `src/tarifalatam/data/` (H1) y, solo como
  referencia de forma, de `material-del-curso/ejemplo-creditsight/src/creditsight/models/`
- Entorno: `C:\Users\Usuario\venvs\tarifalatam\Scripts\python.exe` con `PYTHONUTF8=1`; `pytest` desde la raíz

---

## Phase 1: Setup (infraestructura compartida)

**Purpose**: datos disponibles para los notebooks y una tabla de juguete para las pruebas

- [X] T001 Copiar (no mover) `data/raw/*` y `data/processed/*` desde el checkout principal a las mismas rutas del worktree, y verificar con `git status --short data/` que no aparecen como cambios (están en `.gitignore`). Comprobar que `data/processed/train.csv.gz` existe. **No abrir `test.csv.gz`**. · P5 · Responsable:
- [X] T002 [P] Ampliar `tests/fixtures.py` con `make_train_rows(n_hosts=30, seed=0, **overrides) -> pd.DataFrame`: una tabla de juguete con **las 65 columnas** de `data-model.md` (sección 1), 3 ciudades (`rio-de-janeiro`, `bogota`, `belize`), varios anuncios por anfitrión, `amenities` como lista JSON (incluye `"Pool"`, `"Pool table"`, `"Air conditioning"` y una lista vacía `[]`), columnas `t`/`f`, fechas de reseñas con algunos vacíos, `last_scraped` y un objetivo `log_price_usd` coherente con `price_usd`. Comentario: "datos inventados a mano solo para pruebas". No cambiar `make_listings` (lo usan las pruebas de H1) · P5 · Responsable:

---

## Phase 2: Foundational (prerrequisitos que bloquean todo)

**Purpose**: listas de columnas, revisión de columnas prohibidas, carga y pliegues, que usan las tres historias

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase

- [X] T003 [P] Escribir `tests/test_columns.py` (debe fallar antes de T004 y T005):
  - `test_column_lists_are_disjoint_and_cover_the_65_columns`: `FORBIDDEN_FEATURES`, `SUSPICIOUS_FEATURES`, las tres listas de referencia y `HOST_PROFILE_COLUMNS` no se cruzan, suman 18 + 23 + 13 + 11 = 65 y coinciden con las columnas de `make_train_rows()`.
  - `test_check_feature_columns_rejects_each_forbidden_column`: parametrizada con las 18 prohibidas; el mensaje nombra la columna.
  - `test_check_feature_columns_rejects_suspicious_unless_allowed`.

  · P1 · Responsable:
- [X] T004 Ampliar `src/tarifalatam/config.py` (sin tocar lo de H1) con las constantes de `contracts/model-functions.md`: `TRAIN_PATH`, `FOLDS_PATH`, `TARGET_COLUMNS`, `FORBIDDEN_FEATURES` (18), `SUSPICIOUS_FEATURES` (23), `REFERENCE_CATEGORICAL` (`city`, `neighbourhood_cleansed`, `room_type`, `property_type`), `REFERENCE_NUMERIC` (`latitude`, `longitude`, `accommodates`, `bedrooms`, `beds`, `bathrooms_count`, `minimum_nights`, `maximum_nights`), `REFERENCE_BINARY` (`bathroom_shared`), `HOST_PROFILE_COLUMNS` (11), `AMENITY_FLAGS` (`amenity_pool`: `"Pool"`, `amenity_air_conditioning`: `"Air conditioning"`, `amenity_free_parking`: `"Free parking on premises"`, `amenity_gym`: `"Gym"`, `amenity_elevator`: `"Elevator"`, `amenity_hot_tub`: `"Hot tub"`), `RARE_MIN_COUNT = 30`, `N_FOLDS = 5`, `FOLD_SEED = 42`, `RESERVE_SIZE = 0.25`, `RESERVE_SEED = 7`, `N_TRIALS = 30`, `BOOTSTRAP_N = 1000`, `NIGHTS_SCALE = 30` y `EXPERIMENT_NAME = "tarifalatam-optimizacion"`. Cada lista lleva un comentario con su motivo y la referencia a `especificaciones/04-features-torneo-optimizacion.md` · P1 · Responsable:
- [X] T005 Crear `src/tarifalatam/features/columns.py` con `check_feature_columns(columns, allow_suspicious=False)`: error en español que nombra cada columna prohibida (o sospechosa, si no se permiten). Verificar con `pytest tests/test_columns.py` · P1 · Responsable:
- [X] T006 [P] Escribir `tests/test_load.py` (debe fallar antes de T007): `test_load_train_reads_the_65_columns` (guarda `make_train_rows()` como `.csv.gz` en `tmp_path` y lo lee) y `test_load_train_fails_on_missing_or_extra_columns` (el mensaje nombra la columna) · P1 · Responsable:
- [X] T007 Crear `src/tarifalatam/data/load.py` con `load_train(path=TRAIN_PATH)`, según `contracts/model-functions.md`: solo lee y compara las columnas con las cuatro listas de `config.py`. No crear ninguna función que lea la prueba. Verificar con `pytest tests/test_load.py` · P1 · Responsable:
- [X] T008 [P] Escribir `tests/test_folds.py` (debe fallar antes de T009):
  - `test_make_folds_keeps_each_host_in_one_fold`
  - `test_make_folds_puts_each_listing_in_exactly_one_fold`
  - `test_make_folds_is_deterministic_with_the_same_seed`
  - `test_make_folds_fails_with_missing_host_id`
  - `test_save_and_load_folds_roundtrip` (en `tmp_path`)
  - `test_fold_indices_exact_fails_if_ids_differ`
  - `test_fold_indices_subset_uses_the_same_folds` (con `exact=False`, un subconjunto conserva el pliegue de cada anuncio y falla si un `id` no está en la asignación)
  - `test_reserve_hosts_has_no_shared_hosts_and_loses_no_rows`

  · P1 · Responsable:
- [X] T009 Crear `src/tarifalatam/data/folds.py` con `make_folds`, `save_folds`, `load_folds`, `fold_indices` y `reserve_hosts`, según `contracts/model-functions.md` y `research.md` (puntos 2 y 3): `GroupKFold(n_splits=5, shuffle=True, random_state=42)` por `host_id`; `GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7)`; reutilizar `assert_disjoint_hosts` de `split.py`, **sin modificar `split.py`**. Verificar con `pytest tests/test_folds.py` · P1 · Responsable:

**Checkpoint**: `pytest` en verde (las 76 pruebas de H1 y las nuevas). Las historias pueden empezar.

---

## Phase 3: User Story 1 - Un conjunto de variables decidido con evidencia (Priority: P1) 🎯 MVP

**Goal**: medir la referencia, las cinco ideas, el conjunto final y la versión con sospechosas con el mismo LightGBM y los
mismos pliegues, y decidir cada idea con la regla escrita.

**Independent Test**: ejecutar el notebook 04 desde cero: `folds.csv` tiene 118.513 filas sin anfitriones en dos pliegues,
`reports/04_features_tabla.csv` tiene 40 filas, cada decisión coincide con la regla y `pytest tests/test_columns.py` pasa.

### P2 · Variables (`src/tarifalatam/features/engineering.py`, pruebas en `tests/test_features.py`)

- [X] T010 [P] [US1] Escribir en `tests/test_features.py` las pruebas de `RareCategoryGrouper` (deben fallar antes de T011): aprende las categorías frecuentes **solo** en `fit` (con `min_count` pequeño en el juguete); en `transform`, las raras, las desconocidas y los vacíos pasan a `"Other"`; no modifica la tabla original · P2 · Responsable:
- [X] T011 [US1] Implementar `RareCategoryGrouper(columns, min_count=RARE_MIN_COUNT)` en `src/tarifalatam/features/engineering.py` (decisión 11 del EDA; `research.md`, punto 4). El módulo empieza con un docstring que lista las cinco ideas. Verificar con `pytest tests/test_features.py -k rare` · P2 · Responsable:
- [X] T012 [US1] Escribir las pruebas de `CityCenterDistance`: con un anuncio a 1° de latitud del centro, la distancia es ≈ 111,19 km (haversine, radio 6.371 km); el centro sale de las medianas vistas en `fit` (al transformar datos nuevos no cambia); una ciudad no vista → vacío; no modifica el original · P2 · Responsable:
- [X] T013 [US1] Implementar `CityCenterDistance` (columna `distance_to_center_km`). Verificar con `pytest tests/test_features.py -k center` · P2 · Responsable:
- [X] T014 [US1] Escribir las pruebas de `AmenityFeatures`: `[]` → `amenities_count = 0` e indicadores en 0; `"Pool table"` **no** activa `amenity_pool` (solo nombres exactos); un texto que no es una lista JSON → conteo e indicadores vacíos; no modifica el original · P2 · Responsable:
- [X] T015 [US1] Implementar `AmenityFeatures(flags=AMENITY_FLAGS)` (columnas `amenities_count` y las seis `amenity_*`), leyendo con `json.loads`. Verificar con `pytest tests/test_features.py -k amenit` · P2 · Responsable:
- [X] T016 [US1] Escribir las pruebas de `CapacityRatios` con las reglas de `data-model.md`: "`accommodates / max(bedrooms, 1)` (0 habitaciones = estudio)"; `people_per_bathroom` vacío cuando "`bathrooms_count` es 0 o falta"; `beds_per_person` vacío cuando "`accommodates` es 0 o falta, o falta `beds`"; no modifica el original · P2 · Responsable:
- [X] T017 [US1] Implementar `CapacityRatios` (columnas `people_per_bedroom`, `people_per_bathroom`, `beds_per_person`). Verificar con `pytest tests/test_features.py -k capacity` · P2 · Responsable:
- [X] T018 [US1] Escribir las pruebas de `HostProfile`: `host_tenure_years = hosts_time_as_host_years + hosts_time_as_host_months / 12` (igual para `user_tenure_years`); `t` → 1, `f` → 0, otro valor → vacío en `host_has_profile_pic` y `host_identity_verified`; no modifica el original · P2 · Responsable:
- [X] T019 [US1] Implementar `HostProfile`. Verificar con `pytest tests/test_features.py -k host` · P2 · Responsable:
- [X] T020 [US1] Escribir las pruebas de `SuspiciousFeatures`: `days_since_first_review` y `days_since_last_review` = días entre la fecha y `last_scraped` del anuncio, vacío si no tiene reseñas; `t`/`f` → 1/0 en `has_availability` y `host_is_superhost`; no modifica el original · P2 · Responsable:
- [X] T021 [US1] Implementar `SuspiciousFeatures`. Verificar con `pytest tests/test_features.py` (todo el archivo en verde) · P2 · Responsable:

### P1 · Columnas por variante (`src/tarifalatam/features/columns.py`)

- [X] T022 [P] [US1] Agregar a `tests/test_columns.py` (debe fallar antes de T023): `feature_columns()` devuelve la referencia (4 categóricas, 8 numéricas, 1 binaria); cada idea agrega exactamente sus columnas de `data-model.md` (idea 5 → `target_encoded = ["neighbourhood_cleansed"]`); para cualquier combinación de ideas no aparece ninguna prohibida; sin `with_suspicious` no aparece ninguna sospechosa; `test_app_version_has_no_suspicious_columns` · P1 · Responsable:
- [X] T023 [US1] Implementar `feature_columns(ideas=(), with_suspicious=False)` en `src/tarifalatam/features/columns.py`, según `contracts/model-functions.md`. Verificar con `pytest tests/test_columns.py` · P1 · Responsable:

### P3 · Pipeline, métricas y evaluación (`src/tarifalatam/models/train.py`, pruebas en `tests/test_train.py`)

- [X] T024 [P] [US1] Escribir en `tests/test_train.py` (debe fallar antes de T025):
  - `test_usd_metrics_perfect_prediction` (`mae = bias = 0`, `r2_log = 1`)
  - `test_usd_metrics_hand_case`: MAE, MAPE en % y sesgo calculados a mano, con un caso que sobrestima (sesgo positivo) y otro que subestima
  - `test_improvement_over_noise_hand_case`: `noise` con `ddof=1` del MAE de la variante; `noise = 0` → `ratio = inf`; `folds_won`
  - `test_keep_idea_rule`: 1,3 y se conoce → `True`; 0,8 → `False`; 1,3 y no se conoce → `False`

  · P3 · Responsable:
- [X] T025 [US1] Implementar `usd_metrics`, `improvement_over_noise` y `keep_idea` en `src/tarifalatam/models/train.py` (`research.md`, punto 9). Verificar con `pytest tests/test_train.py -k "metrics or noise or keep"` · P3 · Responsable:
- [X] T026 [US1] Escribir las pruebas del adaptador y los candidatos (deben fallar antes de T027): `BaselineRegressor` da en USD la misma predicción que `MedianBaseline` (incluido el respaldo a la mediana de la ciudad y a la general); `candidates()` devuelve `linea_base`, `ridge`, `random_forest` y `lightgbm`, con las familias `baseline`, `linear`, `forest` y `boosting` y los parámetros de la sección 5.1 de la especificación de etapa · P3 · Responsable:
- [X] T027 [US1] Implementar `BaselineRegressor` y `candidates(random_state=42)` en `src/tarifalatam/models/train.py`, reutilizando `MedianBaseline` **sin modificar `baseline.py`**. Parámetros: `Ridge(alpha=1.0)`; `RandomForestRegressor(n_estimators=200, min_samples_leaf=3, max_features=0.5, n_jobs=-1, random_state=42)`; `LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=42, n_jobs=-1, verbose=-1)`. Verificar con `pytest tests/test_train.py -k "baseline or candidates"` · P3 · Responsable:
- [X] T028 [US1] Escribir las pruebas de `build_pipeline` y `feature_frame` (deben fallar antes de T029):
  - `test_build_pipeline_rejects_a_forbidden_column` (al pedir `price_usd`, error que la nombra)
  - `test_pipeline_ignores_target_and_ids`: con datos de juguete donde `price_usd`, `id` y `host_id` predicen perfecto, los nombres de salida del `ColumnTransformer` no los contienen
  - `test_build_pipeline_fits_each_family_with_each_idea` (ajusta y predice en el juguete)
  - `test_unknown_family_raises`
  - `test_feature_frame_drops_target_columns`

  · P3 · Responsable:
- [X] T029 [US1] Implementar `build_pipeline(model, family, ideas=(), with_suspicious=False)` y `feature_frame(train)` en `src/tarifalatam/models/train.py`, según `data-model.md` (sección 3) y `research.md` (puntos 5 a 7):
  - Transformadores de las ideas activas → `ColumnTransformer(remainder="drop")` → modelo.
  - Llama a `check_feature_columns`.
  - Idea 5: `TargetEncoder(target_type="continuous", cv=KFold(5, shuffle=True, random_state=42))`, **sin** los parámetros obsoletos `shuffle` y `random_state`.
  - Verificar con `pytest tests/test_train.py -k "pipeline or frame or family"`.

  · P3 · Responsable:
- [X] T030 [US1] Escribir las pruebas de `evaluate_folds` (deben fallar antes de T031): una fila por pliegue con `mae`, `mape`, `rmse`, `bias`, `r2_log` y `fit_seconds`; usa exactamente los pliegues dados (cada predicción fuera de pliegue sale de un modelo que no vio esa fila); el `Pipeline` original queda sin ajustar · P3 · Responsable:
- [X] T031 [US1] Implementar `evaluate_folds(pipeline, X, y_log, folds)` en `src/tarifalatam/models/train.py`, que devuelve (tabla por pliegue, predicciones fuera de pliegue en logaritmo), clonando el `Pipeline` en cada pliegue. Verificar con `pytest tests/test_train.py` (todo el archivo en verde) · P3 · Responsable:

### P5 · Notebook 04 e informe

- [X] T032 [US1] Reescribir `notebooks/04_features.ipynb` (solo orquesta; textos en español):
  1. `load_train()`.
  2. `make_folds` + `assert` de anfitriones disjuntos + `save_folds`.
  3. Tabla de ideas escrita **antes** de medir (cálculo, motivo, ¿se conoce al predecir?).
  4. Las 7 variantes con `build_pipeline(candidates()["lightgbm"][0], "boosting", ideas=…)` y `evaluate_folds`.
  5. Tabla con MAE ± ruido, `improvement_over_noise` y `keep_idea`.
  6. Conjunto final y medición `final_con_sospechosas` (`with_suspicious=True`).
  7. Guardar `reports/04_features_tabla.csv` (esquema de `contracts/output-files.md`).

  Sin ninguna referencia que lea `test.csv.gz` · P5 · Responsable:
- [X] T033 [US1] Ejecutar `python -m nbconvert --to notebook --execute --inplace notebooks/04_features.ipynb`. Comprobar que `data/processed/folds.csv` tiene 118.513 filas, que `reports/04_features_tabla.csv` tiene 40 filas y que no hay errores. Anotar el tiempo de ejecución · P5 · Responsable:
- [X] T034 [US1] Completar `reports/04_features.md` (la plantilla actual) **solo con cifras del notebook 04**: cómo se midió, la tabla de ideas, una línea por decisión con su cifra (también las descartadas), cuánto pesan las sospechosas, supuestos y riesgos, y la lista final de variables. Anotar en `config.py` `FINAL_IDEAS = (…)`, con un comentario que cite el informe · P5 · Responsable:
- [X] T035 [US1] (GRUPO) Revisar las decisiones de la etapa 4. Si alguna idea se conserva o descarta como **excepción** a la regla, escribir el motivo en `reports/04_features.md` antes del torneo · Responsable:

**Checkpoint**: la US1 funciona sola: variables decididas y su informe.

---

## Phase 4: User Story 2 - Un torneo que elige 1–2 finalistas, no un campeón (Priority: P2)

**Goal**: comparar la línea base, Ridge, el bosque aleatorio y LightGBM con las mismas variables y pliegues, y elegir 1–2
finalistas.

**Independent Test**: ejecutar el notebook 05: lee `folds.csv` (no recalcula pliegues), escribe `reports/05_torneo_tabla.csv`
(20 filas) y `reports/05_torneo_por_ciudad.csv` (120 filas), y `reports/05_torneo.md` nombra 1–2 finalistas con su motivo.

### P3 · Funciones del torneo

- [X] T036 [P] [US2] Escribir en `tests/test_train.py` (deben fallar antes de T037):
  - `test_city_errors_hand_case` (MAE y sesgo por ciudad y pliegue con una tabla calculada a mano)
  - `test_compare_hand_case` (diferencia media, pliegues que gana y diferencia / ruido con `ddof=1` de las diferencias)
  - `test_value_per_nights` (diferencia × 30)

  · P3 · Responsable:
- [X] T037 [US2] Implementar `city_errors`, `compare` y `value_per_nights` en `src/tarifalatam/models/train.py`, según `contracts/model-functions.md`. Verificar con `pytest tests/test_train.py` · P3 · Responsable:

### P5 · Notebook 05 e informe

- [X] T038 [US2] Reescribir `notebooks/05_torneo.ipynb` (solo orquesta):
  1. `load_train()`, `load_folds()` y `fold_indices(train, folds, exact=True)`.
  2. Los 4 candidatos con `build_pipeline(…, ideas=FINAL_IDEAS)`.
  3. `evaluate_folds` y `city_errors`.
  4. Tabla de negocio (MAE ± desviación) y de técnicas (MAPE, R², RMSE, sesgo), y diagrama de cajas.
  5. `compare` de los 3 mejores y `value_per_nights` frente a la línea base.
  6. Guardar `reports/05_torneo_tabla.csv` y `reports/05_torneo_por_ciudad.csv`.

  Sin ninguna referencia que lea `test.csv.gz` · P5 · Responsable:
- [X] T039 [US2] Ejecutar el notebook 05 con `nbconvert` y comprobar 20 y 120 filas, sin errores. Anotar el tiempo · P5 · Responsable:
- [X] T040 [US2] Completar `reports/05_torneo.md` **solo con cifras del notebook 05**: tablas, error por ciudad (con la advertencia sobre Belice), comparación pareada, diferencia en USD por cada 30 noches, finalistas según el orden de la sección 5.4 de la especificación de etapa y por qué el torneo no elige un campeón. Anotar en `config.py` `FINALISTS = (…)`, con un comentario que cite el informe · P5 · Responsable:
- [X] T041 [US2] (GRUPO) Confirmar los finalistas antes de optimizar · Responsable:

**Checkpoint**: las US1 y US2 funcionan; hay finalistas escritos.

---

## Phase 5: User Story 3 - Una optimización acotada, registrada y comprobada con honestidad (Priority: P3)

**Goal**: 30 ensayos por finalista registrados en el MLflow local, 25 % de anfitriones reservados y una decisión según el
intervalo por anfitrión.

**Independent Test**: ejecutar el notebook 06: el experimento local `tarifalatam-optimizacion` tiene una ejecución por ensayo,
la búsqueda y los reservados no comparten anfitriones, y `reports/06_best_params.json` guarda los parámetros, el intervalo y
la regla.

### P4 · Optimización (`src/tarifalatam/models/tuning.py`, pruebas en `tests/test_tuning.py`)

- [X] T042 [P] [US3] Escribir `tests/test_tuning.py` (debe fallar antes de T043):
  - `test_spaces_stay_within_approved_ranges`: muestrea 50 ensayos de cada espacio con un objetivo ficticio y comprueba los rangos de la sección 6 de la especificación de etapa.
  - `test_make_model_unknown_name_raises`
  - `test_host_bootstrap_ci_constant_difference`: con una diferencia constante, la media y los dos límites son esa constante.
  - `test_host_bootstrap_ci_resamples_hosts_not_rows`: repetir 10 veces las filas de cada anfitrión no estrecha el intervalo.
  - `test_use_optimized_rule`: (−1,2; −0,3) → `True`; (−0,8; 0,4) → `False`; (−0,5; 0,0) → `False`.
  - `test_tune_logs_one_run_per_trial`: con `configure_mlflow(force_local=True, local_db=tmp_path / "mlflow.db", env_file=tmp_path / "no.env")` y `n_trials=2` en el juguete, quedan 2 ejecuciones con nombre `<modelo>-ensayo-<nn>`, parámetros, métricas y las etiquetas `etapa`, `modelo`, `variables`, `datos` y `estado`.
  - `test_tune_records_failed_trials`: forzando un error en un ensayo, queda registrado con `estado=fallido` y cuenta en el presupuesto.
  - `test_save_decision_writes_the_contract_keys` (en `tmp_path`).

  · P4 · Responsable:
- [X] T043 [US3] Implementar `src/tarifalatam/models/tuning.py` según `contracts/model-functions.md` y `research.md` (puntos 10 y 12):
  - `lgbm_space`, `rf_space` y `ridge_space` con los rangos aprobados; `make_model`.
  - `tune`, con `TPESampler(seed=42)` y `catch=(Exception,)`, y **una ejecución por ensayo** con `log_run` de `mlflow_utils.py`, **sin reescribir ese módulo**.
  - `host_bootstrap_ci`, con remuestreos en bloques de 100.
  - `use_optimized` y `save_decision`.
  - Verificar con `pytest tests/test_tuning.py`.

  · P4 · Responsable:

### P5 · Notebook 06 e informe

- [X] T044 [US3] Reescribir `notebooks/06_optimizacion.ipynb` (solo orquesta):
  1. `configure_mlflow(force_local=True)`, mostrando los avisos; `set_experiment(EXPERIMENT_NAME)` e imprimir `MLflow: local | experimento: …`.
  2. `reserve_hosts` con `assert` de anfitriones disjuntos y `fold_indices(search, folds, exact=False)`.
  3. Presupuesto y espacio escritos antes de buscar.
  4. `tune` para cada uno de los `FINALISTS`, con `N_TRIALS`.
  5. Exportar los ensayos a `reports/06_optimizacion_tabla.csv`.
  6. Comprobación honesta: partida contra optimizados en los reservados, diferencia por anuncio, `host_bootstrap_ci` y `use_optimized`. Con dos finalistas, comparación entre ellos.
  7. `save_decision` en `reports/06_best_params.json`.

  La mejor puntuación de la búsqueda se rotula como optimista y no se reporta como resultado. Sin ninguna referencia que lea `test.csv.gz` · P5 · Responsable:
- [X] T045 [US3] Ejecutar el notebook 06 en segundo plano, con `python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/06_optimizacion.ipynb`. Comprobar con `mlflow ui --backend-store-uri sqlite:///mlflow_local.db` (o `mlflow.search_runs`) que hay una ejecución por ensayo, que existen los dos archivos de salida y que `git status` no muestra `mlflow_local.db`. Anotar el tiempo · P5 · Responsable:
- [X] T046 [US3] Completar `reports/06_optimizacion.md` **solo con cifras del notebook 06**: espacio de búsqueda, presupuesto, resultados, comprobación con su intervalo, decisión según la regla y la nota sobre el doble uso de los anfitriones reservados · P5 · Responsable:
- [X] T047 [US3] (GRUPO) Aceptar la decisión de parámetros y el modelo que pasa a la etapa 7 · Responsable:

**Checkpoint**: las tres historias funcionan; el hito H2 tiene su parte de clase 3.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: revisión, registro de decisiones y validación final

- [ ] T048 [P] Ejecutar el subagente `auditor-de-fuga` sobre `src/tarifalatam/features/`, `src/tarifalatam/models/`, `src/tarifalatam/data/folds.py` y los notebooks 04 a 06; atender sus hallazgos y anotarlos en `reports/04_features.md` (sección de riesgos) · Responsable:
- [ ] T049 [P] Ejecutar el subagente `revisor-de-codigo-ia` sobre el código nuevo y corregir lo que encuentre (con una prueba por corrección) · Responsable:
- [X] T050 Ejecutar `pytest` desde la raíz y la validación de `quickstart.md` (incluido el `grep` de `test.csv` y la comprobación de que la barrera de columnas falla con `price_usd`) · Responsable:
- [X] T051 Marcar los criterios de cierre de la sección 10 de `especificaciones/04-features-torneo-optimizacion.md` que se cumplan, y agregar a la sección 7 de `especificacion-proyecto.md` las decisiones nuevas con su cifra (variables finales, finalistas, parámetros elegidos) · Responsable:
- [ ] T052 (GRUPO) Cada integrante explica al menos una función de su paquete con `material-del-curso/kit/checklist-revision-ia.md` · Responsable:
- [ ] T053 (GRUPO) Quien no escribió el código responde las 8 preguntas de la guía (sección 5) · Responsable:

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (fase 1)**: sin dependencias. T001 solo hace falta para ejecutar notebooks; las pruebas no usan datos reales.
- **Foundational (fase 2)**: depende de T002 (la tabla de juguete) y bloquea todas las historias.
- **US1 (fase 3)**: depende de la fase 2.
- **US2 (fase 4)**: su código (T036–T037) solo depende de la fase 2 y de T031. Su notebook (T038) necesita `FINAL_IDEAS` (T034) o, para probarlo antes, la referencia (`ideas=()`).
- **US3 (fase 5)**: su código (T042–T043) depende de T029 y T031. Su notebook (T044) necesita `FINALISTS` (T040).
- **Polish (fase 6)**: al final.

### Within Each User Story

- La prueba primero, y debe fallar; después la función; se marca `[X]` cuando la prueba pasa.
- En P3, `build_pipeline` (T029) necesita los transformadores de P2 (T011–T021) y `feature_columns` (T023). Mientras no estén,
  sus pruebas pueden empezar con `ideas=()` (solo la referencia).
- Notebook → ejecución → informe → decisión del grupo.

### Parallel Opportunities

- T002 con T001.
- T003, T006 y T008 (tres archivos de prueba distintos); después de T004, T005, T007 y T009 van en paralelo.
- Al terminar la fase 2, P2 (T010–T021), P1 (T022–T023) y las pruebas de métricas de P3 (T024–T025) avanzan a la vez.
- P4 (T042–T043) puede avanzar mientras se ejecuta el notebook 04 o el 05.
- T048 y T049.

---

## Parallel Example: User Story 1

```bash
# Tres integrantes a la vez, en archivos distintos:
Task: "T010–T021 Variables en src/tarifalatam/features/engineering.py + tests/test_features.py"      # P2
Task: "T022–T023 feature_columns en src/tarifalatam/features/columns.py + tests/test_columns.py"     # P1
Task: "T024–T025 Métricas y regla en src/tarifalatam/models/train.py + tests/test_train.py"          # P3
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Fases 1 y 2: listas de columnas, carga y pliegues.
2. Fase 3: variables, `build_pipeline` y `evaluate_folds`, notebook 04 y su informe.
3. **Parar y validar**: tabla de ideas con 40 filas, decisiones según la regla y `pytest` en verde.

### Incremental Delivery

1. Fases 1 y 2 → base lista.
2. US1 → variables decididas (MVP).
3. US2 → finalistas.
4. US3 → parámetros decididos y registrados.

### Parallel Team Strategy (cinco integrantes)

1. P1 hace la fase 2 mientras P2 escribe las pruebas de las variables y P5 prepara la tabla de juguete y copia los datos.
2. P2 termina las variables; P3 arma `train.py`; P4 empieza `tuning.py` en cuanto existan `build_pipeline` y `evaluate_folds`.
3. P5 ejecuta los notebooks en orden y redacta los informes, que revisa todo el grupo.

---

## Notes

- [P] = otro archivo y sin dependencias pendientes.
- Hacer un commit por tarea o por grupo lógico de tareas, con la cuenta de quien la hizo.
- No abrir `test.csv.gz` en ninguna tarea.
- No reescribir `mlflow_utils.py`, `baseline.py` ni `split.py`.
- Ninguna cifra entra a un informe sin salir de un notebook ejecutado.
