# Feature Specification: Validación en la prueba, registro del modelo y app local (hito H2, etapas 7 a 9)

**Feature Branch**: `003-validacion-registro-app`

**Created**: 2026-11-05

**Status**: Approved (aprobada por el grupo el 2026-11-05)

**Input**: User description: "Etapas 7 a 9 de TarifaLatam (cierre del hito H2, clase 4): abrir la prueba una sola vez con
las decisiones congeladas, medir el modelo final con intervalo por anfitrión frente a la línea base, registrar el modelo
con versión y alias, exportarlo con su esquema de entrada y dejar una app que corre en local y sugiere el precio por
noche." Guía de etapa: `especificaciones/07-validacion-registro-app.md` (borrador del 2026-11-05).

## Clarifications

### Session 2026-11-05

- Q: ¿Qué meta de éxito se escribe antes de abrir la prueba? → A: La del PR #5 (Rafael Jaramillo): MAE al menos 20 % menor
  que el de la línea base, intervalo del 95 % de la diferencia entero bajo cero y ninguna ciudad con MAE mayor que el de la
  línea base; el costo 2 a 1 (con 1,5 a 1 y 3 a 1) se reporta como control.
- Q: ¿Cómo se entrega el precio sugerido? → A: Precio puntual redondeado al dólar y un rango típico de su ciudad: el precio
  multiplicado por los percentiles 25 y 75 de la razón precio real / precio sugerido en los anfitriones reservados.
- Q: ¿Dónde se registra el modelo? → A: En el MLflow local de la etapa 6 (no hay conexión con Databricks configurada); la
  excepción a la regla 7 de `CLAUDE.md` se anota en `especificacion-proyecto.md`, sección 7.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Una medida honesta del modelo en anuncios nunca vistos (Priority: P1)

El grupo (y el instructor) necesita saber cuánto se equivoca de verdad el modelo elegido con anfitriones que nunca vio,
y si es mejor que la regla simple (la mediana por ciudad y tipo de habitación), sin que la prueba haya servido para
decidir nada.

**Why this priority**: es la única cifra que puede ir a la presentación, al informe y a la ficha del modelo. Sin ella no
hay H2, y todo lo demás (registro, app) entregaría un modelo sin medida.

**Independent Test**: con las decisiones de la sección 1 de la guía ya escritas y fechadas, se ejecuta la etapa 7 de
principio a fin; queda una marca con la fecha y la hora en que se abrió la prueba, una tabla con el MAE del modelo y de la
línea base con sus intervalos, y la diferencia entre ambos con su intervalo.

**Acceptance Scenarios**:

1. **Given** las decisiones congeladas y fechadas, **When** se abre la prueba, **Then** queda la marca de apertura y el
   modelo final no se vuelve a ajustar después de ese momento.
2. **Given** la prueba abierta, **When** se calculan las métricas, **Then** se reportan MAE, MAPE, R² (logaritmo), RMSE y
   sesgo del modelo y de la línea base, con el intervalo del 95 % remuestreando anfitriones completos.
3. **Given** las métricas, **When** se compara con la línea base, **Then** se dice si la meta de éxito se cumple o no,
   según la regla escrita antes de abrir la prueba, aunque el resultado no guste.
4. **Given** la prueba abierta, **When** se revisan los segmentos, **Then** hay una tabla por ciudad y por tipo de
   habitación con anuncios, MAE, MAPE, sesgo y % de sobrestimaciones.
5. **Given** el modelo final, **When** se interpreta, **Then** se listan las variables que más pesan y los límites de esa
   explicación, sin cambiar el modelo.

---

### User Story 2 - Un modelo registrado que cualquiera del grupo puede recuperar (Priority: P2)

El grupo necesita que el modelo evaluado quede guardado con un nombre, una versión y el alias `champion`, junto con lo
necesario para confiar en él, y comprobar que lo recuperado predice igual que lo evaluado.

**Why this priority**: es un criterio explícito del hito H2 ("modelo final registrado con versión") y es la fuente del
archivo que usará la app.

**Independent Test**: se recupera el modelo por su alias y se compara su predicción con la del modelo original en 200
anuncios; deben coincidir.

**Acceptance Scenarios**:

1. **Given** el modelo final y sus métricas de prueba, **When** se registra, **Then** queda una versión con alias
   `champion`, sus parámetros, sus métricas de prueba, la lista de columnas de entrada, un ejemplo de entrada y etiquetas
   de origen.
2. **Given** el registro, **When** se recupera por alias, **Then** predice igual que el original en 200 anuncios.
3. **Given** el registro, **When** alguien del grupo lee `reports/08_registro.md`, **Then** sabe dónde está, qué versión es
   y cómo recuperarlo.

---

### User Story 3 - Un precio sugerido que se niega a responder con datos imposibles, en una app local (Priority: P3)

El anfitrión (o el inversionista) escribe las características del inmueble y recibe un precio por noche en USD. Si un dato
es imposible, recibe un mensaje que dice qué corregir; si no sabe un dato, igual recibe un precio.

**Why this priority**: es el criterio "app local que carga el modelo" del H2 y la base del despliegue de mañana (H3).

**Independent Test**: con la app corriendo en local se prueban tres casos: un inmueble normal (responde), uno con un
campo en «No sé» (responde) y uno con 40 huéspedes (se niega y explica).

**Acceptance Scenarios**:

1. **Given** el archivo exportado del modelo `champion`, **When** se mide el MAE en la prueba con ese archivo, **Then** es
   idéntico al de la etapa 7.
2. **Given** un inmueble con datos normales, **When** se pide el precio, **Then** se muestra en USD por noche, con la
   forma acordada, junto al aviso de uso responsable.
3. **Given** un dato imposible (fuera del rango posible) o un barrio de otra ciudad, **When** se pide el precio, **Then** no
   se muestra precio y se explica qué corregir.
4. **Given** un campo marcado «No sé», **When** se pide el precio, **Then** se muestra un precio y no ocurre ningún error.
5. **Given** un inmueble en Belice, **When** se muestra el precio, **Then** aparece un aviso de que el error en esa ciudad
   es mucho mayor.

---

### Edge Cases

- La marca de apertura de la prueba ya existe al ejecutar la etapa 7: se avisa, se declara en el informe y no se usa lo
  visto para cambiar el modelo.
- El intervalo de la diferencia con la línea base cruza el cero: se reporta "sin evidencia de mejora", no se ajusta nada.
- La comprobación del factor del logaritmo queda en empate: se mantiene la decisión aprobada (sin corrección).
- Una categoría que el modelo no conoce (barrio o tipo de propiedad nuevo): advertencia, no error; el modelo la trata como
  desconocida.
- Un valor dentro de lo posible pero fuera de lo visto en el entrenamiento: advertencia, no error.
- El registro remoto no conecta: se usa el respaldo local y se declara (si se eligió Databricks).
- El seguimiento local de la etapa 6 está solo en el worktree de la pieza 002: se copia antes de registrar y el worktree
  no se borra hasta comprobar la copia.
- El archivo exportado pesa más de lo que GitHub acepta (100 MB): se detiene y se avisa antes de subirlo.

## Requirements *(mandatory)*

### Functional Requirements

**Etapa 7 · Validación**

- **FR-001**: Las decisiones de la sección 1 de la guía (modelo, parámetros, corrección del logaritmo, métricas, forma de
  entregar el precio y meta de éxito) MUST quedar escritas y fechadas en `reports/07_validacion.md` **antes** de abrir la
  prueba.
- **FR-002**: El modelo final MUST ser LightGBM con las 13 columnas de la referencia y los parámetros optimizados de
  `reports/06_best_params.json`, y el informe MUST declarar que su elección fue una excepción a la regla tomada después de
  ver el resultado de la etapa 6 (T047).
- **FR-003**: La necesidad de un factor de corrección al volver del logaritmo MUST evaluarse solo con los anfitriones
  reservados de la etapa 6, con la regla escrita en la guía (se usa solo si todo el intervalo de la diferencia de MAE
  queda bajo cero).
- **FR-004**: El modelo final MUST entrenarse con todo el entrenamiento antes de abrir la prueba y no volver a ajustarse
  después.
- **FR-005**: La prueba MUST abrirse una sola vez y dejar una marca con fecha y hora; ningún otro código del proyecto MUST
  leerla.
- **FR-006**: MUST reportarse MAE (principal), MAPE, R² sobre el logaritmo, RMSE, sesgo y costo 2 a 1 (con 1,5 a 1 y 3 a 1)
  del modelo y de la línea base en la prueba, con intervalo del 95 % remuestreando anfitriones (1.000 remuestreos, semilla 42), y el intervalo de su
  diferencia.
- **FR-007**: La meta de éxito MUST evaluarse con la regla escrita antes de abrir la prueba, y se cumple solo si se dan las
  tres condiciones: (a) MAE del modelo al menos 20 % menor que el de la línea base; (b) intervalo del 95 % de la diferencia
  (modelo − línea base) entero bajo cero; (c) en ninguna ciudad el MAE del modelo es mayor que el de la línea base. El
  veredicto se escribe se cumpla o no.
- **FR-008**: MUST reportarse, una sola vez y sin usarlo para decidir, el MAE en la prueba sin el filtro de precios
  extremos (29.807 anuncios).
- **FR-009**: MUST reportarse el error por ciudad y por tipo de habitación (anuncios, MAE, MAPE, sesgo, % de
  sobrestimaciones) y cuántos anuncios por ciudad quedan con un error mayor a la mitad de su precio.
- **FR-010**: MUST reportarse la importancia de las variables (SHAP sobre 2.000 anuncios del entrenamiento) y dos anuncios
  concretos de la prueba, con los límites de la explicación y la declaración sobre la ubicación como atributo sensible.
- **FR-011**: Las cifras de la etapa MUST guardarse en `reports/07_metricas_test.json`.

**Etapa 8 · Registro**

- **FR-012**: El modelo final MUST registrarse como `tarifalatam_precio_noche`, con alias `champion`, en el MLflow local de
  la etapa 6, con parámetros, métricas de prueba, columnas de entrada, ejemplo de entrada y etiquetas de origen.
- **FR-013**: El modelo recuperado por alias MUST predecir igual que el original en 200 anuncios del entrenamiento.
- **FR-014**: Si el registro es local, el seguimiento de la etapa 6 MUST copiarse del worktree de la pieza 002 al checkout
  principal antes de registrar, sin perder ejecuciones.
- **FR-015**: MUST quedar constancia en `reports/08_registro.json` y `reports/08_registro.md` (dónde, versión, quién y
  cuándo, tracking frente a registro).

**Etapa 9 · Inferencia y app**

- **FR-016**: `models/model.joblib` MUST exportarse desde la versión `champion` y dar en la prueba el mismo MAE que la etapa 7.
- **FR-017**: `models/input_schema.json` MUST describir las 13 columnas, sus categorías conocidas, los barrios de cada
  ciudad, el rango posible (tabla de la guía, sección 7) y el rango observado.
- **FR-018**: La predicción MUST devolver el precio en USD por noche redondeado al dólar y su rango típico: el precio
  multiplicado por los percentiles 25 y 75 de la razón precio real / precio sugerido en los anfitriones reservados de su
  ciudad (medidos sin la prueba y guardados con el esquema).
- **FR-019**: Con un valor fuera del rango posible o un barrio que no es de la ciudad, la predicción MUST negarse y explicar
  qué corregir; fuera del rango observado o con una categoría desconocida MUST advertir y responder.
- **FR-020**: Con un campo vacío («No sé») la predicción MUST responder sin error.
- **FR-021**: La app MUST cargar el modelo y el esquema desde el repositorio, no consultar ninguna plataforma externa,
  filtrar los barrios por ciudad, ofrecer «No sé» en cada campo, mostrar un aviso de uso responsable (precio de referencia;
  la tarifa la fija el anfitrión y el modelo no dice si un inmueble se paga) y un aviso especial para Belice.
- **FR-022**: `models/ficha_modelo.md` MUST completarse a mano con cifras medidas en esta pieza.
- **FR-023**: Cada función nueva de `src/` MUST tener al menos una prueba (lista de la guía, sección 9) y `pytest` MUST
  quedar en verde.

### Key Entities

- **Decisiones congeladas**: modelo, parámetros, corrección del logaritmo, métricas, forma del precio, meta, fecha y hora.
- **Resultado de la prueba**: métricas del modelo y de la línea base, intervalos, diferencia, sensibilidad sin filtro,
  errores por segmento.
- **Modelo registrado**: nombre, versión, alias, parámetros, métricas, columnas de entrada, ejemplo, etiquetas.
- **Esquema de entrada**: columnas, categorías, barrios por ciudad, rangos posibles y observados, textos de la app.
- **Precio sugerido**: valor en USD por noche, rango típico de su ciudad y advertencias.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La prueba se abre exactamente una vez, después de la fecha y hora de las decisiones congeladas (las dos marcas
  lo demuestran).
- **SC-002**: El informe de la etapa 7 trae el MAE del modelo y de la línea base con intervalo del 95 % por anfitrión, la
  diferencia con su intervalo y el veredicto sobre cada una de las tres condiciones de la meta.
- **SC-003**: Las seis ciudades y los tipos de habitación tienen su fila de error; ninguna cifra queda sin medir.
- **SC-004**: El modelo recuperado del registro y el exportado predicen igual que el evaluado (200 de 200 anuncios
  idénticos; MAE en la prueba idéntico).
- **SC-005**: De tres casos de uso (normal, «No sé», imposible), la app responde los dos primeros y rechaza el tercero con
  un mensaje que dice qué corregir.
- **SC-006**: Una persona del grupo que no escribió el código responde las 8 preguntas de la guía de la clase 4.
- **SC-007**: `pytest` en verde desde la raíz.

## Assumptions

- La pieza cubre solo el hito H2. El despliegue en internet y la presentación son la pieza 004 (H3, 2026-11-06).
- Se trabaja en la rama `003-validacion-registro-app`, sin worktree; `data/` sigue fuera de Git.
- La línea base de la prueba se ajusta con todo el entrenamiento (la misma regla del torneo).
- Los datos de la app no se guardan: cada consulta se olvida al cerrar la página.
- Las cifras del torneo de Belice (MAE de unos 205 USD) son de validación cruzada; la prueba dirá la suya.
- La interpretación con SHAP no cambia el modelo; usar dos anuncios de la prueba para explicar no es decidir.
