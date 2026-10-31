# Feature Specification: Variables, torneo de modelos y optimización con seguimiento (hito H2, etapas 4 a 6)

**Feature Branch**: `claude/002-features-torneo-optimizacion-b44fc1` (rama del worktree; no se crea otra)

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Etapas 4 a 6 de TarifaLatam (hito H2, parte de clase 3): variables, torneo de modelos y
optimización con seguimiento local. Entrada obligatoria y aprobada por el grupo el 2026-10-31:
especificaciones/04-features-torneo-optimizacion.md (secciones 0 a 10). […] La prueba (test.csv.gz) no se abre. No crear
rama nueva: se trabaja en la rama actual del worktree."

**Fuentes que manda esta especificación**: `especificaciones/04-features-torneo-optimizacion.md` (aprobada por el grupo el
2026-10-31, sin cambios; **sus cifras, listas, parámetros y rangos son el contrato**), `especificacion-proyecto.md`,
`.specify/memory/constitution.md` (versión 0.3.0), `reports/01_eda.md`, `reports/04_features.md` y
`especificaciones/03-preprocesamiento.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Un conjunto de variables decidido con evidencia (Priority: P1)

Quien modela necesita saber **qué columnas puede usar el modelo** y **qué variables nuevas valen la pena**. Cada idea de variable
se mide contra una referencia con el mismo modelo, los mismos cinco pliegues por anfitrión y la misma métrica, y se conserva solo
si cumple la regla escrita antes de medir. Las columnas que contienen la respuesta nunca entran, y las que son consecuencia del
precio o de la demanda (ocupación, disponibilidad, reseñas) se miden aparte y no pasan a la app.

**Why this priority**: el torneo y la optimización dependen de la lista de variables. Una columna prohibida que se cuele infla
todas las cifras siguientes (fuga), y una variable que la app no puede pedir deja el modelo inservible para el inversionista.

**Independent Test**: ejecutar el notebook 04 desde cero y comprobar que la tabla de ideas tiene la referencia, las cinco ideas,
el conjunto final y la medición con sospechosas, cada una con los cinco pliegues; que cada decisión coincide con la regla; y que
la prueba automática de columnas pasa.

**Acceptance Scenarios**:

1. **Given** el entrenamiento limpio, **When** se calculan los pliegues, **Then** cada anfitrión queda entero en un solo pliegue,
   cada anuncio en exactamente uno, y la asignación queda guardada para las etapas 5 y 6.
2. **Given** una idea con mejora / ruido de 1,3 cuyas columnas se conocen al predecir, **When** se aplica la regla, **Then** se
   conserva; **Given** otra con 0,8, **Then** se descarta y queda anotada con su cifra.
3. **Given** que alguien agrega `price_usd` (o cualquier columna prohibida) a la lista de variables, **When** se construye el
   modelo, **Then** se detiene con un mensaje que nombra la columna.
4. **Given** la medición con las columnas sospechosas, **When** termina, **Then** el informe dice cuánto bajó el MAE y que esa
   versión no se usa en el torneo, la optimización ni la app.

---

### User Story 2 - Un torneo que elige 1–2 finalistas, no un campeón (Priority: P2)

El grupo compara una línea base y tres modelos (Ridge, bosque aleatorio y LightGBM) con las mismas variables y los mismos
pliegues. Ve el MAE en USD de cada modelo con su ruido entre pliegues, las métricas técnicas, el error por ciudad, la comparación
pliegue a pliegue de los mejores y cuánto vale la diferencia en dinero. Con eso elige uno o dos finalistas y explica por qué.

**Why this priority**: es el segundo entregable del hito H2 ("al menos 3 modelos con la misma validación") y decide qué se
optimiza.

**Independent Test**: con el conjunto final de variables (o la referencia, si la etapa 4 no ha terminado), ejecutar el notebook 05
y comprobar que hay cinco cifras por modelo, que todos usan la asignación de pliegues guardada y que `reports/05_torneo.md`
nombra 1–2 finalistas con su motivo.

**Acceptance Scenarios**:

1. **Given** los cuatro candidatos, **When** corre el torneo, **Then** se guarda una fila por modelo y pliegue con MAE, MAPE, R²,
   RMSE, sesgo y segundos de ajuste, y una fila por modelo, pliegue y ciudad con su MAE y su sesgo.
2. **Given** los tres modelos con menor MAE, **When** se comparan de a pares, **Then** se ve la diferencia media, en cuántos
   pliegues gana cada uno y la diferencia / ruido.
3. **Given** dos modelos con diferencia / ruido ≤ 1, **When** se eligen finalistas, **Then** se tratan como empate: pasa el más
   simple o pasan los dos.
4. **Given** un modelo que no supera a la línea base, **When** se redacta el informe, **Then** se dice y se explica por qué.

---

### User Story 3 - Una optimización acotada, registrada y comprobada con honestidad (Priority: P3)

El grupo busca mejores hiperparámetros para los finalistas con un presupuesto fijo de 30 ensayos por finalista. Cada ensayo queda
registrado en el seguimiento local con sus parámetros y métricas. Antes de buscar se reserva el 25 % de los anfitriones, que la
búsqueda nunca ve, y ahí se comprueba si los parámetros optimizados mejoran de verdad a los de partida, con un intervalo del 95 %
que remuestrea anfitriones completos. La decisión sigue una regla escrita antes de mirar.

**Why this priority**: cierra la parte de clase 3 del hito H2 ("optimización con tracking"). Depende de los finalistas.

**Independent Test**: con un finalista, ejecutar el notebook 06 y comprobar en la interfaz local de seguimiento que hay una ejecución
por ensayo (como máximo 30), que los anfitriones reservados no aparecen en la búsqueda, y que `reports/06_best_params.json` guarda
los parámetros elegidos, el intervalo y la regla aplicada.

**Acceptance Scenarios**:

1. **Given** el entrenamiento, **When** se reservan anfitriones, **Then** el 25 % de los anfitriones queda fuera de la búsqueda y
   ninguno aparece en los dos lados.
2. **Given** un presupuesto de 30 ensayos, **When** termina la búsqueda, **Then** hay exactamente tantas ejecuciones registradas
   como ensayos hechos, cada una con hiperparámetros, MAE medio y su desviación, métricas técnicas, tiempo y etiquetas.
3. **Given** un intervalo del 95 % de la diferencia de error entre −1,2 y −0,3 USD, **When** se aplica la regla, **Then** se usan los
   parámetros optimizados; **Given** un intervalo entre −0,8 y +0,4, **Then** se usan los de partida.
4. **Given** el notebook 06 ejecutado, **When** se revisa, **Then** la mejor puntuación de la búsqueda no aparece como resultado
   (es optimista) y la prueba no se abrió.

---

### Edge Cases

- **Un pliegue sin una categoría:** un barrio o tipo de propiedad que no está en la parte de entrenamiento de un pliegue se trata
  como "Other" (desconocido); el modelo no falla.
- **Divisiones por cero:** 0 habitaciones = estudio (cuenta como 1); 0 baños deja vacía `people_per_bathroom`; 0 de capacidad
  deja vacía `beds_per_person`.
- **Amenidades:** una lista vacía (134 anuncios) da conteo 0 e indicadores en 0; un texto que no se puede leer como lista deja
  vacíos el conteo y los indicadores (se imputan dentro del modelo).
- **Belice:** sus anuncios cubren un país entero (la distancia a un único centro dice poco) y son pocos (2.604 en el
  entrenamiento): su error por ciudad será el más ruidoso y se lee con esa advertencia.
- **Pliegues desactualizados:** si el entrenamiento se regenera y sus anuncios ya no coinciden con los del archivo de pliegues, los
  notebooks se detienen con un mensaje en lugar de usar una asignación incompleta.
- **Ninguna idea pasa la regla:** el conjunto final es la referencia; es un resultado válido y se escribe así.
- **Un ensayo que falla** (por ejemplo, por memoria): cuenta dentro del presupuesto, queda registrado como fallido y no se repite
  por encima de los 30.
- **Intervalo que toca el cero:** solo cuenta como mejora si todo el intervalo está estrictamente por debajo de cero.
- **Fechas de reseñas vacías** (anuncios sin reseñas) en la medición con sospechosas: quedan vacías y se imputan dentro del modelo.

## Requirements *(mandatory)*

### Functional Requirements

**Datos y pliegues**

- **FR-001**: Las etapas 4 a 6 MUST leer solo el entrenamiento (`data/processed/train.csv.gz`: 118.513 anuncios de 53.385
  anfitriones y 65 columnas) mediante una única función de carga compartida por los notebooks 04 a 06, que reemplaza la lectura
  de `train.joblib` de los esqueletos. No se crea `train.joblib`.
- **FR-002**: El conjunto de prueba (`test.csv.gz`) MUST NOT leerse ni contarse en estas etapas, y no se escribe ninguna función que
  lo lea (constitución, principio III).
- **FR-003**: MUST calcular **una sola vez** cinco pliegues por anfitrión, barajados con semilla 42, guardarlos (anuncio → pliegue)
  en `data/processed/folds.csv` y reutilizarlos en las etapas 4, 5 y 6. Ningún anfitrión cae en dos pliegues y cada anuncio está en
  exactamente uno. Si los anuncios del archivo no coinciden con los del entrenamiento, se detiene con un mensaje.
- **FR-004**: La línea base de H1 (MAE 55,96 ± 1,94 USD) y la función con que se midió MUST quedar sin cambios como registro; en el
  torneo la línea base se vuelve a medir con los pliegues nuevos.

**Columnas**

- **FR-005**: MUST existir una lista de columnas **prohibidas** que nunca entran al modelo: `log_price_usd`, `price_usd`,
  `price_local`, `id`, `host_id`, `scrape_id`, `last_scraped`, `calendar_last_scraped`, `source`, `bathrooms_text`, `amenities`
  (cruda), `neighbourhood_group_cleansed`, `minimum_minimum_nights`, `maximum_minimum_nights`, `minimum_maximum_nights`,
  `maximum_maximum_nights`, `minimum_nights_avg_ntm` y `maximum_nights_avg_ntm`. Pedir una de ellas MUST detener la construcción
  del modelo con un mensaje que la nombre.
- **FR-006**: MUST existir una lista de columnas **sospechosas**: `estimated_occupancy_l365d`, `availability_30`, `availability_60`,
  `availability_90`, `availability_365`, `availability_eoy`, `has_availability`, `number_of_reviews`, `number_of_reviews_ltm`,
  `number_of_reviews_l30d`, `number_of_reviews_ly`, `reviews_per_month`, `first_review`, `last_review`, `has_reviews`, las siete
  `review_scores_*` y `host_is_superhost`. Solo se usan en la medición de FR-013; MUST NOT estar en las variables del torneo, de la
  optimización ni de la versión para la app.
- **FR-007**: La **referencia** MUST ser: `city`, `neighbourhood_cleansed`, `latitude`, `longitude`, `room_type`, `property_type`,
  `accommodates`, `bedrooms`, `beds`, `bathrooms_count`, `bathroom_shared`, `minimum_nights` y `maximum_nights`. Los barrios y tipos
  de propiedad con menos de 30 anuncios pasan a "Other" (decisión 11 del EDA) y los vacíos se imputan (mediana en números, moda en
  el indicador de baño compartido); el umbral y los valores se aprenden **solo con la parte de entrenamiento de cada pliegue**.
- **FR-008**: Todo cálculo de variables (también los que no aprenden de los datos) MUST ir dentro del modelo guardado, para que
  reciba las columnas crudas y la app no repita cálculos.
- **FR-009**: Las 65 columnas del entrenamiento MUST quedar en exactamente una de estas categorías: prohibida (18), sospechosa
  (23), referencia (13) o insumo de la idea 4 (11 columnas del anfitrión). `amenities` cuenta como prohibida porque no entra cruda:
  solo es el insumo de la idea 2 (FR-010).

**Variables (etapa 4)**

- **FR-010**: MUST implementar y medir cinco ideas, cada una con su cálculo exacto según la sección 2 de la especificación de
  etapa:
  1. **Distancia al centro** (km, haversine) hasta la mediana de latitud y longitud de los anuncios de su ciudad, aprendida con el
     entrenamiento del pliegue.
  2. **Amenidades:** conteo de la lista e indicadores 0/1 por nombre exacto (`Pool`, `Air conditioning`, `Free parking on
     premises`, `Gym`, `Elevator`, `Hot tub`), sin variantes.
  3. **Razones de capacidad:** `people_per_bedroom`, `people_per_bathroom` y `beds_per_person`.
  4. **Perfil del anfitrión:** `host_listings_count`, `calculated_host_listings_count` y sus tres desgloses, `host_tenure_years`,
     `user_tenure_years`, `host_has_profile_pic` y `host_identity_verified` (t/f → 1/0).
  5. **Precio típico del barrio:** el barrio codificado con el promedio del objetivo, aprendido dentro del modelo con validación
     cruzada interna, de modo que ninguna fila ve su propio precio.
- **FR-011**: Cada variante (referencia + **una** idea) MUST medirse con el mismo modelo de parámetros fijos (LightGBM con los
  parámetros de la sección 3.2 de la especificación de etapa, iguales a los del torneo) y los pliegues de FR-003, registrando por
  pliegue MAE en USD, MAPE, R² en logaritmo, RMSE, sesgo medio y segundos de ajuste. Una fila por variante y pliegue MUST guardarse
  en `reports/04_features_tabla.csv`.
- **FR-012**: La decisión MUST seguir la regla escrita: se conserva una idea solo si **mejora / ruido > 1** (mejora = MAE medio de la
  referencia − MAE medio de la variante; ruido = desviación estándar con `ddof=1` del MAE de la variante entre pliegues) **y** todas
  sus columnas se conocen al predecir un inmueble nuevo. Se reportan también los pliegues que gana. Una excepción se justifica por
  escrito antes del torneo. El conjunto final (referencia + ideas conservadas) se mide una vez para confirmar, sin volver a decidir
  con esa cifra.
- **FR-013**: MUST medir el conjunto final **más** las sospechosas, con el mismo modelo y pliegues, y reportar cuánto baja el MAE.
  Las fechas `first_review` y `last_review` se convierten en días hasta el corte de su ciudad. No se aplica la regla y esa versión
  no continúa.

**Torneo (etapa 5)**

- **FR-014**: MUST evaluar cuatro candidatos con el conjunto final sin sospechosas y los pliegues de FR-003: la línea base (mediana
  de `price_usd` por `city` × `room_type`, la que ya existe), Ridge, bosque aleatorio y LightGBM, con los parámetros de la sección
  5.1 de la especificación de etapa. Una fila por modelo y pliegue MUST guardarse en `reports/05_torneo_tabla.csv`.
- **FR-015**: La métrica principal MUST ser el **MAE en USD por noche** (los modelos que aprenden el logaritmo se llevan a USD con la
  exponencial, sin corrección). Las técnicas: MAPE, R² sobre el logaritmo, RMSE en USD y sesgo medio en USD (predicho − real;
  positivo = sobrestima, el error más caro para el inversionista).
- **FR-016**: MUST reportar el **error por ciudad** (MAE y sesgo de cada ciudad en cada pliegue) en
  `reports/05_torneo_por_ciudad.csv`.
- **FR-017**: MUST mostrar la tabla de media ± desviación entre pliegues ordenada por MAE, un diagrama de cajas por modelo y la
  comparación pareada de los tres mejores (diferencia media, pliegues que gana y diferencia / ruido con la desviación de las
  diferencias).
- **FR-018**: MUST traducir la diferencia de MAE frente a la línea base a "USD por cada 30 noches reservadas de un anuncio",
  presentada como escala y no como pronóstico.
- **FR-019**: MUST elegir **1–2 finalistas** en este orden: consistencia (gana en al menos 4 de 5 pliegues al siguiente y
  diferencia / ruido > 1), MAE, sesgo, tiempo y simplicidad, interpretabilidad; y explicar en `reports/05_torneo.md` por qué el
  torneo no elige un campeón.

**Optimización (etapa 6)**

- **FR-020**: Solo se optimizan los finalistas, con un presupuesto de **30 ensayos por finalista** fijado antes de empezar, con una
  búsqueda bayesiana (semilla 42) que minimiza el MAE medio en USD.
- **FR-021**: Antes de buscar MUST reservarse el **25 % de los anfitriones** del entrenamiento (semilla 7), verificando que ningún
  anfitrión queda en los dos lados. La búsqueda usa los pliegues de FR-003 restringidos a sus anfitriones.
- **FR-022**: Los espacios de búsqueda MUST ser los de la sección 6 de la especificación de etapa (LightGBM, bosque aleatorio y, si
  es finalista, Ridge).
- **FR-023**: Cada ensayo MUST quedar como una ejecución en el seguimiento **local**, usando el módulo de seguimiento que ya existe
  en el repositorio **sin reescribirlo**, en el experimento `tarifalatam-optimizacion`, con nombre `<modelo>-ensayo-<nn>`, sus
  hiperparámetros, el MAE medio y su desviación, MAPE, R², RMSE, sesgo, segundos y las etiquetas `etapa=06_optimizacion`,
  `modelo`, `variables=sin_sospechosas` y `datos=train.csv.gz`. No se usa Databricks ni se piden o escriben tokens.
- **FR-024**: **Comprobación honesta:** con todos los datos de búsqueda se entrenan los parámetros de partida y los optimizados; en
  los anfitriones reservados se calcula, por anuncio, |error optimizado| − |error de partida| en USD y su intervalo del 95 % con
  1.000 remuestreos de **anfitriones completos** (semilla 42). Se usan los optimizados solo si **todo** el intervalo está por debajo
  de cero.
- **FR-025**: Con dos finalistas, MUST compararse sus configuraciones elegidas en los mismos anfitriones reservados con el mismo
  intervalo: pasa a la etapa 7 el que tenga todo el intervalo de la diferencia por debajo de cero; si cruza el cero, el más simple y
  rápido. Sin abrir la prueba.
- **FR-026**: La decisión MUST guardarse en `reports/06_best_params.json` (finalista, parámetros, intervalo, regla aplicada y dónde
  quedó el seguimiento). La mejor puntuación de la búsqueda MUST NOT reportarse como resultado.

**Informes y código**

- **FR-027**: `reports/04_features.md`, `reports/05_torneo.md` y `reports/06_optimizacion.md` MUST contener solo cifras medidas por
  los notebooks ejecutados, con las ideas descartadas anotadas con su cifra (constitución, principio VII).
- **FR-028**: La lógica MUST vivir en `src/tarifalatam/` (carga y pliegues, variables, modelos y optimización); los notebooks 04 a
  06 solo la llaman. Textos en español; nombres de código en inglés.

**Pruebas**

- **FR-029**: MUST existir pruebas automáticas para: las listas de columnas (no se cruzan; una prohibida detiene el modelo; un modelo
  ajustado con datos donde `price_usd`, `id` y `host_id` predicen perfecto no las usa); la versión para la app sin sospechosas; la
  carga (65 columnas con sus tipos); los pliegues (anfitriones enteros, cada anuncio en uno, misma semilla = mismos pliegues); cada
  idea (división por cero, vacíos, no modifica el original y, en las ideas 1 y 5, usa solo lo visto al ajustar); las métricas
  (predicción perfecta: MAE y sesgo 0, R² 1; un caso a mano con el signo del sesgo); la evaluación por pliegue (una fila por
  pliegue, con los pliegues dados); los anfitriones reservados (sin cruce); y el intervalo por anfitrión (diferencia constante =
  esa constante; remuestrea anfitriones, no filas).
- **FR-030**: Todas las pruebas MUST pasar desde la raíz del repositorio (hoy 76) antes de dar una tarea por hecha.

### Key Entities

- **Anuncio**: una fila del entrenamiento; un inmueble con su ciudad, barrio, tipo, capacidad, amenidades, anfitrión y precio.
- **Anfitrión** (`host_id`): la unidad por la que se parte y se remuestrea; nunca es variable.
- **Asignación de pliegues**: a qué pliegue (0 a 4) pertenece cada anuncio; se calcula una vez y la comparten las tres etapas.
- **Lista de columnas**: prohibidas, sospechosas, referencia e insumos de ideas.
- **Idea de variable / variante**: una hipótesis (cálculo, motivo, si se conoce al predecir) y su medición contra la referencia.
- **Candidato**: un modelo del torneo con su configuración de partida y sus cifras por pliegue y por ciudad.
- **Ensayo**: una configuración probada en la búsqueda, registrada como una ejecución en el seguimiento local.
- **Anfitriones reservados**: el 25 % de los anfitriones que la búsqueda nunca ve; sirven para la comprobación honesta.
- **Decisión de parámetros**: el finalista, los parámetros elegidos, el intervalo y la regla aplicada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las comparaciones de las etapas 4, 5 y 6 usa la misma asignación de pliegues, con 0 anfitriones en dos
  pliegues.
- **SC-002**: 0 columnas prohibidas en cualquier modelo, y 0 sospechosas en las variables del torneo, de la optimización y de la
  versión para la app, verificado por una prueba automática.
- **SC-003**: La tabla de ideas tiene la referencia, las 5 ideas, el conjunto final y la medición con sospechosas, cada una con sus 5
  valores por pliegue, y el 100 % de las decisiones coincide con la regla escrita (o lleva una excepción escrita).
- **SC-004**: El torneo tiene la línea base y al menos 3 modelos, cada uno con 5 valores por pliegue, y el error de las 6 ciudades.
- **SC-005**: La búsqueda registra una ejecución por ensayo (como máximo 30 por finalista), el 100 % con parámetros, métricas y
  etiquetas.
- **SC-006**: 0 lecturas del conjunto de prueba en estas etapas.
- **SC-007**: El 100 % de las cifras de los tres informes se puede rastrear hasta una salida de notebook ejecutado (0 cifras
  inventadas).
- **SC-008**: Los tres notebooks corren de principio a fin desde los datos procesados, sin pasos manuales.
- **SC-009**: En el punto de control, quien no escribió el código responde las 8 preguntas de la guía (sección 5).

## Assumptions

- **Contrato:** las listas, parámetros, rangos y semillas de `especificaciones/04-features-torneo-optimizacion.md` (aprobada el
  2026-10-31) son fijos. El plan decide cómo implementarlos, pero no cambia valores sin una nueva aprobación del grupo, anotada en
  la sección 7 de `especificacion-proyecto.md`.
- El modelo aprende `log(price_usd)`; el error se mide en USD con la exponencial de la predicción, sin corrección de
  retransformación, porque se acerca a la mediana, que es lo que premia el MAE.
- Usar los mismos anfitriones reservados para dos decisiones (optimizados contra partida y, si hay dos, finalista contra finalista)
  agrega un poco de optimismo; se acepta y se declara en `reports/06_optimizacion.md`.
- **Quién implementa cada tarea** lo decide el grupo al aprobar `tasks.md`: cada integrante con su cuenta de GitHub.
- Los datos de `data/raw/` y `data/processed/` se copian al worktree desde el checkout principal; nunca se mueven ni se modifican, y
  no se suben a GitHub.
- **Fuera de alcance:** abrir la prueba (etapa 7); MLflow en Databricks y el registro del modelo (clase 4); exportar
  `models/model.joblib` y la app; adaptar `src/tarifalatam/inference/`, que hoy es la plantilla de clasificación (etapas 9 y 10).
