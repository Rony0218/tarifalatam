# Quickstart: comprobar las etapas 7 a 9 de principio a fin

Todo desde la raíz del repositorio (checkout principal, rama `003-validacion-registro-app`), con el entorno activado:

```bash
source /c/Users/Usuario/venvs/tarifalatam/Scripts/activate
export PYTHONUTF8=1
```

## 0. Antes de empezar

- `data/processed/train.csv.gz` y `test.csv.gz` existen; `data/raw/` tiene los 7 archivos.
- `reports/prueba_abierta.txt` **no existe** (la prueba sigue cerrada).
- `mlflow_local.db` está en la raíz y `python -c "import mlflow; mlflow.set_tracking_uri('sqlite:///mlflow_local.db'); print(len(mlflow.search_runs(search_all_experiments=True)))"`
  imprime `60`.

## 1. Pruebas automáticas

```bash
python -m pytest -q
```

Esperado: todo en verde (las 194 de H1 y etapas 4 a 6, más las nuevas).

## 2. Etapa 7

```bash
python -m nbconvert --to notebook --execute --inplace notebooks/07_validacion_interpretacion.ipynb
```

Esperado: sin errores; `reports/prueba_abierta.txt` con **una** línea de primera apertura posterior a 2026-11-05 17:42;
`reports/07_metricas_test.json` con `decisiones` y `prueba`, y la meta evaluada; `07_segmentos.csv` con las 6 ciudades y los
tipos de habitación del modelo y de la línea base; `07_shap_global.csv` con 13 filas.

## 3. Etapa 8

```bash
python -m nbconvert --to notebook --execute --inplace notebooks/08_registro_modelo.ipynb
```

Esperado: `reports/08_registro.json` con `version` y `alias: champion`, y la ida y vuelta con 200 de 200 filas iguales.
Para verlo: `mlflow ui --backend-store-uri sqlite:///mlflow_local.db` y abrir <http://127.0.0.1:5000> (pestaña Models).

## 4. Etapa 9

```bash
python -m nbconvert --to notebook --execute --inplace notebooks/09_inferencia.ipynb
```

Esperado: `models/model.joblib` (< 100 MB) y `models/input_schema.json`; el MAE con `model.joblib` en la prueba igual al de
`07_metricas_test.json`; `prueba_abierta.txt` con una segunda línea cuyo propósito es "comprobar el modelo exportado". Las
tres filas de prueba: la normal y la de «No sé» responden y la imposible se rechaza con un mensaje.

## 5. App local

```bash
streamlit run app/streamlit_app.py
```

Comprobar a mano (y anotar en `reports/09_despliegue.md`, sección 3, para mañana):

| Caso | Datos | Esperado |
|---|---|---|
| Normal | Bogotá, un barrio de la lista, apartamento entero, 2 huéspedes | precio y rango en USD |
| «No sé» | igual, con «No sé» en baños y tipo de propiedad | precio y rango, sin error |
| Imposible | 40 huéspedes (el campo lo limita; probar también con `predict_price` en el notebook 09) | mensaje que dice qué corregir |
| Belice | cualquier inmueble en Belice | aviso de error alto |

## 6. Cierre

- `git status` no muestra `mlflow_local.db`, `mlruns/`, `data/` ni `models/final_pipeline.joblib`.
- `reports/07_validacion.md`, `08_registro.md` y `models/ficha_modelo.md` sin campos `_______________` vacíos.
