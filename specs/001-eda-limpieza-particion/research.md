# Research: decisiones técnicas del hito H1

Cada punto: **Decisión**, **Motivo**, **Alternativas consideradas**. No quedan dudas abiertas en el contexto técnico; el único
pendiente es un **dato** que trae el grupo (las tasas), no una decisión.

## 1. Dónde viven las tasas de cambio

- **Decisión:** un diccionario `FX_RATES` en `src/tarifalatam/config.py`, una entrada por ciudad con `currency`,
  `local_per_usd` (unidades de moneda local por 1 USD), `date` y `source` (enlace). Las cinco que faltan valen `None`. Belice:
  `currency="USD"` y `local_per_usd=1.0`. Se calcula `price_usd = price_local / local_per_usd`.
- **Motivo:** queda versionado en Git, con su fuente al lado del valor, y cualquiera lo revisa sin abrir datos. Si una tasa es
  `None`, `to_usd` lanza un error que dice qué ciudad falta (principio VII).
- **Alternativas:** un CSV en `data/raw/`: está en `.gitignore` y es la carpeta "intocable", así que no sirve. Una carpeta nueva
  `data/reference/`: no está en la estructura obligatoria. Descargar las tasas por API: dependencia de red y de una fuente que
  puede cambiar.

## 2. Moneda de cada ciudad

- **Decisión:** `CITY_CURRENCY` fija en `config.py` (Río y São Paulo BRL, Ciudad de México MXN, Buenos Aires ARS, Bogotá COP,
  Santiago CLP, Belice USD). Una función `check_currencies` compara esa tabla con la moneda que trae `price_quote_raw` y falla si
  alguna fila no vacía no coincide. Después, `price_quote_raw` se elimina con el resto de columnas de fuga.
- **Motivo:** el EDA descubrió que Belice está en USD. Si Inside Airbnb cambia la moneda en otro corte, la limpieza debe
  avisarlo y no convertir mal en silencio.
- **Alternativa:** leer la moneda fila por fila desde el JSON. Se descarta porque es más frágil (4,3 % de vacíos) y porque la
  moneda es una propiedad de la ciudad, no del anuncio.

## 3. Cómo identificar la ciudad

- **Decisión:** se toma del nombre del archivo (`listings_<ciudad>_<fecha>.csv.gz`). `load_raw` exige exactamente los siete
  nombres de `CITY_FILES` y falla si falta uno o si sus columnas no son las 90 esperadas.
- **Motivo:** los archivos no traen una columna de ciudad. El nombre del archivo es el que fija el `README.md`.

## 4. Orden de las reglas

- **Decisión:**

  | Paso | Regla | Requisito |
  |---|---|---|
  | 1 | Cargar y quitar datos personales y texto libre | FR-001, FR-002 |
  | 2 | Comprobar monedas | FR-003 |
  | 3 | Excluir "previous scrape" | FR-011 |
  | 4 | Precio a número | FR-003 |
  | 5 | Excluir sin precio | FR-004 |
  | 6 | Pasar a USD | FR-003 |
  | 7 | Quitar columnas de fuga | FR-005 |
  | 8 | Quitar columnas vacías | FR-006 |
  | 9 | Baños | FR-007 |
  | 10 | Excluir arriendos mensuales | FR-008 |
  | 11 | Centinelas a vacío | FR-009 |
  | 12 | `has_reviews` | FR-010 |
  | 13 | **Partir por `host_id`** | FR-013 |
  | 14 | Límites de precio aprendidos en entrenamiento y aplicados a ambos | FR-014 |
  | 15 | Objetivo `log_price_usd` | FR-015 |

- **Motivo:**
  - Primero lo que no aprende de los datos; después la partición; al final lo único que aprende (la mediana por ciudad).
  - "Previous scrape" va antes de "sin precio" para que el registro muestre cuántos anuncios del corte anterior se fueron por
    esa razón (11.701) y no se mezclen con los inactivos.
  - La ciudad (FR-012) no filtra nada: se incluyen las siete.
- **Alternativa:** filtrar los precios extremos antes de partir, con la mediana de todos los datos. Se descarta porque la prueba
  influiría en el umbral (principio III).

## 5. Precios extremos: ¿fuera del `Pipeline` de scikit-learn?

- **Decisión:** dos funciones, `fit_price_bounds(train)` (devuelve los límites por ciudad: 0,1 × y 20 × la mediana de
  `price_usd`) y `drop_price_outliers(df, bounds)`. No van dentro del `Pipeline` del modelo.
- **Motivo:** un `Pipeline` transforma columnas pero **no puede quitar filas**. La regla 5 del proyecto busca que nada aprenda
  de la prueba, y eso se cumple: los límites salen solo del entrenamiento y quedan guardados en el registro.
- **Riesgo declarado:** la regla también se aplica a la prueba (usa el precio real para excluir). Se acepta como regla de
  calidad (precios imposibles) y se dirá en el informe de validación. La app no filtra nada: siempre sugiere un precio.

## 6. Partición y validación cruzada

- **Decisión:** `GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)` con `groups=host_id`. Para la línea base y la
  etapa 4, `GroupKFold(n_splits=5)` por `host_id` (en regresión no hace falta estratificar).
- **Motivo:** es la regla 3 de `CLAUDE.md` y el patrón del ejemplo CreditSight (`split.py`). `test_size` cuenta anfitriones, no
  filas: la prueba tendrá cerca del 20 % de las filas, no exactamente.
- **Alternativa:** `StratifiedGroupKFold` estratificando por ciudad. Mejor balance por ciudad, pero exige una etiqueta discreta y
  complica la explicación. Queda como mejora si el registro muestra que una ciudad (Belice) queda muy desbalanceada.

## 7. Formato de salida

- **Decisión:** `data/processed/train.csv.gz` y `data/processed/test.csv.gz`, más `reports/03_exclusiones.csv`.
- **Motivo:** parquet exigiría agregar `pyarrow` a `requirements.txt`. El CSV comprimido basta para menos de 180.000 filas.
- **Alternativa:** parquet (tipos exactos, más rápido). Se puede adoptar después agregando la dependencia.

## 8. Línea base

- **Decisión:** `src/tarifalatam/models/baseline.py` con `MedianBaseline` (mediana de `price_usd` por `city` × `room_type`; si una
  combinación no se vio en el pliegue, usa la mediana de la ciudad). `baseline_cv_mae(train)` devuelve el MAE en USD por pliegue
  y su promedio con `GroupKFold`. Se calcula en el notebook 03 y se anota en `reports/01_eda.md`.
- **Motivo:** la especificación del proyecto la define así. La mediana aprendida dentro de cada pliegue evita fuga entre
  pliegues. El respaldo por ciudad cubre celdas raras (21 habitaciones de hotel en Río).

## 9. El notebook 02 y sus cifras

- **Decisión:** el notebook carga con `load_raw` (ya sin datos personales) y calcula las cifras de FR-018 con pandas, en celdas
  cortas. La última celda arma una tabla "cifra | esperado (informe) | obtenido | ¿coincide?".
- **Motivo:** las cifras son resúmenes de una sola línea, no lógica reutilizable; por eso pueden vivir en el notebook (los
  notebooks orquestan y resumen). La tabla final cumple SC-005 sin tener que leer todo el notebook.

## 10. Ejecución sin datos reales en las pruebas

- **Decisión:** las pruebas construyen tablas pequeñas a mano. La de `load_raw` escribe siete `.csv.gz` mínimos en una carpeta
  temporal (`tmp_path`). Las tasas de las pruebas son inventadas **a propósito** y se marcan como tales en el código de prueba.
- **Motivo:** `data/raw/` no está en Git; las pruebas deben correr en cualquier computador. Las tasas de prueba nunca llegan a
  `config.py`.
