# Ficha de caso

> Instrucciones y un ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** `tarifa-latam`

- **business_question:** *TarifaLatam* es una startup que asesora a anfitriones e inversionistas de
  alquiler de corta estancia en América Latina. Para cada inmueble queremos responder **¿cuánto debería
  cobrar por noche, según sus características, su barrio y su ciudad?** Hoy el anfitrión fija la tarifa a
  ojo o copiando a los vecinos. El modelo le sugiere un **precio de referencia en dólares** y el anfitrión
  conserva la decisión final. El inversionista recibe ese mismo precio por noche como **un insumo más** de
  sus cuentas: el modelo no dice si un inmueble se paga, porque ocupación confiable, costos y valor de compra
  no están en los datos.

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

  **Desde el 2026-10-31 Buenos Aires se excluye del modelo** por el riesgo de la conversión a USD (sección 7 de
  `especificacion-proyecto.md`). El modelo se entrena con las otras seis ciudades: 148.234 anuncios tras la limpieza.

- **dataset_columns:** 90 (numéricas, categóricas, fechas y texto). Incluye datos personales del anfitrión
  (`host_name`, `host_about`, fotos y URLs de perfil) que se eliminan al inicio.

- **target:** `price`, precio por noche publicado, convertido a USD con la tasa oficial del día del corte de
  cada ciudad (se modela en logaritmo por su asimetría). Unidad de análisis: **un anuncio**. Un mismo
  anfitrión puede tener muchos anuncios (≈ 89.000 anfitriones), por eso la partición para validar se hace
  **por `host_id`**, nunca por fila.

- **problem_type:** regresión

- **primary_metric:** **MAE en USD por noche** (menor es mejor), porque el anfitrión la entiende
  directamente: "el precio sugerido se equivoca en promedio X dólares". Como controles se reportan **MAPE**
  (un error de 20 USD no pesa igual en Bogotá que en Río), **R²**, **sesgo medio por ciudad** y **costo 2 a 1**
  (`promedio de [2 × máx(sugerido − real, 0) + 1 × máx(real − sugerido, 0)]`), repetido con 1,5 a 1 y 3 a 1
  para ver si el ganador por MAE depende del supuesto. Línea base: la **mediana del precio por ciudad y tipo
  de habitación**. **Meta:** MAE al menos **20 % menor** que el de la línea base, con un intervalo del 95 % de
  la mejora que no incluya el cero, y ninguna ciudad peor que con la línea base.

- **business_cost_note:** Equivocarse cuesta en las dos direcciones. Un precio sugerido **muy bajo** llena
  el calendario pero deja de ganar dinero en cada noche reservada. Uno **muy alto** deja el inmueble vacío
  y la plataforma lo baja en las búsquedas. Para el inversionista es peor sobrestimar: compraría un inmueble
  que no rinde lo esperado. **La proporción 2 a 1 es un supuesto del grupo, no una medición:** Inside Airbnb no
  muestra cuánto cae la ocupación al subir el precio. Por eso orienta un control y no la métrica principal.

- **status:** borrador

- **reviewer_notes:**
