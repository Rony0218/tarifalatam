# Registro del modelo

> Cifras de `notebooks/08_registro_modelo.ipynb` (ejecutado el 2026-11-05) y de `reports/08_registro.json`.

## 1. Dónde quedó registrado

| Dato | Valor |
|---|---|
| Plataforma | ☐ Databricks  ☒ MLflow local (respaldo) → motivo: no hay `.env` con conexión a Databricks y el seguimiento de la etapa 6 (60 ejecuciones) ya estaba en el MLflow local. Es una excepción a la regla 7 de `CLAUDE.md`, decidida por el grupo el 2026-11-05 y anotada en `especificacion-proyecto.md`, sección 7 |
| Experimento | `tarifalatam-modelo-final` (en `mlflow_local.db`; artefactos en `mlruns/tarifalatam-modelo-final`, ambos fuera de Git) |
| Nombre del modelo registrado | `tarifalatam_precio_noche` |
| Versión | 1 |
| Alias | `champion` |
| Quién lo registró y cuándo | Rony Guerrero (en su equipo), el 2026-11-05 a las 18:12 (ejecución `7b3281b37c0b4feabc985324d0797082`) |

## 2. Qué se registró junto al modelo

- **Parámetros:** tipo de modelo (`lightgbm`), origen (`optimizados`), factor del logaritmo (1,0: sin corrección), número de
  columnas (13) y los 11 parámetros de LightGBM (los 7 optimizados de `reports/06_best_params.json` y los 4 fijos:
  `subsample_freq = 1`, `random_state = 42`, `n_jobs = -1`, `verbose = -1`).
- **Métricas de la prueba** (la evaluación única de la etapa 7): MAE 41,40 USD con su intervalo [38,29; 45,01], MAPE, RMSE,
  sesgo, R² (logaritmo), los tres costos asimétricos, el MAE de la línea base (57,44), la diferencia (−16,04), la mejora
  (27,9 %) y el MAE sin el filtro de extremos (56,81).
- **Firma y ejemplo de entrada:** las 13 columnas CRUDAS que una persona conoce al decidir: `city`, `neighbourhood_cleansed`,
  `room_type`, `property_type`, `latitude`, `longitude`, `accommodates`, `bedrooms`, `beds`, `bathrooms_count`,
  `minimum_nights`, `maximum_nights` y `bathroom_shared`. La salida es el **logaritmo** del precio en USD. El ejemplo son 5
  anuncios completos del entrenamiento, **sin** `host_id` ni `id`.
- **Etiquetas:** `etapa = 08_registro`, origen de los datos (Inside Airbnb, septiembre de 2026), las seis ciudades, el
  objetivo, la excepción T047, la marca de apertura de la prueba y `meta_cumplida = True`.
- **Formato:** `cloudpickle` (el formato por defecto rechaza un `Pipeline` con transformadores propios). Un archivo *pickle*
  puede ejecutar código al cargarse: solo se cargan modelos guardados por el grupo.

## 3. Comprobación de ida y vuelta

- ¿El modelo recuperado del registro predice igual que el local? ☒ sí  ☐ no
- Cómo se comprobó: `mlflow.sklearn.load_model("models:/tarifalatam_precio_noche@champion")` y `np.isclose` entre sus
  predicciones y las del `Pipeline` original (`models/final_pipeline.joblib`) en los primeros 200 anuncios del
  entrenamiento: **200 de 200 iguales**.

## 4. Tracking frente a registro (en tus palabras)

- **¿Qué guarda el tracking en el proyecto y para qué lo usamos?** Guarda **ejecuciones**: en la etapa 6, los 60 ensayos de la
  optimización (30 por finalista), cada uno con sus hiperparámetros, sus 7 métricas y sus etiquetas. Sirvió para comparar
  los ensayos y elegir los parámetros con evidencia, y deja constancia de qué se probó.
- **¿Qué guarda el registro y por qué ayuda el alias `champion`?** Guarda **versiones del modelo** que se pueden usar: aquí,
  una sola. Quien necesita el modelo (el notebook 09, que lo exporta para la app) pide `@champion` y no un número de versión;
  si mañana se registra uno mejor, se mueve el alias y el código no cambia.

## 5. Reproducibilidad

- ¿Alguien de otro grupo podría recuperar el modelo con lo que dejamos escrito? ☐ sí  ☒ no, no directamente → **qué falta:**
  el registro es **local**: `mlflow_local.db` y `mlruns/` están en el computador de quien lo ejecutó y no se suben a Git. Lo
  que sí está en el repositorio es `models/model.joblib` (exportado del `champion`) y la forma de **regenerarlo**: los
  notebooks 03, 07, 08 y 09, en ese orden, con los datos de Inside Airbnb del README. En Databricks el registro sería
  compartido; queda como mejora si el grupo configura la conexión.
