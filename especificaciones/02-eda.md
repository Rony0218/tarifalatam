# Especificación · Etapa 2 · EDA

> Se llena **antes** de abrir `notebooks/02_eda.ipynb` (las secciones 1 y 2) y se completa **mientras**
> lo ejecutan (3 y 4). El resultado final, con las decisiones, va a `reports/01_eda.md`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md` · Ejemplo: `material-del-curso/ejemplo-creditsight/reports/01_eda.md`.

**Grupo:** TarifaLatam   **Fecha:** 2026-10-30   **Estado:** ☒ borrador  ☐ cerrada

> **Cómo se llenó este borrador.** Las secciones 1 y 2 salen de `especificacion-proyecto.md` (escrita antes de
> abrir los datos). Las cifras de las secciones 3 y 4 se midieron sobre los siete archivos de `data/raw/` con un
> script exploratorio (sin imprimir datos personales). **Falta que `notebooks/02_eda.ipynb` las reproduzca** y que el
> grupo revise y apruebe cada decisión: hasta entonces, la sección 4 es una **propuesta**.

## 1. Qué esperamos encontrar (se escribe ANTES de mirar los datos)

Una hipótesis por pregunta. Si después no se cumple, es un hallazgo: anótenlo.

| Pregunta | Lo que creemos | ¿Se cumplió? |
|---|---|---|
| ¿Qué representa una fila? | Un anuncio de Airbnb (`id`) en la fecha de corte de su ciudad | Sí: `id` no se repite en las 194.628 filas |
| ¿Alguna entidad se repite en varias filas? | Sí, el anfitrión (`host_id`): uno puede tener muchos anuncios | Sí: 89.964 anfitriones; uno llega a 699 anuncios |
| ¿Qué variable **debería** ser estable y no cambiar? | Lo que describe al anfitrión: `host_is_superhost`, `host_listings_count`, antigüedad (`hosts_time_as_host_years`) | Sí: cambian en ≤ 0,18 % de los anfitriones |
| ¿Qué significaría un vacío en nuestras columnas clave? | `price` vacío = anuncio inactivo o sin calendario; `review_scores_*` vacío = anuncio sin reseñas | Sí en ambos (ver sección 3) |
| ¿Qué columna solo se conoce **después** de la decisión que queremos apoyar? | `price_quote_*` y `estimated_revenue_l365d` (contienen el precio); ocupación y disponibilidad (son consecuencia del precio) | Sí: confirmado con cifras (decisión 3) |

**Hallazgos que no esperábamos:** (a) los precios de Belice ya vienen en **USD**, no en BZD; (b) las columnas 100 %
vacías no son solo de Bogotá: **12 columnas están vacías en las siete ciudades**; (c) en Buenos Aires muchos precios son
exactamente 100, 110, 120, 130… × 764,41 ARS, como si el anfitrión hubiera fijado el precio en otra moneda.

## 2. Qué vamos a medir

Marquen lo que aplica a su dataset. Lo que no aplique se tacha **con una razón** (no se deja en blanco).

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar | Quién lo hace |
|---|---|---|---|
| 3.1 Números guardados como texto | ☒ sí ☐ no: | `price` (`"$1,234.00"`), `bathrooms_text` (`"1.5 shared baths"`), `price_quote_raw` (JSON) | |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☒ sí ☐ no: | `maximum_nights` (1.125 por defecto y 2.147.483.647 = máximo entero), `minimum_nights` (999) | |
| 3.3 Valores imposibles (percentiles, negativos) | ☒ sí ☐ no: | `price` (extremos por ciudad), `bedrooms` (> 10, > `accommodates`), `beds` | |
| 3.4 Constancia por entidad | ☒ sí ☐ no: | Por `host_id`: `host_is_superhost`, `host_listings_count`, `hosts_time_as_host_years` | |
| 3.5 Vacíos que significan algo | ☒ sí ☐ no: | `price`, `review_scores_*`, `reviews_per_month`, `first_review`, `license` | |
| 3.6 Duplicados | ☒ sí ☐ no: | `id`; fila completa sin `id`; mismo anfitrión + coordenadas + tipo + capacidad + precio | |
| 3.7 Fechas y orden temporal | ☒ sí ☐ no: | `last_scraped` (un solo corte por ciudad, sin orden temporal entre filas); `first_review`, `last_review` | |
| 3.8 Categorías raras / alta cardinalidad | ☒ sí ☐ no: | `property_type` (123), `neighbourhood_cleansed` (371), `room_type` (4) | |
| 3.9 Identidad y datos personales | ☒ sí ☐ no: | 10 columnas del anfitrión y URLs; texto libre (`name`, `description`) con teléfonos y correos | |

> La columna "Quién lo hace" la asigna el grupo.

## 3. Lo que medimos (se llena mientras corre el notebook)

- **Filas × columnas:** 194.628 × 90 (siete archivos con las mismas 90 columnas; se agrega `city` al unirlos).
- **Unidad de análisis (una frase):** una fila es **un anuncio** de Airbnb en la fecha de corte de su ciudad (14–25 de septiembre de 2026).
- **Columna que identifica a la entidad (`ID_COL`):** `host_id`   **¿Se repite?** ☐ no ☒ sí, 2,2 anuncios por anfitrión en promedio (mediana 1, percentil 99 = 19, máximo 699). El 73 % de los anfitriones tiene un solo anuncio, pero el **31 % de los anuncios** (60.320) es de anfitriones con 10 o más. 258 anfitriones tienen anuncios en más de una ciudad.
- **Objetivo (`TARGET`):** `price` (precio por noche publicado). **Distribución:** muy asimétrica a la derecha en todas las ciudades (asimetría entre 23 y 160 en escala original; entre 0,5 y 2,1 en logaritmo). Medianas en moneda local para "vivienda completa": Río 491 BRL, São Paulo 353 BRL, Ciudad de México 1.828 MXN, Buenos Aires 110.075 ARS, Bogotá 181.250 COP, Santiago 60.000 CLP, Belice 403 USD.
- **Línea base** (regla trivial) y su resultado: mediana del precio por `city` × `room_type`. **MAE = 53,80 ± 2,74 USD por noche** (notebook 03, 5 pliegues por anfitrión, solo entrenamiento; tasas pendientes de confirmar).
- **Vacíos en el objetivo:** 11.642 anuncios (6,0 %; entre 3,5 % en São Paulo y 8,5 % en Río). El 64 % de ellos tiene `availability_365 = 0` (calendario cerrado), frente al 0,2 % de los que tienen precio.   **Qué haremos con esas filas:** excluirlas (no se imputa el objetivo).
- **Datos personales encontrados:** `host_name`, `host_about`, `host_location`, `host_url`, `host_profile_url`, `host_profile_id`, `host_picture_url`, `host_thumbnail_url`, `listing_url`, `picture_url`. Además, el texto libre trae datos de contacto: 91 descripciones con números de teléfono, 9 con correos y 7 nombres de anuncio con teléfonos.
- **Columnas sospechosas de fuga:** `price_quote_price_per_night` (idéntica a `price` en los 182.983 anuncios que tienen ambas), `price_quote_total_price`, `price_quote_raw`, `price_quote_checkin_date`, `price_quote_checkout_date`, `estimated_revenue_l365d` (= `price` × `estimated_occupancy_l365d`). Sospechosas a medir en la etapa 4: `estimated_occupancy_l365d`, `availability_30/60/90/365`, `availability_eoy`, `has_availability`.

## 4. Decisiones (mínimo 5)

> Cada una con **cifra**, acción **concreta** y **motivo**. Se copian tal cual a `reports/01_eda.md`.
> Cada decisión se convierte en una función de `src/tarifalatam/data/` y en una prueba (ver `03-preprocesamiento.md`).
> **Propuesta pendiente de aprobación del grupo.** Los nombres de función son sugerencias.

| # | Hallazgo (con cifra) | Decisión | Motivo | Función que la implementa |
|---|---|---|---|---|
| 1 | `price` llega como texto `"$1,234.00"` en el 100 % de los 182.986 precios, y en seis monedas (BRL, MXN, ARS, COP, CLP y USD en Belice, según `price_quote_raw`) | Quitar `$` y `,`, convertir a número y pasar a USD con la tasa oficial del día del corte de cada ciudad (Belice no se convierte). Modelar `log(price_usd)` | Sin una sola escala numérica no se puede comparar ni modelar; el logaritmo reduce la asimetría de 23–160 a 0,5–2,1 | `parse_price`, `to_usd` |
| 2 | 11.642 anuncios (6,0 %) sin precio; el 64 % tiene el calendario cerrado (`availability_365 = 0`) frente al 0,2 % de los que tienen precio | Excluir los anuncios sin precio | El vacío significa "anuncio inactivo", no un precio perdido; imputar el objetivo sería inventarlo | `drop_missing_price` |
| 3 | `price_quote_price_per_night` es idéntica a `price` (razón = 1,000 en 182.983 anuncios) y `estimated_revenue_l365d` = `price` × ocupación (razón mediana 1,000) | Eliminar al cargar las 5 columnas `price_quote_*` y `estimated_revenue_l365d`. Dejar ocupación y disponibilidad como **sospechosas** para medir con y sin ellas en la etapa 4 | Contienen la respuesta: con ellas el modelo "acierta" y en la app no existirían | `drop_leakage_columns` |
| 4 | 10 columnas con datos personales del anfitrión; el texto libre trae 91 teléfonos y 9 correos en `description` y 7 teléfonos en `name` | Eliminar al cargar las 10 columnas y el texto libre (`name`, `description`, `neighborhood_overview`). `host_id` se queda solo para partir | Privacidad (principio V); el texto libre no se usará como variable en esta versión | `load_raw` (primer paso) |
| 5 | 194.628 anuncios de 89.964 anfitriones; el 31 % de los anuncios es de anfitriones con ≥ 10 anuncios (máximo 699) | Partir entrenamiento/prueba y la validación cruzada **por `host_id`** (`GroupShuffleSplit`, `GroupKFold`) | Los anuncios de un mismo anfitrión se parecen (mismo estilo de precio); partir por fila inflaría la métrica | `split_by_host` |
| 6 | 12 columnas están 100 % vacías en las siete ciudades (`bathrooms`, `host_since`, `host_response_time`, `host_response_rate`, `host_acceptance_rate`, `instant_bookable`, `neighbourhood`, …); `bathrooms_text` solo tiene 0,1 % de vacíos | Eliminar las columnas vacías. Sacar de `bathrooms_text` el número de baños (con "half-bath" = 0,5; 1.010 casos) y un indicador de baño compartido (8,0 %). Usar `hosts_time_as_host_years` como antigüedad del anfitrión | Una columna vacía no aporta; el número de baños sí existe, pero escrito como texto | `drop_empty_columns`, `parse_bathrooms_text` |
| 7 | 6.103 anuncios (3,1 %) piden `minimum_nights ≥ 30`; en Bogotá son el 16,9 % y su precio mediano por noche es 94.102 COP frente a 170.000 COP del resto | Excluir los anuncios con `minimum_nights ≥ 30` | Son arriendos mensuales con otra lógica de precio; el caso es la corta estancia | `drop_monthly_rentals` |
| 8 | 692 anuncios cobran más de 20 veces la mediana de su ciudad (355 en Río) y 61 menos de una décima parte; hay máximos como 258.514.678 COP por noche en Bogotá | Excluir como error de captura los precios fuera de [0,1 ×, 20 ×] la mediana de su ciudad, **calculada con el entrenamiento** (umbral a confirmar por el grupo) | Precios imposibles dominarían el error; el umbral relativo funciona igual en todas las monedas | `drop_price_outliers` |
| 9 | `review_scores_*` está vacío en el 100 % de los 15,5 % de anuncios sin reseñas, y en ninguno con reseñas | Crear `has_reviews` (0/1) y dejar las notas vacías para imputarlas **dentro del `Pipeline`** | El vacío significa "anuncio nuevo", no un dato perdido | `add_review_flags` |
| 10 | `maximum_nights` tiene 21 anuncios con 2.147.483.647 (máximo entero) y 50 por encima de 1.125; `bedrooms` > 10 en 220 anuncios (129 son habitaciones privadas) | Marcar como vacío `maximum_nights > 1.125` y `bedrooms > 10` cuando supere a `accommodates` (124 casos) | Son centinelas o datos del edificio, no del anuncio | `mark_impossible_values` |
| 11 | `property_type` tiene 123 categorías (73 con < 30 anuncios) y `neighbourhood_cleansed` 371 barrios (146 con < 30) | Agrupar las categorías raras en "Other" **dentro del `Pipeline`**, con el umbral aprendido del entrenamiento | Categorías con pocos casos generan ruido y fallan con anuncios nuevos | (etapa 4, `features/`) |

**Decidido el 2026-10-30** (ver `specs/001-eda-limpieza-particion/spec.md`):

- Se incluyen las **siete ciudades**, también Buenos Aires y Belice; su error se reporta por separado.
- Se **excluyen** los 11.701 anuncios `source = "previous scrape"` (3.293 tenían precio).
- Las tasas a USD son las **oficiales del banco central** de cada país en la fecha del corte. **Falta que el grupo traiga los
  cinco valores** (BRL, MXN, ARS, COP, CLP) con su enlace.

## 5. Criterios de cierre

- ☒ `notebooks/02_eda.ipynb` corre de principio a fin sin errores (2026-10-30; su tabla final: 19 de 19 cifras coinciden).
- ☒ Unidad de análisis y `ID_COL` declarados por escrito (sección 3).
- ☐ Al menos **5 decisiones** con cifra, acción y motivo. *(Hay 11 propuestas; falta la aprobación del grupo.)*
- ☒ Datos personales identificados y plan para eliminarlos al cargar.
- ☒ Valores imposibles, centinelas y significado de los vacíos revisados.
- ☒ Fuga sospechada: lista escrita, aunque sea "ninguna, porque…".
- ☐ `reports/01_eda.md` completado. *(Cifras reproducidas y MAE de la línea base calculado; falta la aprobación del grupo y confirmar las tasas.)*
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó.
