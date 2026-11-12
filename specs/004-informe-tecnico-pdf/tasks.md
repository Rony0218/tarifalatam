---

description: "Lista de tareas del informe técnico en PDF y el paquete de entrega (hito H4)"
---

# Tasks: Informe técnico en PDF y paquete de entrega (hito H4)

**Input**: [spec.md](spec.md) y [plan.md](plan.md) de `specs/004-informe-tecnico-pdf/`

**Reglas**:

- Una tarea se marca `[X]` **solo cuando su comprobación pasa** (prueba de `pytest`, archivo generado o revisión).
- **Ninguna tarea abre `data/processed/test.csv.gz`.**
- Las tareas **(GRUPO)** son decisiones del grupo, no código.

## Fase 0 · Decisiones del grupo

- [X] T001 (GRUPO) Responder la pregunta abierta 1 de `spec.md` (F11 fuera de pliegue o lectura de la prueba). *Opción A,
  2026-11-11.*
- [X] T002 (GRUPO) Confirmar roles y nombres de los integrantes (pregunta abierta 2). *Confirmados sin cambios, 2026-11-11.*

## Fase 1 · Entorno

- [X] T003 Crear `.venv` con `uv venv --python 3.12 .venv` e instalar `requirements.txt`. **Comprobación**: `pytest` da las
  288 aprobadas y 1 omitida registradas el 2026-11-06. *Resultado (2026-11-11): 291 aprobadas, 0 omitidas; con las pruebas
  nuevas de esta pieza, 309 aprobadas.*
- [X] T004 Crear `requirements-informe.txt` con `markdown` en versión fijada e instalarlo en `.venv`.

## Fase 2 · Gráficas (US2)

- [X] T005 Escribir `tests/test_report_figures.py`: cada función de figura, con un DataFrame pequeño, crea un PNG no vacío.
  **Debe fallar primero.**
- [X] T006 [P] Figuras del EDA F1 a F5 en `scripts/report_figures.py`, leyendo solo `train.csv.gz`.
- [X] T007 [P] Figuras de modelado F6 a F8 desde `reports/04_features_tabla.csv`, `05_torneo_tabla.csv` y
  `06_optimizacion_tabla.csv`.
- [X] T008 [P] Figuras de la prueba F9 y F10 desde `reports/07_segmentos.csv` y `07_shap_global.csv`.
- [X] T009 Figura F11 según T001, reutilizando `build_pipeline` y `oof_log_predictions`.
- [X] T010 `main()` que regenera las 11 figuras en `reports/figuras/`. **Comprobación**: `pytest tests/test_report_figures.py`
  pasa y `python scripts/report_figures.py` deja 11 PNG.
- [X] T011 Verificar que las cifras de F9 coinciden con `reports/07_validacion.md` (MAE por ciudad).

## Fase 3 · Texto del informe (US1)

- [X] T012 Portada (grupo, roles de T002, enlaces, fecha) y corregir la línea de la app «aún no desplegada».
- [X] T013 Secciones 2 a 6: insertar F1 a F11 con una frase de qué muestran y traer el detalle de `reports/01_eda.md`,
  `04_features.md`, `05_torneo.md`, `06_optimizacion.md` y `07_validacion.md`.
- [X] T014 Nota de por qué no hay curva ROC/AUC (FR-005) junto a F11.
- [X] T015 Sección 8 con la captura de la app; sección 9 sin «(1) desplegar la app».
- [X] T016 Sección 10 nueva «Cómo continuar (versión 2)» con rutas que existen en el repositorio.

## Fase 4 · PDF y paquete (US1, US3)

- [X] T017 `scripts/build_report_pdf.py`: Markdown → HTML con estilos (márgenes, tablas, figuras, números de página) → PDF con
  Edge. Quita la nota de esqueleto y la lista de comprobación.
- [X] T018 Generar `reports/informe_tecnico.pdf`. **Comprobación**: entre 10 y 15 páginas sin portada (contadas con `pypdf`) y
  revisión visual de cada página.
- [X] T019 Revisión final: sin datos personales, sin credenciales, cifras iguales a `reports/07_validacion.md` y a la
  presentación.
- [X] T020 Armar `entrega/Grupo8_TarifaLatam.zip` (informe PDF, presentación PDF y un Word con los enlaces del repo y de la
  app, como pidió el instructor) y agregar `entrega/` a `.gitignore`.
- [ ] T021 (GRUPO) Leer el PDF completo y aprobarlo antes de enviar el correo.
