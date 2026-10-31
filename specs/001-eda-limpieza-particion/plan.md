# Implementation Plan: EDA reproducible, limpieza y partición por anfitrión (hito H1)

**Branch**: `001-eda-limpieza-particion` (se trabaja en `main`) | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-eda-limpieza-particion/spec.md`

## Summary

Convertir las 11 decisiones del EDA en código reproducible. Una función por regla en `src/tarifalatam/data/cleaning.py`,
una partición por `host_id` en `src/tarifalatam/data/split.py` y una función que las encadena en orden y lleva la cuenta de
las filas excluidas (`src/tarifalatam/data/pipeline.py`). Los notebooks solo llaman a esas funciones:

- `02_eda.ipynb` reproduce las cifras del informe.
- `03_preprocesamiento.ipynb` genera `data/processed/train.csv.gz` y `test.csv.gz`, el registro de exclusiones y el MAE de la
  línea base.

Cada regla tiene una prueba `pytest` con datos hechos a mano, así que las pruebas no necesitan los archivos reales.

**Bloqueo conocido:** las cinco tasas de cambio (banco central) aún no existen. El código se escribe y se prueba con tasas de
prueba. El notebook 03 se detiene con un mensaje claro hasta que el grupo las anote en `config.py`.

## Technical Context

**Language/Version**: Python 3.12 (`requirements.txt` fijado; en este equipo hay 3.12.10)

**Primary Dependencies**: pandas, numpy, scikit-learn (`GroupShuffleSplit`, `GroupKFold`), pytest y nbconvert. Todas ya están
en `requirements.txt`; **no se agrega ninguna**.

**Storage**: archivos. Entrada: `data/raw/*.csv.gz` (solo lectura). Salida: `data/processed/*.csv.gz` (se usa CSV comprimido y
no parquet, porque parquet exigiría agregar `pyarrow` a `requirements.txt`) y `reports/03_exclusiones.csv`.

**Testing**: pytest, con tablas pequeñas hechas a mano (`tests/test_cleaning.py`, `tests/test_split.py`,
`tests/test_pipeline.py`, `tests/test_baseline.py`).

**Target Platform**: computadores de los integrantes (Windows, con `PYTHONUTF8=1`), Mac o Linux.

**Project Type**: paquete de Python (`src/tarifalatam`) más notebooks que lo orquestan.

**Performance Goals**: regenerar `data/processed/` desde cero en menos de 10 minutos (SC-001). Leer los siete archivos tarda
alrededor de un minuto.

**Constraints**:

- Nada de `data/raw/` se modifica.
- Los datos personales se eliminan en la misma función que lee los archivos.
- Ninguna regla que aprenda de los datos usa la prueba.
- No se usa ninguna tasa de cambio supuesta.

**Scale/Scope**: 194.628 filas × 90 columnas de entrada. Antes de quitar "previous scrape" y extremos quedan 177.704 filas; la cifra final la
dará el registro.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
|---|---|---|
| I. Los datos originales no se tocan | `load_raw` solo lee; las salidas van a `data/processed/`, que se regenera con el notebook 03 | ✅ |
| II. Se parte por la unidad de análisis | `split_by_host` con `GroupShuffleSplit` por `host_id`; `assert_disjoint_hosts` y una prueba que falla con partición por fila | ✅ |
| III. La prueba se abre una sola vez | Los límites de precio y la línea base se ajustan solo con entrenamiento; el notebook 03 no resume la prueba (solo cuenta sus filas) | ✅ con nota* |
| IV. Cada decisión con su motivo, función y prueba | Una función y al menos una prueba por regla; el registro de exclusiones y el MAE de la línea base se copian a `reports/` | ✅ |
| V. Nada sensible sale del equipo | Las columnas personales y el texto libre se eliminan en `load_raw`; `data/` sigue en `.gitignore`; prueba `test_no_personal_columns` | ✅ |
| VI. El código es nuestro | Funciones pequeñas con docstring en español y nombres en inglés; los notebooks solo orquestan; revisión con `revisor-de-codigo-ia` | ✅ |
| VII. Nunca se inventan datos | Las tasas pendientes valen `None` y la conversión falla si falta una; el notebook 02 compara sus cifras con el informe | ✅ |

\* **Nota del principio III.** La regla de precios extremos (FR-014) también quita filas de la prueba, usando los límites
aprendidos en entrenamiento. No es una decisión tomada mirando la prueba: es la misma regla de calidad aplicada a ambos lados.
Pero el MAE final se medirá sin precios imposibles, y eso debe decirse en `reports/07_validacion.md`. El auditor de fuga
debe revisarlo.

**Re-chequeo después del diseño (fase 1):** sin cambios; no hay violaciones que justificar.

## Project Structure

### Documentation (this feature)

```text
specs/001-eda-limpieza-particion/
├── spec.md
├── plan.md              # este archivo
├── research.md          # fase 0: decisiones técnicas y su motivo
├── data-model.md        # fase 1: columnas de entrada y salida, reglas de validación
├── quickstart.md        # fase 1: cómo comprobar que todo funciona
├── contracts/
│   ├── data-functions.md     # funciones públicas de src/tarifalatam/data y su comportamiento
│   └── processed-files.md    # esquema de train/test y del registro de exclusiones
├── checklists/requirements.md
└── tasks.md             # fase 2 (/speckit-tasks; aún no existe)
```

### Source Code (repository root)

```text
src/tarifalatam/
├── config.py                 # NUEVO: rutas, semilla, host_id, ciudades y monedas, tasas (pendientes), listas de columnas, umbrales
├── data/
│   ├── __init__.py
│   ├── cleaning.py           # NUEVO: load_raw + una función por regla (FR-002 a FR-012, FR-014)
│   ├── split.py              # NUEVO: split_by_host, assert_disjoint_hosts, group_cv
│   └── pipeline.py           # NUEVO: build_datasets (orden de las reglas + registro de exclusiones)
└── models/
    └── baseline.py           # NUEVO: línea base mediana ciudad × room_type y su MAE con GroupKFold

tests/
├── conftest.py               # existe
├── test_cleaning.py          # NUEVO: una prueba (normal + sucio) por regla y test_no_personal_columns
├── test_split.py             # NUEVO: anfitriones disjuntos, sin filas perdidas, falla con partición por fila
├── test_pipeline.py          # NUEVO: el registro cuadra (partida − quitadas = finales) con datos de juguete
└── test_baseline.py          # NUEVO: la mediana se aprende solo del pliegue de entrenamiento

notebooks/
├── 02_eda.ipynb              # SE REESCRIBE: carga con load_raw y reproduce las cifras de FR-018
└── 03_preprocesamiento.ipynb # SE REESCRIBE: llama a build_datasets, guarda salidas, calcula línea base

reports/
├── 01_eda.md                 # se actualiza: cifras confirmadas + MAE de la línea base
└── 03_exclusiones.csv        # NUEVO: registro de exclusiones por regla, ciudad y conjunto
```

**Structure Decision**: es la estructura obligatoria de `CLAUDE.md`. La lógica va en `src/tarifalatam/data/` (limpieza y
partición) y en `src/tarifalatam/models/` (línea base); los notebooks solo orquestan. Las tasas viven en `config.py` para
quedar versionadas en Git con su fuente y su fecha: es una tabla de 7 filas y no justifica una carpeta de datos nueva.

**Cambio de configuración:** `.gitignore` hoy solo ignora `data/raw/*`. Esta pieza agrega `data/processed/*` y
`!data/processed/.gitkeep`, para que los conjuntos generados (que conservan `host_id`) no se suban al repositorio público.

## Complexity Tracking

No hay violaciones de la constitución que justificar.
