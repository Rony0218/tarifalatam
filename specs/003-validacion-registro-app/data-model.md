# Data Model: etapas 7 a 9

## 1. Columnas de entrada (las 13 de la referencia)

| Columna | Tipo | Obligatoria | Rango posible (error) | Fuera de lo observado |
|---|---|---|---|---|
| `city` | categórica | **sí** | una de las 6 ciudades del entrenamiento | — |
| `neighbourhood_cleansed` | categórica | no («No sé») | debe pertenecer a `city` si se conoce | barrio no visto → advertencia |
| `room_type` | categórica | no | — | categoría no vista → advertencia |
| `property_type` | categórica | no | — | categoría no vista → advertencia |
| `latitude` | número | no | −90 a 90 | fuera de la caja de su ciudad → advertencia |
| `longitude` | número | no | −180 a 180 | ídem |
| `accommodates` | entero | no | 1 a 16 | advertencia |
| `bedrooms` | entero | no | 0 a 10 | advertencia |
| `beds` | entero | no | 0 a 50 | advertencia |
| `bathrooms_count` | número | no | 0 a 20 | advertencia |
| `minimum_nights` | entero | no | 1 a 29 | advertencia |
| `maximum_nights` | entero | no | 1 a 1.125 | advertencia |
| `bathroom_shared` | 0/1 | no | 0 o 1 | — |

`host_id` e `id` **no** son entradas: solo sirven para partir y para unir pliegues.

## 2. Decisiones congeladas (`reports/07_metricas_test.json`, clave `decisiones`)

| Campo | Valor |
|---|---|
| `modelo_final` | `"lightgbm"` |
| `parametros` | los de `reports/06_best_params.json` (`parametros`) + `parametros_fijos` |
| `origen_parametros` | `"optimizados"` |
| `excepcion_t047` | texto de `config.STAGE7_GROUP_NOTE` |
| `correccion_log` | `{"evaluada": true, "factor": <float>, "intervalo": [low, high], "se_usa": <bool>}` (se llena en la sección 2 del notebook, **antes** de abrir la prueba) |
| `rango_tipico` | `{ciudad: [p25, p75]}` de la razón real / sugerido en los reservados (sección 2 del notebook, antes de abrir la prueba) |
| `metrica_principal` | `"MAE en USD por noche"` |
| `forma_del_precio` | `"puntual redondeado + rango p25–p75 por ciudad (reservados)"` |
| `meta` | las tres condiciones (texto) |
| `congeladas_el` | `"2026-11-05 17:42 (UTC−5)"` |

## 3. Resultado de la prueba (`reports/07_metricas_test.json`, clave `prueba`)

- `abierta_el`: fecha y hora de la marca.
- `anuncios`, `anfitriones`.
- `modelo` y `linea_base`: `mae`, `mape`, `rmse`, `bias`, `r2_log`, `cost_2_1`, `cost_1.5_1`, `cost_3_1`, y
  `mae_ic95` = `[low, high]`.
- `diferencia_mae` (modelo − línea base): `media`, `ic95`; `mejora_pct` = `(1 − mae_modelo / mae_linea_base) × 100`.
- `meta`: `a_20pct`, `b_intervalo`, `c_ciudades` (booleanos), `ciudades_peores` (lista) y `cumple`.
- `por_ciudad`: tabla de `segment_errors` del modelo y de la línea base.
- `sensibilidad_sin_filtro`: `anuncios`, `mae_modelo`, `mae_linea_base`, `precios_no_positivos`.

## 4. Esquema de entrada (`models/input_schema.json`)

| Clave | Contenido |
|---|---|
| `target` | `"log_price_usd"` (el modelo predice el logaritmo) |
| `numeric`, `categorical`, `binary` | las listas de `config.py` |
| `required` | `["city"]` |
| `categories` | categorías vistas en el entrenamiento, por columna categórica |
| `most_frequent` | la categoría más frecuente de cada columna (valor por defecto del formulario) |
| `neighbourhoods_by_city` | `{ciudad: [barrios]}` |
| `neighbourhood_coords` | `{ciudad: {barrio: [lat_mediana, lon_mediana]}}` |
| `city_box` | `{ciudad: [lat_min, lat_max, lon_min, lon_max]}` (observado) |
| `valid_range` | tabla de la sección 1 (posible) |
| `observed_range`, `median`, `integer_columns` | del entrenamiento |
| `correction_factor` | 1,0 si no se aprueba el factor |
| `price_range_ratios` | `{ciudad: [p25, p75]}` |
| `city_warnings` | `{"belize": "<texto con el MAE medido en la prueba>"}` |
| `city_labels`, `labels`, `app_title`, `responsible_use` | textos en español para la app |

**Regla de validación** (`validate_inputs`): falta una columna o `city` vacía/desconocida → error; un número que no es número o
fuera de `valid_range` → error; barrio de otra ciudad → error; categoría no vista, número fuera de lo observado o
coordenadas fuera de la caja de la ciudad → advertencia.

## 5. Precio sugerido (salida de `predict_price`)

Una fila por fila de entrada: `price_usd` (entero), `low_usd`, `high_usd` (enteros), `city`. Las advertencias van en
`resultado.attrs["warnings"]`.

## 6. Registro (`reports/08_registro.json`)

`tracking` (`"local"`), `experimento` (`"tarifalatam-modelo-final"`), `modelo_registrado` (`"tarifalatam_precio_noche"`),
`version`, `alias` (`"champion"`), `run_id`, `registrado_el`, `artefactos` (ruta relativa), `ida_y_vuelta`
(`{"filas": 200, "iguales": 200}`: cuántas de las 200 predicciones coinciden).
