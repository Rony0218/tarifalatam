# Implementation Plan: Informe técnico en PDF y paquete de entrega (hito H4)

**Branch**: `004-informe-tecnico-pdf` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

## Summary

Convertir el esqueleto `reports/informe_tecnico.md` (unas 2.500 palabras, sin gráficas, ~6 a 7 páginas) en un PDF de 10 a 15
páginas con 12 figuras hechas con datos reales, corregir lo desactualizado y armar el .zip de entrega. **No se cambia el modelo,
la app ni ninguna decisión de las etapas 1 a 9**, y **la prueba no se vuelve a abrir**.

## Technical Context

- **Python 3.12** en un entorno nuevo `.venv` creado con `uv` desde `requirements.txt` (hoy el proyecto no tiene `.venv`; hace
  falta para LightGBM y para cargar el modelo).
- **Conversión a PDF**: Markdown → HTML con la librería `markdown` → PDF con el navegador en modo sin ventana
  (`--headless --print-to-pdf`). `markdown` y `pypdf` van en un archivo aparte, `requirements-informe.txt`, para no tocar las
  dependencias de la app en Streamlit Cloud. *Cambio durante la implementación (2026-11-11): Edge devuelve el control antes de
  escribir el PDF, así que se usa Chrome primero y, con Edge, el script espera a que aparezca el archivo.*
- **Gráficas**: `matplotlib` y `seaborn` (ya están en `requirements.txt`), PNG a 150 ppp en `reports/figuras/`.

## Constitution Check

| Principio | Cómo se cumple |
|---|---|
| I. Datos originales | Solo se lee `data/processed/train.csv.gz`; `data/raw/` no se toca |
| II. Partición por anfitrión | Las predicciones fuera de pliegue usan `oof_log_predictions` (pliegues por anfitrión, ya probada) |
| III. Prueba una sola vez | No se abre `test.csv.gz`; los resultados en prueba salen de tablas ya guardadas |
| IV. Decisiones con motivo | Cada figura nueva lleva una frase de qué muestra y de dónde sale |
| V. Nada sensible | Las gráficas no muestran `host_id` ni datos de anfitriones; solo agregados |
| VII. Nada inventado | Toda cifra sale de un archivo de `reports/` o del script |

## Figuras (fuente → archivo)

| # | Figura | Fuente | Sección |
|---|---|---|---|
| F1 | Anuncios y anfitriones por ciudad | `train.csv.gz` | 2 |
| F2 | Distribución del precio en USD y en logaritmo | `train.csv.gz` | 2 |
| F3 | Precio por ciudad y tipo de habitación (cajas) | `train.csv.gz` | 2 |
| F4 | **Matriz de correlación** (Spearman) de las 8 numéricas del modelo y `log_price_usd` | `train.csv.gz` | 2 |
| F5 | Concentración de anuncios por tamaño del anfitrión (motivo de partir por anfitrión) | `train.csv.gz` | 2 |
| F6 | MAE de las 5 ideas de variables frente a la referencia | `reports/04_features_tabla.csv` | 3 |
| F7 | MAE por pliegue de los 4 candidatos del torneo | `reports/05_torneo_tabla.csv` | 4 |
| F8 | MAE de cada ensayo de Optuna (60) | `reports/06_optimizacion_tabla.csv` | 5 |
| F9 | MAE por ciudad en la prueba: modelo contra línea base | `reports/07_segmentos.csv` | 6 |
| F10 | Importancia de las variables (SHAP) | `reports/07_shap_global.csv` | 6 |
| F11 | **Real contra predicho y residuos** (en lugar de la curva AUC) | según la pregunta abierta 1 | 6 |
| F12 | Captura de la app desplegada | `reports/09_captura_app_2026-11-06.jpg` (ya existe) | 8 |

## Archivos

```text
scripts/report_figures.py        # NUEVO: una función por figura (recibe un DataFrame, guarda un PNG) + main()
scripts/build_report_pdf.py      # NUEVO: informe_tecnico.md → HTML con estilos → reports/informe_tecnico.pdf
requirements-informe.txt         # NUEVO: markdown (versión fijada)
tests/test_report_figures.py     # NUEVO: cada función de figura genera un PNG con un DataFrame pequeño de prueba
reports/figuras/F01…F11.png      # GENERADO
reports/informe_tecnico.md       # SE AMPLÍA Y CORRIGE
reports/informe_tecnico.pdf      # GENERADO
entrega/Grupo8_TarifaLatam.zip   # GENERADO (en .gitignore): PDF del informe + PDF de la presentación + enlaces
```

Las funciones de figura van en `scripts/` y no en `src/`, porque solo sirven para este informe y así no se altera la estructura
obligatoria de `src/tarifalatam/`. Reutilizan `load_train`, `build_pipeline` y `oof_log_predictions` de `src/` sin cambiarlos.

## Cómo crece el informe (de ~7 a 10–15 páginas)

- **Portada** con grupo, roles, enlaces y fecha.
- **Secciones 2 a 6**: se agregan las figuras F1 a F11 y se trae el detalle que ya está escrito en `reports/01_eda.md`,
  `04_features.md`, `05_torneo.md`, `06_optimizacion.md` y `07_validacion.md` (tabla completa de las 11 decisiones del EDA,
  tabla de las 5 ideas, espacio de búsqueda, tabla por ciudad y por tipo de habitación).
- **Nota sobre la curva AUC** (FR-005) en la sección 6.
- **Sección 8**: la captura de la app.
- **Sección 10 nueva, «Cómo continuar (versión 2)»**: mapa del repositorio, cómo agregar una ciudad, qué vigilar, qué
  mejoras quedaron propuestas (marcadas como propuestas).
- Se quitan la nota de esqueleto y la lista de comprobación (quedan en el `.md`, no en el PDF).

## Riesgos

- **F11 con datos fuera de pliegue (opción A)**: los hiperparámetros se eligieron con esos mismos pliegues, así que el error se
  ve un poco más optimista que en la prueba. Se dice en el pie de la figura.
- **Edge y la conversión a PDF**: si Edge no imprime bien (márgenes, números de página), el plan B es Chrome con los mismos
  parámetros.
- **Largo**: si pasa de 15 páginas, se recortan tablas que ya están en `reports/` y se deja la referencia.
