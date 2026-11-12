# Feature Specification: Informe técnico en PDF y paquete de entrega (hito H4)

**Feature Branch**: `004-informe-tecnico-pdf` | **Created**: 2026-11-11 | **Status**: Aprobada el 2026-11-11 (opción A en la pregunta abierta 1)

**Input**: lo que pidió el instructor al cierre de la clase del 2026-11-07 (grabación de la reunión, minuto 3:36 en adelante)
y el esqueleto existente `reports/informe_tecnico.md`.

## Lo que pidió el instructor

1. **Repositorio** (enlace) y **app** desplegada (enlace).
2. **Informe técnico en PDF**, de **10 a 15 páginas como mínimo**, con toda la trazabilidad de lo que se hizo y los resultados
   de los modelos, **con gráficas** (mencionó la matriz de correlación del EDA y la curva AUC). Criterio: que una persona que no
   participó lo lea tres meses después, entienda lo que se hizo y pueda sacar una **segunda versión**.
3. **La presentación** mostrada en clase.
4. Todo en una carpeta comprimida (**.zip**); el enlace del repositorio en un Word o en el cuerpo del correo.
5. Plazo: el fin de semana siguiente a la clase (**sábado 14 o domingo 15 de noviembre de 2026**). El informe ya dice
   «se entrega el domingo 15 de noviembre (hito H4)».

## User Scenarios

### US1 — Un tercero entiende el proyecto y puede continuarlo (prioridad P1)

Una persona ajena al grupo abre el PDF y, sin leer el código, entiende el caso, los datos, cada decisión con su motivo, los
resultados y los límites; con la guía final sabe dónde está cada cosa en el repositorio y qué haría en una versión 2.

**Prueba de aceptación**: el PDF tiene entre 10 y 15 páginas; cada sección cita su fuente en `reports/`; la sección
«Cómo continuar» nombra archivos que existen en el repositorio.

### US2 — Las gráficas muestran lo que dicen las cifras (prioridad P1)

Cada gráfica sale de datos reales del proyecto (entrenamiento procesado o tablas ya guardadas en `reports/`) y coincide con
las cifras del texto.

**Prueba de aceptación**: un script regenera todas las gráficas desde cero; las cifras de las gráficas de resultados coinciden
con `reports/07_validacion.md` y `reports/07_segmentos.csv`.

### US3 — El paquete se puede enviar (prioridad P2)

**Prueba de aceptación**: existe un .zip con el PDF del informe, el PDF de la presentación y un archivo con los enlaces del
repositorio y de la app.

## Requisitos funcionales

- **FR-001**: El PDF MUST tener entre 10 y 15 páginas (sin contar portada) y conservar las 9 secciones del esqueleto.
- **FR-002**: El PDF MUST incluir al menos: matriz de correlación de las variables numéricas del modelo, distribución del
  precio (USD y logaritmo), precio por ciudad y tipo de habitación, resultados del torneo, de la optimización, error por
  ciudad en la prueba, importancia de variables y una gráfica de precio real contra predicho con sus residuos.
- **FR-003**: Las gráficas del EDA MUST salir **solo del entrenamiento** (`data/processed/train.csv.gz`).
- **FR-004**: **La prueba MUST NOT abrirse de nuevo.** Las gráficas de resultados en la prueba salen de las tablas ya guardadas
  (`reports/07_segmentos.csv`, `reports/07_shap_global.csv`, `reports/07_metricas_test.json`).
- **FR-005**: El PDF MUST explicar en una frase por qué no hay curva ROC/AUC: es un problema de **regresión** (se predice un
  precio), y esa curva es de clasificación; su equivalente aquí es real contra predicho y residuos.
- **FR-006**: MUST corregirse lo desactualizado: la línea de encabezado que dice que la app «aún no está desplegada», la
  mejora «(1) desplegar la app» de la sección 9, la nota de esqueleto del inicio y la lista de comprobación final (no van en
  el PDF).
- **FR-007**: MUST agregarse una sección «Cómo continuar (versión 2)» basada solo en hechos del repositorio; lo que sean
  propuestas se marca como propuesta.
- **FR-008**: Ninguna cifra nueva se escribe a mano: o viene de un archivo de `reports/`, o la calcula el script de gráficas.
- **FR-009**: Sin datos personales ni credenciales; sin menciones de autoría de herramientas de IA en el texto.
- **FR-010**: Los roles del grupo y los nombres de los integrantes MUST quedar confirmados por el grupo antes de generar el
  PDF final.

## Fuera de alcance

- Volver a entrenar, cambiar el modelo, la app o cualquier decisión de las etapas 1 a 9.
- Enviar el correo (lo envía una persona del grupo).

## Preguntas abiertas (las responde el grupo antes de escribir código)

1. **Gráfica real contra predicho**: ¿(A) con predicciones fuera de pliegue en el **entrenamiento** (no toca la prueba;
   recomendado) o (B) con una lectura adicional de la prueba, declarada en el informe? **Respuesta (2026-11-11): opción A.**
2. **Roles**: ¿se confirman los roles sorteados el 2026-11-06 (app: Rony Guerrero y Jesica Tarazona; modelado: Carolina
   Jiménez; datos: Dulce Vargas; negocio: Rafael Jaramillo) y el apellido de Jesica? **Respuesta (2026-11-11): quedan así.**
