# Quickstart: comprobar que las etapas 4 a 6 funcionan

## Requisitos previos

- Entorno con `requirements.txt` instalado (ver `README.md`) y `PYTHONUTF8=1` en Windows.
- `data/processed/train.csv.gz`, generado por `notebooks/03_preprocesamiento.ipynb`. **En un worktree**, se copian (no se
  mueven) `data/raw/*` y `data/processed/*` desde el checkout principal a la misma ruta.
- No hace falta `.env` ni Databricks: el seguimiento de esta clase es local.

## 1. Pruebas (no necesitan los datos reales)

```bash
pytest
```

Esperado: todo en verde, las 76 pruebas de H1 más las nuevas (`test_load.py`, `test_folds.py`, `test_columns.py`,
`test_features.py`, `test_train.py`, `test_tuning.py`).

**Comprobación de que la barrera de columnas sirve:** agrega temporalmente `price_usd` a `REFERENCE_NUMERIC` en `config.py`,
ejecuta `pytest tests/test_columns.py` y verifica que **falla**. Después deja la lista como estaba.

## 2. Etapa 4 · Variables

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/04_features.ipynb
```

Esperado:

- Se crea `data/processed/folds.csv` con 118.513 filas y los pliegues 0 a 4, y el notebook confirma que ningún anfitrión está en
  dos pliegues.
- `reports/04_features_tabla.csv` tiene 40 filas (8 variantes × 5 pliegues).
- La tabla del notebook muestra, por variante, MAE ± ruido, mejora / ruido, pliegues que gana y la decisión según la regla.

## 3. Etapa 5 · Torneo

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/05_torneo.ipynb
```

Esperado: `reports/05_torneo_tabla.csv` (20 filas) y `reports/05_torneo_por_ciudad.csv` (120 filas). El notebook muestra la
tabla de negocio y técnicas, el diagrama de cajas, la comparación pareada de los 3 mejores y la diferencia en USD por cada 30
noches. Lee `folds.csv` y no recalcula pliegues.

## 4. Etapa 6 · Optimización

```bash
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/06_optimizacion.ipynb
```

Esperado: el notebook muestra `MLflow: local | experimento: tarifalatam-optimizacion`, el número de anfitriones de búsqueda y
de reservados (sin cruce) y el intervalo del 95 % con la decisión. Se escriben `reports/06_optimizacion_tabla.csv` y
`reports/06_best_params.json`.

Para revisar los ensayos registrados:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow_local.db
```

En <http://127.0.0.1:5000>, el experimento `tarifalatam-optimizacion` debe tener una ejecución por ensayo (como máximo 30 por
finalista), cada una con parámetros, métricas y las etiquetas `etapa`, `modelo`, `variables`, `datos` y `estado`.

## 5. La prueba sigue cerrada

```bash
grep -rn "test.csv" src notebooks/04_features.ipynb notebooks/05_torneo.ipynb notebooks/06_optimizacion.ipynb
```

Esperado: ninguna línea que lea el archivo (como mucho, un comentario que diga que no se abre).

## 6. Cierre

- Los tres informes solo tienen cifras que aparecen en las salidas de los notebooks.
- Se ejecutan los subagentes `auditor-de-fuga` y `revisor-de-codigo-ia`, y se atienden sus hallazgos.
- `git status` no muestra `data/`, `mlflow_local.db` ni `.env`.
