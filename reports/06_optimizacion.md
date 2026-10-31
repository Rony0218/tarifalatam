# Informe de la optimización

> Resultado de `notebooks/06_optimizacion.ipynb`, ejecutado el 2026-10-31 (15 minutos). La mejor puntuación de una búsqueda
> es **optimista**: se comprueba en anfitriones que la búsqueda no vio. Un ensayo por fila en
> `reports/06_optimizacion_tabla.csv`; la decisión en `reports/06_best_params.json`. Especificación:
> `especificaciones/04-features-torneo-optimizacion.md`, sección 6. Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`,
> secciones 3 y 4.

## En una frase

Los dos finalistas mejoran un poco con la optimización, y la mejora se distingue del ruido en los anfitriones reservados; entre
ellos hay empate, y el grupo eligió **LightGBM optimizado** para la etapa 7 (MAE de 38,52 USD por noche en los reservados,
frente a 38,86 con los parámetros de partida).

## Diseño de la búsqueda

- **Finalistas optimizados:** bosque aleatorio y LightGBM (decisión del grupo, `reports/05_torneo.md`), con la referencia de
  13 columnas (`config.FINAL_IDEAS = ()`), sin columnas sospechosas.
- **Método:** Optuna con `TPESampler(seed=42)`, minimizando el MAE medio en USD sobre los pliegues de búsqueda.
- **Espacio de búsqueda** (aprobado antes de buscar):

| Finalista | Parámetro | Rango | Motivo |
|---|---|---|---|
| LightGBM | `learning_rate` | 0,01–0,2 (logarítmica) | Más bajo aprende más despacio pero generaliza mejor; la escala logarítmica explora los dos extremos |
| LightGBM | `n_estimators` | 200–1.000 | Compensa la tasa de aprendizaje: con una tasa baja hacen falta más árboles |
| LightGBM | `num_leaves` | 15–255 | Complejidad de cada árbol (31 en la partida) |
| LightGBM | `min_child_samples` | 10–200 | Anuncios mínimos por hoja: evita hojas con pocos casos raros |
| LightGBM | `subsample` (`subsample_freq=1`) | 0,6–1,0 | Cada árbol ve una parte de los anuncios: reduce el sobreajuste |
| LightGBM | `colsample_bytree` | 0,5–1,0 | Cada árbol ve una parte de las variables |
| LightGBM | `reg_lambda` | 0,001–10 (logarítmica) | Regularización L2 de las hojas |
| Bosque | `n_estimators` | fijo en 200 | Más árboles casi nunca empeoran; se fija para que el presupuesto se gaste en la forma del árbol |
| Bosque | `max_depth` | 8–40 | Profundidad máxima (sin límite en la partida) |
| Bosque | `min_samples_leaf` | 1–20 | Anuncios mínimos por hoja (3 en la partida) |
| Bosque | `max_features` | 0,2–1,0 | Proporción de variables que mira cada corte (0,5 en la partida) |

- **Presupuesto:** 30 ensayos por finalista (60 en total), fijado antes de empezar. Es un número acotado: con pocos ensayos,
  una búsqueda inteligente suele llegar al mismo lugar que una más larga, y cada ensayo es una validación de 5 pliegues
  (guía, sección 3.3).
- **Anfitriones reservados:** el 25 % de los anfitriones del entrenamiento (`GroupShuffleSplit`, semilla 7; la plantilla decía
  semilla 42, pero la especificación aprobada fija 7): **13.347 anfitriones y 29.023 anuncios**, que la búsqueda nunca vio. La
  búsqueda usó los otros 40.038 anfitriones (89.490 anuncios), con los pliegues de `folds.csv` restringidos a ellos (entre
  17.597 y 18.400 anuncios de validación por pliegue). Ningún anfitrión está en los dos lados.

## Seguimiento (tracking)

- **Dónde quedó registrado:** MLflow **local** (`configure_mlflow(force_local=True)`, archivo `mlflow_local.db` en la raíz,
  fuera de Git), experimento **`tarifalatam-optimizacion`**. No se usó Databricks ni se escribieron tokens.
- **¿Está cada ensayo como una ejecución con parámetros, métrica y etiquetas?** ☒ sí ☐ no. Hay 60 ejecuciones (30 por
  finalista), todas en estado `completo`, cada una con sus hiperparámetros, 7 métricas (`mae`, `mae_std`, `mape`, `rmse`,
  `bias`, `r2_log`, `fit_seconds`, ninguna vacía) y las etiquetas `etapa=06_optimizacion`, `modelo`,
  `variables=sin_sospechosas`, `datos=train.csv.gz` y `estado`. El notebook comprueba que hay exactamente una ejecución por
  ensayo.
- **Mejor ejecución:** `lightgbm-ensayo-30` (id `90ef5cae5e464f63af43f4114c1ca61a`), MAE medio de 39,69 USD en los pliegues de
  búsqueda. Del bosque, `random_forest-ensayo-26` (id `fe25f4298b6440078e5c7d28cefdd3e5`), con 40,03 USD.
- **Para verlo:** `mlflow ui --backend-store-uri sqlite:///mlflow_local.db` desde la raíz del repositorio.
- **Corrida final:** después de la revisión se corrigió el desempate y el notebook se volvió a ejecutar. Las cifras de error
  salieron idénticas; los tiempos cambian un poco entre corridas. La base de la primera corrida quedó en
  `mlruns/mlflow_local_primera_corrida_2026-10-31.db` (fuera de Git). Así el experimento actual tiene exactamente las 60
  ejecuciones de la corrida final.

## Resultados de la búsqueda

> Cifras en los pliegues de búsqueda (anfitriones de búsqueda). La mejor de 30 es **optimista**: no es el resultado.

| Finalista | Tiempo de la búsqueda | MAE de partida (mismos pliegues) | Mejor ensayo (optimista) | Parámetros del mejor ensayo |
|---|---|---|---|---|
| Bosque aleatorio | 6,4 min | 40,17 | 40,03 ± 2,46 (ensayo 26) | `max_depth` 24 · `min_samples_leaf` 4 · `max_features` 0,444 (200 árboles) |
| LightGBM | 7,6 min | 40,26 | 39,69 ± 2,50 (ensayo 30) | `n_estimators` 522 · `learning_rate` 0,0167 · `num_leaves` 215 · `min_child_samples` 19 · `subsample` 0,928 · `colsample_bytree` 0,542 · `reg_lambda` 2,886 |

- **Lo que comparten los 5 mejores ensayos de cada finalista** (observación, no una medición de importancia):
  - **LightGBM:** tasa de aprendizaje baja (0,017–0,023), muchas hojas (133–215), cada árbol mira poco más de la mitad de las
    variables (`colsample_bytree` 0,52–0,61) y casi todos los anuncios (`subsample` 0,92–0,97).
  - **Bosque:** cada corte mira entre el 40 % y el 48 % de las variables, con 4 a 6 anuncios por hoja y profundidad de 19 a 27.
- Los 30 ensayos de cada finalista terminaron sin fallos. Se respetó el presupuesto: 30 por finalista.

## Comprobación honesta (anfitriones reservados)

> Cada finalista se entrenó dos veces con **todos** los datos de búsqueda, con los parámetros de partida y con los optimizados,
> y se evaluó en los 13.347 anfitriones reservados. Diferencia = |error optimizado| − |error de partida| por anuncio, en USD.
> Intervalo del 95 % con 1.000 remuestreos de **anfitriones completos** (semilla 42).

| Modelo | MAE con parámetros de partida | MAE con parámetros optimizados | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| Bosque aleatorio | 38,87 | 38,70 | −0,17 | [−0,28 ; −0,06] |
| LightGBM | 38,86 | 38,52 | −0,34 | [−0,64 ; −0,01] |

Sesgo medio en los reservados: bosque −13,09 (partida) y −13,56 (optimizado); LightGBM −13,45 y −12,97. Los dos siguen
subestimando, como en el torneo.

**Regla de decisión escrita antes de mirar:** se usan los parámetros optimizados solo si **todo** el intervalo está por debajo
de cero; si cruza el cero, la mejora no se distingue del ruido y se usan los de partida.

**Resultado de la regla:** en los dos finalistas todo el intervalo está por debajo de cero, así que se usan los optimizados. En
LightGBM el límite superior es −0,01: pasa la regla por muy poco.

**Comparación entre los dos finalistas optimizados** (mismos reservados, mismo intervalo): bosque 38,70 frente a LightGBM 38,52
USD. Diferencia (bosque − LightGBM) de +0,17 USD, con intervalo [−0,20 ; +0,55]. **Cruza el cero: empate.**

## Decisión

- **Modelo que pasa a la etapa 7: LightGBM con los parámetros optimizados** (los del ensayo 30, en
  `reports/06_best_params.json`). **Decisión del grupo del 2026-10-31 (tarea T047).**
- **Es una excepción a la regla escrita, decidida después de ver el resultado.** La regla aprobada dice: si el intervalo cruza
  el cero, pasa "el más simple y rápido".
  - La regla se aplica con `choose_finalist`, que compara el tiempo de ajuste de las configuraciones elegidas (las optimizadas),
    medido en los pliegues de búsqueda: bosque 2,41 s y LightGBM 3,09 s por pliegue. **La regla elige el bosque**
    (`regla_elegiria` en el JSON).
  - El grupo eligió LightGBM por dos motivos. Primero, tiene el MAE más bajo en los reservados (38,52 frente a 38,70), aunque
    es justo la diferencia que el intervalo no distingue del ruido. Segundo, se considera más simple de operar: un modelo de
    boosting suele guardarse en un archivo más liviano que 200 árboles profundos, y la app carga `models/model.joblib` desde el
    repositorio. El tamaño del archivo **no se midió**; hay que comprobarlo al exportar el modelo.
  - El modelo elegido está en `config.STAGE7_MODEL`, y el notebook escribe la nota de la excepción en el campo
    `decision_del_grupo` del JSON.
  - **Historia:** la primera corrida desempataba con los tiempos del **torneo** (parámetros de partida), donde LightGBM era
    más rápido, y su JSON decía "pasa el más rápido de ajustar (lightgbm)". La revisión lo detectó. Se corrigió el notebook y
    se volvió a ejecutar (en la primera corrida, LightGBM optimizado había tardado 5,11 s por pliegue; ver el commit
    `664d4b0`).
- **Cómo se arma el modelo en la etapa 7.** Con `make_model("lightgbm", parametros)` de `src/tarifalatam/models/tuning.py`,
  no con `LGBMRegressor(**parametros)`. `make_model` agrega `subsample_freq=1`, sin el cual LightGBM ignora `subsample`, y fija
  `random_state=42`. El JSON lo indica en `como_se_arma` y `parametros_fijos`.
- **Lo que no pudimos concluir:**
  - No hay un ganador claro entre los dos finalistas optimizados: la diferencia de 0,17 USD está dentro del ruido.
  - La mejora de LightGBM por optimizar (0,34 USD por noche, menos del 1 %) es real según la regla, pero pequeña. Pasa por muy
    poco: el límite superior del intervalo es −0,01. Con otra semilla de reserva podría haber tocado el cero, y entonces se
    habrían usado los parámetros de partida.
  - **El 38,52 es optimista: no es el rendimiento esperado.** Los mismos anfitriones reservados se usaron en **cuatro**
    decisiones, no en dos: optimizados contra partida en cada finalista (dos), finalista contra finalista, y la elección del
    grupo. Además, esos anfitriones no eran nuevos para las etapas 4 y 5, porque estaban dentro de sus pliegues. La cifra
    honesta la dará la prueba en la etapa 7.

## Para la clase siguiente

- **Etapa 7 (validación):**
  - Entrenar con `build_pipeline(make_model("lightgbm", parametros), "boosting")`, con los parámetros de
    `reports/06_best_params.json`, las 13 columnas de la referencia y **todo** el entrenamiento.
  - Abrir `test.csv.gz` **una sola vez**. Reportar el MAE con su intervalo por anfitrión, el error por ciudad (Belice) y el
    sesgo.
  - Declarar tres límites heredados de la etapa 3 (`reports/01_eda.md`):
    - la regla de precios extremos también quitó filas de la prueba, así que la prueba no tiene precios extremos;
    - los límites de precio por ciudad se calcularon con todo el entrenamiento, antes de los pliegues (efecto mínimo, porque
      son medianas de miles de anuncios);
    - los umbrales de limpieza se fijaron mirando los siete archivos.
- **Clase 4:** pasar el seguimiento a Databricks (quitar `force_local`) y registrar el modelo. Medir el tamaño de
  `models/model.joblib` antes de subirlo.

## Revisión de los subagentes (2026-10-31)

El código de las etapas 4 a 6 se revisó con `auditor-de-fuga` (T048) y `revisor-de-codigo-ia` (T049). El auditor no encontró
fuga hacia la prueba ni columnas prohibidas o sospechosas en los modelos del torneo y la optimización. Todo lo que aprende de
los datos está dentro del `Pipeline`, los pliegues y los reservados mantienen a cada anfitrión entero, y el intervalo
remuestrea anfitriones. Lo que encontró y lo que se hizo está en la tabla de `reports/04_features.md`, sección "Revisión de
los subagentes".
