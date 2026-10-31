# Informe del torneo de modelos

> Plantilla en blanco. Resultado de `notebooks/05_torneo.ipynb`. El torneo **descarta**: elige 1–2
> finalistas con evidencia, no un campeón definitivo. Guía:
> `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 2.

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos** (partidos por qué entidad): `GroupKFold` por `host_id`
- **Línea base** (qué es y cuánto da): mediana de `price_usd` por `city` × `room_type`; MAE =
- **Métrica principal** (la del negocio) y **métricas técnicas** que reportas: MAE en USD por noche; técnicas: MAPE, R², RMSE
  y sesgo medio (predicho − real, para ver si el modelo tiende a sobrestimar):
- **Variables usadas** (las decididas en `reports/04_features.md`):

## Tabla comparativa

> Media ± desviación entre pliegues. Ordena por la métrica principal.

| Modelo | Métrica de negocio (± ruido) | Segundos de ajuste |
|---|---|---|
| Línea base | | |
| | | |
| | | |
| | | |

## Métricas técnicas

> Media entre pliegues, con la misma validación. Todas se calculan en USD, después de volver del logaritmo
> (`exp` de la predicción). Guía: sección 2.2.

| Modelo | MAE (USD) | MAPE (%) | R² | RMSE (USD) | Sesgo medio (USD) | Peor ciudad (MAE) |
|---|---|---|---|---|---|---|
| Línea base | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

## ¿Coinciden los rankings de negocio y técnico?

> Posición de cada modelo (1 = mejor) en la métrica de negocio y en las técnicas.

| Modelo | Negocio (MAE) | MAPE | R² | RMSE |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

- **¿El mejor por MAE también es el mejor por MAPE?** (si no, gana en las ciudades caras y pierde en las baratas)
- **¿Hay modelos con MAE casi igual pero RMSE distinto? ¿Qué dice eso de los precios extremos?**
- **¿Hay alguna ciudad o tipo de habitación donde un modelo falle mucho más? ¿Qué le cuesta al anfitrión de ahí?**

## Comparación pareada de los mejores

> Todos se evaluaron en los mismos pliegues: ¿gana siempre el mismo?

| Mejor | Contra | Diferencia media | Pliegues que gana | Diferencia / ruido |
|---|---|---|---|---|
| | | | | |
| | | | | |

## ¿Cuánto vale la diferencia?

<!-- Traducción a dinero o volumen: métrica por decisión × decisiones al mes. -->

- **Decisiones estimadas al mes** (precios sugeridos):
- **Ahorro frente a la línea base:**
- **Diferencia entre el mejor y el siguiente:**

## Finalistas

| Finalista | Por qué (consistencia, métrica, tiempo, interpretabilidad) | Qué podría cambiar con la optimización |
|---|---|---|
| | | |
| | | |

**Modelos descartados y por qué:**

**Por qué el torneo no elige un campeón** (con tus palabras):

## Efectos que la métrica principal no ve

<!-- Por ejemplo: un modelo que sobrestima de forma sistemática (malo para el inversionista), o uno que va bien en
     promedio pero falla en Belice o en habitaciones de hotel, donde hay pocos anuncios. -->

-
