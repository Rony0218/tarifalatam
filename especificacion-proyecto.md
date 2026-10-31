# Especificación del proyecto

> Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| Rony Guerrero | Por definir |
| Carolina Jiménez | Por definir |
| Jesica Tarazona | Por definir |
| Dulce Vargas | Por definir |
| Rafael Jaramillo | Por definir |

Nombre de la "startup": **TarifaLatam**   Repositorio (público): <https://github.com/Rony0218/tarifalatam>

## 2. Caso de negocio

- **Pregunta de negocio** (una frase, que alguien sin formación técnica entienda): ¿Cuánto debería cobrar
  por noche un inmueble de Airbnb en América Latina, según sus características, su barrio y su ciudad?
- **¿Quién usará el resultado y qué decisión tomará con él?** El anfitrión, para fijar su tarifa por noche
  (él conserva la decisión final). El inversionista, para estimar si un inmueble que piensa comprar para
  alquilar se pagaría.
- **¿Qué cuesta equivocarse?** (cuál error es peor y por qué): Sugerir un precio **muy bajo** hace perder
  ingreso en cada noche reservada. Sugerir uno **muy alto** deja el inmueble vacío y la plataforma lo baja en
  las búsquedas. Para el inversionista es peor **sobrestimar**: compraría un inmueble que no rinde lo esperado.

## 3. Datos

- **Fuente** (enlace de Kaggle, empresa, etc.): Inside Airbnb, <https://insideairbnb.com/get-the-data/>,
  archivos `listings.csv.gz` de septiembre de 2026 de Río de Janeiro, São Paulo, Ciudad de México, Buenos
  Aires, Bogotá, Santiago y Belice (enlaces exactos en el `README.md`).
- **Filas / columnas:** 194.628 anuncios (182.986 con precio) / 90 columnas por ciudad.
- **Variable objetivo** (columna que queremos predecir o describir): `price`, precio por noche publicado,
  convertido a USD con la tasa oficial del día del corte de cada ciudad (Belice ya viene en USD, según
  `price_quote_raw`). Se modela en logaritmo.
- **Tipo de problema:** ☐ clasificación  ☒ regresión  ☐ clusterización
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☐ no  ☒ sí → la partición
  será por: **`host_id`** (anfitrión). Hay ≈ 89.000 anfitriones y uno puede tener muchos anuncios.
- **Datos personales o confidenciales presentes:** ☐ no  ☒ sí → se eliminarán/anonimizarán así: se borran
  al inicio `host_name`, `host_about`, `host_location`, `host_url`, `host_profile_url`, `host_profile_id`,
  `host_picture_url`, `host_thumbnail_url`, `listing_url` y `picture_url`. `host_id` se conserva solo para
  partir los datos, nunca como variable del modelo. Los archivos crudos no se suben al repo (`data/raw/*` está
  en `.gitignore`).
- **Licencia o permiso de uso de los datos:** Creative Commons Atribución 4.0 Internacional (se cita a
  Inside Airbnb como fuente).

## 4. Métrica

- **Métrica principal:** **MAE en USD por noche**   **Por qué esa y no otra:** se lee directo en dinero
  ("el precio sugerido se equivoca en promedio X dólares"), que es como lo entiende el anfitrión. No se usa
  RMSE como principal porque los pocos precios extremos lo dominarían.
- **Métricas secundarias:** MAPE (un error de 20 USD no pesa igual en Bogotá que en Río) y R².
- **Línea base** (qué resultado obtiene una regla simple o un modelo trivial): la mediana del precio por
  ciudad y tipo de habitación (`room_type`). El valor se calcula en el EDA con el conjunto de entrenamiento.

## 5. Riesgos

- **Fuga de información posible:** `price_quote_checkin_date`, `price_quote_checkout_date`,
  `price_quote_total_price`, `price_quote_price_per_night` y `price_quote_raw` contienen el precio;
  `estimated_revenue_l365d` es precio × ocupación. Se eliminan. `estimated_occupancy_l365d` y las variables
  de disponibilidad son consecuencia del precio: el auditor de fuga debe revisarlas antes de usarlas.
- **Sesgos o equidad:** las ciudades tienen tamaños muy distintos (Río 48 mil, Belice 3,7 mil); el modelo
  puede ajustarse mejor a las grandes. Se reporta el error por ciudad. La tasa de cambio elegida afecta los
  precios en dólares, sobre todo en Buenos Aires por la inflación de Argentina.
- **Datos faltantes o de mala calidad:** el precio viene como texto (`"$1,234.00"`) en seis monedas; entre
  3,5 % y 8,5 % de los anuncios no tiene precio, según la ciudad (se excluyen); en las siete ciudades hay 12
  columnas 100 % vacías (`bathrooms`, `host_since`, `host_response_rate`…; el número de baños se rescata de
  `bathrooms_text` y la antigüedad del anfitrión de `hosts_time_as_host_years`); el 15,5 % de los anuncios no
  tiene reseñas; hay precios extremos (692 anuncios cobran más de 20 veces la mediana de su ciudad). Detalle en
  `reports/01_eda.md`.
- **Límites de lo que el modelo puede decir:** predice el precio **publicado**, no el que realmente se
  cobró; solo cubre siete ciudades grandes (no ciudades intermedias como Medellín o Cartagena); es una foto
  de septiembre de 2026, sin efecto de temporada.

## 6. Entregables y fechas

| Hito | Contenido | Fecha |
|---|---|---|
| H1 | Ficha aprobada, EDA y preprocesamiento reproducible | Cierre de la clase 2 (vie 30 oct) |
| H2 | Torneo, optimización con tracking, modelo registrado, repo modular, app local | Cierre de la clase 4 (jue 5 nov) |
| H3 | App desplegada y presentación (≤ 5 diapositivas) | Clase 5 (vie 6 nov) |
| H4 | Informe técnico final (hasta 8 días tras la última clase) | Domingo 15 nov |

## 7. Decisiones tomadas (agréguenlas a medida que avancen)

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-30 | Se descarta el dataset de hoteles de Kaggle (*Hotel Booking Demand*) | Está en la lista de datasets prohibidos del curso (`criterios-dataset.md`, "hoteles (reservas de playa en Portugal)") |
| 2026-10-30 | Se usan los anuncios de Inside Airbnb de las siete ciudades de América Latina disponibles | Ninguna ciudad sola llega al mínimo de 50.000 filas; juntas suman 194.628. No hay datos abiertos de países completos |
| 2026-10-30 | Los precios se convierten a USD con la tasa del día del corte de cada ciudad | Hay seis monedas distintas y el modelo necesita una sola escala |
| 2026-10-30 | Quedan pendientes de decidir en grupo: incluir o no Buenos Aires y Belice | Buenos Aires por la inflación; Belice por su tamaño pequeño y ser el único país angloparlante |
| 2026-10-30 | Se incluyen las siete ciudades (también Buenos Aires y Belice); se excluyen los anuncios `source = "previous scrape"`; las tasas a USD son las oficiales del banco central de cada país en la fecha del corte | El error se reporta por ciudad para vigilar Buenos Aires y Belice; los anuncios del corte anterior pueden tener precios desactualizados; la tasa oficial es verificable. Ver `specs/001-eda-limpieza-particion/spec.md` |
| 2026-10-30 | Corrección tras el EDA: Belice publica en USD (no en BZD); las columnas vacías están en las siete ciudades (no solo en Bogotá); sin reseñas hay 15,5 % (no 21 %) | Medido en los archivos de `data/raw/` (`price_quote_raw` trae la moneda); ver `reports/01_eda.md` |
