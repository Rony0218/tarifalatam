# Contrato: archivos que produce el hito H1

## `data/processed/train.csv.gz` y `data/processed/test.csv.gz`

- Una fila por anuncio. Las mismas columnas en ambos, en el mismo orden.
- **Siempre presentes:** `id`, `host_id`, `city`, `room_type`, `price_local`, `price_usd`, `log_price_usd`, `bathrooms_count`,
  `bathroom_shared`, `has_reviews`.
- **Nunca presentes:** las 10 columnas personales, `name`, `description`, `neighborhood_overview`, las 6 de fuga, las 12 vacías y
  `price` (texto).
- Ningún `host_id` en ambos archivos.
- `price_usd > 0` y `log_price_usd` finito en todas las filas.
- `minimum_nights < 30` y `source != "previous scrape"` en todas las filas.
- No se suben a Git: hoy `.gitignore` solo ignora `data/raw/*`, así que esta pieza agrega `data/processed/*` (conservando
  `!data/processed/.gitkeep`). Se regeneran con `notebooks/03_preprocesamiento.ipynb`.
- **`test.csv.gz` no se abre** hasta la etapa 7: el notebook 03 solo cuenta sus filas y anfitriones.

## `reports/03_exclusiones.csv`

| Columna | Significado |
|---|---|
| `step` | Nombre del paso (`previous_scrape`, `missing_price`, `monthly_rental`, `price_outlier`…) |
| `split` | `all` (antes de partir), `train` o `test` |
| `city` | Ciudad |
| `before` | Filas antes del paso |
| `removed` | Filas quitadas por el paso |
| `after` | `before − removed` |

Además, una línea por ciudad con los límites de precio aprendidos (`step = price_bounds`, columnas `low_usd`, `high_usd`).

## `reports/01_eda.md` (actualización)

- Las cifras confirmadas por el notebook 02.
- El MAE en USD de la línea base (promedio ± desviación entre 5 pliegues por anfitrión, solo con el entrenamiento).
