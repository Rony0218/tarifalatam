# Implementation Plan: Variables, torneo de modelos y optimización con seguimiento (hito H2, etapas 4 a 6)

**Branch**: `claude/002-features-torneo-optimizacion-b44fc1` (rama del worktree) | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-features-torneo-optimizacion/spec.md`

## Summary

Convertir en código las reglas que el grupo aprobó antes de medir (`especificaciones/04-features-torneo-optimizacion.md`) y
dejar tres notebooks que solo orquestan:

- **Columnas, carga y pliegues** (`config.py`, `src/tarifalatam/data/load.py`, `src/tarifalatam/data/folds.py`). Las 65
  columnas quedan en cuatro listas: prohibidas, sospechosas, referencia y perfil del anfitrión. `load_train()` reemplaza
  `train.joblib`. Los cinco pliegues por anfitrión se calculan una vez y se guardan en `data/processed/folds.csv`.
- **Variables** (`src/tarifalatam/features/`). Cada idea es un transformador pequeño de scikit-learn que agrega columnas, más un
  agrupador de categorías raras (decisión 11 del EDA) y una revisión que detiene el modelo si le llega una columna prohibida.
- **Modelos** (`src/tarifalatam/models/train.py`). `build_pipeline` arma variables, preprocesamiento y modelo en un solo
  `Pipeline`, y `evaluate_folds` devuelve una fila por pliegue con MAE en USD, MAPE, R², RMSE, sesgo y tiempo, más las
  predicciones fuera de pliegue para el error por ciudad. La línea base que ya existe se usa a través de un adaptador, sin
  modificarla.
- **Optimización** (`src/tarifalatam/models/tuning.py`). Optuna con 30 ensayos por finalista; cada ensayo es una ejecución en el
  MLflow local, registrada con el módulo que ya existe. Incluye el intervalo del 95 % remuestreando anfitriones y la regla de
  decisión.
- **Notebooks 04, 05 y 06 e informes** `reports/04_features.md`, `05_torneo.md` y `06_optimizacion.md`, solo con cifras medidas.

Todo se prueba con tablas pequeñas hechas a mano (`tests/fixtures.py`), sin los datos reales. El trabajo se divide en
**cinco paquetes** que pueden tomar integrantes distintos, cada uno con sus propios commits (ver "Reparto del trabajo").

## Technical Context

**Language/Version**: Python 3.12 (`requirements.txt` fijado; entorno `C:\Users\Usuario\venvs\tarifalatam`)

**Primary Dependencies**: versiones de `requirements.txt` comprobadas en el entorno el 2026-10-31: pandas 3.0.6, numpy,
scikit-learn 1.9.1, lightgbm 4.7.0, optuna 5.0.0 y mlflow 3.17.1, más pytest y nbconvert. **No se agrega ninguna dependencia.**

**Storage**: archivos. Entrada: `data/processed/train.csv.gz` (solo lectura). Salidas: `data/processed/folds.csv`; los
`reports/*.csv`, `*.json` y `*.md` de las tres etapas; y `mlflow_local.db` en la raíz (en `.gitignore`).

**Testing**: pytest con tablas de juguete (`tests/fixtures.py`). Archivos nuevos: `test_load.py`, `test_folds.py`,
`test_columns.py`, `test_features.py`, `test_train.py` y `test_tuning.py`.

**Target Platform**: computadores de los integrantes (Windows con `PYTHONUTF8=1`, Mac o Linux).

**Project Type**: paquete de Python (`src/tarifalatam`) más notebooks que lo orquestan.

**Performance Goals** (metas, no cifras medidas): los notebooks 04 y 05 deberían correr en menos de 30 minutos cada uno en un
portátil. El 06 depende del presupuesto (máximo 60 ensayos con dos finalistas), y cada ensayo es una validación de 5 pliegues
sobre ≈ 89 mil anuncios. El tiempo real se mide y se anota en los informes.

**Constraints**:

- `test.csv.gz` no se lee.
- `mlflow_utils.py`, `baseline.py` y `split.py` no se reescriben: `group_cv` sigue igual y las funciones nuevas de pliegues van
  en un módulo aparte.
- Todo lo que aprende de los datos (medianas, categorías frecuentes, centros de ciudad y codificación por objetivo) va dentro
  del `Pipeline`.
- No se usa Databricks ni se escriben tokens.
- Los valores aprobados (listas, parámetros, rangos y semillas) no se cambian sin una nueva aprobación del grupo.

**Scale/Scope**: 118.513 anuncios × 65 columnas, 53.385 anfitriones y 6 ciudades. 7 variantes en la etapa 4 (referencia, 5
ideas y conjunto final, más la medición con sospechosas), 4 candidatos en la etapa 5 y hasta 2 × 30 ensayos en la etapa 6.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
|---|---|---|
| I. Los datos originales no se tocan | Solo se lee `data/processed/train.csv.gz`; `data/raw/` no se usa. En el worktree los datos se copian, nunca se mueven | ✅ |
| II. Se parte por la unidad de análisis | `make_folds` (`GroupKFold` por `host_id`) y `reserve_hosts` (`GroupShuffleSplit` por `host_id`) verifican con `assert_disjoint_hosts`, que ya existe; el intervalo remuestrea anfitriones completos; hay pruebas automáticas | ✅ |
| III. La prueba se abre una sola vez | No hay función que lea `test.csv.gz`. Los finalistas y los parámetros se eligen con validación cruzada y anfitriones reservados del entrenamiento. Todo lo que aprende va dentro del `Pipeline` | ✅ con nota* |
| IV. Cada decisión con su motivo, función y prueba | Una función por idea y por regla, con su prueba. Las tablas por pliegue y las decisiones se guardan en `reports/` | ✅ |
| V. Nada sensible sale del equipo | No se agregan columnas personales; `folds.csv` queda en `data/processed/` (en `.gitignore`); no se escriben tokens | ✅ |
| VI. El código es nuestro | Funciones y transformadores pequeños con docstring en español y nombres en inglés; los notebooks solo orquestan; cinco paquetes repartibles; revisión con `revisor-de-codigo-ia` | ✅ |
| VII. Nunca se inventan datos | Los informes se llenan con salidas de notebooks ejecutados; las metas de tiempo se rotulan como metas | ✅ |

\* **Nota del principio III.** Los anfitriones reservados se usan para dos decisiones: parámetros optimizados contra los de
partida y, si hay dos finalistas, finalista contra finalista. Eso agrega un poco de optimismo. Se acepta y se declara en
`reports/06_optimizacion.md`; el auditor de fuga debe revisarlo. *(Auditoría del 2026-10-31: al final fueron cuatro usos,
porque hubo dos finalistas y un desempate del grupo. Esos anfitriones además estaban en los pliegues de las etapas 4 y 5.
Queda declarado en `reports/06_optimizacion.md`.)*

**Re-chequeo después del diseño (fase 1):** sin cambios y sin violaciones. El diseño agrega un solo archivo de datos
(`folds.csv`), dentro de `data/processed/`.

## Project Structure

### Documentation (this feature)

```text
specs/002-features-torneo-optimizacion/
├── spec.md
├── plan.md              # este archivo
├── research.md          # fase 0: decisiones técnicas y su motivo
├── data-model.md        # fase 1: listas de columnas, variables nuevas, tablas de resultados
├── quickstart.md        # fase 1: cómo comprobar que funciona
├── contracts/
│   ├── model-functions.md    # funciones públicas nuevas y lo que prometen
│   └── output-files.md       # esquema de folds.csv, tablas de reports/, JSON y ejecuciones de MLflow
├── checklists/requirements.md
└── tasks.md             # fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
src/tarifalatam/
├── config.py                 # SE AMPLÍA: listas de columnas, nombres de amenidades, semillas, presupuesto, rutas
├── data/
│   ├── load.py               # NUEVO: load_train
│   ├── folds.py              # NUEVO: make_folds, save_folds, load_folds, fold_indices, reserve_hosts
│   └── split.py              # existe, SIN CAMBIOS (group_cv, assert_disjoint_hosts)
├── features/
│   ├── columns.py            # NUEVO: feature_columns, check_feature_columns
│   └── engineering.py        # NUEVO: RareCategoryGrouper, CityCenterDistance, AmenityFeatures, CapacityRatios,
│                             #        HostProfile, SuspiciousFeatures
├── models/
│   ├── baseline.py           # existe, SIN CAMBIOS
│   ├── train.py              # NUEVO: BaselineRegressor, candidates, build_pipeline, usd_metrics, evaluate_folds,
│   │                         #        city_errors, improvement_over_noise, keep_idea, compare, value_per_nights
│   └── tuning.py             # NUEVO: espacios, make_model, tune, host_bootstrap_ci, use_optimized, save_decision
└── tracking/
    └── mlflow_utils.py       # existe, SIN CAMBIOS (configure_mlflow, set_experiment, log_run)

tests/
├── fixtures.py               # SE AMPLÍA: make_train_rows (tabla de juguete con las 65 columnas)
├── test_load.py              # NUEVO
├── test_folds.py             # NUEVO
├── test_columns.py           # NUEVO: listas, columnas prohibidas y versión para la app
├── test_features.py          # NUEVO: una prueba por idea
├── test_train.py             # NUEVO: métricas, adaptador de la línea base, evaluación por pliegue
└── test_tuning.py            # NUEVO: intervalo por anfitrión, regla, espacios y registro en MLflow local

notebooks/
├── 04_features.ipynb         # SE REESCRIBE: pliegues, variantes, tabla de ideas, con y sin sospechosas
├── 05_torneo.ipynb           # SE REESCRIBE: candidatos, tablas, por ciudad, pareada, dinero, finalistas
└── 06_optimizacion.ipynb     # SE REESCRIBE: reserva, búsqueda con registro, comprobación, decisión

reports/
├── 04_features.md + 04_features_tabla.csv
├── 05_torneo.md + 05_torneo_tabla.csv + 05_torneo_por_ciudad.csv
└── 06_optimizacion.md + 06_best_params.json + 06_optimizacion_tabla.csv
```

**Structure Decision**: es la estructura obligatoria de `CLAUDE.md`. Los pliegues van en un módulo nuevo (`folds.py`) para no
reescribir `split.py`, como pidió el grupo. Las listas de columnas viven en `config.py`, junto a las de H1 (`PII_COLUMNS`,
`LEAKAGE_COLUMNS`…), para que se revisen sin abrir el código de los modelos.

## Reparto del trabajo (cinco paquetes)

Cada paquete es una pieza con sus pruebas y sus propios commits. El grupo decide al aprobar `tasks.md` quién toma cada uno.

| Paquete | Qué incluye | Depende de | Historia |
|---|---|---|---|
| **P1 · Columnas, carga y pliegues** | Listas en `config.py`, `data/load.py`, `data/folds.py`, `features/columns.py` y sus pruebas | — | US1 |
| **P2 · Variables** | `features/engineering.py` (las cinco ideas, el agrupador de categorías raras y las conversiones de las sospechosas) y sus pruebas | Nombres de columnas de P1 (se pueden escribir en paralelo) | US1 |
| **P3 · Pipeline, métricas y evaluación** | `models/train.py` y sus pruebas | P1 y P2 | US1, US2 |
| **P4 · Optimización** | `models/tuning.py` y sus pruebas | P3 | US3 |
| **P5 · Notebooks e informes** | Notebooks 04, 05 y 06 y los informes, en ese orden | 04 ← P1–P3; 05 ← 04; 06 ← 05 y P4 | US1–US3 |

P1 y P2 pueden empezar a la vez. Al terminar P3 se puede ejecutar el notebook 04. P4 puede avanzar mientras corre el 04.

## Complexity Tracking

No hay violaciones de la constitución que justificar.
