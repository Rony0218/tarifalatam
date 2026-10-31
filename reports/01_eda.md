# Informe del EDA

> Resultado de `notebooks/02_eda.ipynb`. Cada hallazgo termina en una decisión,
> y cada decisión está implementada con pruebas en `src/tarifalatam/data/`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`.

> **Cifras reproducidas por `notebooks/02_eda.ipynb` el 2026-10-30** (su tabla final compara 19 cifras con este informe:
> todas coinciden). Dos cifras que la tabla no cubría se corrigieron con el valor del notebook (ver "Qué queda abierto").
> El grupo aprobó las 11 decisiones el 2026-10-31 (`especificaciones/02-eda.md`, sección 4).

## Qué son los datos

- **Filas × columnas:** 194.628 anuncios × 90 columnas, de siete ciudades (Inside Airbnb, cortes del 14 al 25 de
  septiembre de 2026). Río 48.247 · São Paulo 44.080 · Ciudad de México 30.468 · Buenos Aires 29.753 · Bogotá 19.505 ·
  Santiago 18.904 · Belice 3.671.
- **Unidad de análisis (qué es una fila):** un anuncio (`id`, sin repetidos) en la fecha de corte de su ciudad.
- **¿Una entidad aparece en varias filas?** Sí, el anfitrión (`host_id`): 89.964 anfitriones, 2,2 anuncios cada uno en
  promedio (mediana 1, máximo 699). El 73 % tiene un solo anuncio, pero el 31 % de los anuncios es de anfitriones con 10 o
  más. 258 anfitriones aparecen en más de una ciudad. **Se parte por `host_id`.**
- **Objetivo y distribución:** `price`, precio por noche publicado, en la moneda de cada ciudad (BRL, MXN, ARS, COP, CLP y
  USD en Belice). Muy asimétrico: unos pocos anuncios cobran decenas de veces la mediana. En logaritmo la asimetría baja de
  23–160 a 0,5–2,1, por eso se modela `log(price_usd)`.

  | Mediana por noche (moneda local) | Vivienda completa | Habitación privada | Anuncios |
  |---|---|---|---|
  | Río de Janeiro (BRL) | 491 | 290 | 48.247 |
  | São Paulo (BRL) | 353 | 181 | 44.080 |
  | Ciudad de México (MXN) | 1.828 | 849 | 30.468 |
  | Buenos Aires (ARS) | 110.075 | 52.836 | 29.753 |
  | Bogotá (COP) | 181.250 | 90.000 | 19.505 |
  | Santiago (CLP) | 60.000 | 32.716 | 18.904 |
  | Belice (USD) | 403 | 260 | 3.671 |

  El 80,6 % de los anuncios es vivienda completa y el 18,4 % habitación privada; "habitación de hotel" (492) y
  "habitación compartida" (1.484) son raras.
- **Línea base** (resultado de una regla trivial): mediana de `price_usd` por `city` × `room_type`. **MAE = 55,96 ± 1,94
  USD por noche** sin Buenos Aires (5 pliegues por anfitrión, solo con el entrenamiento; pliegues: 57,95 · 54,45 · 54,77 ·
  58,64 · 53,99). Calculado en `notebooks/03_preprocesamiento.ipynb` el 2026-10-31 con las tasas de `config.py`
  (aprobadas por el grupo el 2026-10-31). Con las siete ciudades era 53,80 ± 2,74; no son comparables directamente,
  porque cambian las ciudades y el sorteo de la partición. El modelo de la etapa 4 tiene que bajar este número.

## Calidad de los datos

- **Precio como texto:** el 100 % de los 182.986 precios llega como `"$1,234.00"`; el símbolo `$` aparece aunque la moneda
  sea real, peso o dólar. La moneda real está en `price_quote_raw`.
- **Precios faltantes:** 11.642 anuncios (6,0 %) no tienen precio. No es un vacío al azar: el 64 % de ellos tiene el
  calendario cerrado, frente al 0,2 % de los que sí tienen precio. Son anuncios inactivos.
- **Precios imposibles:** 692 anuncios cobran más de 20 veces la mediana de su ciudad y 61 menos de una décima parte.
  Máximos: 258.514.678 COP por noche en Bogotá, 160.563.760 ARS en Buenos Aires.
- **Buenos Aires:** el **38,6 %** de los precios con precio son múltiplos exactos de 764,41 ARS (76.441; 84.085; 91.729;
  99.373 = 100, 110, 120, 130 unidades); con la tasa oficial del BCRA (1.516,30) solo el 0,2 %. Parecen precios fijados en
  otra moneda y convertidos a 764,41, casi la mitad de la tasa oficial. Con la tasa oficial la mediana de Buenos Aires es
  70 USD; con 764,41 sería 140 USD. **Es el mayor riesgo de la conversión a USD** (ver "Qué queda abierto").
- **Columnas vacías:** 12 columnas están 100 % vacías en **las siete ciudades** (no solo en Bogotá): `bathrooms`,
  `host_since`, `host_response_time`, `host_response_rate`, `host_acceptance_rate`, `host_neighbourhood`,
  `host_total_listings_count`, `host_verifications`, `instant_bookable`, `neighbourhood`, `neighborhood_overview` y
  `calendar_updated`. `license` solo existe en Bogotá (84,9 %) y `neighbourhood_group_cleansed` solo en São Paulo y Belice.
- **Lo que se rescata:** el número de baños está en `bathrooms_text` (0,1 % vacío; 1.010 dicen "half-bath" sin número;
  8,0 % son baños compartidos). La antigüedad del anfitrión está en `hosts_time_as_host_years` (sin vacíos).
- **Centinelas:** `maximum_nights` vale 1.125 (valor por defecto de Airbnb) en 60.322 anuncios y 2.147.483.647 (el máximo
  entero) en 21.
- **Valores dudosos:** `bedrooms` vale 0 en 10.502 anuncios (sobre todo estudios y lofts: es plausible) y más de 10 en 220
  (129 son "habitación privada", que reportan las habitaciones del edificio).
- **Arriendos mensuales:** 6.103 anuncios (3,1 %) piden 30 noches o más; en Bogotá son el 16,9 %, con un precio mediano por
  noche de 94.102 COP frente a 170.000 COP del resto.
- **Vacíos que significan algo:** el 15,5 % de los anuncios no tiene reseñas; en todos ellos, y solo en ellos, las notas
  (`review_scores_*`) y `reviews_per_month` están vacías. Significa "anuncio nuevo".
- **Duplicados:** ningún `id` repetido; 159 filas idénticas salvo el `id` (sin contar el texto libre, que se elimina al
  cargar); 3.076 anuncios del mismo anfitrión con las
  mismas coordenadas, tipo, capacidad y precio (unidades gemelas de un mismo edificio). Al partir por `host_id` quedan
  siempre del mismo lado.
- **Constancia por anfitrión:** `host_is_superhost` no cambia nunca dentro de un anfitrión; `host_listings_count` cambia en
  el 0,18 % y la antigüedad (`hosts_time_as_host_years`) en el 0,02 % de los anfitriones con varios anuncios. No hay ruido
  que reparar.
- **Fechas:** un solo corte por ciudad (`last_scraped` entre el 16 y el 29 de septiembre de 2026): no hay orden temporal
  que respetar al partir. Las reseñas van de 2010 a 2026 sin incoherencias (ninguna última reseña anterior a la primera).
- **Coordenadas:** todas dentro del área de su ciudad (Belice cubre el país entero).
- **Datos personales:** 10 columnas del anfitrión (nombre, descripción, ubicación, fotos y URLs) y datos de contacto en el
  texto libre (91 descripciones con teléfonos, 9 con correos).
- **Anuncios del corte anterior:** 11.701 (6,0 %) tienen `source = "previous scrape"`; el 71,9 % no tiene precio.

## Sospechas de fuga de información

- **Confirmadas (se eliminan):** `price_quote_price_per_night` es idéntica a `price` (razón 1,000 en 182.983 anuncios);
  `price_quote_total_price` es el total de esa misma cotización; `price_quote_raw` la contiene completa en JSON;
  `price_quote_checkin_date` y `price_quote_checkout_date` son de la misma cotización; `estimated_revenue_l365d` es
  `price` × `estimated_occupancy_l365d`.
- **Sospechosas (se miden con y sin ellas en la etapa 4):** `estimated_occupancy_l365d`, `availability_30/60/90/365`,
  `availability_eoy` y `has_availability`. Son consecuencia del precio: un precio alto deja el calendario libre.
- **Disponibles solo para anuncios que ya existen:** reseñas y notas. El inversionista que evalúa un inmueble para comprar
  no las tiene: la app debe funcionar sin ellas.

## Decisiones

> Mínimo **5**. Cada una con una cifra que la respalda, una acción concreta y un motivo.
> **Aprobadas por el grupo el 2026-10-31.**

| # | Hallazgo (con cifra) | Decisión | Motivo |
|---|---|---|---|
| 1 | `price` es texto `"$1,234.00"` en el 100 % de los casos, en seis monedas | Convertir a número, pasar a USD con la tasa del día del corte (Belice ya está en USD) y modelar `log(price_usd)` | Una sola escala numérica; el logaritmo reduce la asimetría de 23–160 a 0,5–2,1 |
| 2 | 11.642 anuncios (6,0 %) sin precio; 64 % con calendario cerrado vs 0,2 % | Excluirlos | Son anuncios inactivos; imputar el objetivo sería inventarlo |
| 3 | `price_quote_price_per_night` = `price` (razón 1,000); `estimated_revenue_l365d` = precio × ocupación | Eliminar `price_quote_*` (5) y `estimated_revenue_l365d` al cargar | Contienen la respuesta |
| 4 | 10 columnas personales; 91 teléfonos y 9 correos en `description` | Eliminarlas al cargar, junto con el texto libre | Privacidad (principio V) |
| 5 | 89.964 anfitriones; 31 % de los anuncios es de anfitriones con ≥ 10 | Partir por `host_id` | Partir por fila inflaría la métrica |
| 6 | 12 columnas 100 % vacías; `bathrooms_text` con 0,1 % de vacíos | Eliminarlas; extraer baños y baño compartido de `bathrooms_text` | Rescatar la información que sí existe |
| 7 | 6.103 anuncios (3,1 %; 16,9 % en Bogotá) con `minimum_nights ≥ 30` | Excluirlos | Son arriendos mensuales, fuera del caso |
| 8 | 692 precios > 20 × la mediana de su ciudad y 61 < 0,1 × | Excluirlos como error de captura (umbral calculado en entrenamiento) | Dominarían el error |
| 9 | 15,5 % sin reseñas; notas vacías exactamente en ellos | `has_reviews` + imputar dentro del `Pipeline` | El vacío significa "anuncio nuevo" |
| 10 | `maximum_nights` = 2.147.483.647 en 21; `bedrooms` > 10 y > capacidad en 124 | Marcarlos como vacío | Centinelas o datos del edificio |
| 11 | 123 tipos de propiedad (73 con < 30) y 371 barrios (146 con < 30) | Agrupar raras en "Other" dentro del `Pipeline` | Ruido y categorías nuevas en la app |

## Qué queda abierto

- **Tasas de cambio (cerrado el 2026-10-31):** tasa oficial del banco central para la fecha del corte. Los valores se
  consultaron en las fuentes oficiales el 2026-10-30, están en `config.py` con su fuente y el grupo los aprobó el
  2026-10-31 (tarea T014).
- **Buenos Aires, 764,41 frente a 1.516,30 (decidido el 2026-10-31):** el grupo decidió **excluir Buenos Aires** del
  modelo por el riesgo de la conversión a USD. Se consideró mantener la tasa oficial: en entrenamiento, los anuncios
  múltiplos de 764,41 cuestan en pesos lo mismo que los demás (mediana de vivienda completa 111.604 frente a 111.298
  ARS). El archivo crudo se conserva y este EDA lo sigue describiendo; la exclusión es una regla del preprocesamiento
  (29.753 anuncios, en `reports/03_exclusiones.csv`).
- **Decidido el 2026-10-30:** se incluyen las siete ciudades y se excluyen los 11.701 anuncios `previous scrape`.
  *(El 2026-10-31 se excluyó Buenos Aires: ver el punto anterior.)*
- **Correcciones hechas al reproducir con el notebook (2026-10-30):**
  - Filas idénticas salvo el `id`: **159**, no 26. El script exploratorio comparaba también `name` y `description`; el
    notebook ya no los tiene porque se eliminan al cargar. No hay decisión sobre ellas: al partir por anfitrión quedan del
    mismo lado.
  - Antigüedad del anfitrión que cambia entre sus anuncios: **0,02 %**, no 0,01 % (se mide sobre anfitriones con varios
    anuncios).
- **Umbrales congelados (2026-10-30):** 20 × la mediana para precios extremos (con 10 × se excluirían 1.898),
  30 noches para arriendos mensuales, 10 habitaciones y 1.125 noches máximas. Se eligieron mirando **todos** los datos
  en este EDA, antes de partir; desde ahora no se cambian mirando la prueba.
- **Ocupación y disponibilidad:** medir en la etapa 4 si aportan sin hacer trampa (ver la clasificación de columnas en
  `reports/04_features.md`).
- **Celdas pequeñas para la línea base:** "habitación de hotel" tiene 21 anuncios en Río y 29 en Bogotá; su mediana será
  inestable.

## Revisión de los subagentes (2026-10-30)

Se revisó el código del hito H1 con `auditor-de-fuga` (T029) y `revisor-de-codigo-ia` (T030). Ninguno encontró una fuga
confirmada ni un error que invalide el resultado. Lo que encontraron y lo que se hizo:

| Hallazgo | Gravedad | Qué se hizo |
|---|---|---|
| `price_usd`, `price_local`, `id`, `host_id` y las columnas posteriores al precio siguen en los conjuntos: si entran al modelo, hay fuga | Alta (etapa 4) | Lista de columnas prohibidas y sospechosas en `reports/04_features.md`; la lista explícita de variables y su prueba van en la especificación de la etapa 4 |
| La regla de extremos también quita filas de la prueba usando su precio real: el MAE de prueba será algo optimista | Media | Se acepta como regla de calidad; queda la instrucción de declararlo en `reports/07_validacion.md` |
| Los umbrales se eligieron viendo todos los datos | Media | Se declaran congelados (ver "Qué queda abierto") |
| Gemelos entre anfitriones distintos: la partición por anfitrión no los separa | Media | **Medido:** 939 anuncios (0,54 %) idénticos a menos de ≈ 11 m con otro anfitrión; 2.214 (1,26 %) a ≈ 110 m. Inside Airbnb además desplaza las coordenadas. Riesgo bajo: no se cambia la partición |
| Ninguna prueba demostraba que los límites de precio ignoran la prueba | Media | Prueba nueva `test_price_bounds_ignore_test_prices` (pasa) |
| `to_usd` solo detectaba tasas vacías; 0, negativas o con otra moneda pasaban | Media | Ahora se detiene en esos casos (4 pruebas nuevas) |
| `host_id` vacío no se controlaba | Baja | `split_by_host` se detiene con un mensaje (prueba nueva) |
| La línea base fallaba si una ciudad entera caía en un pliegue | Baja | Usa la mediana general como respaldo (prueba nueva y prueba con un MAE calculado a mano) |
| Docstring de `mark_impossible_values` citaba mal el EDA ("habitaciones de hotel") | Baja | Corregido: de los 220 con más de 10 habitaciones, 129 son "habitación privada" |
| "12 columnas vacías" frente a 11 en los datos | Baja | Aclarado: son 12 en los crudos; `neighborhood_overview` ya sale como texto libre |
| El registro de exclusiones guardaba `11701.0` | Baja | Ahora guarda enteros |
| `license` solo existe en Bogotá y es un número de registro | Baja | **Decidido el 2026-10-31:** se elimina (`drop_unused_columns`) |
| Las pruebas corrieron con pandas 3.0.3 y scikit-learn 1.9.0; `requirements.txt` fija 3.0.6 y 1.9.1 | Baja | Hecho el 2026-10-31: 76 pruebas en verde con las versiones de `requirements.txt` |
| La línea base usa límites de precio aprendidos con todo el entrenamiento | Baja | Efecto mínimo (la mediana es robusta); en la etapa 4 todo lo que aprende va dentro del `Pipeline` |
