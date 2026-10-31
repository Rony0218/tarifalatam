# Informe de variables

> Plantilla en blanco. Resultado de `notebooks/04_features.ipynb`. Cada idea de variable es una
> **hipótesis medida** con la misma validación; se conserva solo si la mejora supera el ruido entre
> pliegues. Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 1.

## Cómo se midió

<!-- Modelo con parámetros fijos, métrica principal y de control, número y tipo de pliegues
     (por qué entidad se parte), semilla. Los MISMOS pliegues para todas las variantes. -->

- **Modelo (parámetros fijos):**
- **Métrica principal** (y por qué): MAE en USD por noche (el anfitrión la lee en dinero)
- **Métricas de control:** MAPE (compara ciudades con precios distintos) y R²
- **Pliegues** (cuántos y partidos por qué entidad): `GroupKFold` por `host_id`; número de pliegues:
- **Regla de decisión escrita antes de medir:**

## Tabla de ideas medidas

> La fila 0 es la **referencia** (las variables actuales). "Mejora / ruido" = mejora de la métrica
> principal dividida por su desviación entre pliegues; menor que ~1 está dentro del ruido.

| # | Idea (variable y cómo se calcula) | ¿Se conoce al predecir? | Métrica (± ruido) | Mejora / ruido | Decisión |
|---|---|---|---|---|---|
| 0 | **Referencia** | — | | 0 | — |
| 1 | | ☐ sí ☐ no | | | ☐ conservar ☐ descartar |
| 2 | | ☐ sí ☐ no | | | ☐ conservar ☐ descartar |
| 3 | | ☐ sí ☐ no | | | ☐ conservar ☐ descartar |

## Decisiones y motivos

<!-- Una línea por idea: qué decidiste, con qué cifra y por qué. Las ideas descartadas se anotan
     igual: documentan lo que ya probaste. -->

-
-
-

## Supuestos y riesgos

<!-- Variables que solo valen si cierto dato se conoce al momento de decidir; riesgos de fuga;
     lo que complicaría la app si se conserva. -->

- **Nunca son variables** (son el objetivo o identificadores): `price_usd`, `price_local`, `log_price_usd`, `id`, `host_id`,
  `scrape_id`, `last_scraped`, `calendar_last_scraped`, `source`. Hace falta una lista explícita de variables permitidas y
  una prueba que falle si entra una de estas (auditoría de fuga, 2026-10-30).
- **Medir con y sin ellas** (son consecuencia del precio o de la demanda): `estimated_occupancy_l365d`,
  `availability_30/60/90/365`, `availability_eoy`, `has_availability`, `number_of_reviews*`, `reviews_per_month`,
  `last_review`, `has_reviews`, `review_scores_*`, `first_review`.
- **Recomendación:** entrenar dos versiones, una con las sospechosas (solo para medir cuánto pesan) y otra sin ellas. Solo la
  segunda puede ir a la app: el inversionista evalúa inmuebles nuevos, sin reseñas ni ocupación.
- `license` solo existe en Bogotá (84,9 %): funciona como un indicador de ciudad. Descartarla o dejar solo `has_license`.
-

## Qué se lleva el pipeline final

<!-- La lista final de variables, y dónde está el código (`src/tarifalatam/features/`). -->
