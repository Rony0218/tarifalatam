# Ficha del modelo

> Cifras de la prueba (`reports/07_metricas_test.json`, etapa 7) y del registro (`reports/08_registro.json`, etapa 8),
> medidas el 2026-11-05. Un documento corto para leer antes de usar el modelo: qué es, con qué datos, qué rendimiento tiene
> y **qué no hay que hacer con él**.

## Qué es

Sugiere el precio por noche, en USD, de un inmueble de Airbnb en seis ciudades de América Latina (Río de Janeiro, São Paulo,
Ciudad de México, Bogotá, Santiago y Belice), según sus características, su barrio y su ciudad. Lo usa el anfitrión para
fijar su tarifa (él conserva la decisión). Para el inversionista es un insumo más: **no dice si un inmueble se paga**.

- **Modelo:** LightGBM (522 árboles de hasta 215 hojas, parámetros optimizados con Optuna) dentro de un `Pipeline` de
  scikit-learn que agrupa barrios y tipos de propiedad raros y codifica las categorías. Aprende el logaritmo del precio.
  Lo eligió el grupo como excepción a la regla de la etapa 6 (T047), después de ver que empataba con el bosque aleatorio.
- **Registro:** `tarifalatam_precio_noche` versión 1, alias `champion` (MLflow **local**; exportado a `models/model.joblib`)
- **Regla de decisión:** precio = `exp` de la predicción del logaritmo, **sin corrección** (el factor de Duan empeoraba el
  MAE en los anfitriones reservados: +2,64 USD [+2,21; +3,06]), redondeado al dólar. Se muestra con un **rango típico** de
  su ciudad: el precio × los percentiles 25 y 75 de *real / sugerido* en los anfitriones reservados (por ejemplo, en Bogotá
  0,781 y 1,149). Ese rango se midió con el modelo ajustado al 75 % de los anfitriones (los reservados no los vio) y se
  aplica al modelo final, ajustado con el 100 %: es una aproximación, no una garantía.

## Datos de entrenamiento

- **Fuente y licencia:** Inside Airbnb, anuncios de septiembre de 2026 (CC BY 4.0)
- **Tamaño:** 118.513 filas de 53.385 anfitriones (prueba: 29.721 anuncios de 13.345 anfitriones)
- **Entradas:** 13 columnas que se conocen al publicar: ciudad, barrio, tipo de alojamiento, tipo de propiedad, latitud,
  longitud, huéspedes, habitaciones, camas, baños, noches mínimas, noches máximas y si el baño es compartido.
- **Partición:** por `host_id` (anfitrión); la prueba se abrió **una sola vez** (2026-11-05 18:09:33) y se leyó una segunda
  vez solo para comprobar que el archivo exportado es el evaluado (`reports/prueba_abierta.txt`)
- **Datos personales:** se eliminaron al cargar los datos del anfitrión (nombre, presentación, ubicación, fotos, URLs) y el texto libre del anuncio; `host_id` solo se usó para partir

## Rendimiento (prueba, entidades nunca vistas)

| Métrica | Valor | Intervalo del 95 % |
|---|---|---|
| MAE (USD por noche) | **41,40** | [38,29; 45,01] |
| Baseline (mediana por ciudad × tipo de habitación) | 57,44 | [53,18; 62,50] |
| Diferencia (modelo − baseline) | −16,04 (27,9 % menos) | [−17,84; −14,36] |
| MAPE (%) | 31,78 | — |
| R² (sobre el logaritmo) | 0,67 | — |
| Sesgo medio (sugerido − real) | −14,36 USD | — |
| MAE sin el filtro de precios extremos (29.807 anuncios) | 56,81 | — |

**Meta del grupo** (escrita antes de abrir la prueba): MAE al menos 20 % menor que el baseline, intervalo de la mejora sin
cero y ninguna ciudad peor. **Se cumple.** MAE por ciudad: São Paulo 21,35 · Bogotá 22,32 · Santiago 23,80 · Ciudad de
México 45,38 · Río de Janeiro 53,25 · **Belice 245,96**.

## Variables que más pesan

Promedio del aporte SHAP absoluto (en logaritmo; 0,10 ≈ 10 % del precio), sobre 2.000 anuncios del entrenamiento:
habitaciones (0,119), huéspedes (0,108), longitud (0,102), baños (0,093), latitud (0,079), barrio (0,065), ciudad (0,056),
tipo de propiedad (0,045), tipo de alojamiento (0,044), noches mínimas (0,042), baño compartido (0,035), noches máximas
(0,014) y camas (0,010). En resumen: **tamaño** y **ubicación**. Explican al modelo, no al mundo, y las variables de ubicación
se reparten el crédito entre sí.

## Límites y usos no recomendados

- Datos con los que se entrenó (¿sintéticos, de una época, de una región?): una sola foto (septiembre de 2026) de seis ciudades (Buenos Aires se excluyó por el riesgo de la conversión a USD); sin efecto de temporada ni ciudades intermedias
- Supuestos de negocio de los que depende (p. ej. una variable que debe conocerse al decidir): predice el precio **publicado**, no el cobrado; depende de la tasa de cambio usada para cada ciudad; supone que el anuncio se parece a los de Inside Airbnb (no ve fotos, reseñas, amenidades ni calendario)
- Atributos sensibles o de uso regulado: no usa datos del anfitrión. Usa la **ubicación** (coordenadas y barrio), así que reproduce los precios de mercado de cada barrio con sus desigualdades
- Qué **no** debe hacerse con este modelo: usarlo en **Belice** sin revisión (error de 246 USD por noche, y se queda corto en los inmuebles caros); usarlo para habitaciones de hotel (MAE de 149 USD) o compartidas (ahí la regla simple es mejor: 12,98 frente a 15,42 USD); fijar la tarifa sin que el anfitrión la revise; tomarlo como respuesta a si un inmueble se paga; usarlo fuera de las seis ciudades
- Lo que **no se evaluó** (estabilidad en el tiempo, otros grupos, deriva): cómo cambia con la temporada o con otra fecha de corte; otras ciudades; la ocupación que lograría un anuncio con el precio sugerido; el efecto de la tasa de cambio

## Reproducibilidad

Código en `src/`, pruebas en `tests/`, notebooks en `notebooks/` (03 → 07 → 08 → 09). El registro es local
(`mlflow_local.db`, fuera de Git); el archivo que usa la app es `models/model.joblib`, exportado del `champion`, con su
esquema en `models/input_schema.json`.
