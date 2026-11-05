# Implementation Plan: Validación en la prueba, registro del modelo y app local (hito H2, etapas 7 a 9)

**Branch**: `003-validacion-registro-app` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-validacion-registro-app/spec.md` (aprobada por el grupo el 2026-11-05,
decisiones congeladas a las 17:42, hora de Colombia) y la guía de etapa `especificaciones/07-validacion-registro-app.md`.

## Summary

Cerrar el hito H2 con tres entregas que dependen una de la otra:

1. **Etapa 7 · validación (US1).** Antes de abrir la prueba se mide, solo con los anfitriones reservados de la etapa 6, si
   conviene un factor de corrección al volver del logaritmo y cuál es el **rango típico** de error de cada ciudad. Después
   se entrena LightGBM optimizado con todo el entrenamiento, se abre `test.csv.gz` **una vez** (queda la marca
   `reports/prueba_abierta.txt`), se mide el modelo y la línea base con intervalo por anfitrión, se evalúa la meta del PR #5,
   se calcula el error por ciudad y tipo de habitación, la sensibilidad sin el filtro de extremos y la interpretación con
   SHAP.
2. **Etapa 8 · registro (US2).** El MLflow local de la etapa 6 se copia del worktree de la pieza 002 al checkout principal; el
   modelo se registra como `tarifalatam_precio_noche` con alias `champion`, y se comprueba la ida y vuelta.
3. **Etapa 9 · inferencia y app (US3).** `src/tarifalatam/inference/` y la app se reescriben para **regresión**: el esquema
   lleva los barrios por ciudad, los rangos posibles y el rango típico; `predict_price` se niega con datos imposibles y
   responde con «No sé»; `models/model.joblib` se exporta desde el `champion` y se comprueba que da el mismo MAE.

Casi todo lo que se necesita ya existe y se **reutiliza sin cambiarlo**: `load_train`, `reserve_hosts`, `build_pipeline`,
`make_model`, `usd_metrics`, `host_bootstrap_ci`, `paired_abs_error_difference`, `BaselineRegressor`, `configure_mlflow` y
`registered_model_name`. Lo nuevo va en un módulo de validación (`models/validation.py`), uno de interpretación
(`models/interpret.py`) y la reescritura de `inference/`. El trabajo se reparte en **cinco paquetes** (ver "Reparto").

## Technical Context

**Language/Version**: Python 3.12 (`requirements.txt` fijado; entorno `C:\Users\Usuario\venvs\tarifalatam`).

**Primary Dependencies**: versiones comprobadas en el entorno el 2026-11-05: pandas 3.0.6, numpy 2.5.4, scikit-learn
1.9.1, lightgbm 4.7.0, shap 0.54.1, mlflow 3.17.1, streamlit 1.66.0, joblib 1.6.0. **No se agrega ninguna dependencia.**

**Storage**: archivos. Entradas: `data/processed/train.csv.gz`, `data/processed/test.csv.gz` (una vez), `data/raw/*` (solo
para la sensibilidad sin filtro), `reports/06_best_params.json`. Seguimiento y registro: `mlflow_local.db` (SQLite, en
`.gitignore`) con los artefactos en `mlruns/` en la raíz (en `.gitignore`). Salidas en `models/` y `reports/`.

**Testing**: pytest con datos de juguete (`tests/fixtures.py`, `make_train_rows`). Pruebas nuevas: `tests/test_validation.py`,
`tests/test_interpret.py`; se reescribe `tests/test_inference.py` (hoy prueba la plantilla de clasificación) y se amplían
`tests/test_no_test_set.py`, `tests/test_tracking.py` y `tests/test_pipeline.py`.

**Target Platform**: computadores de los integrantes (Windows con `PYTHONUTF8=1`). La app corre con `streamlit run` en local;
mañana, en Streamlit Community Cloud (pieza 004).

**Project Type**: paquete de Python (`src/tarifalatam`) + notebooks que orquestan + app de Streamlit.

**Performance Goals** (metas, no cifras medidas): el notebook 07 en menos de 15 minutos (un ajuste final, cinco ajustes para
el factor del logaritmo, 3 × 1.000 remuestreos y SHAP sobre 2.000 anuncios); los notebooks 08 y 09 en menos de 5 minutos;
la app responde en menos de 2 segundos por consulta. `models/model.joblib` debe pesar menos de 100 MB (límite de GitHub).

**Constraints**:

- La prueba se abre una sola vez y **después** de las decisiones congeladas (2026-11-05 17:42). Ninguna función de `src/`
  contiene la ruta de la prueba: la recibe como argumento desde los notebooks 07 y 09.
- No se vuelve a medir nada de las etapas 4 a 6 (columnas, modelo y parámetros quedan como están).
- La app no consulta Databricks ni MLflow: lee `models/model.joblib` y `models/input_schema.json`.
- Sin datos personales en el repo: `host_id` no entra al esquema ni al ejemplo de entrada; `data/` sigue fuera de Git.

**Scale/Scope**: 118.513 anuncios de entrenamiento (53.385 anfitriones) y 29.721 de prueba (29.807 sin el filtro de
extremos); 13 columnas de entrada; 6 ciudades.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y otra vez después del diseño.*

| Principio | Cómo lo cumple el plan | Estado |
|---|---|---|
| I. Los datos originales no se tocan | La sensibilidad sin filtro **lee** `data/raw/` con la misma limpieza del notebook 03; no escribe nada en `data/` | ✅ |
| II. Se parte por anfitrión | Los reservados son los de la etapa 6 (`reserve_hosts`); todos los intervalos remuestrean anfitriones (`host_bootstrap_ci`); la partición de la prueba es la de H1 | ✅ |
| III. La prueba se abre una sola vez | Decisiones congeladas antes; `open_test` deja la marca y la segunda lectura (notebook 09, solo para comprobar el exportado) queda anotada en la misma marca con su propósito; el factor del logaritmo y el rango típico salen de los reservados; el `Pipeline` se ajusta solo con entrenamiento | ✅ |
| IV. Cada decisión con su motivo | `reports/07_validacion.md`, `08_registro.md` y la ficha del modelo; cada función nueva con prueba | ✅ |
| V. Nada sensible sale del equipo | Sin `.env` ni tokens; el esquema y el ejemplo de entrada solo tienen las 13 columnas (sin `host_id` ni `id`) | ✅ |
| VI. El código es nuestro | Lógica en `src/`, notebooks que orquestan, reparto en paquetes y las 8 preguntas de la guía (T0xx de cierre) | ✅ |
| VII. Nunca se inventan resultados | Las cifras de los informes y de la ficha salen de los notebooks ejecutados; la meta se evalúa con la regla escrita | ✅ |

**Desviaciones declaradas (no violan la constitución):** el modelo final fue una excepción del grupo a la regla de la etapa 6
(T047), y el registro es local en vez de Databricks (regla 7 de `CLAUDE.md`). Las dos están escritas en
`especificacion-proyecto.md`, sección 7, y se repiten en los informes.

**Re-chequeo después del diseño (fase 1):** sin violaciones. El diseño agrega una segunda lectura de la prueba en el notebook
09, que pide la guía del curso para comprobar que el archivo exportado es el evaluado; no decide nada y queda anotada.

## Project Structure

### Documentation (this feature)

```text
specs/003-validacion-registro-app/
├── spec.md              # aprobada
├── plan.md              # este archivo
├── research.md          # decisiones de diseño (fase 0)
├── data-model.md        # entidades: decisiones, resultados, esquema, precio (fase 1)
├── quickstart.md        # cómo comprobar todo de principio a fin (fase 1)
├── contracts/
│   ├── functions.md     # firmas y reglas de las funciones nuevas de src/
│   └── output-files.md  # claves de los JSON y forma de los informes
├── checklists/requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/tarifalatam/
├── config.py                 # + constantes de las etapas 7 a 9 (nombres, rangos posibles, SHAP, marca)
├── data/pipeline.py          # + build_unfiltered_test (sensibilidad); build_datasets no cambia su resultado
├── models/
│   ├── validation.py         # NUEVO: open_test, smearing, rango típico, costo asimétrico, meta, segmentos, intervalos
│   └── interpret.py          # NUEVO: SHAP global y por anuncio sobre el Pipeline de LightGBM
├── tracking/mlflow_utils.py  # + artefactos del experimento en ROOT/mlruns cuando es local
└── inference/
    ├── schema.py             # REESCRITO para regresión
    └── predict.py            # REESCRITO para regresión (predict_price)
notebooks/07_validacion_interpretacion.ipynb  08_registro_modelo.ipynb  09_inferencia.ipynb   # adaptados a regresión
app/streamlit_app.py          # REESCRITA para regresión
models/model.joblib  models/input_schema.json  models/ficha_modelo.md
reports/prueba_abierta.txt  07_metricas_test.json  07_validacion.md  07_segmentos.csv  07_shap_global.csv
        08_registro.json  08_registro.md
tests/test_validation.py  test_interpret.py  test_inference.py  test_no_test_set.py  test_tracking.py  test_pipeline.py
```

**Structure Decision**: la estructura obligatoria de `CLAUDE.md`. La validación va en un módulo propio
(`models/validation.py`) para no mezclarla con el torneo (`train.py`) ni con la optimización (`tuning.py`), que ya están
cerrados. La inferencia reemplaza la plantilla de clasificación en el mismo lugar, porque la app y la guía la buscan ahí.

## Reparto del trabajo (cinco paquetes)

| Paquete | Qué incluye | Archivos |
|---|---|---|
| **P1 · Validación** | apertura de la prueba, factor del logaritmo, rango típico, costo 2 a 1, meta, segmentos | `models/validation.py`, `tests/test_validation.py`, `data/pipeline.py` |
| **P2 · Interpretación** | SHAP global y por anuncio | `models/interpret.py`, `tests/test_interpret.py` |
| **P3 · Registro** | copia del MLflow local, artefactos en la raíz, notebook 08 | `tracking/mlflow_utils.py`, `tests/test_tracking.py`, `notebooks/08_registro_modelo.ipynb` |
| **P4 · Inferencia y app** | esquema, `predict_price`, app | `inference/`, `tests/test_inference.py`, `app/streamlit_app.py` |
| **P5 · Notebooks e informes** | notebooks 07 y 09, informes, ficha | `notebooks/07…`, `notebooks/09…`, `reports/`, `models/ficha_modelo.md` |

Cada integrante hace los commits de su paquete con su cuenta de GitHub. Orden: P1 y P2 en paralelo → notebook 07 (P5) → P3
→ P4 → notebook 09 (P5). P4 puede empezar con el modelo de juguete de las pruebas antes de que exista el real.

## Complexity Tracking

| Desviación | Por qué hace falta | Alternativa más simple descartada porque |
|---|---|---|
| Segunda lectura de la prueba (notebook 09) | La guía exige comprobar que `model.joblib` da el mismo MAE que el evaluado | Comparar solo predicciones en el entrenamiento no prueba que el archivo sea el mismo que se midió en la prueba |
| Reescritura de `inference/` y de la app | La plantilla es de clasificación (`predict_proba`, matriz de costos) | Adaptarla a medias dejaría funciones que no aplican y confundirían a quien la lea |
| Registro local en vez de Databricks | No hay `.env` con Databricks; el seguimiento de la etapa 6 está en el local | Configurar Databricks hoy pone en riesgo el H2 y separaría seguimiento y registro |
