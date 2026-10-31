# Data model: columnas, variables nuevas y tablas de resultados

## 1. Entrenamiento (entrada)

`data/processed/train.csv.gz`: 118.513 anuncios × 65 columnas, 53.385 anfitriones, 6 ciudades. Una fila = un anuncio. Cada
columna está en **exactamente una** lista de `config.py` (comprobado el 2026-10-31: 18 + 23 + 13 + 11 = 65).

| Lista (`config.py`) | Columnas | Cuántas |
|---|---|---|
| `FORBIDDEN_FEATURES` | `log_price_usd`, `price_usd`, `price_local` (también `TARGET_COLUMNS`), `id`, `host_id`, `scrape_id`, `last_scraped`, `calendar_last_scraped`, `source`, `bathrooms_text`, `amenities`, `neighbourhood_group_cleansed`, `minimum_minimum_nights`, `maximum_minimum_nights`, `minimum_maximum_nights`, `maximum_maximum_nights`, `minimum_nights_avg_ntm`, `maximum_nights_avg_ntm` | 18 |
| `SUSPICIOUS_FEATURES` | `estimated_occupancy_l365d`, `availability_30`, `availability_60`, `availability_90`, `availability_365`, `availability_eoy`, `has_availability`, `number_of_reviews`, `number_of_reviews_ltm`, `number_of_reviews_l30d`, `number_of_reviews_ly`, `reviews_per_month`, `first_review`, `last_review`, `has_reviews`, `review_scores_rating`, `review_scores_accuracy`, `review_scores_cleanliness`, `review_scores_checkin`, `review_scores_communication`, `review_scores_location`, `review_scores_value`, `host_is_superhost` | 23 |
| `REFERENCE_CATEGORICAL` + `REFERENCE_NUMERIC` + `REFERENCE_BINARY` | `city`, `neighbourhood_cleansed`, `room_type`, `property_type` · `latitude`, `longitude`, `accommodates`, `bedrooms`, `beds`, `bathrooms_count`, `minimum_nights`, `maximum_nights` · `bathroom_shared` | 4 + 8 + 1 = 13 |
| `HOST_PROFILE_COLUMNS` (insumo de la idea 4) | `host_listings_count`, `calculated_host_listings_count`, `calculated_host_listings_count_entire_homes`, `calculated_host_listings_count_private_rooms`, `calculated_host_listings_count_shared_rooms`, `hosts_time_as_host_years`, `hosts_time_as_host_months`, `hosts_time_as_user_years`, `hosts_time_as_user_months`, `host_has_profile_pic`, `host_identity_verified` | 11 |

`amenities` es prohibida como columna cruda: solo entra a través de las variables de la idea 2. Los textos `t`/`f`
(`host_has_profile_pic`, `host_identity_verified`, `host_is_superhost`, `has_availability`) se convierten a 1/0; cualquier otro
valor queda vacío.

## 2. Variables nuevas (calculadas dentro del `Pipeline`)

| Idea | Transformador | Columna nueva | Regla | Vacío cuando |
|---|---|---|---|---|
| 1 | `CityCenterDistance` | `distance_to_center_km` | Haversine (radio 6.371 km) hasta (mediana de `latitude`, mediana de `longitude`) de la ciudad, **aprendidas en `fit`** | La ciudad no se vio al ajustar, o faltan coordenadas |
| 2 | `AmenityFeatures` | `amenities_count` | Número de elementos de la lista JSON (`[]` → 0) | El texto no se puede leer como lista |
| 2 | `AmenityFeatures` | `amenity_pool`, `amenity_air_conditioning`, `amenity_free_parking`, `amenity_gym`, `amenity_elevator`, `amenity_hot_tub` | 1 si la lista contiene exactamente `Pool`, `Air conditioning`, `Free parking on premises`, `Gym`, `Elevator`, `Hot tub` (`AMENITY_FLAGS`); si no, 0 | El texto no se puede leer como lista |
| 3 | `CapacityRatios` | `people_per_bedroom` | `accommodates / max(bedrooms, 1)` (0 habitaciones = estudio) | Falta `bedrooms` |
| 3 | `CapacityRatios` | `people_per_bathroom` | `accommodates / bathrooms_count` | `bathrooms_count` es 0 o falta |
| 3 | `CapacityRatios` | `beds_per_person` | `beds / accommodates` | `accommodates` es 0 o falta, o falta `beds` |
| 4 | `HostProfile` | `host_tenure_years`, `user_tenure_years` | años + meses / 12 (`hosts_time_as_host_*`, `hosts_time_as_user_*`) | Falta alguno de los dos |
| 4 | `HostProfile` | `host_has_profile_pic`, `host_identity_verified` | `t` → 1, `f` → 0 | Otro valor |
| 4 | (sin cambio) | los cinco `*listings_count*` | Se usan tal cual | — |
| 5 | `TargetEncoder` en el `ColumnTransformer` | `neighbourhood_price_level` | Promedio suavizado de `log_price_usd` del barrio, con validación cruzada interna al ajustar (`cv=KFold(5, shuffle=True, random_state=42)`) | — (barrio desconocido → promedio general) |
| Sospechosas | `SuspiciousFeatures` | `days_since_first_review`, `days_since_last_review` | Días entre la fecha y `last_scraped` del anuncio | El anuncio no tiene reseñas |
| Sospechosas | `SuspiciousFeatures` | `has_availability`, `host_is_superhost` | `t` → 1, `f` → 0 | Otro valor |

Las ideas que **aprenden** de los datos (1 y 5) lo hacen solo con la parte de entrenamiento de cada pliegue. Las demás no
aprenden nada, pero también van dentro del `Pipeline` (FR-008).

## 3. Preprocesamiento por tipo de columna y familia de modelo

| Tipo de columna | `linear` (Ridge) | `forest` (bosque) | `boosting` (LightGBM) |
|---|---|---|---|
| Categórica (`city`, `room_type`, `property_type`, `neighbourhood_cleansed`) | `RareCategoryGrouper(30)` → one-hot | `RareCategoryGrouper(30)` → ordinal | `RareCategoryGrouper(30)` → ordinal |
| Numérica | Mediana → escalado | Mediana | Sin imputar (LightGBM maneja vacíos) |
| Indicador 0/1 | Moda | Moda | Sin imputar |
| Codificación por objetivo (idea 5) | `TargetEncoder` → escalado | `TargetEncoder` | `TargetEncoder` |

La línea base (`BaselineRegressor`) usa solo `city` y `room_type`, sin preprocesamiento.

## 4. Asignación de pliegues

`data/processed/folds.csv` (no se sube a Git):

| Columna | Tipo | Regla |
|---|---|---|
| `id` | entero | Un anuncio del entrenamiento; único |
| `fold` | entero 0–4 | Pliegue de validación del anuncio. Todos los anuncios de un anfitrión tienen el mismo `fold` |

Validación al leer: el conjunto de `id` coincide con el del entrenamiento (o lo contiene, para el subconjunto de búsqueda); si no,
error.

## 5. Variantes, candidatos y ensayos

- **Variante** (etapa 4): nombre (`referencia`, `idea_1_distancia`, `idea_2_amenidades`, `idea_3_capacidad`,
  `idea_4_anfitrion`, `idea_5_barrio`, `final`, `final_con_sospechosas`), lista de ideas activas y si usa sospechosas. Se mide con
  el LightGBM fijo.
- **Candidato** (etapa 5): nombre (`linea_base`, `ridge`, `random_forest`, `lightgbm`), estimador de partida y familia.
- **Ensayo** (etapa 6): número, finalista, parámetros, métricas, estado (`completo` / `fallido`).
- **Decisión** (etapa 6): finalista elegido, parámetros (de partida u optimizados), intervalo, regla y resultado.

Transiciones de la etapa 6: `búsqueda` (30 ensayos) → `comprobación` (partida contra optimizados en los reservados) →
`decisión` (`optimizados` si todo el intervalo < 0; si no, `partida`) → con dos finalistas, `elección` entre los dos.

Las tablas de resultados (CSV, JSON y ejecuciones de MLflow) están en [contracts/output-files.md](contracts/output-files.md).
