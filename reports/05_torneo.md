# Informe del torneo de modelos

> Resultado de `notebooks/05_torneo.ipynb`, ejecutado el 2026-10-31 (unos 40 segundos). El torneo **descarta**: elige 1–2
> finalistas con evidencia, no un campeón definitivo. Cifras por pliegue en `reports/05_torneo_tabla.csv` y por ciudad en
> `reports/05_torneo_por_ciudad.csv`. Especificación: `especificaciones/04-features-torneo-optimizacion.md`, sección 5.
> Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, sección 2.

## Reglas del torneo

- **Mismos datos y mismos pliegues para todos:** el entrenamiento completo (118.513 anuncios de 53.385 anfitriones) y los 5
  pliegues por `host_id` de `data/processed/folds.csv` (`GroupKFold` barajado con semilla 42), los mismos de la etapa 4. El
  notebook los lee y se detiene si no coinciden con el entrenamiento.
- **Línea base:** mediana de `price_usd` por `city` × `room_type`. **MAE = 55,90 ± 2,55 USD** en estos pliegues. En H1 dio
  55,96 ± 1,94 con otros pliegues, sin barajar.
- **Métrica principal:** MAE en USD por noche. **Técnicas:** MAPE, R² sobre el logaritmo, RMSE y sesgo medio (predicho −
  real; positivo = sobrestima). Además, el error por ciudad.
- **Variables usadas:** la referencia de 13 columnas, porque ninguna idea pasó la regla de la etapa 4 (`reports/04_features.md`,
  `config.FINAL_IDEAS = ()`). Sin columnas sospechosas.
- **Parámetros de partida, sin optimizar:** `Ridge(alpha=1.0)`; `RandomForestRegressor(n_estimators=200, min_samples_leaf=3,
  max_features=0.5)`; `LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31)`. Todos aprenden `log(price_usd)`.

## Tabla comparativa

> Media ± desviación entre pliegues, ordenada por la métrica principal.

| Modelo | MAE, USD (± ruido) | Mejor / peor pliegue | Segundos de ajuste por pliegue (varían entre corridas) |
|---|---|---|---|
| Bosque aleatorio | **39,67 ± 1,60** | 38,18 / 42,12 | 3,48 |
| LightGBM | 39,90 ± 1,73 | 38,29 / 42,47 | 0,59 |
| Ridge | 43,64 ± 1,88 | 41,80 / 45,93 | 0,55 |
| Línea base | 55,90 ± 2,55 | 53,17 / 58,91 | 0,07 |

## Métricas técnicas

> Media entre pliegues, con la misma validación. Todas en USD después de volver del logaritmo (`exp` de la predicción), salvo
> el R², que se calcula sobre el logaritmo.

| Modelo | MAE (USD) | MAPE (%) | R² (log) | RMSE (USD) | Sesgo medio (USD) | Peor ciudad (MAE) |
|---|---|---|---|---|---|---|
| Bosque aleatorio | 39,67 | 32,78 | 0,638 | 110,52 | −13,01 | Belice (204,10) |
| LightGBM | 39,90 | 32,70 | 0,636 | 111,05 | −14,03 | Belice (206,49) |
| Ridge | 43,64 | 37,08 | 0,569 | 121,94 | −15,41 | Belice (226,49) |
| Línea base | 55,90 | 43,54 | 0,278 | 152,90 | −32,64 | Belice (316,13) |

**Error por ciudad** (MAE medio en USD; entre paréntesis, el sesgo):

| Modelo | Belice | Bogotá | Ciudad de México | Río de Janeiro | Santiago | São Paulo |
|---|---|---|---|---|---|---|
| Bosque aleatorio | 204,10 (−72,92) | 24,05 (−6,99) | 41,74 (−13,17) | 55,48 (−20,41) | 22,69 (−6,42) | 22,12 (−5,82) |
| LightGBM | 206,49 (−82,71) | 24,03 (−7,63) | 41,80 (−14,23) | 55,38 (−21,35) | 23,78 (−7,24) | 22,40 (−6,47) |
| Ridge | 226,49 (−84,41) | 27,53 (−6,59) | 46,80 (−14,52) | 59,99 (−25,27) | 25,01 (−6,95) | 24,46 (−7,61) |
| Línea base | 316,13 (−192,76) | 32,04 (−18,29) | 56,48 (−30,98) | 75,35 (−46,75) | 43,80 (−28,29) | 29,12 (−13,88) |

Anuncios de validación por pliegue, en promedio: Belice 521, Bogotá 2.441, Ciudad de México 4.458, Río 6.818, Santiago
2.826 y São Paulo 6.639.

## ¿Coinciden los rankings de negocio y técnico?

> Posición de cada modelo (1 = mejor) en cada métrica.

| Modelo | Negocio (MAE) | MAPE | R² (log) | RMSE | \|Sesgo\| |
|---|---|---|---|---|---|
| Bosque aleatorio | 1 | 2 | 1 | 1 | 1 |
| LightGBM | 2 | 1 | 2 | 2 | 2 |
| Ridge | 3 | 3 | 3 | 3 | 3 |
| Línea base | 4 | 4 | 4 | 4 | 4 |

- **¿El mejor por MAE también es el mejor por MAPE?** Casi: LightGBM tiene un MAPE apenas menor (32,70 % frente a 32,78 %).
  Es un empate práctico; los dos primeros se intercambian según la métrica, y los dos últimos no cambian de puesto en ninguna.
- **¿Modelos con MAE casi igual pero RMSE distinto?** No: el bosque y LightGBM tienen RMSE muy parecidos (110,52 y 111,05).
  En todos los modelos el RMSE es casi el triple del MAE, es decir, hay errores grandes en pocos anuncios (los precios más
  altos). Por eso la métrica principal es el MAE.
- **¿Hay alguna ciudad donde un modelo falle mucho más?** Sí, **Belice**, con todos los modelos: un MAE de unos 205 USD por
  noche en los dos finalistas, frente a 22–56 USD en las otras ciudades, y un sesgo de −73 a −83 USD (subestima mucho). Belice
  tiene pocos anuncios (2.604 en el entrenamiento, 521 por pliegue) y precios más altos. Un anfitrión de Belice que siguiera el
  precio sugerido cobraría bastante menos de lo que se publica allí. Le sigue **Río de Janeiro** (unos 55 USD).

## Comparación pareada de los mejores

> Todos se evaluaron en los mismos pliegues. Diferencia positiva: gana el de la columna "Mejor".

| Mejor | Contra | Diferencia media (USD) | Pliegues que gana | Diferencia / ruido |
|---|---|---|---|---|
| Bosque aleatorio | LightGBM | 0,23 | 4 de 5 | 1,13 |
| Bosque aleatorio | Ridge | 3,97 | 5 de 5 | 6,91 |
| LightGBM | Ridge | 3,74 | 5 de 5 | 7,72 |

El bosque y LightGBM le ganan a Ridge con claridad (en los 5 pliegues, con varias veces el ruido). Entre ellos la diferencia es
pequeña (0,23 USD por noche) y apenas supera el ruido (1,13).

## ¿Cuánto vale la diferencia?

> Escala aprobada: la diferencia de MAE × 30 = USD por cada 30 noches reservadas de un anuncio. Es una escala para entender la
> cifra, no un pronóstico de ingresos: no se estimó cuántas noches se reservan.

- **Mejora frente a la línea base:** el bosque se equivoca 16,23 USD menos por noche (486,85 USD por cada 30 noches; 29,0 %
  menos error). LightGBM, 16,00 USD menos (480,08 USD por cada 30 noches; 28,6 %). Ridge, 12,26 USD menos (367,91 USD).
- **Diferencia entre el mejor y el siguiente:** bosque frente a LightGBM, 0,23 USD por noche, unos 6,8 USD por cada 30 noches
  (486,85 − 480,08).

## Finalistas

**Decisión del grupo (2026-10-31, tarea T041): pasan dos finalistas.**

| Finalista | Por qué (consistencia, métrica, tiempo, interpretabilidad) | Qué podría cambiar con la optimización |
|---|---|---|
| **Bosque aleatorio** | El menor MAE (39,67) y el menor sesgo (−13,01). Gana a LightGBM en 4 de 5 pliegues, con diferencia / ruido de 1,13: cumple, por poco, el criterio de consistencia | Su forma (profundidad, hojas mínimas, variables por corte) puede afinarse. Es el más lento de ajustar (3,48 s por pliegue) |
| **LightGBM** | A 0,23 USD del bosque, con el mejor MAPE (32,70 %), y unas 6 veces más rápido de ajustar (0,59 s por pliegue) | Tiene más hiperparámetros que afinar (tasa de aprendizaje, árboles, hojas, submuestreo), así que el orden podría cambiar |

**Modelos descartados y por qué:**

- **Ridge:** 43,64 USD, peor que los dos finalistas en los 5 pliegues (diferencia / ruido de 6,9 y 7,7). Es el más
  interpretable, pero cuesta unos 3,7 a 4,0 USD más de error por noche.
- **Línea base:** 55,90 USD. Sirve de referencia: cualquier modelo serio debe superarla, y los tres la superan con holgura.

**Por qué el torneo no elige un campeón:** el torneo compara configuraciones de partida, sin afinar. La optimización puede
cambiar el orden, sobre todo entre dos modelos separados por 0,23 USD. Además, qué tan bueno es el modelo elegido solo lo dice
la prueba final (etapa 7). Por eso el torneo **descarta** (Ridge y la línea base) y deja dos finalistas. Cuál pasa a la etapa 7
lo decide la comprobación en los anfitriones reservados de la etapa 6.

## Efectos que la métrica principal no ve

- **Todos los modelos subestiman** en promedio: el sesgo va de −13 USD (bosque) a −33 USD (línea base). Predecir en logaritmo y
  volver con la exponencial se acerca a la mediana, que es menor que el promedio en precios asimétricos. Para el inversionista
  es el error menos caro (es peor sobrestimar); para el anfitrión, el riesgo es cobrar de menos.
- **Belice** concentra el error: un MAE de unos 205 USD y un sesgo de −73 a −83 USD en los finalistas. El MAE global lo esconde,
  porque Belice es el 2,2 % de los anuncios. Hay que decirlo en la ficha del modelo y en la app.
- **Errores grandes en pocos anuncios:** el RMSE es casi el triple del MAE en todos los modelos.
