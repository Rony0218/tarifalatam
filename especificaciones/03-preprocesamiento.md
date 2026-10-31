# Especificación · Etapa 3 · Preprocesamiento (limpieza y partición)

> Se llena **antes** de pedirle código a Claude, a partir de la tabla de decisiones de
> `especificaciones/02-eda.md`. Claude la lee y la implementa; ustedes revisan que el código haga
> **exactamente** esto (`material-del-curso/kit/checklist-revision-ia.md`).
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`, sección 4 · Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/data/`.

**Grupo:** TarifaLatam   **Fecha:** 2026-10-30   **Estado:** ☒ borrador  ☐ cerrada

> Llenado el 2026-10-30 con las reglas **implementadas** (`specs/001-eda-limpieza-particion/`). Las filas quitadas salen
> de una prueba en seco del notebook 03 con tasa ficticia: **los conteos no dependen de la tasa** (el umbral de precios es
> relativo a la mediana de cada ciudad), pero se confirman al ejecutar el notebook con las tasas oficiales (tarea T014).

## 1. Unidad de análisis y partición

- **Una fila es:** un anuncio de Airbnb (`id`) en la fecha de corte de su ciudad.
- **Entidad que se repite (columna):** `host_id` (89.964 anfitriones; hasta 699 anuncios cada uno)  ☐ no se repite → partir por fila es válido porque: no aplica
- **Se parte por:** ☒ grupo (`GroupShuffleSplit` para entrenamiento/prueba y `GroupKFold` para la validación cruzada) ☐ fila
- **Proporción de prueba:** 20 % de los **anfitriones** (≈ 20,5 % de las filas)   **Semilla:** 42
- **¿Hay orden temporal que respetar?** ☒ no ☐ sí → un solo corte por ciudad (septiembre de 2026)
- **Dónde se guarda la prueba:** `data/processed/` (cerrada: **no se mira** hasta la etapa 7)

## 2. Datos personales

| Columna | Qué es | Se elimina en | Prueba que lo verifica |
|---|---|---|---|
| `host_name`, `host_about`, `host_location` | Nombre, presentación y ubicación del anfitrión | `load_raw()` (primer paso al cargar) | `test_load_raw_adds_city_and_drops_personal_and_free_text` |
| `host_url`, `host_profile_url`, `host_profile_id`, `host_picture_url`, `host_thumbnail_url` | Perfil y fotos del anfitrión | `load_raw()` | `test_load_raw_adds_city_and_drops_personal_and_free_text` |
| `listing_url`, `picture_url` | Enlaces al anuncio y su foto | `load_raw()` | `test_load_raw_adds_city_and_drops_personal_and_free_text` |
| `name`, `description`, `neighborhood_overview` | Texto libre (91 descripciones con teléfonos, 9 con correos) | `load_raw()` | `test_load_raw_adds_city_and_drops_personal_and_free_text` |

## 3. Reglas de limpieza

Una fila por decisión del EDA. **Una función, una prueba.** Se marca como vacío lo imposible; no se borran filas sin criterio.

| # (de la tabla del EDA) | Columna(s) | Problema | Regla exacta (con el umbral o valor) | Función en `src/tarifalatam/data/cleaning.py` | Prueba en `tests/test_cleaning.py` |
|---|---|---|---|---|---|
| 1 | `price`, `price_quote_raw` | Texto `"$1,234.00"` en seis monedas | Quitar `$` y `,`; texto no numérico → vacío. Comprobar que la moneda de `price_quote_raw` coincide con la ciudad (si no, error). `price_usd = price_local / local_per_usd` de la ciudad; si falta la tasa, error | `parse_price`, `check_currencies`, `to_usd` | `test_parse_price_*`, `test_check_currencies_*`, `test_to_usd_*` |
| 2 | `price` | Sin precio = anuncio inactivo | Excluir si `price_local` está vacío → **3.234 filas** (tras quitar el corte anterior) | `drop_missing_price` | `test_drop_missing_price` |
| 3 | `price_quote_*` (5), `estimated_revenue_l365d` | Contienen el precio (fuga) | Eliminar las 6 columnas, después de comprobar la moneda | `drop_leakage_columns` | `test_drop_leakage_columns_*` |
| 4 | Datos personales y texto libre | Privacidad | Ver sección 2 | `load_raw` | `test_load_raw_*` |
| 5 | `host_id` | El anfitrión se repite | Partir por `host_id` (ver sección 1) | `split_by_host` | `tests/test_split.py` |
| 6 | 12 columnas vacías; `bathrooms_text` | Vacías; baños escritos como texto | Eliminar las 12. Baños: número del texto; "half-bath" sin número → 0,5; "No bathroom" → 0; `bathroom_shared` = 1 si dice "shared"; texto vacío → vacío | `drop_empty_columns`, `parse_bathrooms_text` | `test_drop_empty_columns_*`, `test_parse_bathrooms_text_*` |
| 7 | `minimum_nights` | Arriendos mensuales | Excluir si `minimum_nights >= 30`; vacío se conserva → **4.274 filas** (2.873 en Bogotá) | `drop_monthly_rentals` | `test_drop_monthly_rentals_*` |
| 8 | `price_usd` | Precios imposibles | Excluir fuera de [0,1 ×, 20 ×] la mediana de su ciudad, **aprendida solo con entrenamiento** → **506 filas en entrenamiento y 182 en prueba** | `fit_price_bounds`, `drop_price_outliers` | `test_fit_price_bounds_*`, `test_drop_price_outliers_*` |
| 9 | `number_of_reviews` | Sin reseñas = anuncio nuevo | `has_reviews` = 1 si `number_of_reviews > 0`, si no 0; las notas no se imputan aquí | `add_review_flags` | `test_add_review_flags_*` |
| 10 | `maximum_nights`, `bedrooms` | Centinelas y datos del edificio | `maximum_nights > 1.125` → vacío; `bedrooms > 10` **y** `> accommodates` → vacío. No quita filas | `mark_impossible_values` | `test_mark_impossible_values` |
| — | `source` | Anuncios del corte anterior (decisión del grupo) | Excluir `source == "previous scrape"` → **11.701 filas** | `drop_previous_scrape` | `test_drop_previous_scrape_*` |
| — | `price_usd` | Objetivo asimétrico | `log_price_usd = ln(price_usd)` | `add_target` | `test_add_target_is_log_of_price_usd` |

Resultado: de **194.628** anuncios cargados quedan **174.731** (138.891 en entrenamiento y 35.840 en prueba). El detalle por
ciudad queda en `reports/03_exclusiones.csv` al ejecutar el notebook 03. La decisión 11 del EDA (agrupar categorías raras)
va en la etapa 4, dentro del `Pipeline`.

## 4. Vacíos

| Columna | Qué significa el vacío | Tratamiento hoy | Tratamiento en la etapa 4 (dentro del `Pipeline`) |
|---|---|---|---|
| `review_scores_*`, `reviews_per_month` | ☒ no aplica (anuncio sin reseñas: 15,5 %) | ☒ dejar vacío + `has_reviews` | Imputar con la mediana del entrenamiento; `has_reviews` le dice al modelo que no había nota |
| `bathrooms_count`, `bathroom_shared` | ☒ no se anotó (0,1 %) | ☒ dejar vacío | Imputar con la mediana (conteo) y la moda (indicador) |
| `bedrooms` | ☒ no se anotó (122) o ☒ imposible (124 marcados) | ☒ dejar vacío | Imputar con la mediana por `room_type` o global |
| `maximum_nights` | ☒ imposible (centinela > 1.125: 50) | ☒ dejar vacío | Imputar con la mediana; evaluar si la variable aporta |
| `beds` | ☒ no se anotó (≈ 1,1 %) | ☒ dejar vacío | Imputar con la mediana |
| `license` | ☒ no aplica (solo existe en Bogotá: 84,9 %) | ☒ dejar vacío | Probablemente descartar (confunde con la ciudad); decidir en la etapa 4 |

> Imputar con medias o medianas **no se hace aquí**: depende del entrenamiento y va dentro del `Pipeline`.

## 5. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `data/raw/listings_<ciudad>_<fecha>.csv.gz` (siete archivos; nunca se modifican) |
| Salida: entrenamiento | `data/processed/train.csv.gz` |
| Salida: prueba (cerrada) | `data/processed/test.csv.gz` |
| Registro de exclusiones | `reports/03_exclusiones.csv` |
| Código que encadena los pasos | `src/tarifalatam/data/pipeline.py` |
| Código de limpieza | `src/tarifalatam/data/cleaning.py` |
| Código de partición | `src/tarifalatam/data/split.py` |
| Notebook que orquesta | `notebooks/03_preprocesamiento.ipynb` (solo llama a las funciones) |

## 6. Pruebas que deben existir

- ☒ **Partición:** ninguna entidad aparece en dos particiones y no se pierde ninguna fila (`tests/test_split.py`).
- ☒ **La prueba de partición falla** si se cambia temporalmente a partición por fila (comprobado el 2026-10-30: fallan 4 pruebas; restaurada).
- ☒ **Una prueba por regla de limpieza** de la sección 3, con un caso normal y un caso sucio hechos a mano.
- ☒ **Datos personales:** el resultado de cargar no contiene las columnas de la sección 2.
- ☒ `pytest` en verde desde la raíz del repo.

## 7. Criterios de cierre (H1)

- ☐ La limpieza corre **de principio a fin desde cero** (`data/processed/` borrada y regenerada con el notebook 03), sin pasos manuales.
- ☐ Unidad de análisis y forma de partir **escritas** (sección 1) y documentadas en `reports/01_eda.md`.
- ☐ `pytest` en verde.
- ☐ Conjunto de prueba guardado y sin mirar.
- ☐ `data/raw/` intacta y `.env` fuera de Git (`git status`).
- ☐ Todo subido a GitHub.
- ☐ Revisaron el código de Claude con `checklist-revision-ia.md` y cada integrante puede explicar una función.
- ☐ **Hallazgo que no esperaban** (para la puesta en común): _______________
