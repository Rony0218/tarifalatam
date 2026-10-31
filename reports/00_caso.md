# Ficha de caso

> Instrucciones y un ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** `tarifa-latam`

- **business_question:** *TarifaLatam* es una startup que asesora a anfitriones e inversionistas de
  alquiler de corta estancia en América Latina. Para cada inmueble queremos responder **¿cuánto debería
  cobrar por noche, según sus características, su barrio y su ciudad?** Hoy el anfitrión fija la tarifa a
  ojo o copiando a los vecinos. El modelo le sugiere un **precio de referencia en dólares** y el anfitrión
  conserva la decisión final. Al inversionista le sirve para estimar si un inmueble que piensa comprar para
  alquilar se pagaría.

- **dataset_source:** *Inside Airbnb* (<https://insideairbnb.com/get-the-data/>), archivos
  `listings.csv.gz` de septiembre de 2026 de las siete ciudades de América Latina que publica: Río de
  Janeiro, São Paulo, Ciudad de México, Buenos Aires, Bogotá, Santiago y Belice. **Licencia: Creative
  Commons Atribución 4.0 Internacional** (se puede redistribuir citando la fuente). Los enlaces de
  descarga están en el `README.md`.

- **dataset_rows:** 194.628 anuncios (182.986 con precio).

  | Ciudad | País | Moneda | Corte | Anuncios | Anfitriones |
  |---|---|---|---|---|---|
  | Río de Janeiro | Brasil | BRL | 2026-09-22 | 48.247 | 26.869 |
  | São Paulo | Brasil | BRL | 2026-09-14 | 44.080 | 15.883 |
  | Ciudad de México | México | MXN | 2026-09-23 | 30.468 | 13.381 |
  | Buenos Aires | Argentina | ARS | 2026-09-23 | 29.753 | 14.623 |
  | Bogotá | Colombia | COP | 2026-09-14 | 19.505 | 8.497 |
  | Santiago | Chile | CLP | 2026-09-23 | 18.904 | 9.920 |
  | Belice | Belice | USD* | 2026-09-25 | 3.671 | 1.054 |

  \* La moneda oficial de Belice es el BZD, pero sus precios en Inside Airbnb vienen en USD (lo dice `price_quote_raw`).

- **dataset_columns:** 90 (numéricas, categóricas, fechas y texto). Incluye datos personales del anfitrión
  (`host_name`, `host_about`, fotos y URLs de perfil) que se eliminan al inicio.

- **target:** `price`, precio por noche publicado, convertido a USD con la tasa oficial del día del corte de
  cada ciudad (se modela en logaritmo por su asimetría). Unidad de análisis: **un anuncio**. Un mismo
  anfitrión puede tener muchos anuncios (≈ 89.000 anfitriones), por eso la partición para validar se hace
  **por `host_id`**, nunca por fila.

- **problem_type:** regresión

- **primary_metric:** **MAE en USD por noche** (menor es mejor), porque el anfitrión la entiende
  directamente: "el precio sugerido se equivoca en promedio X dólares". Como controles se reportan **MAPE**
  (un error de 20 USD no pesa igual en Bogotá que en Río) y **R²**. Línea base: la **mediana del precio por
  ciudad y tipo de habitación**; si el modelo no la mejora, no aporta.

- **business_cost_note:** Equivocarse cuesta en las dos direcciones. Un precio sugerido **muy bajo** llena
  el calendario pero deja de ganar dinero en cada noche reservada. Uno **muy alto** deja el inmueble vacío
  y la plataforma lo baja en las búsquedas. Para el inversionista es peor sobrestimar: compraría un inmueble
  que no rinde lo esperado.

- **status:** borrador

- **reviewer_notes:**
