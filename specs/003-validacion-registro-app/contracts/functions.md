# Contrato: funciones nuevas o cambiadas de `src/`

Nombres en inglés, docstrings y mensajes en español. Cada función lleva al menos una prueba (lista en `tasks.md`).

## `config.py` (se agrega, no se cambia lo anterior)

```python
TEST_MARK_PATH = REPORTS_DIR / "prueba_abierta.txt"
FINAL_EXPERIMENT = "tarifalatam-modelo-final"
REGISTERED_MODEL = "tarifalatam_precio_noche"
MODEL_ALIAS = "champion"
GOAL_IMPROVEMENT = 0.20            # meta (a): MAE al menos 20 % menor que la línea base
COST_RATIOS = ((2.0, 1.0), (1.5, 1.0), (3.0, 1.0))  # costo asimétrico: (sobrestimar, subestimar)
RANGE_QUANTILES = (0.25, 0.75)     # rango típico
SHAP_SAMPLE = 2000
VALID_RANGE = {"accommodates": (1, 16), "bedrooms": (0, 10), "beds": (0, 50), "bathrooms_count": (0, 20),
               "minimum_nights": (1, 29), "maximum_nights": (1, 1125), "latitude": (-90, 90),
               "longitude": (-180, 180), "bathroom_shared": (0, 1)}
```

## `data/pipeline.py`

- `build_unfiltered_test(raw_dir=RAW_DIR, rates=FX_RATES) -> pd.DataFrame`: la prueba con los pasos 1 a 15 y `add_target`,
  **sin** `drop_price_outliers`. `build_datasets` no cambia su resultado.

## `models/validation.py`

- `open_test(path, mark_path=TEST_MARK_PATH, purpose: str) -> pd.DataFrame`: lee la prueba y escribe o agrega la marca
  (`research.md`, punto 1). No acepta un archivo cuyo nombre no empiece por `test`.
- `to_usd_price(pred_log, factor=1.0) -> np.ndarray`: `exp(pred_log) × factor`.
- `oof_log_predictions(pipeline, X, y_log, groups, n_splits=5, seed=RANDOM_STATE) -> np.ndarray`: predicciones fuera de pliegue
  por anfitrión.
- `smearing_factor(residuals_log) -> float`: promedio de `exp(residuo)`; con residuos 0 vale 1.
- `check_log_correction(pipeline, search, reserved) -> dict`: `factor`, `mae_sin`, `mae_con`, `media`, `low`, `high`,
  `se_usa` (= `high < 0`) y las predicciones en los reservados (para el rango).
- `price_range_ratios(cities, y_true_usd, y_pred_usd, quantiles=RANGE_QUANTILES) -> dict`: `{ciudad: [p25, p75]}` de
  `real / sugerido`.
- `asymmetric_cost(y_true_usd, y_pred_usd, over=2.0, under=1.0) -> float`.
- `test_metrics(y_true_log, y_pred_log, factor=1.0) -> dict` (empieza por `test_`: en las pruebas se marca con
  `__test__ = False` para que pytest no la tome como prueba): las de `usd_metrics` + los tres costos asimétricos, en USD
  con `to_usd_price`.
- `mae_with_ci(y_true_log, y_pred_log, hosts, factor=1.0) -> dict` y `paired_mae_difference(...) -> dict`: reutilizan
  `host_bootstrap_ci`.
- `segment_errors(frame, by, true_col="price_usd", pred_col="pred_usd") -> pd.DataFrame`: `n`, `mae`, `mape`, `bias`,
  `pct_over`, `n_error_over_half`.
- `success_goal(model_mae, baseline_mae, diff_high, city_mae: pd.DataFrame) -> dict`: `a_20pct`, `b_intervalo`,
  `c_ciudades`, `ciudades_peores`, `cumple`.

## `models/interpret.py`

- `shap_values(pipeline, X) -> pd.DataFrame`: aportes en logaritmo por anuncio y por columna original (13 columnas).
- `global_importance(contributions) -> pd.DataFrame`: promedio de `|aporte|` por columna, ordenado.
- `top_contributions(contributions, row, k=5) -> pd.DataFrame`.

## `tracking/mlflow_utils.py`

- `set_experiment(name)`: en local, si el experimento no existe, lo crea con `artifact_location = (ROOT / "mlruns" /
  name).as_uri()`. En Databricks, sin cambios.

## `inference/schema.py` (reescrito)

- `build_schema(df, numeric, categorical, binary, valid_range, price_range_ratios, correction_factor=1.0, city_warnings=None,
  labels=None, city_labels=None, app_title=..., responsible_use=..., path=None) -> dict` (claves en `data-model.md`,
  sección 4). `df` es el entrenamiento; se llama con argumentos por nombre.
- `save_schema(schema, path)`, `load_schema(path)`: sin cambios de comportamiento.

## `inference/predict.py` (reescrito)

- `InputValidationError(ValueError)`, `load_model(path)`: se conservan.
- `validate_inputs(df, schema) -> list[str]`: reglas de `data-model.md`, sección 4.
- `predict_price(df, model, schema) -> pd.DataFrame`: `price_usd`, `low_usd`, `high_usd`, `city`; advertencias en
  `attrs["warnings"]`.
- Se retiran `decide_min_cost`, `_ordered_proba` y `predict_with_scores` (son de clasificación).
