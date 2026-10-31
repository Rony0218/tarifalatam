# Especificación · Etapas 4 a 6 · Variables, torneo y optimización

> Se llena **antes de medir nada**: las columnas, las ideas, la regla de decisión, los candidatos y el presupuesto se
> escriben aquí y no se cambian después de ver un resultado. Es la entrada de `/speckit-specify` para la pieza
> `specs/002-…`. Los resultados van a `reports/04_features.md`, `05_torneo.md` y `06_optimizacion.md`.
> Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, secciones 0 a 4 · Ejemplo (la forma, no las cifras):
> `material-del-curso/ejemplo-creditsight/notebooks/04_features.ipynb` a `06_optimizacion.ipynb` y `src/creditsight/models/`.

**Grupo:** TarifaLatam   **Fecha:** 2026-10-31   **Estado:** ☐ borrador  ☒ aprobada por el grupo (2026-10-31)  ☐ cerrada

> **Cómo se llenó este borrador.** Sale de `especificacion-proyecto.md`, la constitución (versión 0.3.0),
> `reports/01_eda.md`, la clasificación de columnas de `reports/04_features.md` (auditoría de fuga del 2026-10-30) y
> `especificaciones/03-preprocesamiento.md`. Las únicas cifras nuevas se midieron el 2026-10-31 en
> `data/processed/train.csv.gz` (columnas, vacíos y amenidades); **la prueba no se abrió**.
> **El grupo aprobó el borrador completo el 2026-10-31, sin cambios.** Las propuestas quedan como decisiones y se marcan
> *(aprobado por el grupo el 2026-10-31)*; las respuestas a las preguntas están en la sección 9.

## 0. Datos de entrada

- **Entrenamiento:** `data/processed/train.csv.gz`, 118.513 anuncios de 53.385 anfitriones y 65 columnas (lo genera el
  notebook 03). Anuncios por ciudad: Río 34.091 · São Paulo 33.194 · Ciudad de México 22.291 · Santiago 14.128 ·
  Bogotá 12.205 · Belice 2.604.
- **`ID_COL` = `host_id`**, **`TARGET` = `log_price_usd`**. El modelo aprende el logaritmo; el error se mide en USD con
  `exp(predicción)`. No se aplica corrección de retransformación: `exp` de la predicción en logaritmo se acerca a la
  mediana del precio, que es lo que premia el MAE. *(aprobado por el grupo el 2026-10-31)*
- **`train.joblib` no existe.** Los esqueletos de los notebooks 04 a 06 leen `data/processed/train.joblib`, pero el
  notebook 03 guarda `train.csv.gz`. **Decisión:** una función `load_train()` en `src/tarifalatam/data/` lee
  `train.csv.gz` con tipos fijos, y los notebooks 04 a 06 la usan en lugar de `joblib.load`. No se crea `train.joblib`
  (sería una segunda copia que puede quedar desactualizada). *(aprobado por el grupo el 2026-10-31)*
- **`test.csv.gz` no se abre** en estas tres etapas, ni siquiera para contar filas. Se usa una sola vez, en la etapa 7
  (constitución, principio III). No se escribe ninguna función que lea la prueba antes de esa etapa.
- **En un worktree:** `data/raw/` y `data/processed/` están en `.gitignore`. Se copian desde el checkout principal; nunca
  se mueven ni se modifican.

## 1. Columnas: prohibidas, sospechosas y permitidas

Las 65 columnas del entrenamiento quedan en una sola de estas listas. Las listas viven en `src/tarifalatam/config.py`
y una prueba automática las verifica (sección 7).

### 1.1 Prohibidas: nunca son variables

| Columna(s) | Por qué |
|---|---|
| `log_price_usd` | Es el objetivo |
| `price_usd`, `price_local` | Son el objetivo en otra escala |
| `id` | Identifica el anuncio (se usa solo para unir los pliegues) |
| `host_id` | Identifica al anfitrión: solo sirve para partir (constitución, principio II) |
| `scrape_id`, `last_scraped`, `calendar_last_scraped` | Metadatos de la descarga: dicen la ciudad y la fecha del corte, no describen el inmueble (`reports/04_features.md`) |
| `source` | 100 % vacía en el entrenamiento (los anuncios `previous scrape` ya se excluyeron) |
| `bathrooms_text` | Ya convertida en `bathrooms_count` y `bathroom_shared` (decisión 6 del EDA): usarla duplicaría la información |
| `amenities` (texto crudo) | Lista de texto con 15.938 nombres distintos en el entrenamiento. No entra cruda: solo a través de las variables de la idea 2 |

**También fuera, por redundantes** *(aprobado por el grupo el 2026-10-31)*:

| Columna(s) | Por qué |
|---|---|
| `neighbourhood_group_cleansed` | 69,8 % vacía: solo existe en São Paulo y Belice. Agrupa barrios que ya da `neighbourhood_cleansed` y, como `license`, delata la ciudad |
| `minimum_minimum_nights`, `maximum_minimum_nights`, `minimum_maximum_nights`, `maximum_maximum_nights`, `minimum_nights_avg_ntm`, `maximum_nights_avg_ntm` | Resumen del calendario de los próximos 12 meses: repiten `minimum_nights` y `maximum_nights`, y quien usa la app no los conoce |

### 1.2 Sospechosas: consecuencia del precio o de la demanda

Lista de la auditoría de fuga (`reports/04_features.md`):

- **Ocupación y disponibilidad:** `estimated_occupancy_l365d`, `availability_30`, `availability_60`, `availability_90`,
  `availability_365`, `availability_eoy`, `has_availability`.
- **Reseñas:** `number_of_reviews`, `number_of_reviews_ltm`, `number_of_reviews_l30d`, `number_of_reviews_ly`,
  `reviews_per_month`, `first_review`, `last_review`, `has_reviews` y las siete `review_scores_*` (`rating`, `accuracy`,
  `cleanliness`, `checkin`, `communication`, `location`, `value`).
- **Se agrega `host_is_superhost`** *(aprobado por el grupo el 2026-10-31)*. Airbnb lo otorga por las notas, las
  estancias y las cancelaciones del anfitrión: es consecuencia de la demanda, y un anfitrión nuevo no lo tiene.

**Regla.** Se miden **con y sin** ellas (sección 3.4). **Solo la versión sin ellas puede ir al torneo, a la optimización y a
la app**, porque el inversionista evalúa inmuebles nuevos, sin reseñas ni ocupación. La versión con ellas sirve solo para
saber cuánto pesan.

`first_review` y `last_review` son fechas. Para medirlas se convierten en días hasta el corte de su ciudad (`last_scraped`
se usa como fecha de referencia, no como variable). *(aprobado por el grupo el 2026-10-31)*

### 1.3 Permitidas: se conocen al predecir

**Referencia (fila 0 de la tabla de ideas)** *(aprobado por el grupo el 2026-10-31)*: lo que describe el inmueble, dónde está y
sus reglas de estadía. Vacíos medidos en el entrenamiento.

| Grupo | Columna | Tipo | Vacíos | Tratamiento dentro del `Pipeline` |
|---|---|---|---|---|
| Ubicación | `city` | categoría (6) | 0 % | — |
| Ubicación | `neighbourhood_cleansed` | categoría (320) | 0 % | Barrios con menos de 30 anuncios → "Other" (decisión 11 del EDA, **aprobada**) |
| Ubicación | `latitude`, `longitude` | número | 0 % | — |
| Inmueble | `room_type` | categoría (4) | 0 % | — |
| Inmueble | `property_type` | categoría (112) | 0 % | Tipos con menos de 30 anuncios → "Other" (decisión 11, **aprobada**) |
| Inmueble | `accommodates` | número | 0 % | — |
| Inmueble | `bedrooms` | número | 0,1 % | Imputar con la mediana del entrenamiento |
| Inmueble | `beds` | número | 0,9 % | Imputar con la mediana |
| Inmueble | `bathrooms_count` | número | 0,1 % | Imputar con la mediana |
| Inmueble | `bathroom_shared` | 0/1 | 0,1 % | Imputar con la moda |
| Reglas | `minimum_nights` | número | 0,1 % | Imputar con la mediana |
| Reglas | `maximum_nights` | número | 0,1 % | Imputar con la mediana (incluye los centinelas que la decisión 10 dejó vacíos) |

El umbral de 30 anuncios y las medianas se aprenden **dentro del `Pipeline`**, solo con la parte de entrenamiento de cada
pliegue (regla 5 de `CLAUDE.md`). Las columnas del anfitrión (`host_*`, `hosts_time_*`, `calculated_host_listings_count*`)
no están en la referencia: se miden como idea 4.

**Todo cálculo de variables va dentro del `Pipeline`** (también los que no aprenden de los datos), para que el modelo
guardado reciba las columnas crudas y la app no tenga que repetir ningún cálculo. *(aprobado por el grupo el 2026-10-31)*

## 2. Ideas de variables

Cada idea es una hipótesis: se escribe **antes** de medirla qué es, por qué podría ayudar y si se conoce al predecir.
*(Las cinco ideas fueron aprobadas por el grupo el 2026-10-31.)*

| # | Idea | Cómo se calcula | Por qué podría ayudar | ¿Se conoce al predecir? |
|---|---|---|---|---|
| 1 | **Distancia al centro** (`distance_to_center_km`) | Distancia en km (fórmula de haversine) desde `latitude`/`longitude` hasta el "centro" de su ciudad = mediana de la latitud y de la longitud de los anuncios de esa ciudad, **aprendida con el entrenamiento** de cada pliegue | En las ciudades grandes el precio cambia con la cercanía a las zonas turísticas; una distancia es una señal más directa que las coordenadas sueltas | ☒ sí: es la dirección del inmueble |
| 2 | **Amenidades** (`amenities_count` y 6 indicadores 0/1) | Número de elementos de la lista `amenities` (mediana 30; percentil 1 = 4; percentil 99 = 64; 134 anuncios con 0) e indicadores por nombre exacto: `Pool` (18,2 %), `Air conditioning` (40,3 %), `Free parking on premises` (25,8 %), `Gym` (12,5 %), `Elevator` (47,6 %), `Hot tub` (2,9 %) | Piscina, aire acondicionado o parqueadero suben el precio a igual tamaño; el conteo resume qué tan equipado está | ☒ sí: el anfitrión y el inversionista saben qué tiene el inmueble |
| 3 | **Razones de capacidad** | `people_per_bedroom` = `accommodates` / `bedrooms` (0 habitaciones = estudio, cuenta como 1); `people_per_bathroom` = `accommodates` / `bathrooms_count` (0 baños → vacío); `beds_per_person` = `beds` / `accommodates` | A igual capacidad, más habitaciones y baños significan más espacio y comodidad; una razón muy alta sugiere un alojamiento tipo hostal | ☒ sí: salen de columnas del inmueble |
| 4 | **Perfil del anfitrión** (columnas que ya existen) | `host_listings_count`, `calculated_host_listings_count`, `calculated_host_listings_count_entire_homes`, `calculated_host_listings_count_private_rooms`, `calculated_host_listings_count_shared_rooms`; `host_tenure_years` = `hosts_time_as_host_years` + `hosts_time_as_host_months` / 12; `user_tenure_years` = `hosts_time_as_user_years` + `hosts_time_as_user_months` / 12; `host_has_profile_pic` y `host_identity_verified` (t/f → 1/0) | Los anfitriones profesionales (muchos anuncios) fijan precios distintos a los particulares | ☒ sí: el anfitrión lo sabe; un inversionista nuevo pondría su número de anuncios y 0 años |
| 5 | **Precio típico del barrio** (`neighbourhood_price_level`) | `neighbourhood_cleansed` codificado con el promedio de `log_price_usd` del barrio, con `TargetEncoder` de scikit-learn **dentro del `Pipeline`** (usa validación cruzada interna al ajustar, así una fila no ve su propio precio) | Resume en un número lo que hoy son 320 categorías; ayuda sobre todo a Ridge | ☒ sí: el barrio se conoce; el promedio se aprende solo con el entrenamiento |

**Riesgos que hay que vigilar:**

- **Idea 1:** Belice es un país entero (sus anuncios cubren todo el territorio): una distancia a un único centro dice poco
  allí. Por eso se mira el error por ciudad. Inside Airbnb desplaza un poco las coordenadas (`reports/01_eda.md`).
- **Idea 2:** el texto de las amenidades tiene variantes. Buscar la palabra no sirve: "pool" aparece en 748 nombres distintos,
  incluido `Pool table` (4.802 anuncios), que es una mesa de billar, y hay variantes reales como `Shared pool` (2.849). Se
  usan solo los nombres exactos de la tabla, sin variantes (decisión del grupo del 2026-10-31). Cada indicador es una pregunta más en el formulario de la app.
- **Idea 4:** si se conserva, la app debe preguntar por el anfitrión, no solo por el inmueble.
- **Idea 5:** es la única que aprende del objetivo. Calculada fuera del `Pipeline` sería fuga; la prueba de la sección 7 lo
  vigila.

## 3. Medición de variables (notebook 04)

### 3.1 Pliegues: se calculan una sola vez

- `GroupKFold(n_splits=5, shuffle=True, random_state=42)` por `host_id` sobre todo el entrenamiento (scikit-learn 1.9.1 acepta
  `shuffle` y `random_state` en `GroupKFold`).
- **Decisión:** el notebook 04 los calcula con una función `make_folds(train)` y los guarda en `data/processed/folds.csv`
  (`id` y `fold`); los notebooks 05 y 06 los leen con `load_folds()`. Así **todas** las comparaciones de las tres etapas usan
  exactamente los mismos pliegues. *(aprobado por el grupo el 2026-10-31)*
- Comprobaciones con `assert`: ningún anfitrión cae en dos pliegues y cada anuncio está en exactamente uno.
- `group_cv()` de `src/tarifalatam/data/split.py` **no se cambia**: con ella se midió la línea base de H1
  (55,96 ± 1,94 USD, sin barajar). En el torneo la línea base se vuelve a medir con los pliegues nuevos, para que la
  comparación sea en los mismos pliegues; la cifra de H1 queda como registro.

### 3.2 Modelo de parámetros fijos

`LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=42, n_jobs=-1, verbose=-1)` sobre
`log_price_usd`: es rápido con 118.513 filas y acepta vacíos. Son **los mismos parámetros del LightGBM del torneo**
(sección 5). *(aprobado por el grupo el 2026-10-31)*

### 3.3 Qué se mide en cada variante

- Una variante = la referencia + **una** idea (no se acumulan). Al final se mide una vez el conjunto final (referencia +
  ideas conservadas) para confirmar, sin volver a decidir con esa cifra.
- Por pliegue: MAE en USD (principal), MAPE y R² (control), RMSE y sesgo medio (sección 5.2) y segundos de ajuste.
- Se guarda **una fila por variante y pliegue** en `reports/04_features_tabla.csv`.
- En la tabla del informe: media ± desviación entre pliegues, mejora / ruido y cuántos pliegues gana la variante.

### 3.4 Con y sin las columnas sospechosas

Después de decidir las ideas: conjunto final **+** las sospechosas de la sección 1.2, con el mismo modelo y los mismos
pliegues. Se reporta cuánto baja el MAE. No se aplica la regla de decisión: esa versión **nunca** se usa en el torneo, la
optimización ni la app. *(aprobado por el grupo el 2026-10-31)*

## 4. Regla de decisión (escrita antes de medir)

**Regla aprobada por el grupo el 2026-10-31:**

> Se conserva una idea **solo si** (a) **mejora / ruido > 1** y (b) **todas sus columnas se conocen al momento de
> predecir** para un inmueble nuevo.
>
> - **mejora** = MAE medio de la referencia − MAE medio de la variante (positivo: la variante es mejor);
> - **ruido** = desviación estándar (`ddof=1`) del MAE de la variante entre los 5 pliegues (guía, sección 1.3).
>
> Cualquier excepción (por ejemplo, descartar una idea que pasa la regla porque agrega muchas preguntas a la app) se
> justifica por escrito en `reports/04_features.md` antes de pasar al torneo.

Nota: el ruido entre pliegues incluye lo distintos que son los pliegues entre sí (en la línea base fue 1,94 USD), así que la
regla es exigente. La comparación pareada (diferencia pliegue a pliegue y pliegues que gana) se reporta como complemento,
pero **la decisión la toma la regla escrita**.

## 5. Torneo de modelos (notebook 05)

### 5.1 Candidatos y reglas

Mismas variables (el conjunto final de la etapa 4, **sin sospechosas**), mismos pliegues (`folds.csv`) y una fila guardada
por modelo y pliegue en `reports/05_torneo_tabla.csv`.

| Candidato | Configuración propuesta (sin optimizar) | Preprocesamiento |
|---|---|---|
| Línea base | `MedianBaseline`: mediana de `price_usd` por `city` × `room_type` (ya existe en `src/tarifalatam/models/baseline.py`) | Ninguno; predice USD directamente |
| Ridge | `Ridge(alpha=1.0)` sobre `log_price_usd` | Imputación, escalado y one-hot (categorías raras → "Other") |
| Bosque aleatorio | `RandomForestRegressor(n_estimators=200, min_samples_leaf=3, max_features=0.5, n_jobs=-1, random_state=42)` sobre `log_price_usd` | Imputación y codificación ordinal (categorías raras → "Other") |
| LightGBM | Los parámetros de la sección 3.2, sobre `log_price_usd` | Codificación ordinal (categorías raras → "Other"); los vacíos los maneja el modelo |

*(Candidatos y parámetros aprobados por el grupo el 2026-10-31.)* El preprocesamiento puede variar por familia de modelo, pero
las **columnas de entrada son las mismas** para todos.

### 5.2 Métricas

| Métrica | Cómo se calcula | Para qué |
|---|---|---|
| **MAE (USD por noche)** · principal | Promedio de \|precio predicho − precio real\| en USD | Decide quién gana: "el precio sugerido se equivoca en promedio X dólares" |
| MAPE | Promedio de \|predicho − real\| / real, en % | Compara ciudades con precios distintos |
| R² | Sobre `log_price_usd` (la escala que aprende el modelo) *(aprobado por el grupo el 2026-10-31)* | Qué parte de la variación explica |
| RMSE (USD) | Raíz del promedio de los errores al cuadrado | Castiga los errores grandes |
| Sesgo medio (USD) | Promedio de (predicho − real) | Positivo = sobrestima: es el error **más caro para el inversionista** (`especificacion-proyecto.md`, sección 2) |
| **Error por ciudad** | MAE (y sesgo) de cada ciudad en cada pliegue → `reports/05_torneo_por_ciudad.csv` | Vigilar que el modelo no sirva solo para las ciudades grandes; Belice tiene 2.604 anuncios y su cifra será más ruidosa |

### 5.3 Lectura del resultado

- Tabla con media ± desviación entre pliegues, ordenada por MAE, y un diagrama de cajas por modelo.
- **Comparación pareada** de los 3 mejores (guía, sección 2.4): diferencia media, pliegues que gana y diferencia / ruido (con
  la desviación de las diferencias pliegue a pliegue).
- **Diferencia en dinero:** la diferencia de MAE frente a la línea base × 30 noches = USD por cada 30 noches reservadas de un
  anuncio. Es una escala para entender la cifra, no un pronóstico de ingresos. *(aprobado por el grupo el 2026-10-31)*
- Si un modelo **no** supera a la línea base, se escribe y se explica por qué.

### 5.4 Elegir 1–2 finalistas (no un campeón)

En este orden *(aprobado por el grupo el 2026-10-31)*:

1. **Consistencia:** gana en al menos 4 de 5 pliegues al siguiente y su diferencia / ruido es mayor que 1.
2. **MAE** medio.
3. **Sesgo:** ante MAE parecidos, el que sobrestima menos.
4. **Tiempo de ajuste y simplicidad:** ante un empate (diferencia / ruido ≤ 1), el más simple; o pasan los dos.
5. **Interpretabilidad**, si el grupo la pide para explicarle el precio al anfitrión.

El torneo **descarta, no corona**: la optimización puede cambiar el orden.

## 6. Optimización con seguimiento (notebook 06)

| Punto | Decisión *(aprobado por el grupo el 2026-10-31)* |
|---|---|
| Qué se optimiza | Solo los finalistas del torneo |
| Presupuesto | **30 ensayos por finalista**, fijados antes de empezar |
| Entidades reservadas | **25 % de los anfitriones** del entrenamiento con `GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7)`; `assert` de que no comparten ningún anfitrión con la búsqueda |
| Validación de la búsqueda | Los pliegues de `folds.csv` restringidos a los anfitriones de búsqueda (cada anfitrión sigue entero en un pliegue) |
| Método | Optuna con `TPESampler(seed=42)`, minimizando el MAE medio en USD |
| Espacio: LightGBM | `learning_rate` 0,01–0,2 (escala logarítmica) · `n_estimators` 200–1.000 · `num_leaves` 15–255 · `min_child_samples` 10–200 · `subsample` 0,6–1,0 (con `subsample_freq=1`) · `colsample_bytree` 0,5–1,0 · `reg_lambda` 0,001–10 (logarítmica) |
| Espacio: bosque aleatorio | `n_estimators` fijo en 200 · `max_depth` 8–40 · `min_samples_leaf` 1–20 · `max_features` 0,2–1,0 |
| Espacio: Ridge (si es finalista) | `alpha` 0,001–1.000 (logarítmica) |
| Seguimiento | **Local**: `configure_mlflow(force_local=True)` del módulo que ya existe (`src/tarifalatam/tracking/mlflow_utils.py`, **sin reescribirlo**); experimento `tarifalatam-optimizacion` con `set_experiment`. Databricks entra en la clase 4; no se piden ni se escriben tokens |
| Qué se registra por ensayo | Una ejecución por ensayo con `log_run`, nombre `<modelo>-ensayo-<nn>` (por ejemplo `lightgbm-ensayo-07`): hiperparámetros; MAE medio y su desviación entre pliegues, MAPE, R², RMSE, sesgo y segundos; etiquetas `etapa=06_optimizacion`, `modelo`, `variables=sin_sospechosas` y `datos=train.csv.gz` |
| Lo que no se reporta como resultado | La mejor puntuación de la búsqueda: es optimista (el máximo de muchas estimaciones con ruido) |

**Comprobación honesta** *(aprobado por el grupo el 2026-10-31)*:

1. Se entrenan dos modelos con **todos** los datos de búsqueda: parámetros de **partida** (los del torneo) y **optimizados**.
2. Se predicen las entidades reservadas. Diferencia por anuncio = \|error optimizado\| − \|error de partida\|, en USD.
3. Intervalo del 95 % **remuestreando anfitriones completos** (no filas): 1.000 remuestreos, semilla 42 (guía, sección 3.6).
4. **Regla escrita antes de mirar:** se usan los parámetros optimizados **solo si todo el intervalo está por debajo de cero**;
   si cruza el cero, la mejora no se distingue del ruido y se usan los de partida.
5. Si hay dos finalistas, se comparan sus configuraciones elegidas en las mismas entidades reservadas, con el mismo intervalo
   por anfitrión: pasa a la etapa 7 el que tenga todo el intervalo de la diferencia por debajo de cero; si cruza el cero, el
   más simple y rápido. Esta elección se hace **sin abrir la prueba**.
6. La decisión se guarda en `reports/06_best_params.json` (finalista, parámetros, intervalo y dónde quedó el seguimiento).

## 7. Pruebas automáticas que deben existir

- ☒ **Columnas prohibidas:** las listas de `config.py` no se cruzan; una función que revisa las columnas del modelo falla si
  le llega una prohibida; y un `Pipeline` ajustado con datos donde `price_usd`, `id` y `host_id` predicen perfecto **no** las
  usa (sus nombres de salida no las contienen).
- ☒ **Versión para la app:** sus columnas no incluyen ninguna sospechosa.
- ☒ **Carga:** `load_train()` devuelve las 65 columnas esperadas con sus tipos. *(La prueba verifica las 65 columnas; los tipos
  no se prueban uno por uno.)*
- ☒ **Pliegues:** ningún anfitrión en dos pliegues, cada anuncio en exactamente uno, y la misma semilla da los mismos pliegues.
- ☒ **Una prueba por idea** (`tests/test_features.py`): división por cero, vacíos, que no modifica el original y, en las
  ideas que aprenden (1 y 5), que usan solo lo visto al ajustar. *(La idea 5 es el `TargetEncoder` de scikit-learn; la
  prueba verifica que queda dentro del `Pipeline`, que es lo que garantiza que se ajuste solo con el entrenamiento.)*
- ☒ **Métricas:** con predicción perfecta el MAE y el sesgo dan 0 y el R² da 1; un caso calculado a mano para MAE, MAPE y
  sesgo (incluido el signo).
- ☒ **Evaluación por pliegue:** una fila por pliegue, con los pliegues dados (no otros).
- ☒ **Entidades reservadas:** no comparten anfitriones con la búsqueda.
- ☒ **Intervalo por anfitrión:** con una diferencia constante el intervalo es esa constante; remuestrea anfitriones, no filas.
- ☒ `pytest` en verde desde la raíz (194 pruebas el 2026-10-31: las 76 de H1 y 118 nuevas).

## 8. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `data/processed/train.csv.gz` (la prueba no se abre) |
| Pliegues | `data/processed/folds.csv` (no se sube a Git, como todo `data/processed/`) |
| Listas de columnas | `src/tarifalatam/config.py` |
| Carga y pliegues | `src/tarifalatam/data/` (`load_train`, `make_folds`, `load_folds`) |
| Variables | `src/tarifalatam/features/` |
| Pipeline, métricas y evaluación por pliegue | `src/tarifalatam/models/train.py` (`build_pipeline`, `evaluate_folds`) |
| Optimización e intervalo por anfitrión | `src/tarifalatam/models/tuning.py` |
| Seguimiento | `src/tarifalatam/tracking/mlflow_utils.py` (ya existe; no se reescribe) → `mlflow_local.db` (en `.gitignore`) |
| Notebooks que orquestan | `notebooks/04_features.ipynb`, `05_torneo.ipynb`, `06_optimizacion.ipynb` (solo llaman a `src/`) |
| Informes | `reports/04_features.md` + `04_features_tabla.csv`; `reports/05_torneo.md` + `05_torneo_tabla.csv` + `05_torneo_por_ciudad.csv`; `reports/06_optimizacion.md` + `06_best_params.json` |

**Fuera de alcance:** abrir la prueba (etapa 7); MLflow en Databricks y el registro del modelo (clase 4); exportar
`models/model.joblib` y la app; adaptar `src/tarifalatam/inference/`, que hoy es la plantilla de **clasificación** (etapas 9
y 10).

## 9. Decisiones del grupo (2026-10-31)

El grupo aprobó el borrador completo, sin cambios. Respuestas a las preguntas que planteaba:

1. **Columnas:** se aprueban las listas de la sección 1. Salen `neighbourhood_group_cleansed` y las seis variantes de noches
   mínimas y máximas; `host_is_superhost` se trata como sospechosa.
2. **Ideas:** se aprueban las cinco. Los indicadores de amenidades usan solo los nombres exactos, sin variantes.
3. **Regla de decisión:** la de la sección 4, tal como está.
4. **Candidatos:** los cuatro de la sección 5.1 con sus parámetros; el R² se calcula sobre el logaritmo.
5. **Presupuesto:** 30 ensayos **por finalista**.
6. **Pliegues:** se guardan en `data/processed/folds.csv`.
7. **Dinero:** la diferencia de MAE se traduce a "USD por cada 30 noches reservadas".
8. **Quién implementa:** se reparte al aprobar `tasks.md` (cada integrante con su cuenta de GitHub). *Pendiente.*

## 10. Criterios de cierre

**Etapa 4 · Variables**

- ☒ Pliegues calculados una sola vez y reutilizados en las tres etapas (con su comprobación por anfitrión).
- ☒ Tabla de ideas medidas (referencia + cada idea) con MAE ± ruido, mejora / ruido, pliegues que gana y decisión.
- ☒ Ideas descartadas anotadas con su cifra en `reports/04_features.md`.
- ☒ Medición con y sin las columnas sospechosas, y constancia de que la versión con ellas no sigue.
- ☒ Lista final de variables escrita y su código en `src/tarifalatam/features/` con pruebas.

**Etapa 5 · Torneo**

- ☒ Línea base + al menos 3 modelos en los mismos pliegues, con una fila guardada por modelo y pliegue.
- ☒ MAE (principal) y MAPE, R², RMSE y sesgo (técnicas), más el error por ciudad.
- ☒ Comparación pareada de los 3 mejores y la diferencia traducida a dinero.
- ☒ 1–2 finalistas justificados en `reports/05_torneo.md`, y por qué no hay campeón.

**Etapa 6 · Optimización**

- ☒ Presupuesto y espacio de búsqueda escritos antes de empezar, y respetados.
- ☒ 25 % de los anfitriones reservados que la búsqueda nunca vio.
- ☒ Un ensayo = una ejecución en el MLflow local, con parámetros, métricas y etiquetas. *(Comprobado el 2026-10-31 con
  `mlflow.search_runs`: 60 ejecuciones completas, ninguna métrica vacía. Falta que el grupo lo vea en `mlflow ui`.)*
- ☒ Comprobación honesta con intervalo por anfitrión, decisión según la regla y `reports/06_best_params.json`.
- ☒ `reports/06_optimizacion.md` completado.

**Para las tres**

- ☒ `test.csv.gz` sin abrir. *(Ningún archivo de `src/` ni los notebooks 04 a 06 lo leen.)*
- ☒ Toda cifra de los informes sale de un notebook ejecutado (ninguna inventada).
- ☒ `pytest` en verde desde la raíz (194 pruebas).
- ☐ Revisión con `auditor-de-fuga` y `revisor-de-codigo-ia` antes de dar las etapas por cerradas.
- ☐ Quien no escribió el código sabe responder las 8 preguntas de la guía (sección 5).
