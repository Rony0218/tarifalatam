# Informe del EDA

> Resultado de `notebooks/02_eda.ipynb`. Cada hallazgo termina en una decisión,
> y cada decisión está implementada con pruebas en `src/tarifalatam/data/`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`.

> **Estado: borrador (2026-10-30).** Las cifras salen de una exploración de los siete archivos de `data/raw/`.
> Se cierra cuando `notebooks/02_eda.ipynb` las reproduzca y el grupo apruebe las decisiones
> (`especificaciones/02-eda.md`, sección 4).

## Qué son los datos

- **Filas × columnas:** 194.628 anuncios × 90 columnas, de siete ciudades (Inside Airbnb, cortes del 14 al 25 de
  septiembre de 2026). Río 48.247 · São Paulo 44.080 · Ciudad de México 30.468 · Buenos Aires 29.753 · Bogotá 19.505 ·
  Santiago 18.904 · Belice 3.671.
- **Unidad de análisis (qué es una fila):** un anuncio (`id`, sin repetidos) en la fecha de corte de su ciudad.
- **¿Una entidad aparece en varias filas?** Sí, el anfitrión (`host_id`): 89.964 anfitriones, 2,2 anuncios cada uno en
  promedio (mediana 1, máximo 699). El 73 % tiene un solo anuncio, pero el 31 % de los anuncios es de anfitriones con 10 o
  más. 258 anfitriones aparecen en más de una ciudad. **Se parte por `host_id`.**
- **Objetivo y distribución:** `price`, precio por noche publicado, en la moneda de cada ciudad (BRL, MXN, ARS, COP, CLP y
  USD en Belice). Muy asimétrico: unos pocos anuncios cobran decenas de veces la mediana. En logaritmo la asimetría baja de
  23–160 a 0,5–2,1, por eso se modela `log(price_usd)`.

  | Mediana por noche (moneda local) | Vivienda completa | Habitación privada | Anuncios |
  |---|---|---|---|
  | Río de Janeiro (BRL) | 491 | 290 | 48.247 |
  | São Paulo (BRL) | 353 | 181 | 44.080 |
  | Ciudad de México (MXN) | 1.828 | 849 | 30.468 |
  | Buenos Aires (ARS) | 110.075 | 52.836 | 29.753 |
  | Bogotá (COP) | 181.250 | 90.000 | 19.505 |
  | Santiago (CLP) | 60.000 | 32.716 | 18.904 |
  | Belice (USD) | 403 | 260 | 3.671 |

  El 80,6 % de los anuncios es vivienda completa y el 18,4 % habitación privada; "habitación de hotel" (492) y
  "habitación compartida" (1.484) son raras.
- **Línea base** (resultado de una regla trivial): mediana de `price_usd` por `city` × `room_type`. **Su MAE está
  pendiente**: se calcula sobre el entrenamiento en el notebook 03, después de partir y de convertir a USD.

## Calidad de los datos

- **Precio como texto:** el 100 % de los 182.986 precios llega como `"$1,234.00"`; el símbolo `$` aparece aunque la moneda
  sea real, peso o dólar. La moneda real está en `price_quote_raw`.
- **Precios faltantes:** 11.642 anuncios (6,0 %) no tienen precio. No es un vacío al azar: el 64 % de ellos tiene el
  calendario cerrado, frente al 0,2 % de los que sí tienen precio. Son anuncios inactivos.
- **Precios imposibles:** 692 anuncios cobran más de 20 veces la mediana de su ciudad y 61 menos de una décima parte.
  Máximos: 258.514.678 COP por noche en Bogotá, 160.563.760 ARS en Buenos Aires.
- **Buenos Aires:** muchos precios repetidos son exactamente 100, 110, 120, 130 × 764,41 ARS (76.441; 84.085; 91.729;
  99.373). Parecen precios fijados en otra moneda y convertidos por Airbnb. La tasa con la que los pasemos a USD cambia
  mucho el resultado.
- **Columnas vacías:** 12 columnas están 100 % vacías en **las siete ciudades** (no solo en Bogotá): `bathrooms`,
  `host_since`, `host_response_time`, `host_response_rate`, `host_acceptance_rate`, `host_neighbourhood`,
  `host_total_listings_count`, `host_verifications`, `instant_bookable`, `neighbourhood`, `neighborhood_overview` y
  `calendar_updated`. `license` solo existe en Bogotá (84,9 %) y `neighbourhood_group_cleansed` solo en São Paulo y Belice.
- **Lo que se rescata:** el número de baños está en `bathrooms_text` (0,1 % vacío; 1.010 dicen "half-bath" sin número;
  8,0 % son baños compartidos). La antigüedad del anfitrión está en `hosts_time_as_host_years` (sin vacíos).
- **Centinelas:** `maximum_nights` vale 1.125 (valor por defecto de Airbnb) en 60.322 anuncios y 2.147.483.647 (el máximo
  entero) en 21.
- **Valores dudosos:** `bedrooms` vale 0 en 10.502 anuncios (sobre todo estudios y lofts: es plausible) y más de 10 en 220
  (129 son "habitación privada", que reportan las habitaciones del edificio).
- **Arriendos mensuales:** 6.103 anuncios (3,1 %) piden 30 noches o más; en Bogotá son el 16,9 %, con un precio mediano por
  noche de 94.102 COP frente a 170.000 COP del resto.
- **Vacíos que significan algo:** el 15,5 % de los anuncios no tiene reseñas; en todos ellos, y solo en ellos, las notas
  (`review_scores_*`) y `reviews_per_month` están vacías. Significa "anuncio nuevo".
- **Duplicados:** ningún `id` repetido; 26 filas idénticas salvo el `id`; 3.076 anuncios del mismo anfitrión con las
  mismas coordenadas, tipo, capacidad y precio (unidades gemelas de un mismo edificio). Al partir por `host_id` quedan
  siempre del mismo lado.
- **Constancia por anfitrión:** `host_is_superhost` no cambia nunca dentro de un anfitrión; `host_listings_count` cambia en
  el 0,18 % y la antigüedad en el 0,01 %. No hay ruido que reparar.
- **Fechas:** un solo corte por ciudad (`last_scraped` entre el 16 y el 29 de septiembre de 2026): no hay orden temporal
  que respetar al partir. Las reseñas van de 2010 a 2026 sin incoherencias (ninguna última reseña anterior a la primera).
- **Coordenadas:** todas dentro del área de su ciudad (Belice cubre el país entero).
- **Datos personales:** 10 columnas del anfitrión (nombre, descripción, ubicación, fotos y URLs) y datos de contacto en el
  texto libre (91 descripciones con teléfonos, 9 con correos).
- **Anuncios del corte anterior:** 11.701 (6,0 %) tienen `source = "previous scrape"`; el 71,9 % no tiene precio.

## Sospechas de fuga de información

- **Confirmadas (se eliminan):** `price_quote_price_per_night` es idéntica a `price` (razón 1,000 en 182.983 anuncios);
  `price_quote_total_price` es el total de esa misma cotización; `price_quote_raw` la contiene completa en JSON;
  `price_quote_checkin_date` y `price_quote_checkout_date` son de la misma cotización; `estimated_revenue_l365d` es
  `price` × `estimated_occupancy_l365d`.
- **Sospechosas (se miden con y sin ellas en la etapa 4):** `estimated_occupancy_l365d`, `availability_30/60/90/365`,
  `availability_eoy` y `has_availability`. Son consecuencia del precio: un precio alto deja el calendario libre.
- **Disponibles solo para anuncios que ya existen:** reseñas y notas. El inversionista que evalúa un inmueble para comprar
  no las tiene: la app debe funcionar sin ellas.

## Decisiones

> Mínimo **5**. Cada una con una cifra que la respalda, una acción concreta y un motivo.
> **Propuesta pendiente de aprobación del grupo.**

| # | Hallazgo (con cifra) | Decisión | Motivo |
|---|---|---|---|
| 1 | `price` es texto `"$1,234.00"` en el 100 % de los casos, en seis monedas | Convertir a número, pasar a USD con la tasa del día del corte (Belice ya está en USD) y modelar `log(price_usd)` | Una sola escala numérica; el logaritmo reduce la asimetría de 23–160 a 0,5–2,1 |
| 2 | 11.642 anuncios (6,0 %) sin precio; 64 % con calendario cerrado vs 0,2 % | Excluirlos | Son anuncios inactivos; imputar el objetivo sería inventarlo |
| 3 | `price_quote_price_per_night` = `price` (razón 1,000); `estimated_revenue_l365d` = precio × ocupación | Eliminar `price_quote_*` (5) y `estimated_revenue_l365d` al cargar | Contienen la respuesta |
| 4 | 10 columnas personales; 91 teléfonos y 9 correos en `description` | Eliminarlas al cargar, junto con el texto libre | Privacidad (principio V) |
| 5 | 89.964 anfitriones; 31 % de los anuncios es de anfitriones con ≥ 10 | Partir por `host_id` | Partir por fila inflaría la métrica |
| 6 | 12 columnas 100 % vacías; `bathrooms_text` con 0,1 % de vacíos | Eliminarlas; extraer baños y baño compartido de `bathrooms_text` | Rescatar la información que sí existe |
| 7 | 6.103 anuncios (3,1 %; 16,9 % en Bogotá) con `minimum_nights ≥ 30` | Excluirlos | Son arriendos mensuales, fuera del caso |
| 8 | 692 precios > 20 × la mediana de su ciudad y 61 < 0,1 × | Excluirlos como error de captura (umbral calculado en entrenamiento) | Dominarían el error |
| 9 | 15,5 % sin reseñas; notas vacías exactamente en ellos | `has_reviews` + imputar dentro del `Pipeline` | El vacío significa "anuncio nuevo" |
| 10 | `maximum_nights` = 2.147.483.647 en 21; `bedrooms` > 10 y > capacidad en 124 | Marcarlos como vacío | Centinelas o datos del edificio |
| 11 | 123 tipos de propiedad (73 con < 30) y 371 barrios (146 con < 30) | Agrupar raras en "Other" dentro del `Pipeline` | Ruido y categorías nuevas en la app |

## Qué queda abierto

- **Tasas de cambio:** falta elegir la fuente oficial y anotar el valor usado para cada ciudad. En Buenos Aires la tasa
  implícita de Airbnb (764,41 ARS) puede diferir mucho de la oficial.
- **Buenos Aires y Belice:** incluirlos o no (pendiente desde la especificación del proyecto).
- **`source = "previous scrape"`:** 3.293 anuncios con precio que vienen del corte anterior; ¿se quedan?
- **Umbral de precios extremos** (decisión 8): 20 × es una propuesta; con 10 × se excluirían 1.898.
- **Ocupación y disponibilidad:** medir en la etapa 4 si aportan sin hacer trampa (el auditor de fuga debe revisarlas).
- **Celdas pequeñas para la línea base:** "habitación de hotel" tiene 21 anuncios en Río y 29 en Bogotá; su mediana será
  inestable.
