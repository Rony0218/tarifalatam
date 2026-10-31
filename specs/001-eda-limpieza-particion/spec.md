# Feature Specification: EDA reproducible, limpieza y partición por anfitrión (hito H1)

**Feature Branch**: `001-eda-limpieza-particion` (sin rama propia por ahora; se trabaja en `main`)

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Hito H1 de TarifaLatam: EDA reproducible y preprocesamiento (limpieza y partición). Entradas obligatorias: especificacion-proyecto.md, especificaciones/02-eda.md (sección 4, 11 decisiones con cifras), especificaciones/03-preprocesamiento.md y reports/01_eda.md. […] Quedan sin decidir y deben marcarse como dudas: fuente y valor de las tasas de cambio por ciudad, incluir o no Buenos Aires y Belice, qué hacer con source = "previous scrape", umbral de precios extremos (propuesta 20x) y proporción de prueba."

**Fuentes que manda esta especificación**: `especificacion-proyecto.md`, `especificaciones/02-eda.md` (sección 4),
`especificaciones/03-preprocesamiento.md`, `reports/01_eda.md` y `.specify/memory/constitution.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Datos limpios y partidos por anfitrión, listos para modelar (Priority: P1)

Quien modela en la etapa 4 necesita un conjunto de **entrenamiento** y otro de **prueba** con los anuncios de las ciudades
del caso, el precio por noche en dólares, sin datos personales ni columnas que contengan la respuesta, y con cada anfitrión
entero de un solo lado. Se regeneran desde cero con un solo paso, sin tocar los archivos originales.

**Why this priority**: sin esto no hay modelo honesto. Es el entregable central del hito H1 y lo que exige la regla 3 del
proyecto (partir por la unidad correcta).

**Independent Test**: borrar `data/processed/`, ejecutar la limpieza y comprobar que aparecen los dos conjuntos, que ningún
anfitrión está en ambos y que los archivos de `data/raw/` no cambiaron.

**Acceptance Scenarios**:

1. **Given** los siete archivos originales en `data/raw/`, **When** se ejecuta la limpieza desde cero, **Then** se generan un
   conjunto de entrenamiento y uno de prueba, y la huella (tamaño y fecha) de los originales es la misma de antes.
2. **Given** los dos conjuntos generados, **When** se cruzan los anfitriones de ambos, **Then** no hay ningún anfitrión en común
   y la suma de filas de ambos es igual a las filas que quedaron después de las reglas que se aplican antes de partir.
3. **Given** los dos conjuntos generados, **When** se buscan las columnas personales, el texto libre y las columnas de fuga,
   **Then** ninguna aparece.
4. **Given** un anuncio con precio `"$1,234.00"` en reales, **When** se limpia, **Then** su precio en dólares es 1.234 dividido por
   la tasa de esa ciudad y su objetivo es el logaritmo de ese valor.

---

### User Story 2 - El notebook del EDA reproduce las cifras del informe (Priority: P2)

El grupo y el instructor abren `notebooks/02_eda.ipynb`, lo ejecutan de principio a fin y ven las mismas cifras que dice
`reports/01_eda.md`. Así cualquier integrante puede defender una decisión mostrando de dónde sale su número.

**Why this priority**: hoy las cifras del informe salen de un script exploratorio fuera del repositorio. Es criterio de cierre
del EDA que el notebook las reproduzca (principio VII: nunca se inventan resultados).

**Independent Test**: ejecutar el notebook en un entorno limpio y comparar la tabla de cifras clave con `reports/01_eda.md`.

**Acceptance Scenarios**:

1. **Given** los datos en `data/raw/`, **When** se ejecuta el notebook completo, **Then** termina sin errores y muestra cada cifra
   clave de la lista de FR-018.
2. **Given** que una cifra del notebook no coincide con el informe, **When** se detecta, **Then** se corrige el informe con la
   cifra del notebook y se anota el cambio (no se ajusta el código para que "dé" el número).
3. **Given** el notebook ejecutado, **When** se revisa su salida, **Then** no se ve ningún nombre, foto, URL, teléfono ni correo de
   un anfitrión.

---

### User Story 3 - Cada regla tiene prueba y deja rastro escrito (Priority: P3)

Cada regla de limpieza tiene una prueba automática con un caso normal y uno sucio hechos a mano, y la limpieza deja un
**registro de exclusiones**: cuántas filas quitó cada regla en cada ciudad. Ese registro se copia a `reports/`.

**Why this priority**: lo exige el principio IV (cada decisión con su cifra, su función y su prueba) y permite discutir las
reglas sin leer el código.

**Independent Test**: ejecutar las pruebas y ver que todas pasan; romper a propósito la partición (por fila) y ver que la prueba
de partición falla.

**Acceptance Scenarios**:

1. **Given** las reglas de FR-003 a FR-015, **When** se ejecutan las pruebas, **Then** hay al menos una prueba por regla y todas pasan.
2. **Given** la partición cambiada temporalmente a "por fila", **When** se ejecuta su prueba, **Then** la prueba falla.
3. **Given** la limpieza ejecutada, **When** se abre el registro de exclusiones, **Then** muestra, por ciudad, las filas de partida,
   las quitadas por cada regla y las finales, y los totales cuadran.

---

### Edge Cases

- Un precio que no se puede convertir a número (texto inesperado) se trata como vacío y el anuncio sale por la regla de "sin
  precio", con su conteo en el registro.
- `bathrooms_text` sin número: "Half-bath", "Shared half-bath", "Private half-bath" = 0,5 baños; "No bathroom" = 0; vacío = vacío.
- Un anfitrión con anuncios en dos ciudades (258 casos) queda entero en un solo conjunto.
- Una ciudad con muy pocos anuncios en entrenamiento para calcular su mediana (Belice, si se incluye): la mediana se calcula
  igual; si una ciudad no tuviera anuncios en entrenamiento, la limpieza se detiene con un mensaje claro.
- Si falta uno de los siete archivos o cambian sus columnas, la carga se detiene con un mensaje que dice cuál.
- Si no existe la tabla de tasas de cambio o le falta una ciudad, la conversión se detiene: nunca se usa una tasa inventada.

## Requirements *(mandatory)*

### Functional Requirements

**Carga**

- **FR-001**: La limpieza MUST leer los siete archivos `listings_<ciudad>_<fecha>.csv.gz` de `data/raw/` sin modificarlos, unirlos y
  agregar la ciudad de cada anuncio.
- **FR-002**: Como primer paso de la carga, MUST eliminar las 10 columnas personales (`host_name`, `host_about`, `host_location`,
  `host_url`, `host_profile_url`, `host_profile_id`, `host_picture_url`, `host_thumbnail_url`, `listing_url`, `picture_url`) y el
  texto libre (`name`, `description`, `neighborhood_overview`), antes de cualquier resumen o impresión. `host_id` se conserva solo
  para partir. *(Decisión 4 del EDA.)*

**Reglas de limpieza (decisiones del EDA)**

- **FR-003**: MUST convertir `price` de texto (`"$1,234.00"`) a número y pasarlo a USD con una tasa por ciudad leída de una tabla
  versionada en el repositorio; Belice ya está en USD (tasa 1). La tabla dice la fuente y la fecha de cada tasa.
  **Fuente: la tasa oficial del banco central de cada país en la fecha del corte de cada ciudad.** El grupo trae los cinco
  valores (BRL, MXN, ARS, COP, CLP) con su enlace; mientras falten, la conversión se detiene (no se usa ningún valor supuesto).
  *(Decisión 1; aclarado el 2026-10-30.)*
- **FR-004**: MUST excluir los anuncios sin precio (11.642 en los datos completos). *(Decisión 2.)*
- **FR-005**: MUST eliminar las columnas de fuga: `price_quote_checkin_date`, `price_quote_checkout_date`,
  `price_quote_total_price`, `price_quote_price_per_night`, `price_quote_raw` y `estimated_revenue_l365d`. La moneda se lee de
  `price_quote_raw` antes de eliminarla, solo para verificar que coincide con la de la ciudad. *(Decisión 3.)*
- **FR-006**: MUST eliminar las 12 columnas 100 % vacías en las siete ciudades (`bathrooms`, `host_since`, `host_response_time`,
  `host_response_rate`, `host_acceptance_rate`, `host_neighbourhood`, `host_total_listings_count`, `host_verifications`,
  `instant_bookable`, `neighbourhood`, `neighborhood_overview`, `calendar_updated`). *(Decisión 6.)*
- **FR-007**: MUST crear, a partir de `bathrooms_text`, el número de baños (con las reglas de los casos límite) y un indicador de
  baño compartido. *(Decisión 6.)*
- **FR-008**: MUST excluir los anuncios con `minimum_nights ≥ 30` (arriendos mensuales). *(Decisión 7.)*
- **FR-009**: MUST marcar como vacío `maximum_nights > 1.125` y `bedrooms` cuando sea mayor que 10 **y** mayor que `accommodates`.
  *(Decisión 10.)*
- **FR-010**: MUST crear `has_reviews` (1 si `number_of_reviews > 0`, 0 si no) y dejar vacías las notas de los anuncios sin
  reseñas; no se imputa aquí. *(Decisión 9.)*
- **FR-011**: MUST excluir los anuncios con `source = "previous scrape"` (11.701; 3.293 de ellos con precio), porque no se
  vieron en este corte y su precio puede estar desactualizado. *(Aclarado el 2026-10-30.)*
- **FR-012**: MUST incluir las **siete ciudades**, Buenos Aires y Belice incluidas. El error se reportará por ciudad en las etapas
  siguientes para vigilar a las dos. *(Aclarado el 2026-10-30.)*

**Partición y reglas que aprenden de los datos**

- **FR-013**: MUST partir en entrenamiento y prueba **por anfitrión** (`host_id`), con 20 % de los anfitriones en prueba y semilla 42,
  **después** de las reglas FR-002 a FR-012 y **antes** de cualquier regla que aprenda de los datos. *(Decisión 5.)*
- **FR-014**: MUST excluir los precios extremos: fuera de [0,1 ×, 20 ×] la mediana del precio en USD de su ciudad, con la mediana
  calculada **solo con el entrenamiento** y aplicada igual a ambos conjuntos. *(Decisión 8.)*
- **FR-015**: MUST guardar en cada conjunto el objetivo `log(price_usd)` y el precio en USD.
- **FR-016**: MUST guardar los dos conjuntos en `data/processed/`. Ningún notebook calcula estadísticas sobre la prueba antes de
  la etapa de validación.
- **FR-017**: MUST escribir un registro de exclusiones (filas de partida, quitadas por cada regla y finales, por ciudad y por
  conjunto) y copiarlo a `reports/`.
- **FR-018**: El notebook del EDA MUST reproducir al menos estas cifras de `reports/01_eda.md`: filas por ciudad (194.628 en total);
  89.964 anfitriones; porcentaje de anuncios sin precio por ciudad; razón precio / `price_quote_price_per_night` = 1; 12 columnas
  vacías; 6.103 anuncios con `minimum_nights ≥ 30`; 692 precios > 20 × la mediana de su ciudad; 15,5 % sin reseñas.
- **FR-019**: MUST calcular la línea base (mediana de `price_usd` por ciudad × `room_type`) y su MAE en USD con validación por
  anfitrión **dentro del entrenamiento**, y anotarla en `reports/01_eda.md`.

**Pruebas**

- **FR-020**: Cada regla de FR-002 a FR-014 MUST tener una prueba automática con un caso normal y uno sucio hechos a mano.
- **FR-021**: MUST existir una prueba que verifique que ningún anfitrión cae en los dos conjuntos y que no se pierde ninguna fila
  al partir; esa prueba MUST fallar si la partición se hace por fila.
- **FR-022**: MUST existir una prueba que verifique que el resultado de la carga no contiene columnas personales ni texto libre.

### Key Entities

- **Anuncio**: una fila; un inmueble publicado en Airbnb en la fecha de corte de su ciudad. Tiene ciudad, barrio, tipo,
  capacidad, baños, reseñas y precio por noche.
- **Anfitrión** (`host_id`): dueño o administrador de uno o más anuncios; es la unidad por la que se parte. Nunca es variable del
  modelo.
- **Tabla de tasas de cambio**: una fila por ciudad con moneda, tasa a USD, fecha y fuente.
- **Conjunto de entrenamiento / de prueba**: anuncios limpios, con objetivo, sin anfitriones en común. La prueba queda cerrada.
- **Registro de exclusiones**: cuántas filas quitó cada regla, por ciudad y conjunto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los dos conjuntos se regeneran desde cero con un solo paso, sin intervención manual, en menos de 10 minutos en el
  computador de cualquier integrante.
- **SC-002**: 0 anfitriones aparecen en ambos conjuntos, y 0 filas se pierden al partir.
- **SC-003**: 0 columnas personales, de texto libre o de fuga en los conjuntos guardados.
- **SC-004**: El 100 % de las reglas de limpieza tiene al menos una prueba, y todas pasan.
- **SC-005**: Las cifras clave de FR-018 que muestra el notebook coinciden exactamente con `reports/01_eda.md` (o el informe se
  corrige con su motivo).
- **SC-006**: Los totales del registro de exclusiones cuadran: filas de partida − filas quitadas = filas finales, en cada ciudad.
- **SC-007**: Cada integrante del grupo puede explicar al menos una regla, con su cifra y su motivo, en el punto de control.

## Assumptions

- **Proporción de prueba: 20 % de los anfitriones**, semilla 42 (práctica habitual del curso; se puede cambiar antes de partir,
  nunca después de mirar la prueba).
- **Umbral de precios extremos: [0,1 ×, 20 ×] la mediana de la ciudad**, como propone el EDA (con 10 × se excluirían 1.898
  anuncios en lugar de 692). El grupo puede cambiarlo antes de implementar.
- Las 26 filas idénticas salvo el `id` y las 3.076 "unidades gemelas" **no se eliminan** en esta pieza: no hay decisión aprobada y,
  al partir por anfitrión, quedan del mismo lado.
- Agrupar categorías raras (`property_type`, barrios) e imputar vacíos **no** es parte de esta pieza: va dentro del `Pipeline` de la
  etapa 4 (decisión 11 del EDA).
- Ocupación y disponibilidad se conservan en los conjuntos como sospechosas; se miden con y sin ellas en la etapa 4.
- Una sola fecha de corte por ciudad: no hay orden temporal que respetar al partir.
- La lógica vive en `src/tarifalatam/data/`; los notebooks solo la llaman. Los archivos de `data/raw/` y `data/processed/` no se
  suben a GitHub.
