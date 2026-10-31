# Research: decisiones técnicas de las etapas 4 a 6

Cada punto: **Decisión**, **Motivo**, **Alternativas consideradas**. Las decisiones de **qué** medir ya las aprobó el grupo
(`especificaciones/04-features-torneo-optimizacion.md`); aquí solo se decide **cómo** implementarlas. No queda ninguna duda
abierta en el contexto técnico. Las comprobaciones sobre las librerías se hicieron el 2026-10-31 en el entorno con las versiones
de `requirements.txt`.

## 1. Cómo se carga el entrenamiento

- **Decisión:** `load_train(path=PROCESSED_DIR / "train.csv.gz")` en `src/tarifalatam/data/load.py`. Lee el CSV comprimido,
  verifica que las columnas sean exactamente las 65 de las cuatro listas de `config.py` (si no, error que nombra las que faltan
  o sobran) y devuelve la tabla en el orden del archivo. No hay función para la prueba.
- **Motivo:** el notebook 03 guarda `.csv.gz` (H1 eligió CSV para no agregar `pyarrow`). Una sola función evita que cada
  notebook lea distinto, y la verificación de columnas avisa si el notebook 03 cambia.
- **Alternativas:** guardar `train.joblib` desde el notebook 03 (una segunda copia que puede quedar desactualizada, y cambiaría H1
  ya cerrado); leer con `pd.read_csv` en cada notebook (lógica repetida, contra el principio VI).

## 2. Pliegues: cómo se calculan, se guardan y se reutilizan

- **Decisión:** `make_folds(train)` usa `GroupKFold(n_splits=5, shuffle=True, random_state=42)` con `groups=host_id` y devuelve
  una tabla `id → fold` (0 a 4). `save_folds` la escribe en `data/processed/folds.csv`. `load_folds` la lee y `fold_indices(frame,
  folds)` la convierte en la lista de pares (índices de ajuste, índices de validación) para las filas de `frame`. Si algún `id`
  de `frame` no está en el archivo (o, con el entrenamiento completo, si sobran o faltan ids), se detiene con un mensaje.
- **Motivo:** guardar la asignación deja una prueba física de que las tres etapas usan los mismos pliegues (SC-001). Guardarla
  por `id` y no por posición la hace robusta al orden de las filas, y sirve igual para el subconjunto de búsqueda de la etapa 6.
  Comprobado: en scikit-learn 1.9.1 `GroupKFold` acepta `shuffle` y `random_state`, y dos llamadas con la misma semilla dan los
  mismos pliegues.
- **Alternativas:** recalcular en cada notebook con la misma función (funciona, pero no deja rastro y depende del orden de las
  filas); usar `group_cv()` de `split.py` (no baraja; con ella se midió la línea base de H1 y no se cambia).

## 3. Anfitriones reservados para la comprobación

- **Decisión:** `reserve_hosts(train, size=0.25, seed=7)` en `folds.py`, con `GroupShuffleSplit(n_splits=1, test_size=0.25,
  random_state=7)`, que llama a `assert_disjoint_hosts` de `split.py`. La búsqueda usa `fold_indices(search, folds)`: los mismos
  pliegues, restringidos a los anfitriones de búsqueda.
- **Motivo:** es exactamente lo aprobado (guía, sección 3.4) y reutiliza la comprobación que ya existe.
- **Alternativas:** calcular pliegues nuevos dentro de la búsqueda (rompe "los mismos pliegues en todo").

## 4. Categorías raras (decisión 11 del EDA)

- **Decisión:** un transformador propio, `RareCategoryGrouper(min_count=30)`, que en `fit` aprende qué categorías tienen al menos
  30 anuncios en la parte de entrenamiento y en `transform` cambia las demás, las desconocidas y los vacíos por `"Other"`. Va antes
  del codificador de cada familia de modelo.
- **Motivo:** se comporta igual para todos los modelos (one-hot u ordinal), sigue la decisión 11 al pie de la letra (umbral
  absoluto de 30, aprendido con el entrenamiento) y un barrio nuevo en la app cae en "Other" sin romper nada. Es fácil de explicar
  y de probar.
- **Alternativas:** `OneHotEncoder(min_frequency=30, handle_unknown="infrequent_if_exist")` hace lo mismo para Ridge, pero
  `OrdinalEncoder` manda los desconocidos a un código distinto del de las raras, así que las dos familias se comportarían distinto.

## 5. Preprocesamiento por familia de modelo

- **Decisión:** las mismas columnas de entrada para todos, con tres familias de preprocesamiento:
  - `linear` (Ridge): imputación (mediana en números, moda en indicadores 0/1), escalado y one-hot (`handle_unknown="ignore"`)
    después del agrupador;
  - `forest` (bosque aleatorio): la misma imputación y `OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)`
    después del agrupador;
  - `boosting` (LightGBM): el mismo codificador ordinal, **sin imputar** los números, porque LightGBM maneja los vacíos
    (especificación de etapa, sección 5.1).

  La línea base no usa preprocesamiento.
- **Motivo:** Ridge necesita escalas comparables y no entiende códigos ordinales; los árboles no necesitan one-hot y con 320
  barrios el one-hot los haría lentos. Usar las mismas columnas de entrada mantiene la comparación justa (guía, sección 2.1).
- **Alternativas:** el manejo de categorías propio de LightGBM (`categorical_feature`): más rápido de ajustar, pero agrega una
  diferencia entre modelos difícil de explicar. Queda como idea para la optimización, no para el torneo.

## 6. Cómo se implementan las ideas de variables

- **Decisión:** un transformador de scikit-learn por idea en `features/engineering.py`. Cada uno recibe la tabla cruda, devuelve
  una copia con columnas nuevas y no modifica la original:
  - `CityCenterDistance`: aprende en `fit` la mediana de latitud y longitud por ciudad y calcula la distancia de haversine (radio
    terrestre de 6.371 km). Una ciudad que no vio al ajustar → vacío.
  - `AmenityFeatures`: lee `amenities` como lista JSON (verificado: las 118.513 filas se leen con `json.loads`). Calcula el conteo
    y seis indicadores por nombre exacto. Un texto ilegible deja vacíos.
  - `CapacityRatios`: las tres razones, con las reglas de división por cero de la spec.
  - `HostProfile`: antigüedades (años + meses / 12) y `t`/`f` → 1/0.
  - `SuspiciousFeatures` (solo para la medición con sospechosas): días desde la primera y la última reseña hasta `last_scraped`, y
    `t`/`f` → 1/0 en `has_availability` y `host_is_superhost`.
  - Idea 5: `TargetEncoder(target_type="continuous", cv=KFold(5, shuffle=True, random_state=42))` sobre
    `neighbourhood_cleansed`, dentro del `ColumnTransformer`.
- **Motivo:** dentro del `Pipeline`, el modelo guardado recibe las columnas crudas y la app no repite cálculos (FR-008). Un
  transformador por idea permite medir cada una sola y probarla sola.
- **Comprobado en el entorno:** dentro de un `Pipeline`, scikit-learn llama a `TargetEncoder.fit_transform`, que hace la
  validación cruzada interna (ninguna fila ve su propio precio al ajustar). En scikit-learn 1.9 los parámetros `shuffle` y
  `random_state` de `TargetEncoder` están **obsoletos**: se pasa un `KFold` en `cv`.
- **Alternativas:** calcular las variables en el notebook antes de modelar (la app tendría que repetirlas y la idea 5 tendría
  fuga); un solo transformador para todas las ideas (no se podrían medir por separado).

## 7. Revisión de columnas prohibidas

- **Decisión:** `feature_columns(ideas, with_suspicious)` en `features/columns.py` devuelve las columnas que el
  `ColumnTransformer` selecciona, por tipo. `check_feature_columns(columns, allow_suspicious=False)` lanza un error que nombra
  cualquier columna prohibida, o sospechosa si no se permiten. `build_pipeline` la llama siempre, y el `ColumnTransformer` usa
  `remainder="drop"`. Además, la tabla que entra al modelo se arma sin las tres columnas del objetivo.
- **Motivo:** son dos barreras. La lista revisada evita que se pida una columna prohibida, y `remainder="drop"` evita que se cuele
  una que nadie pidió. La prueba con datos donde `price_usd`, `id` y `host_id` predicen perfecto demuestra que funcionan.
- **Alternativas:** confiar solo en la lista (una sola barrera).

## 8. Línea base dentro del mismo esquema

- **Decisión:** un adaptador `BaselineRegressor` en `train.py`. En `fit(X, y_log)` arma una tabla con `city`, `room_type` y
  `price_usd = exp(y_log)` y ajusta el `MedianBaseline` que ya existe; en `predict` devuelve `log` de su predicción.
- **Motivo:** así los cuatro candidatos se evalúan con la misma función y en la misma escala, sin tocar `baseline.py`. Como la
  mediana de `exp(y)` es exactamente la mediana del precio, la predicción en USD es la misma que en H1.
- **Alternativas:** un caso especial en `evaluate_folds` (más ramas que explicar); reescribir `baseline.py` (el grupo pidió no
  hacerlo).

## 9. Métricas

- **Decisión:** `usd_metrics(y_true_log, y_pred_log)` lleva ambas a USD con `exp` y calcula MAE, MAPE (%), RMSE, sesgo medio
  (predicho − real) y R² sobre el logaritmo. `evaluate_folds` devuelve una fila por pliegue con esas métricas y `fit_seconds`, y
  también las predicciones fuera de pliegue (en logaritmo). `city_errors` calcula, a partir de esas predicciones, el MAE y el sesgo
  por ciudad y pliegue.
- **Motivo:** una sola función de métricas para las tres etapas. Las predicciones fuera de pliegue dan el error por ciudad sin
  volver a ajustar.
- **Alternativas:** `cross_validate` con `scoring` (no devuelve predicciones ni el error por ciudad, y el MAE en USD necesitaría
  un *scorer* propio).

## 10. Búsqueda y registro

- **Decisión:** `tune(name, X, y_log, folds, n_trials=30, seed=42)` crea un estudio de Optuna en memoria con
  `TPESampler(seed=42)`, minimiza el MAE medio en USD y registra **cada ensayo** con `log_run` del módulo existente: nombre
  `<modelo>-ensayo-<nn>`, parámetros, métricas (`mae`, `mae_std`, `mape`, `rmse`, `r2_log`, `bias`, `fit_seconds`) y etiquetas
  (`etapa`, `modelo`, `variables`, `datos`, `estado`). No hay ejecución "padre". Un ensayo que falla se registra con
  `estado=fallido` y cuenta en el presupuesto (`catch=(Exception,)`).
- **Motivo:** "un ensayo = una ejecución" (US3), así que el número de ejecuciones coincide con el de ensayos. Reutiliza
  `log_run` sin reescribir `mlflow_utils.py`. La semilla hace la búsqueda reproducible.
- **Alternativas:** una ejecución padre con ensayos anidados, como CreditSight (agrega una ejecución que no es ensayo); guardar el
  estudio en SQLite para reanudarlo (útil si se corta, pero al reanudar registraría ejecuciones duplicadas; si hace falta, se
  vuelve a correr desde cero).

## 11. Seguimiento local

- **Decisión:** en el notebook 06, `configure_mlflow(force_local=True)` y `set_experiment("tarifalatam-optimizacion")`. El
  archivo `mlflow_local.db` queda en la raíz del repositorio (del worktree, si se trabaja en uno) y ya está en `.gitignore`.
  Se revisa con `mlflow ui --backend-store-uri sqlite:///mlflow_local.db`.
- **Motivo:** es lo que pide la guía para la clase 3. Databricks entra en la clase 4 sin cambiar código: basta quitar
  `force_local`.
- **Alternativas:** ninguna: es obligatorio.

## 12. Intervalo remuestreando anfitriones

- **Decisión:** `host_bootstrap_ci(diff_per_row, hosts, n=1000, seed=42)` agrupa por anfitrión (suma y conteo), remuestrea
  anfitriones con reemplazo y devuelve (media, percentil 2,5, percentil 97,5). Los remuestreos se calculan en bloques de 100 para
  no crear de una vez una matriz de 1.000 × ≈ 13 mil anfitriones. `use_optimized(low, high)` devuelve verdadero solo si
  `high < 0`.
- **Motivo:** es la función de la guía (sección 3.6), con el mismo resultado y menos memoria. La regla queda en una función
  probada, no en una celda.
- **Alternativas:** remuestrear filas (prohibido: las filas de un anfitrión no son independientes).

## 13. Paralelismo y tiempos

- **Decisión:** los modelos usan todos los núcleos (`n_jobs=-1`) y los pliegues se ajustan uno tras otro. El tiempo de ajuste de
  cada pliegue se registra.
- **Motivo:** paralelizar pliegues y modelos a la vez multiplica la memoria en portátiles.
- **Alternativas:** `n_jobs` en la validación cruzada (más memoria; tiempos por pliegue menos claros).

## 14. Datos en el worktree

- **Decisión:** antes de ejecutar los notebooks se **copian** `data/raw/*` y `data/processed/*` del checkout principal a la misma
  ruta del worktree. Nunca se mueven ni se modifican. Las pruebas no los necesitan.
- **Motivo:** `data/` está en `.gitignore`, así que un worktree nuevo no los trae.
