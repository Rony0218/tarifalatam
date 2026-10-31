---

description: "Lista de tareas del hito H1: EDA reproducible, limpieza y partición por anfitrión"
---

# Tasks: EDA reproducible, limpieza y partición por anfitrión (hito H1)

**Input**: Documentos de diseño en `specs/001-eda-limpieza-particion/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: **Sí se piden.** FR-020, FR-021 y FR-022 y la regla 9 de `CLAUDE.md` exigen una prueba por regla. En cada historia,
la prueba se escribe **antes** que la función y debe fallar primero.

**Organization**: tareas agrupadas por historia de usuario (US1 = datos limpios y partidos, US2 = notebook del EDA,
US3 = registro de exclusiones y rastro escrito).

**Regla del proyecto**: una tarea se marca `[X]` **solo cuando su prueba pasa** (`CLAUDE.md`). Las tareas marcadas
**(GRUPO)** las hace una persona del grupo, no Claude.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas pendientes)
- **[Story]**: historia a la que pertenece (US1, US2, US3)
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

- Paquete: `src/tarifalatam/` · Pruebas: `tests/` · Notebooks: `notebooks/` · Informes: `reports/`
- Todo el código usa nombres en inglés y docstrings/comentarios en español, al estilo de
  `material-del-curso/ejemplo-creditsight/src/creditsight/` (solo como referencia de estilo; sus cifras no aplican)

---

## Phase 1: Setup (infraestructura compartida)

**Purpose**: dejar el repo listo para que las salidas no se suban y las pruebas encuentren el paquete

- [X] T001 Agregar a `.gitignore`, debajo del bloque de `data/raw/*`, las líneas `data/processed/*` y `!data/processed/.gitkeep`, con un comentario en español: "los conjuntos procesados conservan host_id: no se suben al repo público". Verificar con `git status --short data/` que `data/processed/.gitkeep` sigue versionado
- [X] T002 [P] Crear `tests/fixtures.py` con la función `make_listings(**overrides) -> pd.DataFrame`: una tabla de juguete de ~12 anuncios, 2 ciudades (`rio-de-janeiro`, `belize`) y 5 `host_id` (uno con anuncios en ambas ciudades). Debe tener las columnas que usan las reglas: `id`, `host_id`, `city`, `source`, `price` (texto `"$1,234.00"`), `price_quote_raw` (JSON con `{"quote": {"currency": ...}}`), las 5 `price_quote_*`, `estimated_revenue_l365d`, `estimated_occupancy_l365d`, `bathrooms_text`, `minimum_nights`, `maximum_nights`, `bedrooms`, `accommodates`, `room_type`, `number_of_reviews`, `review_scores_rating` y las 12 columnas vacías. Comentario en el archivo: "datos inventados a mano solo para pruebas"

---

## Phase 2: Foundational (prerrequisitos que bloquean todo)

**Purpose**: constantes del proyecto y la carga sin datos personales, que usan las tres historias

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase

- [X] T003 Crear `src/tarifalatam/config.py` con docstring en español y estas constantes:
  - **Rutas y partición:** `ROOT` (raíz del repo: `Path(__file__).resolve().parents[2]`), `RAW_DIR`, `PROCESSED_DIR`, `REPORTS_DIR`, `RANDOM_STATE = 42`, `GROUP_COL = "host_id"`, `TARGET = "log_price_usd"` y `TEST_SIZE = 0.2`.
  - **Archivos:** `CITY_FILES` (diccionario ciudad → nombre de archivo, exactamente los siete del `README.md`).
  - **Monedas:** `CITY_CURRENCY` (`rio-de-janeiro`/`sao-paulo` "BRL", `mexico-city` "MXN", `buenos-aires` "ARS", `bogota` "COP", `santiago` "CLP", `belize` "USD").
  - **Tasas:** `FX_RATES` (por ciudad: `currency`, `local_per_usd`, `date` = fecha del corte, `source`). `local_per_usd=None` y `source=None` en las cinco pendientes; `belize` con `local_per_usd=1.0` y `source` = "Inside Airbnb publica en USD (price_quote_raw)". Comentario: "unidades de moneda local por 1 USD; las anota el grupo desde el banco central".
  - **Listas de columnas:** `PII_COLUMNS` (las 10), `FREE_TEXT_COLUMNS` (`name`, `description`, `neighborhood_overview`), `LEAKAGE_COLUMNS` (las 6 de `data-model.md`), `EMPTY_COLUMNS` (las 12 de `data-model.md`).
  - **Umbrales:** `MONTHLY_MIN_NIGHTS = 30`, `MAX_NIGHTS_CAP = 1125`, `MAX_BEDROOMS = 10` y `PRICE_RATIO_BOUNDS = (0.1, 20.0)`.
  - Cada umbral lleva un comentario con la cifra del EDA que lo respalda.
- [X] T004 Escribir en `tests/test_cleaning.py` las pruebas de carga, que deben fallar antes de T005:
  - `test_load_raw_adds_city_and_drops_personal_and_free_text`: escribe siete `.csv.gz` mínimos en `tmp_path` con los nombres de `CITY_FILES` y verifica que aparece `city` y que no queda ninguna columna de `PII_COLUMNS` ni de `FREE_TEXT_COLUMNS`. Esta es la `test_no_personal_columns` de FR-022.
  - `test_load_raw_fails_if_a_city_file_is_missing`.
  - `test_load_raw_does_not_modify_raw_files`: compara el tamaño y la fecha de modificación antes y después.
- [X] T005 Implementar `load_raw(raw_dir=RAW_DIR) -> pd.DataFrame` en `src/tarifalatam/data/cleaning.py`, según `contracts/data-functions.md`:
  - Lee los siete archivos de `CITY_FILES`, falla con un mensaje en español si falta alguno o si sus columnas difieren entre archivos, y agrega `city`.
  - Elimina `PII_COLUMNS` y `FREE_TEXT_COLUMNS` **en la misma función**, antes de devolver nada.
  - El módulo empieza con un docstring que lista las 11 decisiones del EDA.
  - Verificar con `pytest tests/test_cleaning.py -k load_raw`.

**Checkpoint**: `pytest` en verde para la carga; las historias pueden empezar

---

## Phase 3: User Story 1 - Datos limpios y partidos por anfitrión (Priority: P1) 🎯 MVP

**Goal**: generar `data/processed/train.csv.gz` y `test.csv.gz` desde cero, sin datos personales ni fuga, sin anfitriones en común

**Independent Test**: borrar `data/processed/` (salvo `.gitkeep`), ejecutar `notebooks/03_preprocesamiento.ipynb` y comprobar que aparecen los dos archivos, que la intersección de `host_id` está vacía y que `data/raw/` no cambió (quickstart §3 y §4)

### Tests for User Story 1 (se escriben primero y deben fallar) ⚠️

- [X] T006 [P] [US1] En `tests/test_cleaning.py`, con `make_listings`, escribir una prueba (caso normal + caso sucio) para cada regla:
  - `test_check_currencies_passes_and_fails_on_mismatch`: Belice con "BRL" en `price_quote_raw` → error que nombra la ciudad; JSON vacío → no falla.
  - `test_drop_previous_scrape`: `source == "previous scrape"` → excluir la fila.
  - `test_parse_price`: `"$1,234.00"` → 1234.0; `"abc"` → vacío.
  - `test_drop_missing_price`.
  - `test_to_usd_divides_by_local_per_usd`: con tasas inventadas en la prueba, comentadas como tales.
  - `test_to_usd_fails_when_rate_is_none`: el mensaje incluye el nombre de la ciudad.
  - `test_drop_leakage_columns`: ignora las columnas que ya no estén.
  - `test_drop_empty_columns`.
  - `test_parse_bathrooms_text`: `"1.5 shared baths"` → 1.5 y `bathroom_shared = 1`; `"Half-bath"`, `"Shared half-bath"`, `"Private half-bath"` → 0.5; `"No bathroom"` → 0; vacío → vacío.
  - `test_drop_monthly_rentals`: `minimum_nights >= 30` → excluir; 29 se queda.
  - `test_mark_impossible_values`: `maximum_nights > 1125` → vacío; `bedrooms > 10` y `bedrooms > accommodates` → vacío; `bedrooms = 12` con `accommodates = 16` se queda; no se quitan filas.
  - `test_add_review_flags`: `number_of_reviews > 0` → `has_reviews = 1`, si no 0; las notas no se imputan.
  - `test_fit_price_bounds_uses_only_given_table`.
  - `test_drop_price_outliers`: fuera de [0,1 × mediana, 20 × mediana] de su ciudad → excluir; ciudad sin límites → error.
  - `test_add_target_is_log_of_price_usd`.
  - `test_functions_do_not_modify_input`: la tabla de entrada queda igual.
- [X] T007 [P] [US1] Crear `tests/test_split.py`:
  - `test_split_by_host_never_shares_a_host`: incluye el anfitrión con anuncios en dos ciudades.
  - `test_split_by_host_loses_no_rows`: `len(train) + len(test) == len(df)`.
  - `test_split_by_host_is_reproducible_with_seed`.
  - `test_assert_disjoint_hosts_raises_on_overlap`.
  - `test_row_split_would_be_caught`: parte la tabla de juguete por fila con `train_test_split` y verifica que `assert_disjoint_hosts` lanza error. Así se prueba que el control detecta la partición por fila (FR-021).
  - `test_group_cv_folds_do_not_share_hosts`.
- [X] T008 [P] [US1] Crear `tests/test_baseline.py`:
  - `test_median_baseline_by_city_and_room_type`.
  - `test_median_baseline_falls_back_to_city_median`: combinación no vista → mediana de la ciudad.
  - `test_baseline_cv_mae_fits_only_on_train_folds`: un anuncio extremo en un solo pliegue de validación no cambia la mediana aprendida.
- [X] T009 [P] [US1] Crear `tests/test_pipeline.py`:
  - `test_build_datasets_output_contract`: con siete `.csv.gz` de juguete en `tmp_path` y tasas inventadas en la prueba, verifica el contrato de `contracts/processed-files.md`.
    - Siempre presentes: `id`, `host_id`, `city`, `room_type`, `price_local`, `price_usd`, `log_price_usd`, `bathrooms_count`, `bathroom_shared`, `has_reviews`.
    - Nunca presentes: personales, texto libre, fuga, vacías y `price`.
    - "`price_usd > 0` y `log_price_usd` finito en todas las filas".
    - "`minimum_nights < 30` y `source != "previous scrape"` en todas las filas".
    - Ningún `host_id` en ambos conjuntos.

### Implementation for User Story 1

- [X] T010 [US1] Implementar en `src/tarifalatam/data/cleaning.py` las funciones de reglas, en este orden y una por decisión, con docstring en español que cite la cifra del EDA. Ninguna modifica la tabla recibida: todas trabajan sobre `df.copy()`.
  - `check_currencies`
  - `drop_previous_scrape`
  - `parse_price`: crea `price_local` y quita `price`.
  - `drop_missing_price`
  - `to_usd(df, rates=FX_RATES)`: error en español "falta la tasa de cambio de <ciudad>" si es `None`.
  - `drop_leakage_columns`
  - `drop_empty_columns`
  - `parse_bathrooms_text`
  - `drop_monthly_rentals`
  - `mark_impossible_values`
  - `add_review_flags`
  - `fit_price_bounds(train)`
  - `drop_price_outliers(df, bounds)`
  - `add_target`
  - Verificar con `pytest tests/test_cleaning.py`.
- [X] T011 [P] [US1] Implementar en `src/tarifalatam/data/split.py`:
  - `split_by_host(df, test_size=TEST_SIZE, seed=RANDOM_STATE)`: con `GroupShuffleSplit`, y llamando a `assert_disjoint_hosts` antes de devolver.
  - `assert_disjoint_hosts(*frames)`
  - `group_cv(n_splits=5)`: con `GroupKFold`.
  - Docstring del módulo: por qué se parte por anfitrión (31 % de los anuncios es de anfitriones con ≥ 10 anuncios).
  - Verificar con `pytest tests/test_split.py`.
- [X] T012 [P] [US1] Implementar en `src/tarifalatam/models/baseline.py`:
  - `MedianBaseline` con `fit(train)` y `predict(df)`: mediana de `price_usd` por `city` × `room_type`, y respaldo con la mediana de la ciudad.
  - `baseline_cv_mae(train, n_splits=5) -> dict` con `per_fold`, `mean` y `std`: usa `group_cv` y `groups=train[GROUP_COL]`.
  - Verificar con `pytest tests/test_baseline.py`.
- [X] T013 [US1] Implementar `build_datasets(raw_dir=RAW_DIR, rates=FX_RATES) -> (train, test, bounds)` en `src/tarifalatam/data/pipeline.py`:
  - Aplica los 15 pasos en el orden exacto de la tabla de `research.md` §4.
  - Parte con `split_by_host` y ajusta `fit_price_bounds` **solo** con `train`; después aplica `drop_price_outliers` y `add_target` a ambos.
  - En esta tarea no lleva registro de exclusiones (lo agrega T024).
  - Verificar con `pytest tests/test_pipeline.py`.
- [X] T014 [US1] **(GRUPO)** Anotar en `src/tarifalatam/config.py` (`FX_RATES`) las cinco tasas oficiales del banco central (BRL, MXN, ARS, COP, CLP), en unidades de moneda local por 1 USD, para la fecha del corte de cada ciudad, con el enlace en `source`. Registrar la decisión en la sección 7 de `especificacion-proyecto.md`. **Bloquea T015.** *(Hecho: tasas anotadas con su fuente el 2026-10-30 y aprobadas por el grupo el 2026-10-31.)*
- [X] T015 [US1] Reescribir `notebooks/03_preprocesamiento.ipynb` para que **solo orqueste**: *(Hecho 2026-10-30: ejecutado desde cero con las tasas oficiales en 24 s; 174.731 filas, 0 anfitriones en común.)*
  - Celdas en orden: importar de `tarifalatam`; `train, test, bounds = build_datasets()`; guardar `data/processed/train.csv.gz` y `test.csv.gz` (con `index=False`).
  - Imprimir los controles: anfitriones en común = 0, filas y anfitriones por conjunto y por ciudad, límites de precio por ciudad.
  - Calcular y mostrar `baseline_cv_mae(train)`.
  - **No** mostrar estadísticas de `test` más allá de contar filas y anfitriones.
  - Ejecutar desde cero (quickstart §3) y anotar el tiempo.
- [X] T016 [US1] Copiar a `reports/01_eda.md`, sección "Qué son los datos" → "Línea base", el MAE de la línea base en USD (promedio ± desviación de 5 pliegues por anfitrión, solo con el entrenamiento), tal como lo imprimió T015. Si T014 no está hecho, dejarlo como pendiente: no se inventa.

**Checkpoint**: US1 funciona sola; `pytest` en verde y los dos conjuntos generados desde cero

---

## Phase 4: User Story 2 - El notebook del EDA reproduce las cifras del informe (Priority: P2)

**Goal**: que `notebooks/02_eda.ipynb` corra de principio a fin y muestre las cifras de FR-018 iguales a `reports/01_eda.md`

**Independent Test**: `jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb` termina sin errores y su tabla final dice "coincide = sí" en todas las filas (quickstart §2). No necesita las tasas de cambio

- [X] T017 [US2] Reescribir la carga y las secciones 0 a 2 de `notebooks/02_eda.ipynb`:
  - Celda inicial con `sys.path` a `src/`, `from tarifalatam.data.cleaning import load_raw` y `from tarifalatam.config import GROUP_COL`; `df = load_raw()`, que ya viene sin datos personales.
  - Sección 1 (unidad de análisis): filas por ciudad, anfitriones, anuncios por anfitrión, % de anuncios de anfitriones con ≥ 10 y anfitriones en más de una ciudad.
  - Sección 2 (objetivo): `price` a número **con `parse_price`** (no se repite lógica), % sin precio por ciudad, asimetría en escala original y en logaritmo, y medianas por ciudad × `room_type`.
  - Cada sección cierra con una celda markdown con la respuesta en una frase.
- [X] T018 [US2] Reescribir las secciones 3 a 5 de `notebooks/02_eda.ipynb`:
  - Calidad: columnas 100 % vacías por ciudad, conteo de `minimum_nights >= 30` (y % en Bogotá), centinelas de `maximum_nights`, `bedrooms > 10`, precios > 20 × y < 0,1 × la mediana de su ciudad, % sin reseñas y coincidencia con notas vacías, duplicados y `source == "previous scrape"`.
  - Constancia por anfitrión.
  - Fuga: razón `price` / `price_quote_price_per_night` y `estimated_revenue_l365d` / (precio × ocupación).
  - Monedas por ciudad leídas de `price_quote_raw`.
  - Ninguna celda imprime filas completas: solo conteos y resúmenes.
- [X] T019 [US2] Agregar al final de `notebooks/02_eda.ipynb` una celda que arme la tabla "cifra | esperado (informe) | obtenido | coincide". Los valores esperados se copian de `reports/01_eda.md`: 194.628 filas; 89.964 anfitriones; % sin precio por ciudad; razón precio/cotización = 1; 12 columnas vacías; 6.103 con `minimum_nights >= 30`; 692 precios > 20 ×; 15,5 % sin reseñas.
- [X] T020 [US2] Ejecutar `jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb` (con `PYTHONUTF8=1`).
  - Si alguna cifra no coincide, **corregir `reports/01_eda.md` con la cifra del notebook** y anotar el cambio en su sección "Qué queda abierto". No se ajusta el código para que "dé".
  - Revisar que la salida no muestre nombres, fotos, URLs, teléfonos ni correos.
- [X] T021 [US2] Quitar de `reports/01_eda.md` la nota "Estado: borrador … script exploratorio" y reemplazarla por "Cifras reproducidas por `notebooks/02_eda.ipynb` el <fecha>". En `especificaciones/02-eda.md`, marcar ☒ los criterios de cierre que ya se cumplen.

**Checkpoint**: US2 funciona sola (no depende de US1 ni de las tasas)

---

## Phase 5: User Story 3 - Cada regla deja rastro escrito (Priority: P3)

**Goal**: registro de exclusiones por regla, ciudad y conjunto, que cuadra y se copia a `reports/`

**Independent Test**: `pytest tests/test_pipeline.py` en verde; en `reports/03_exclusiones.csv` cada fila cumple `before − removed = after`

### Tests for User Story 3 ⚠️

- [X] T022 [P] [US3] Agregar a `tests/test_pipeline.py`:
  - `test_exclusion_log_balances`: en cada fila `before - removed == after`, y el `after` de un paso es el `before` del siguiente para la misma ciudad y el mismo `split`.
  - `test_exclusion_log_has_expected_steps`: aparecen `previous_scrape`, `missing_price`, `monthly_rental` con `split = all`, y `price_outlier` con `split = train` y `split = test`.
  - `test_exclusion_log_includes_price_bounds`: filas con `step = price_bounds` y columnas `low_usd` y `high_usd`.

### Implementation for User Story 3

- [X] T023 [US3] Crear en `src/tarifalatam/data/pipeline.py` el ayudante `log_step(log, step, split, before_df, after_df)`. Agrega una fila por ciudad con `step`, `split`, `city`, `before`, `removed` y `after`, según `contracts/processed-files.md`.
- [X] T024 [US3] Cambiar `build_datasets` en `src/tarifalatam/data/pipeline.py` para que:
  - Registre cada paso que quita filas.
  - Agregue las filas `price_bounds` con `low_usd` y `high_usd`.
  - Devuelva `(train, test, exclusions, bounds)`.
  - Actualizar `tests/test_pipeline.py` (T009) al nuevo retorno y verificar con `pytest tests/test_pipeline.py`.
- [X] T025 [US3] En `notebooks/03_preprocesamiento.ipynb`, guardar `exclusions` en `reports/03_exclusiones.csv` (`index=False`) y mostrar una tabla resumen: filas de partida, quitadas por regla y finales, por ciudad. Volver a ejecutar desde cero. *(Hecho 2026-10-30: reports/03_exclusiones.csv generado.)*
- [X] T026 [US3] Llenar las secciones 3 y 4 de `especificaciones/03-preprocesamiento.md` con las reglas implementadas (columna, regla exacta con su umbral, función, prueba) y las cifras de `reports/03_exclusiones.csv`. Marcar ☒ en su sección 6 lo que ya se verificó.

**Checkpoint**: las tres historias funcionan por separado

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T027 Ejecutar `pytest` sobre `tests/` desde la raíz (con `PYTHONUTF8=1`) y confirmar que todo está en verde. Pegar el resumen de la salida en la descripción del cambio *(Hecho 2026-10-30: 66 pruebas en verde. `tests/test_tracking.py` no corre fuera del `.venv` porque necesita `mlflow`.)*
- [X] T028 Verificación manual de FR-021 (quickstart §1): cambiar temporalmente `split_by_host` para que parta por fila, ejecutar `pytest tests/test_split.py`, confirmar que falla, **revertir** y confirmar que vuelve a pasar
- [X] T029 [P] Ejecutar el subagente `auditor-de-fuga` sobre `src/tarifalatam/data/`, `src/tarifalatam/models/baseline.py` y los notebooks 02 y 03. Anotar sus hallazgos y lo que se hizo con cada uno en `reports/01_eda.md` → "Qué queda abierto". En especial: la regla de extremos aplicada a la prueba
- [X] T030 [P] Ejecutar el subagente `revisor-de-codigo-ia` sobre los archivos nuevos de `src/` y aplicar `material-del-curso/kit/checklist-revision-ia.md`
- [X] T031 Recorrer `specs/001-eda-limpieza-particion/quickstart.md` de principio a fin (§1 a §4) y confirmar `git status --short data/` sin líneas
- [ ] T032 **(GRUPO)** Repartir las funciones de `cleaning.py` entre los cinco integrantes. Cada uno debe poder explicar la suya, con su cifra y su motivo (SC-007)

---

## Phase 7: Cambio del 2026-10-31 — se excluye Buenos Aires (FR-012)

**Purpose**: aplicar la decisión del grupo (sección 7 de `especificacion-proyecto.md`) sin borrar el archivo crudo ni rehacer
el EDA. La exclusión es una regla más del preprocesamiento, con su prueba y su fila en el registro de exclusiones.

**Estado**: aprobado por el grupo el 2026-10-31 y hecho (T033 a T046).

**Efectos que hay que aceptar**: la partición se vuelve a sortear (cambian los anfitriones de cada conjunto; la prueba no se ha
usado para nada, así que no hay fuga) y cambian todas las cifras de filas, extremos y línea base.

- [X] T033 Enmendar la constitución con `/speckit-constitution`: en "Restricciones del proyecto", cambiar "siete ciudades" por
  "seis ciudades (Buenos Aires se excluye desde el 2026-10-31)". Subir la versión a 0.3.0 y anotar la enmienda en la sección 7
  de `especificacion-proyecto.md`
- [X] T034 [P] Escribir primero, en `tests/test_cleaning.py`, la prueba `test_drop_excluded_cities` (debe fallar antes de T036):
  - con `make_listings` y `cities=("belize",)`, solo quedan las filas de `rio-de-janeiro`;
  - con `cities=()` no se quita ninguna fila;
  - la tabla de entrada no cambia.
- [X] T035 En `src/tarifalatam/config.py`, agregar `EXCLUDED_CITIES = ("buenos-aires",)` con un comentario que dé el motivo y la
  cifra (29.753 anuncios; 38,6 % de precios múltiplos de 764,41 ARS). Buenos Aires **se queda** en `CITY_FILES`,
  `CITY_CURRENCY` y `FX_RATES` (el EDA sigue leyendo su archivo); en su tasa, anotar "no se usa: se excluye antes de convertir"
- [X] T036 En `src/tarifalatam/data/cleaning.py`, implementar `drop_excluded_cities(df, cities=EXCLUDED_CITIES)` sobre
  `df.copy()`, con docstring en español que cite la decisión. Verificar con `pytest tests/test_cleaning.py`
- [X] T037 En `src/tarifalatam/data/pipeline.py`, aplicarla como **primer paso después de `load_raw`** y antes de
  `check_currencies`, registrada como `excluded_city` con `split = all`. Actualizar el orden de pasos en `research.md` §4
- [X] T038 Actualizar `tests/test_pipeline.py`:
  - `test_exclusion_log_has_expected_steps` también exige `("excluded_city", "all")`;
  - los límites de precio (`bounds`) cubren las ciudades de `CITY_FILES` **menos** `EXCLUDED_CITIES`;
  - prueba nueva `test_build_datasets_excludes_buenos_aires`: ninguna fila de `buenos-aires` en entrenamiento ni en prueba.
- [X] T039 Ejecutar `pytest tests` (con `PYTHONUTF8=1`) y confirmar todo en verde
- [X] T040 Borrar `data/processed/` (salvo `.gitkeep`) y volver a ejecutar `notebooks/03_preprocesamiento.ipynb` desde cero:
  regenera `train.csv.gz`, `test.csv.gz`, `reports/03_exclusiones.csv` y la línea base. Controles: 0 anfitriones en común y
  ninguna fila de Buenos Aires. De la prueba solo se cuentan filas y anfitriones
- [X] T041 Reemplazar las cifras viejas por las que imprimió T040 (sin inventar ninguna) en:
  - `especificaciones/03-preprocesamiento.md` (fila nueva en la tabla de reglas y el resultado final);
  - `especificacion-proyecto.md` (secciones 3 y 4);
  - `reports/01_eda.md` (línea base y "Qué queda abierto": Buenos Aires decidido) y `especificaciones/02-eda.md`.
- [X] T042 Cambiar "siete ciudades" por "seis ciudades" donde se habla **del modelo**: `reports/00_caso.md`,
  `models/ficha_modelo.md`, `notebooks/01_caso_negocio.ipynb` y la fila de Buenos Aires en `reports/07_validacion.md`. En el
  `README.md`, el archivo de Buenos Aires se queda en la tabla con la nota "se descarga, pero se excluye del modelo"
- [X] T043 [P] Escribir primero, en `tests/test_cleaning.py`, `test_drop_unused_columns_removes_license` y
  `test_drop_unused_columns_ignores_columns_already_gone` (decisión del grupo del 2026-10-31: se elimina `license`)
- [X] T044 Agregar `UNUSED_COLUMNS = ["license"]` en `config.py` y `drop_unused_columns` en `cleaning.py`; aplicarla en
  `pipeline.py` después de `drop_empty_columns`. En `tests/test_pipeline.py`, los archivos de juguete traen `license` y
  el contrato exige que no llegue a los conjuntos
- [X] T045 Agregar `pytest.ini` con `testpaths = tests`: `pytest` desde la raíz ya no recoge las pruebas del ejemplo
  CreditSight (`material-del-curso/`), que tienen los mismos nombres de archivo y chocaban con las nuestras
- [X] T046 Crear un entorno con las versiones de `requirements.txt` y correr `pytest` desde la raíz: 76 pruebas en verde,
  incluida `tests/test_tracking.py` (necesita `mlflow`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sin dependencias.
- **Foundational (Fase 2)**: depende de la Fase 1 (T002 para las pruebas). **Bloquea todas las historias.**
- **US1 (Fase 3)**: depende de la Fase 2.
  - T015 y T016 dependen además de **T014 (tasas del grupo)**.
- **US2 (Fase 4)**: depende de la Fase 2 (usa `load_raw`) y de T010 (usa `parse_price`). No depende de las tasas ni del resto de US1.
- **US3 (Fase 5)**: depende de T013 (`build_datasets`). T025 depende de T015.
- **Polish (Fase 6)**: al final.

### Dentro de cada historia

- Pruebas primero (deben fallar), después la implementación y por último el notebook.
- `cleaning.py` (T010) y `split.py` (T011) antes de `pipeline.py` (T013).

### Parallel Opportunities

- T002 en paralelo con T001.
- En US1: T006, T007, T008 y T009 (cuatro archivos de prueba distintos); después T011 y T012 en paralelo con T010.
- US2 puede avanzar en paralelo con T013–T016 una vez hecho T010: no necesita las tasas.
- T029 y T030 en paralelo.

---

## Parallel Example: User Story 1

```text
# Pruebas de US1, al mismo tiempo (archivos distintos):
T006 tests/test_cleaning.py · T007 tests/test_split.py · T008 tests/test_baseline.py · T009 tests/test_pipeline.py

# Implementación sin dependencias entre sí:
T010 src/tarifalatam/data/cleaning.py · T011 src/tarifalatam/data/split.py · T012 src/tarifalatam/models/baseline.py
```

---

## Implementation Strategy

### MVP First (solo US1)

1. Fase 1 y Fase 2 (config y carga sin datos personales).
2. Fase 3 hasta T013: todas las reglas y la partición, probadas con datos de juguete. **Esto no necesita las tasas.**
3. Cuando el grupo anote las tasas (T014): T015 y T016 generan los conjuntos reales y la línea base.
4. **Parar y validar** con quickstart §3 y §4.

### Entrega incremental

1. US1 → conjuntos listos para la etapa 4.
2. US2 → EDA reproducible (cierra la especificación 02).
3. US3 → registro de exclusiones (cierra la especificación 03).
4. Revisión con los subagentes y cierre del hito H1.

---

## Notes

- Cada tarea se marca `[X]` solo cuando su prueba pasa.
- Nunca se escriben tasas de cambio inventadas en `config.py`. Las de las pruebas viven solo en `tests/` y dicen que son inventadas.
- `data/raw/` no se modifica; `data/processed/` no se sube a Git (T001).
- Hacer commit después de cada grupo lógico de tareas, **solo cuando el grupo lo pida**.
