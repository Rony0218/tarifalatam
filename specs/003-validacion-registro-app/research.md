# Research: decisiones de diseño de las etapas 7 a 9

Cada punto: **Decisión**, **Motivo** y **Alternativas descartadas**. No hay cifras nuevas: la prueba sigue cerrada.

## 1. Cómo se abre la prueba y cómo queda la constancia

- **Decisión:** `open_test(path, mark_path, purpose)` en `models/validation.py`. La primera vez escribe en
  `reports/prueba_abierta.txt` la línea `Primera apertura: <fecha y hora> · propósito: <purpose>`; si la marca ya existe,
  **agrega** una línea `Nueva lectura: <fecha y hora> · propósito: <purpose>` y avisa. La ruta de la prueba la pasan los
  notebooks 07 (evaluación) y 09 (comprobar que el exportado es el evaluado); ninguna función de `src/` la contiene.
- **Motivo:** la plantilla sobrescribía la marca solo si no existía y no dejaba rastro de lecturas posteriores. Así el
  instructor ve cuántas veces y para qué se leyó.
- **Alternativas:** una constante `TEST_PATH` en `config.py` (rompería `tests/test_no_test_set.py`, que protege a `src/`);
  no volver a leer la prueba en el notebook 09 (la guía pide esa comprobación).

## 2. Factor de corrección al volver del logaritmo

- **Decisión:** factor de Duan = promedio de `exp(residuo)`, con residuos **fuera de pliegue** dentro de la búsqueda
  (5 pliegues por anfitrión con `GroupKFold`, semilla 42). Se ajusta LightGBM optimizado con toda la búsqueda, se predice en
  los reservados con y sin el factor y se aplica la regla aprobada: se usa solo si el límite superior del intervalo de
  `|error con factor| − |error sin factor|` (por anfitrión, 1.000 remuestreos, semilla 42) es menor que cero.
- **Motivo:** con residuos dentro de la muestra, un LightGBM de 215 hojas se ajusta demasiado y el factor sale casi 1. Los
  reservados son los mismos de la etapa 6, así que no se toca la prueba.
- **Alternativas:** no medirlo (la especificación pide la comprobación); un factor por ciudad (más parámetros, sin evidencia
  previa que lo pida).

## 3. Rango típico de cada ciudad

- **Decisión:** con el mismo ajuste del punto 2 (búsqueda → reservados), la razón `precio real / precio sugerido` de cada
  anuncio reservado; por ciudad se guardan sus percentiles 25 y 75. El rango que ve el usuario es
  `[sugerido × p25, sugerido × p75]`, redondeado al dólar. Si se aprueba el factor, la razón se calcula con el precio
  corregido. Se guarda en el esquema (`price_range_ratios`).
- **Motivo:** una razón (y no una diferencia en USD) escala con el precio: 20 USD no pesan igual en un estudio que en una casa.
  Se mide sin la prueba, como pidió el grupo.
- **Alternativas:** cuantiles de la prueba (sería usarla para construir el producto); regresión por cuantiles (otro modelo
  que habría que validar).

## 4. Costo asimétrico 2 a 1

- **Decisión:** `asymmetric_cost(y_true_usd, y_pred_usd, over=2.0, under=1.0)` =
  `promedio de [over × máx(sugerido − real, 0) + under × máx(real − sugerido, 0)]`. Se reporta con (2, 1), (1,5, 1) y (3, 1)
  para el modelo y la línea base. Es un **control**: no cambia el modelo ni la meta.
- **Motivo:** es la fórmula del PR #5, copiada tal cual.

## 5. La meta de éxito

- **Decisión:** `success_goal(model_mae, baseline_mae, diff_high, city_mae)` devuelve las tres condiciones y el veredicto:
  (a) `model_mae ≤ 0,8 × baseline_mae`; (b) `diff_high < 0` (límite superior del intervalo de la diferencia
  modelo − línea base); (c) en cada ciudad, MAE del modelo ≤ MAE de la línea base (valor puntual, como lo escribe el PR #5).
- **Motivo:** escrita como función probada, no se puede reinterpretar después de ver la prueba.
- **Alternativas:** exigir intervalo por ciudad en (c) (no es lo que dice el PR #5; sería más estricto que lo aprobado).

## 6. Intervalos y línea base en la prueba

- **Decisión:** se reutiliza `host_bootstrap_ci` (etapa 6) con `|error|` por anuncio para el MAE del modelo, el de la línea
  base y su diferencia pareada (`paired_abs_error_difference`). La línea base es `BaselineRegressor` ajustado con **todo**
  el entrenamiento, igual que el modelo.
- **Motivo:** mismas funciones probadas que la etapa 6; remuestrean anfitriones, no filas.

## 7. Sensibilidad sin el filtro de precios extremos

- **Decisión:** `build_unfiltered_test(raw_dir, rates)` en `data/pipeline.py`. Se separan los pasos 1 a 15 de
  `build_datasets` en una función interna compartida y se devuelve la prueba **sin** `drop_price_outliers` (con
  `add_target`). `build_datasets` produce exactamente lo mismo que hoy (una prueba lo comprueba con datos de juguete). En el
  notebook 07 se verifica que son 29.807 anuncios y que contienen los 29.721 de `test.csv.gz`. El MAE se calcula en USD con
  `price_usd`; si hay precios ≤ 0, se excluyen del MAPE y se declara cuántos.
- **Motivo:** la app no filtra nada; hay que reportar el error con todos los anuncios, una sola vez y sin decidir con él.
- **Alternativas:** guardar un `test_unfiltered.csv.gz` en el notebook 03 (habría que volver a ejecutar H1).

## 8. Errores por segmento

- **Decisión:** `segment_errors(frame, by)` con columnas `n`, `mae`, `mape`, `bias`, `pct_over` (% de anuncios sobrestimados) y
  `n_error_over_half` (anuncios con `|error| > 0,5 × precio real`), para `city` y `room_type`. Se guarda en
  `reports/07_segmentos.csv`.

## 9. Interpretación con SHAP

- **Decisión:** `shap.TreeExplainer` sobre el paso `model` del `Pipeline`, con la tabla ya transformada por `pipeline[:-1]`
  y los nombres de `get_feature_names_out()`, que se devuelven a las 13 columnas originales. Importancia global = promedio de
  `|SHAP|` (en logaritmo) sobre 2.000 anuncios del entrenamiento (muestra con semilla 42), en `reports/07_shap_global.csv`.
  Dos anuncios de la prueba: el de error absoluto mediano y el de mayor error, con sus 5 aportes más grandes. Si SHAP falla
  con estas versiones, se usa `permutation_importance` de scikit-learn sobre la misma muestra y se declara.
- **Motivo:** es la herramienta de la guía y ya está en `requirements.txt`. Usar dos anuncios de la prueba para explicar no
  cambia el modelo.

## 10. Seguimiento y registro local

- **Hallazgo (2026-11-05):** `mlflow_local.db` y `mlruns/` de la etapa 6 están solo en `.claude/worktrees/002-…/`, con 60
  ejecuciones y ningún modelo registrado. Los experimentos guardan sus artefactos con una ruta absoluta dentro del worktree
  (`…/002-…/notebooks/mlruns/<id>`), porque se crearon desde la carpeta `notebooks/`.
- **Decisión:** se **copia** (no se mueve) `mlflow_local.db` a la raíz del checkout principal y `notebooks/mlruns/` a la misma
  ruta, y se comprueba con `mlflow.search_runs` que siguen las 60 ejecuciones. `set_experiment` crea los experimentos nuevos
  en local con `artifact_location = <raíz>/mlruns/<nombre>`, así el modelo registrado no depende de la carpeta desde la que
  se ejecuta el notebook. El worktree no se borra hasta que el grupo lo decida.
- **Registro:** `mlflow.sklearn.log_model(pipeline, name="model", input_example=5 filas de las 13 columnas,
  signature=infer_signature(ejemplo, predicción), registered_model_name="tarifalatam_precio_noche",
  serialization_format="cloudpickle")`; alias `champion` con `MlflowClient.set_registered_model_alias`; ida y vuelta con
  `np.allclose` en 200 filas.
- **Alternativas:** volver a correr la etapa 6 en el checkout principal (gasta tiempo y cambia los identificadores de las
  ejecuciones); editar las rutas dentro de la base SQLite (frágil).

## 11. Esquema y predicción para regresión

- **Decisión:** el modelo registrado y exportado es el `Pipeline` que predice el **logaritmo**; la conversión a USD
  (`exp`, el factor del punto 2 y el rango del punto 3) la hace `predict_price` con los datos del esquema, usando la misma
  función `to_usd_price` que la validación, para que el exportado dé el mismo MAE. El esquema guarda: columnas, categorías,
  barrios por ciudad, mediana de latitud y longitud por barrio (para rellenar el formulario), rango posible, rango observado,
  columnas enteras, factor, razones del rango, avisos por ciudad, etiquetas en español, título y aviso de uso responsable.
  `city` es obligatoria (sin ella no hay barrios ni rango); el resto admite «No sé».
- **Motivo:** el `Pipeline` ya trata vacíos (LightGBM los acepta) y categorías desconocidas (`unknown_value=-1`), así que
  «No sé» funciona sin código extra.
- **Alternativas:** envolver el `Pipeline` en un regresor que devuelva USD (el registro tendría otro objeto que el evaluado).

## 12. La app

- **Decisión:** ciudad y barrio se eligen **fuera** del formulario (un formulario de Streamlit no se actualiza al cambiar un
  campo); el resto va dentro. Latitud y longitud vienen rellenadas con la mediana del barrio y se pueden cambiar o marcar
  «No sé». Se muestra el precio (`st.metric`), el rango, las advertencias, el aviso de Belice y el uso responsable. Etiquetas
  y textos salen de `models/input_schema.json`.

## 13. Guardas de la prueba en las pruebas automáticas

- **Decisión:** `tests/test_no_test_set.py` sigue prohibiendo la ruta de la prueba en todo `src/` y en los notebooks 04, 05,
  06 y 08; los notebooks 07 y 09 son los únicos que pueden leerla, y solo con `open_test`.
