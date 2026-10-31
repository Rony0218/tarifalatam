# Informe de variables

> Resultado de `notebooks/04_features.ipynb`, ejecutado el 2026-10-31 (unos 70 segundos). Cada idea de variable es una
> **hipótesis medida** con la misma validación; se conserva solo si cumple la regla escrita antes de medir. Las cifras por
> pliegue están en `reports/04_features_tabla.csv`. Especificación: `especificaciones/04-features-torneo-optimizacion.md`.
> Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 1.

## Cómo se midió

- **Modelo (parámetros fijos):** `LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=42)`
  sobre `log(price_usd)`. Son los mismos parámetros del LightGBM del torneo.
- **Métrica principal** (y por qué): MAE en USD por noche, porque el anfitrión la lee en dinero. Las predicciones se llevan a
  USD con la exponencial.
- **Métricas de control:** MAPE (compara ciudades con precios distintos) y R² sobre el logaritmo. Se registran también el
  RMSE y el sesgo medio.
- **Pliegues:** `GroupKFold` por `host_id`, 5 pliegues, barajados con semilla 42. Se calcularon **una sola vez** y se guardaron
  en `data/processed/folds.csv`, que leen los notebooks 05 y 06. Cada pliegue de validación tiene 10.677 anfitriones (entre
  23.358 y 24.184 anuncios), y ningún anfitrión está en dos pliegues.
- **Datos:** el entrenamiento completo, 118.513 anuncios de 53.385 anfitriones. La prueba no se abrió.
- **Regla de decisión escrita antes de medir:** se conserva una idea solo si **mejora / ruido > 1**, donde mejora = MAE medio
  de la referencia − MAE medio de la variante y ruido = desviación estándar del MAE de la variante entre los 5 pliegues, **y**
  si todas sus columnas se conocen al momento de predecir un inmueble nuevo. Una variante = la referencia + una idea.

## Tabla de ideas medidas

> La fila 0 es la **referencia**: las 13 columnas que describen el inmueble, dónde está y sus reglas de estadía.
> "Mejora / ruido" menor que 1 está dentro del ruido. Las dos columnas de la derecha son un complemento que **no decide**:
> pliegues que gana la variante y la comparación pareada (diferencia pliegue a pliegue dividida por su propia desviación).

| # | Idea (variable y cómo se calcula) | ¿Se conoce al predecir? | MAE (± ruido), USD | Mejora / ruido | Decisión | Pliegues que gana | Pareada |
|---|---|---|---|---|---|---|---|
| 0 | **Referencia** (13 columnas) | — | 39,90 ± 1,73 | 0 | — | — | — |
| 1 | Distancia al centro: km (haversine) hasta la mediana de las coordenadas de la ciudad, aprendida en el entrenamiento del pliegue | ☒ sí ☐ no | 39,88 ± 1,71 | 0,01 | ☐ conservar ☒ descartar | 3 de 5 | 0,13 |
| 2 | Amenidades: número de amenidades y 6 indicadores por nombre exacto | ☒ sí ☐ no | 38,99 ± 1,88 | 0,49 | ☐ conservar ☒ descartar | 5 de 5 | 4,42 |
| 3 | Razones de capacidad: personas por habitación, personas por baño y camas por persona | ☒ sí ☐ no | 39,90 ± 1,70 | −0,00 | ☐ conservar ☒ descartar | 3 de 5 | −0,05 |
| 4 | Perfil del anfitrión: 5 conteos de anuncios, antigüedad del anfitrión y de su cuenta, foto e identidad verificada | ☒ sí ☐ no | 40,21 ± 1,92 | −0,16 | ☐ conservar ☒ descartar | 1 de 5 | −1,12 |
| 5 | Precio típico del barrio: el barrio codificado con el promedio del objetivo (`TargetEncoder` con validación cruzada interna, dentro del `Pipeline`) | ☒ sí ☐ no | 39,74 ± 1,69 | 0,09 | ☐ conservar ☒ descartar | 5 de 5 | 1,54 |

Métricas de control de la referencia: MAPE 32,70 %, R² (log) 0,636 y sesgo medio −14,03 USD. Con las amenidades: MAPE
31,63 %, R² 0,655 y sesgo −13,59 USD. MAE de la referencia por pliegue: 38,35 · 42,47 · 38,29 · 39,88 · 40,50.

**Medición con las columnas sospechosas** (conjunto final + ocupación, disponibilidad, reseñas y superanfitrión): MAE
**37,39 ± 1,61 USD**. Baja 2,51 USD frente al conjunto final (mejora / ruido 1,56; gana en 5 de 5 pliegues; pareada 12,61).
**Esa versión no sigue** al torneo ni a la app (ver "Supuestos y riesgos").

## Decisiones y motivos

- **Idea 1, distancia al centro: descartada.** Mejora 0,02 USD (mejora / ruido 0,01; gana en 3 de 5). Una explicación probable,
  no medida: la latitud y la longitud ya están en la referencia, y los árboles aprenden de ellas lo mismo.
- **Idea 2, amenidades: descartada por la regla.** Es la mejora más grande (0,91 USD, de 39,90 a 38,99) y la más consistente:
  gana en los 5 pliegues y la comparación pareada da 4,42. Pero su mejora / ruido es 0,49: la mejora es menor que lo que varía
  el MAE de un pliegue a otro (1,88 USD). El 2026-10-31 el grupo decidió **aplicar la regla sin excepciones** (tarea T035), por
  dos motivos: la regla se fijó antes de medir, y conservarla agregaría 7 preguntas al formulario de la app (el conteo y 6
  casillas).
- **Idea 3, razones de capacidad: descartada.** Sin cambio (mejora −0,004 USD). `accommodates`, `bedrooms`, `beds` y
  `bathrooms_count` ya están en la referencia.
- **Idea 4, perfil del anfitrión: descartada.** Empeora el MAE (+0,31 USD; gana solo en 1 de 5). Además, obligaría a la app a
  preguntar por el anfitrión, no solo por el inmueble.
- **Idea 5, precio típico del barrio: descartada.** Mejora 0,16 USD (mejora / ruido 0,09), aunque gana en los 5 pliegues
  (pareada 1,54). Los barrios ya entran como categoría (los raros agrupados en "Other").
- **Conjunto final = la referencia** (`config.FINAL_IDEAS = ()`). Medido otra vez como "final": 39,90 ± 1,73 USD, igual a la
  referencia.

## Supuestos y riesgos

- **La regla es exigente.** El ruido entre pliegues (1,7 a 1,9 USD) incluye lo distintos que son los pliegues entre sí, no solo
  el efecto de la idea. Por eso una mejora pequeña pero constante, como la de las amenidades, no la pasa. Lo dice la
  especificación de la etapa (sección 4) y queda como aprendizaje para la próxima ronda de ideas.
- **Columnas prohibidas.** Nunca son variables: el objetivo (`log_price_usd`, `price_usd`, `price_local`), los identificadores
  (`id`, `host_id`), los metadatos de la descarga (`scrape_id`, `last_scraped`, `calendar_last_scraped`), `source`,
  `bathrooms_text`, `amenities` cruda, `neighbourhood_group_cleansed` y las seis variantes de noches del calendario (18 en
  total, en `config.FORBIDDEN_FEATURES`). La auditoría de fuga del 2026-10-30 pedía una lista explícita y una prueba:
  `tests/test_columns.py` falla si se pide una de ellas, y `tests/test_train.py` comprueba que el modelo no las usa aunque
  predigan perfecto.
- **Columnas sospechosas: pesan, pero no se usan.** Bajan el MAE 2,51 USD, de forma muy consistente. Precisamente por eso se
  dejan fuera: son consecuencia del precio y de la demanda (un precio alto deja el calendario libre), y un inmueble nuevo, el
  caso del inversionista, no tiene reseñas ni ocupación. Son 23 columnas (`config.SUSPICIOUS_FEATURES`), incluida
  `host_is_superhost`, que se agregó a la lista el 2026-10-31.
- **El modelo subestima.** El sesgo medio es de −14 USD por noche: predecir en logaritmo y volver con la exponencial se acerca
  a la mediana, que es menor que el promedio en precios asimétricos. Para el inversionista es el lado menos caro (es peor
  sobrestimar), pero el anfitrión podría cobrar de menos. Se vigila en el torneo.
- **`license`** ya no llega al modelo: se eliminó el 2026-10-31 porque solo existe en Bogotá.
- **La comparación con la línea base de H1 (55,96 USD) no es directa:** se midió con otros pliegues (sin barajar). El torneo
  vuelve a medir la línea base con los mismos pliegues de esta etapa.

## Qué se lleva el pipeline final

- **Variables:** la referencia de 13 columnas.
  - Categóricas: `city`, `neighbourhood_cleansed`, `room_type` y `property_type`. Las que tienen menos de 30 anuncios en el
    entrenamiento pasan a "Other" (decisión 11 del EDA, `RareCategoryGrouper`).
  - Numéricas: `latitude`, `longitude`, `accommodates`, `bedrooms`, `beds`, `bathrooms_count`, `minimum_nights` y
    `maximum_nights`.
  - Indicador: `bathroom_shared`.
- **Código:**
  - Listas de columnas: `src/tarifalatam/config.py`.
  - Columnas por variante y revisión de prohibidas: `src/tarifalatam/features/columns.py`.
  - Transformadores de las ideas (se conservan, apagados, porque documentan lo que se probó):
    `src/tarifalatam/features/engineering.py`.
  - `Pipeline`: `build_pipeline` en `src/tarifalatam/models/train.py`.
- **Para la app:** el formulario solo necesita estas 13 entradas. Ninguna es sospechosa.
