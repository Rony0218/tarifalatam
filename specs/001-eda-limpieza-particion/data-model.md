# Data Model: hito H1

## Anuncio (una fila)

**Entrada** (`data/raw/listings_<ciudad>_<fecha>.csv.gz`): 90 columnas de Inside Airbnb. `load_raw` agrega `city` (el
nombre de la ciudad tomado del archivo).

**Salida** (`data/processed/train.csv.gz` y `test.csv.gz`): las columnas de entrada menos las eliminadas, más las creadas.

| Grupo | Columnas | Qué pasa |
|---|---|---|
| Identidad | `id`, `host_id`, `city` | Se conservan. `host_id` solo sirve para partir; **nunca** es variable del modelo |
| Datos personales (10) | `host_name`, `host_about`, `host_location`, `host_url`, `host_profile_url`, `host_profile_id`, `host_picture_url`, `host_thumbnail_url`, `listing_url`, `picture_url` | Se eliminan en `load_raw` |
| Texto libre (3) | `name`, `description`, `neighborhood_overview` | Se eliminan en `load_raw` |
| Fuga (6) | `price_quote_checkin_date`, `price_quote_checkout_date`, `price_quote_total_price`, `price_quote_price_per_night`, `price_quote_raw`, `estimated_revenue_l365d` | Se eliminan (después de comprobar la moneda con `price_quote_raw`) |
| Vacías (12) | `bathrooms`, `host_since`, `host_response_time`, `host_response_rate`, `host_acceptance_rate`, `host_neighbourhood`, `host_total_listings_count`, `host_verifications`, `instant_bookable`, `neighbourhood`, `neighborhood_overview`*, `calendar_updated` | Se eliminan |
| Precio | `price` (texto) | Se reemplaza por `price_local` (número), `price_usd` y `log_price_usd` (objetivo) |
| Baños | `bathrooms_text` | Se conserva y se crean `bathrooms_count` (número) y `bathroom_shared` (0/1) |
| Reseñas | `number_of_reviews` | Se crea `has_reviews` (0/1) |
| Centinelas | `maximum_nights`, `bedrooms` | Pasan a vacío según las reglas de abajo |
| Sospechosas de fuga | `estimated_occupancy_l365d`, `availability_*`, `has_availability` | Se conservan; se miden en la etapa 4 |
| Resto | barrio, tipo, capacidad, coordenadas, reseñas, notas, `license`, `source`, etc. | Pasan sin cambios |

\* `neighborhood_overview` ya sale en `load_raw` como texto libre. Que también esté en la lista de vacías no causa error.

### Reglas de validación y transformación

| Regla | Condición | Acción | Requisito |
|---|---|---|---|
| Precio a número | `price` como `"$1,234.00"` | Quitar `$` y `,`; si no es número, queda vacío | FR-003 |
| Moneda | Moneda de `price_quote_raw` (si no está vacía) distinta de `CITY_CURRENCY[city]` | **Error** que nombra la ciudad | FR-003 |
| A USD | Siempre | `price_usd = price_local / local_per_usd`; si la tasa de una ciudad presente es `None`, **error** | FR-003 |
| Sin precio | `price_local` vacío | Excluir la fila | FR-004 |
| Corte anterior | `source == "previous scrape"` | Excluir la fila | FR-011 |
| Baños | Texto con número (`"1.5 shared baths"`) | `bathrooms_count = 1.5`; `bathroom_shared = 1` si dice "shared" | FR-007 |
| Baños | `"Half-bath"`, `"Shared half-bath"`, `"Private half-bath"` | `bathrooms_count = 0.5` | FR-007 |
| Baños | `"No bathroom"` | `bathrooms_count = 0` | FR-007 |
| Arriendo mensual | `minimum_nights >= 30` | Excluir la fila | FR-008 |
| Centinela | `maximum_nights > 1125` | `maximum_nights` vacío | FR-009 |
| Imposible | `bedrooms > 10` y `bedrooms > accommodates` | `bedrooms` vacío | FR-009 |
| Reseñas | `number_of_reviews > 0` | `has_reviews = 1`; si no, 0. Las notas quedan como vienen | FR-010 |
| Extremos | `price_usd` fuera de [0,1 × mediana, 20 × mediana] de su ciudad (mediana del **entrenamiento**) | Excluir la fila, en ambos conjuntos | FR-014 |
| Objetivo | Siempre | `log_price_usd = ln(price_usd)` | FR-015 |

## Anfitrión

`host_id` (entero). Un anfitrión pertenece a **un solo** conjunto, aunque tenga anuncios en varias ciudades (258 casos).
Validación: `assert_disjoint_hosts(train, test)` falla si algún `host_id` está en ambos.

## Tabla de tasas de cambio (`FX_RATES` en `config.py`)

| Campo | Tipo | Regla |
|---|---|---|
| clave | nombre de la ciudad | Una por cada uno de los siete archivos |
| `currency` | texto | Igual a `CITY_CURRENCY` |
| `local_per_usd` | número > 0 o `None` | `None` = pendiente; la conversión falla |
| `date` | fecha | Fecha del corte de la ciudad (por ejemplo 2026-09-14 para Bogotá) |
| `source` | texto | Enlace al banco central |

Fechas de corte: Bogotá y São Paulo 2026-09-14; Río 2026-09-22; Ciudad de México, Buenos Aires y Santiago 2026-09-23;
Belice 2026-09-25 (USD, tasa 1).

## Límites de precio (`fit_price_bounds`)

Un diccionario `{city: (low_usd, high_usd)}`, aprendido del entrenamiento y guardado en el registro de exclusiones.

## Registro de exclusiones (`reports/03_exclusiones.csv`)

Una fila por paso que quita filas, por ciudad y por conjunto. Ver `contracts/processed-files.md`.

**Estado:** `before` − `removed` = `after`. El `after` de un paso es el `before` del siguiente.
