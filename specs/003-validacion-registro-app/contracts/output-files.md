# Contrato: archivos que deja la pieza 003

| Archivo | Lo escribe | ¿Se sube a Git? | Contenido |
|---|---|---|---|
| `reports/prueba_abierta.txt` | `open_test` (notebooks 07 y 09) | sí | una línea por lectura: fecha, hora y propósito |
| `reports/07_decisiones.json` | notebook 07, **antes** de abrir la prueba | sí | las decisiones congeladas, con el factor y el rango típico, y la hora en que se escribieron |
| `reports/07_metricas_test.json` | notebook 07 | sí | claves `decisiones` y `prueba` (`data-model.md`, secciones 2 y 3) |
| `reports/07_segmentos.csv` | notebook 07 | sí | `segmento`, `valor`, `modelo` (`final` / `linea_base`), `n`, `mae`, `mape`, `bias`, `pct_over`, `n_error_over_half` |
| `reports/07_shap_global.csv` | notebook 07 | sí | `columna`, `importancia` (promedio de \|SHAP\| en logaritmo) |
| `reports/07_validacion.md` | a mano, con cifras del notebook 07 | sí | la plantilla existente, completa |
| `models/final_pipeline.joblib` | notebook 07 | **no** (`.gitignore`) | `Pipeline` ajustado con todo el entrenamiento |
| `mlflow_local.db`, `mlruns/` | notebook 08 | **no** | seguimiento y registro local |
| `reports/08_registro.json` | notebook 08 | sí | `data-model.md`, sección 6 |
| `reports/08_registro.md` | a mano | sí | la plantilla existente, completa |
| `models/model.joblib` | notebook 09, desde `champion` | **sí** (< 100 MB) | el mismo `Pipeline` |
| `models/input_schema.json` | notebook 09 | sí | `data-model.md`, sección 4 |
| `models/ficha_modelo.md` | a mano | sí | la plantilla existente, completa |

Los JSON se escriben con `ensure_ascii=False`, `indent=2` y sin `NaN` ni infinitos (`allow_nan=False`).
