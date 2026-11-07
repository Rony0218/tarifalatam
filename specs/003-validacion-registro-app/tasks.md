---

description: "Lista de tareas del cierre del hito H2 (etapas 7 a 9): validación en la prueba, registro del modelo y app local"
---

# Tasks: Validación en la prueba, registro del modelo y app local (hito H2, etapas 7 a 9)

**Input**: Documentos de diseño en `specs/003-validacion-registro-app/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: **Sí se piden** (FR-023 y la regla 9 de `CLAUDE.md`). En cada tarea de código, la prueba se escribe **antes** que
la función y debe **fallar primero**.

**Organization**: tareas agrupadas por historia de usuario (US1 = medida honesta en la prueba, US2 = modelo registrado,
US3 = precio sugerido y app local) y, dentro de cada una, por paquete del plan (P1 a P5).

**Reglas del proyecto**:

- Una tarea se marca `[X]` **solo cuando su prueba pasa** (para notebooks e informes: cuando se cumple su comprobación).
- **La prueba se abre una sola vez, en T018.** Ninguna tarea anterior la lee, ni siquiera para contar filas.
- **Responsable**: lo asigna el grupo al aprobar esta lista. Cada integrante hace los commits de sus tareas con su cuenta de
  GitHub.
- Las tareas marcadas **(GRUPO)** son decisiones o revisiones del grupo, no código.

## Reparto por paquete (lo llena el grupo)

| Paquete | Tareas | Responsable |
|---|---|---|
| P1 · Validación | T003–T004, T005–T014 | |
| P2 · Interpretación | T015–T016 | |
| P3 · Registro | T001, T021–T025 | |
| P4 · Inferencia y app | T026–T030, T033 | |
| P5 · Notebooks e informes | T002, T017–T019, T031–T032, T034 | |
| Decisiones del grupo | T020, T038, T039 | Todo el grupo |
| Cierre | T035–T037, T040 | |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo, sin depender de tareas pendientes)
- **[Story]**: historia a la que pertenece (US1, US2, US3)
- Cada tarea termina con su paquete y un campo `Responsable:` vacío

## Path Conventions

- Paquete: `src/tarifalatam/` · Pruebas: `tests/` · Notebooks: `notebooks/` · Informes: `reports/` · Modelo: `models/`
- Todos los comandos desde la raíz del checkout principal, con `PYTHONUTF8=1` y el entorno `C:\Users\Usuario\venvs\tarifalatam`

---

## Phase 1: Setup (infraestructura compartida)

- [X] T001 **Copiar** (no mover) `mlflow_local.db` y `notebooks/mlruns/` desde `.claude/worktrees/002-features-torneo-optimizacion-b44fc1/` a las mismas rutas del checkout principal. Comprobar con `mlflow.search_runs(search_all_experiments=True)` que hay **60** ejecuciones y anotar si alguna tiene artefactos (`research.md`, punto 10). Verificar con `git status --short` que no aparecen como cambios. **No borrar el worktree** *(2026-11-05: copiados `mlflow_local.db` y la base de respaldo `mlruns/mlflow_local_primera_corrida_2026-10-31.db`; el worktree no tenía `notebooks/mlruns`. `search_runs`: 60 ejecuciones FINISHED, ninguna con artefactos.)* · P3 · Responsable:
- [X] T002 [P] Comprobar que la prueba sigue cerrada (`reports/prueba_abierta.txt` no existe) y que `python -m pytest -q` está en verde antes de empezar (194 pruebas). Anotar la cifra *(2026-11-05: sin marca; `pytest` 243 en verde, no 194: `main` ya traía más pruebas.)* · P5 · Responsable:

---

## Phase 2: Foundational (prerrequisitos que bloquean todo)

- [X] T003 Agregar a `src/tarifalatam/config.py`, sin tocar lo anterior, las constantes de `contracts/functions.md`: `TEST_MARK_PATH`, `FINAL_EXPERIMENT = "tarifalatam-modelo-final"`, `REGISTERED_MODEL = "tarifalatam_precio_noche"`, `MODEL_ALIAS = "champion"`, `GOAL_IMPROVEMENT = 0.20`, `COST_RATIOS = ((2.0, 1.0), (1.5, 1.0), (3.0, 1.0))`, `RANGE_QUANTILES = (0.25, 0.75)`, `SHAP_SAMPLE = 2000` y `VALID_RANGE` ("`accommodates` 1 a 16", "`bedrooms` 0 a 10", "`beds` 0 a 50", "`bathrooms_count` 0 a 20", "`minimum_nights` 1 a 29", "`maximum_nights` 1 a 1.125", "`latitude` −90 a 90", "`longitude` −180 a 180", "`bathroom_shared` 0 a 1"), cada una con un comentario que cite `especificaciones/07-validacion-registro-app.md` · P1 · Responsable:
- [X] T004 [P] Ampliar `tests/test_no_test_set.py`: el notebook 08 tampoco puede leer la prueba; los notebooks 07 y 09 solo pueden hacerlo a través de `open_test` (una celda que lea `test.csv` sin `open_test` falla). Todo `src/` sigue sin poder contener la ruta. Verificar con `pytest tests/test_no_test_set.py` · P1 · Responsable:

**Checkpoint**: constantes y guardas listas; empiezan P1 y P2 en paralelo.

---

## Phase 3: User Story 1 - Una medida honesta del modelo en anuncios nunca vistos (Priority: P1) 🎯 MVP

**Goal**: la prueba abierta una sola vez, con intervalo por anfitrión, comparación con la línea base, meta evaluada,
errores por segmento e interpretación.

**Independent Test**: `reports/prueba_abierta.txt` con una sola línea de primera apertura posterior a 2026-11-05 17:42 y
`reports/07_metricas_test.json` con `decisiones` y `prueba` completos.

### P1 · Validación (`src/tarifalatam/models/validation.py`, pruebas en `tests/test_validation.py`)

- [X] T005 [P] [US1] Escribir en `tests/test_validation.py` las pruebas de `open_test` y `to_usd_price` (deben fallar antes de T006): la primera lectura crea la marca con "Primera apertura" y el propósito; la segunda **agrega** una línea "Nueva lectura" sin borrar la primera; un archivo cuyo nombre no empieza por `test` se rechaza; `to_usd_price(log(100), 1.1) == 110` (todo con archivos en `tmp_path`) · P1 · Responsable:
- [X] T006 [US1] Crear `src/tarifalatam/models/validation.py` con `open_test(path, mark_path=TEST_MARK_PATH, purpose)` y `to_usd_price(pred_log, factor=1.0)` (`research.md`, punto 1). El módulo empieza con un docstring que explica que la prueba se abre una sola vez. Verificar con `pytest tests/test_validation.py -k "open or usd"` · P1 · Responsable:
- [X] T007 [US1] Escribir las pruebas de `smearing_factor` ("con residuos nulos vale 1"; con residuos `[log 2, 0]` vale 1,5), `oof_log_predictions` (cada predicción sale de un modelo que no vio a ese anfitrión) y `check_log_correction` (`se_usa` es verdadero solo si `high < 0`; devuelve las predicciones de los reservados) · P1 · Responsable:
- [X] T008 [US1] Implementar `smearing_factor`, `oof_log_predictions` (`GroupKFold(5, shuffle=True, random_state=42)` por `host_id`) y `check_log_correction(pipeline, search, reserved)` reutilizando `paired_abs_error_difference` y `host_bootstrap_ci` **sin modificar `tuning.py`**. Verificar con `pytest tests/test_validation.py -k "smearing or oof or correction"` · P1 · Responsable:
- [X] T009 [US1] Escribir las pruebas de `price_range_ratios` (con razones conocidas devuelve sus percentiles 25 y 75 por ciudad; el precio sugerido queda dentro de `[p25, p75]` cuando la mediana de la razón es 1) y `asymmetric_cost` ("sobrestimar 10 USD cuesta 20; subestimar 10 USD cuesta 10" con `over=2, under=1`) · P1 · Responsable:
- [X] T010 [US1] Implementar `price_range_ratios(cities, y_true_usd, y_pred_usd, quantiles=RANGE_QUANTILES)` y `asymmetric_cost(y_true_usd, y_pred_usd, over=2.0, under=1.0)`. Verificar con `pytest tests/test_validation.py -k "range or cost"` · P1 · Responsable:
- [X] T011 [US1] Escribir las pruebas de `test_metrics` (incluye los tres costos de `COST_RATIOS`), `mae_with_ci` y `paired_mae_difference` (con una diferencia constante el intervalo es esa constante), `segment_errors` (caso calculado a mano: `n`, `mae`, `mape`, `bias`, `pct_over`, `n_error_over_half`) y `success_goal` (un caso que cumple las tres condiciones y uno que falla **cada una**: 19 % de mejora; intervalo que toca el cero; una ciudad peor, que aparece en `ciudades_peores`) · P1 · Responsable:
- [X] T012 [US1] Implementar `test_metrics`, `mae_with_ci`, `paired_mae_difference`, `segment_errors` y `success_goal` según `contracts/functions.md` y `research.md` (puntos 5, 6 y 8). Verificar con `pytest tests/test_validation.py` (todo el archivo en verde) · P1 · Responsable:
- [X] T013 [US1] Agregar a `tests/test_pipeline.py` (debe fallar antes de T014): con los archivos crudos de juguete, `build_unfiltered_test` devuelve la prueba **con** los precios extremos (contiene todos los `id` de la prueba filtrada de `build_datasets` y los anuncios que el filtro quitó) y `build_datasets` sigue devolviendo exactamente lo mismo que antes · P1 · Responsable:
- [X] T014 [US1] Implementar `build_unfiltered_test(raw_dir=RAW_DIR, rates=FX_RATES)` en `src/tarifalatam/data/pipeline.py`, separando los pasos 1 a 15 de `build_datasets` en una función interna compartida (`research.md`, punto 7). Verificar con `pytest tests/test_pipeline.py` · P1 · Responsable:

### P2 · Interpretación (`src/tarifalatam/models/interpret.py`, pruebas en `tests/test_interpret.py`)

- [X] T015 [P] [US1] Escribir `tests/test_interpret.py` (debe fallar antes de T016), con un LightGBM pequeño armado con `build_pipeline` sobre `make_train_rows()`: `shap_values` devuelve una columna por cada una de las 13 columnas originales; para cada anuncio, la suma de aportes + el valor base ≈ la predicción en logaritmo; `global_importance` queda ordenada de mayor a menor; `top_contributions` devuelve `k` filas · P2 · Responsable:
- [X] T016 [US1] Implementar `shap_values`, `global_importance` y `top_contributions` en `src/tarifalatam/models/interpret.py` (`research.md`, punto 9). Si SHAP falla con las versiones fijadas, implementar la alternativa con `permutation_importance` y anotarlo. Verificar con `pytest tests/test_interpret.py` · P2 · Responsable:

### P5 · Notebook 07 e informe

- [X] T017 [US1] Adaptar `notebooks/07_validacion_interpretacion.ipynb` a regresión, solo llamando a `src/`: (0) `load_train`, `ID_COL = GROUP_COL`, `TARGET`; (1) `DECISIONES` congeladas con los valores de `data-model.md`, sección 2 (`congeladas_el = "2026-11-05 17:42 (UTC−5)"`); (2) `reserve_hosts` + `check_log_correction` + `price_range_ratios` → completar `correccion_log` y `rango_tipico` **antes** de abrir la prueba; (3) ajuste final con `build_pipeline(make_model("lightgbm", parametros), "boosting")` y todo el entrenamiento → `models/final_pipeline.joblib`; (4) `open_test(..., purpose="evaluación única de la etapa 7")`; (5) métricas, intervalos, diferencia y meta; (6) `segment_errors` por ciudad y `room_type` para el modelo y la línea base → `reports/07_segmentos.csv`; sensibilidad con `build_unfiltered_test`; (7) SHAP → `reports/07_shap_global.csv` y los dos anuncios; (8) `reports/07_metricas_test.json` con `allow_nan=False`. Quitar todo lo de clasificación de la plantilla · P5 · Responsable:
- [X] T018 [US1] **Abrir la prueba (una sola vez):** antes de ejecutar, el grupo confirma que la sección 1 del notebook coincide con `especificaciones/07-validacion-registro-app.md`. Ejecutar `python -m nbconvert --to notebook --execute --inplace notebooks/07_validacion_interpretacion.ipynb`. Comprobar: `reports/prueba_abierta.txt` con **una** línea; 29.721 anuncios; sensibilidad con 29.807; `07_segmentos.csv` con las 6 ciudades; `07_shap_global.csv` con 13 filas; sin errores. Anotar el tiempo *(2026-11-05: ensayo previo con los reservados en el scratchpad, sin la prueba. Apertura real 18:09:33, una línea en la marca; 29.721 anuncios de 13.345 anfitriones; sensibilidad 29.807; 1,0 minutos.)* · P5 · Responsable:
- [X] T019 [US1] Completar `reports/07_validacion.md` (la plantilla actual) **solo con cifras del notebook 07**: decisiones congeladas y su hora, la corrección del logaritmo, la apertura, la tabla de métricas con intervalos, la sensibilidad, el veredicto de cada condición de la meta, la tabla por ciudad, sobrestimación, interpretación y sus límites, la ubicación como atributo sensible y la conclusión. Declarar la excepción T047 · P5 · Responsable:
- [ ] T020 [US1] (GRUPO) Leer el veredicto. **No se cambia nada del modelo** por lo que se vio en la prueba; lo que no guste se escribe como límite en `reports/07_validacion.md` · Responsable:

**Checkpoint**: H2 ya tiene la medida honesta; US2 y US3 dependen de `models/final_pipeline.joblib` y `07_metricas_test.json`.

---

## Phase 4: User Story 2 - Un modelo registrado que cualquiera del grupo puede recuperar (Priority: P2)

**Goal**: `tarifalatam_precio_noche` con alias `champion` en el MLflow local, recuperable.

**Independent Test**: `reports/08_registro.json` con versión y alias, y la ida y vuelta con 200 de 200 filas iguales.

- [X] T021 [P] [US2] Agregar a `tests/test_tracking.py` (debe fallar antes de T022): en local, `set_experiment("x")` crea el experimento con `artifact_location` que termina en `mlruns/x`; si el experimento ya existe, no lo cambia · P3 · Responsable:
- [X] T022 [US2] Cambiar `set_experiment` en `src/tarifalatam/tracking/mlflow_utils.py` para que, en local, cree los experimentos nuevos con `artifact_location = (ROOT / "mlruns" / name).as_uri()` (`research.md`, punto 10). En Databricks no cambia nada. Verificar con `pytest tests/test_tracking.py` · P3 · Responsable:
- [X] T023 [US2] Adaptar `notebooks/08_registro_modelo.ipynb` a regresión: `configure_mlflow()` (debe decir `local`), `set_experiment(FINAL_EXPERIMENT)`; registrar `final_pipeline.joblib` con parámetros, métricas de la prueba (de `07_metricas_test.json`), firma (`infer_signature`) y ejemplo de entrada de **5 filas con solo las 13 columnas** (sin `host_id` ni `id`), etiquetas (`etapa`, `datos = "Inside Airbnb, septiembre de 2026"`, `ciudades`, `excepcion = "T047"`), `serialization_format="cloudpickle"`; alias `champion`; ida y vuelta con `predict` (no `predict_proba`) en 200 filas; `reports/08_registro.json` · P3 · Responsable:
- [X] T024 [US2] Ejecutar `python -m nbconvert --to notebook --execute --inplace notebooks/08_registro_modelo.ipynb`. Comprobar la versión, el alias, la ida y vuelta y que el modelo aparece en `mlflow ui --backend-store-uri sqlite:///mlflow_local.db` *(versión 1, alias `champion`, 200 de 200 iguales. La ruta absoluta de los artefactos se cambió por una relativa en la constancia, para no publicar rutas del equipo.)* · P3 · Responsable:
- [X] T025 [US2] Completar `reports/08_registro.md`: plataforma local y su motivo (excepción a la regla 7 de `CLAUDE.md`), experimento, nombre, versión, alias, quién y cuándo, qué se registró, ida y vuelta, tracking frente a registro y reproducibilidad · P3 · Responsable:

---

## Phase 5: User Story 3 - Un precio sugerido que se niega a responder con datos imposibles, en una app local (Priority: P3)

**Goal**: `models/model.joblib` + `models/input_schema.json` exportados desde el `champion`, `predict_price` que valida y
una app que corre en local.

**Independent Test**: las cuatro filas de `quickstart.md`, sección 5, en la app; el MAE con `model.joblib` igual al de la
etapa 7.

### P4 · Esquema, predicción y app

- [X] T026 [P] [US3] Reescribir `tests/test_inference.py` para regresión (debe fallar antes de T027 y T028), con un LightGBM pequeño sobre `make_train_rows()`: `build_schema` guarda y recarga lo mismo (columnas, categorías, `neighbourhoods_by_city`, `neighbourhood_coords`, `valid_range`, `price_range_ratios`); `predict_price` con una fila normal devuelve enteros con `low_usd ≤ price_usd ≤ high_usd`; con «No sé» (un número vacío y una categoría vacía) responde sin error; **rechaza** `accommodates = 40` con un mensaje que nombra la columna; rechaza un barrio de otra ciudad y una fila sin `city`; **advierte** con una categoría no vista y con un número fuera de lo observado · P4 · Responsable:
- [X] T027 [US3] Reescribir `src/tarifalatam/inference/schema.py` para regresión según `data-model.md`, sección 4 (`build_schema`, `save_schema`, `load_schema`). Verificar con `pytest tests/test_inference.py -k schema` · P4 · Responsable:
- [X] T028 [US3] Reescribir `src/tarifalatam/inference/predict.py`: `InputValidationError`, `load_model`, `validate_inputs` (reglas de `data-model.md`, sección 4) y `predict_price` usando `to_usd_price` de `models/validation.py`; retirar `decide_min_cost`, `_ordered_proba` y `predict_with_scores`. Verificar con `pytest tests/test_inference.py` · P4 · Responsable:
- [X] T029 [US3] Agregar a `tests/test_inference.py` una prueba con **una fila real** del entrenamiento y `models/model.joblib` (se salta con `pytest.mark.skipif` si el archivo no existe) · P4 · Responsable:
- [X] T030 [US3] Reescribir `app/streamlit_app.py` para regresión (`research.md`, punto 12): ciudad y barrio fuera del formulario; latitud y longitud rellenadas con la mediana del barrio; «No sé» en cada campo salvo la ciudad; `st.metric` con el precio y el rango; advertencias; aviso de Belice; uso responsable ("precio de referencia; la tarifa la fija el anfitrión y el modelo no dice si un inmueble se paga"). Sin ninguna llamada a MLflow ni Databricks · P4 · Responsable:

### P5 · Notebook 09, exportación y ficha

- [X] T031 [US3] Adaptar `notebooks/09_inferencia.ipynb`: (1) exportar el `champion` a `models/model.joblib` (si el registro no responde, se detiene: no usar la copia local en silencio); (2) `build_schema` con el factor y el rango de `07_metricas_test.json` y el aviso de Belice con el MAE **medido** en la prueba; (3) las tres filas (normal, «No sé», imposible); (4) `open_test(..., purpose="comprobar el modelo exportado (no decide)")` y `assert` de MAE igual al de la etapa 7; (5) recuento de campos en blanco de la ficha · P5 · Responsable:
- [X] T032 [US3] Ejecutar `python -m nbconvert --to notebook --execute --inplace notebooks/09_inferencia.ipynb`. Comprobar: `model.joblib` pesa menos de 100 MB; `git check-ignore models/model.joblib models/input_schema.json` no devuelve nada; `prueba_abierta.txt` tiene exactamente dos líneas (la segunda con el propósito de comprobación) *(`model.joblib` 10,3 MB; la marca tiene dos líneas. El esquema se regeneró después, sin leer la prueba, al agregar `most_frequent`.)* · P5 · Responsable:
- [X] T033 [US3] Ejecutar `streamlit run app/streamlit_app.py` y probar los cuatro casos de `quickstart.md`, sección 5. Anotar datos y resultados en `reports/09_despliegue.md`, sección 3 (columna "Resultado real", indicando "local") *(probado con `streamlit.testing` en vez del navegador; los cuatro casos en `reports/09_despliegue.md`.)* · P4 · Responsable:
- [X] T034 [US3] Completar `models/ficha_modelo.md` **a mano** con las cifras de `07_metricas_test.json` y `08_registro.json`: modelo, registro, regla de entrega del precio, tamaño, rendimiento con intervalo y línea base, variables que más pesan, límites (Belice, precio publicado, una sola fecha, ubicación) y lo que no se evaluó · P5 · Responsable:

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T035 `python -m pytest -q` en verde desde la raíz; anotar el número de pruebas · Responsable: *(2026-11-05: 281 pruebas en verde.)*
- [X] T036 Revisión con los subagentes `auditor-de-fuga` (¿la prueba decidió algo? ¿el rango o el factor vieron la prueba?) y `revisor-de-codigo-ia` (código nuevo de `src/`, notebooks y app); atender los hallazgos y anotarlos en `reports/07_validacion.md` · Responsable:
- [X] T037 Marcar los criterios de cierre de `especificaciones/07-validacion-registro-app.md` (sección 12) que se cumplan, con su evidencia; agregar a `especificacion-proyecto.md`, sección 7, la fila del resultado de la prueba y el veredicto de la meta · Responsable:
- [ ] T038 (GRUPO) Cada integrante explica al menos una función de su paquete con `material-del-curso/kit/checklist-revision-ia.md` · Responsable:
- [ ] T039 (GRUPO) Quien no escribió el código responde las 8 preguntas de la guía de la clase 4 (sección 10) · Responsable:
- [ ] T040 Commits por paquete y PR de `003-validacion-registro-app` hacia `main` (cuando el grupo lo pida) · Responsable:

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → **Foundational (T003–T004)** → US1 → US2 → US3 → Polish.
- **Dentro de US1:** P1 (T005–T014) y P2 (T015–T016) en paralelo; T017 necesita los dos; **T018 abre la prueba** y bloquea
  T019, US2 y US3.
- **US2:** T021–T022 pueden hacerse antes de T018 (no usan la prueba); T023–T025 necesitan `final_pipeline.joblib`.
- **US3:** T026–T030 pueden hacerse antes (con el modelo de juguete); T031–T034 necesitan el `champion` (T024).
- **No se puede adelantar:** T018 (una sola vez) ni T031 (necesita el registro).

## Parallel Example

```text
# Mientras P1 escribe validation.py (T005–T014):
P2: T015–T016 (interpret.py)
P3: T001, T021–T022 (copia del MLflow y set_experiment)
P4: T026–T028, T030 (esquema, predict_price y app con el modelo de juguete)
```

## Implementation Strategy

1. **MVP = US1** (T001–T020): con eso el H2 ya tiene la prueba abierta una vez, con intervalo y meta evaluada.
2. **US2** (T021–T025): registro con versión y alias, otro criterio explícito del H2.
3. **US3** (T026–T034): archivo exportado y app local, el último criterio del H2 y la base del despliegue de mañana.
4. **Cierre** (T035–T040).
