# Ficha del modelo

> Plantilla en blanco. Complétala a mano con **tus** resultados (los de la prueba de `reports/07_metricas_test.json`).
> Un documento corto que cualquiera pueda leer antes de usar el modelo: qué es, con qué datos, qué rendimiento tiene
> y **qué no hay que hacer con él**.

## Qué es

Sugiere el precio por noche, en USD, de un inmueble de Airbnb en seis ciudades de América Latina (Río de Janeiro, São Paulo, Ciudad de México, Bogotá, Santiago y Belice), según sus características,
su barrio y su ciudad. Lo usan el anfitrión, para fijar su tarifa (él conserva la decisión), y el inversionista, para estimar si
un inmueble se pagaría.

- **Modelo:** _______________
- **Registro:** _______________ versión _______________, alias `champion` (Databricks o local)
- **Regla de decisión:** _______________  (cómo se entrega el precio: `exp` de la predicción del logaritmo, con o sin corrección, y si se muestra un rango)

## Datos de entrenamiento

- **Fuente y licencia:** Inside Airbnb, anuncios de septiembre de 2026 (CC BY 4.0)
- **Tamaño:** _______________ filas de _______________ entidades
- **Partición:** por `host_id` (anfitrión); la prueba se abrió **una sola vez**
- **Datos personales:** se eliminaron al cargar los datos del anfitrión (nombre, presentación, ubicación, fotos, URLs) y el texto libre del anuncio; `host_id` solo se usó para partir

## Rendimiento (prueba, entidades nunca vistas)

| Métrica | Valor | Intervalo del 95 % |
|---|---|---|
| MAE (USD por noche) | | |
| Baseline (mediana por ciudad × tipo de habitación) | | |
| MAPE (%) | | |
| R² | | |

## Variables que más pesan

_______________

## Límites y usos no recomendados

- Datos con los que se entrenó (¿sintéticos, de una época, de una región?): una sola foto (septiembre de 2026) de seis ciudades (Buenos Aires se excluyó por el riesgo de la conversión a USD); sin efecto de temporada ni ciudades intermedias
- Supuestos de negocio de los que depende (p. ej. una variable que debe conocerse al decidir): predice el precio **publicado**, no el cobrado; depende de la tasa de cambio usada para cada ciudad; _______________
- Atributos sensibles o de uso regulado: _______________
- Qué **no** debe hacerse con este modelo: _______________
- Lo que **no se evaluó** (estabilidad en el tiempo, otros grupos, deriva): _______________

## Reproducibilidad

Código en `src/`, pruebas en `tests/`, notebooks en `notebooks/`.
