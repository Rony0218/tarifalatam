# Contrato: archivos de salida de las etapas 4 a 6

Todas las cifras de estos archivos salen de notebooks ejecutados. Los MAE, RMSE y sesgos van en USD por noche y el MAPE en %.

## `data/processed/folds.csv` (notebook 04; no se sube a Git)

| Columna | Tipo | Nota |
|---|---|---|
| `id` | entero | Uno por anuncio del entrenamiento (118.513 filas) |
| `fold` | entero 0–4 | Pliegue de validación |

## `reports/04_features_tabla.csv` (notebook 04)

Una fila por variante y pliegue (8 variantes × 5 pliegues = 40 filas).

| Columna | Nota |
|---|---|
| `variant` | `referencia`, `idea_1_distancia`, `idea_2_amenidades`, `idea_3_capacidad`, `idea_4_anfitrion`, `idea_5_barrio`, `final`, `final_con_sospechosas` |
| `fold` | 0–4 |
| `mae`, `mape`, `rmse`, `bias`, `r2_log`, `fit_seconds` | Métricas del pliegue |

## `reports/05_torneo_tabla.csv` (notebook 05)

Una fila por modelo y pliegue (4 × 5 = 20 filas): `model` (`linea_base`, `ridge`, `random_forest`, `lightgbm`), `fold`, `mae`,
`mape`, `rmse`, `bias`, `r2_log`, `fit_seconds`.

## `reports/05_torneo_por_ciudad.csv` (notebook 05)

Una fila por modelo, pliegue y ciudad (4 × 5 × 6 = 120 filas): `model`, `fold`, `city`, `n` (anuncios de esa ciudad en el
pliegue de validación), `mae`, `bias`.

## `reports/06_optimizacion_tabla.csv` (notebook 06)

Una fila por ensayo: `model`, `trial`, `state` (`completo` / `fallido`), los hiperparámetros del ensayo, `mae`, `mae_std`, `mape`,
`rmse`, `bias`, `r2_log` y `fit_seconds`. Es la misma información que el MLflow local, guardada en el repositorio para el informe.

## `reports/06_best_params.json` (notebook 06)

```json
{
  "finalista": "<modelo que pasa a la etapa 7>",
  "parametros": {"<hiperparámetro>": "<valor>"},
  "origen_parametros": "partida | optimizados",
  "comprobacion": {
    "anfitriones_reservados": 0,
    "anuncios_reservados": 0,
    "mae_partida": 0.0,
    "mae_optimizado": 0.0,
    "diferencia_media": 0.0,
    "intervalo_95": [0.0, 0.0],
    "remuestreos": 1000,
    "semilla": 42
  },
  "regla": "Se usan los optimizados solo si todo el intervalo está por debajo de cero",
  "comparacion_finalistas": {
    "finalista_a": "<nombre>",
    "finalista_b": "<nombre>",
    "mae_a": 0.0,
    "mae_b": 0.0,
    "diferencia_media": 0.0,
    "intervalo_95": [0.0, 0.0],
    "segundos_por_pliegue": {"<nombre>": 0.0},
    "motivo_regla": "<texto de choose_finalist>"
  },
  "regla_elegiria": "<lo que elige la regla>",
  "decision_del_grupo": "<null si coincide con la regla; si no, la nota de la excepción (config.STAGE7_GROUP_NOTE)>",
  "como_se_arma": "make_model('<nombre>', parametros) de src/tarifalatam/models/tuning.py, dentro de build_pipeline",
  "parametros_fijos": {"<parámetro>": "<valor>"},
  "tracking": "local",
  "experimento": "tarifalatam-optimizacion",
  "ensayos": 60,
  "ensayos_por_finalista": 30
}
```

Los ceros son marcadores del tipo de dato, no cifras. Con un solo finalista, `comparacion_finalistas` es `null`. `comprobacion`
es la del modelo que pasa a la etapa 7. `ensayos` es el total de todos los finalistas. Todo el archivo lo escribe el notebook 06
(actualizado tras la revisión del 2026-10-31; antes no traía `regla_elegiria`, `decision_del_grupo`, `como_se_arma` ni
`parametros_fijos`).

## Ejecuciones en el MLflow local (`mlflow_local.db`, experimento `tarifalatam-optimizacion`)

| Parte | Contenido |
|---|---|
| Nombre | `<modelo>-ensayo-<nn>` (por ejemplo `lightgbm-ensayo-07`) |
| Parámetros | Los hiperparámetros del ensayo |
| Métricas | `mae`, `mae_std`, `mape`, `rmse`, `bias`, `r2_log`, `fit_seconds` (si el ensayo falla, ninguna) |
| Etiquetas | `etapa=06_optimizacion`, `modelo=<nombre>`, `variables=sin_sospechosas`, `datos=train.csv.gz`, `estado=completo` o `fallido` |

## Informes en Markdown

- `reports/04_features.md`: la plantilla actual completada (cómo se midió, tabla de ideas, decisiones con su cifra, supuestos y
  riesgos, lista final de variables).
- `reports/05_torneo.md`: tabla de negocio y técnicas, error por ciudad, comparación pareada, diferencia en dinero, finalistas y
  por qué no hay campeón.
- `reports/06_optimizacion.md`: espacio de búsqueda, presupuesto, resultados, comprobación, decisión, la excepción del grupo y la nota sobre el uso repetido
  de los anfitriones reservados.
