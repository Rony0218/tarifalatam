# Quickstart: comprobar que el hito H1 funciona

## Requisitos previos

- Entorno con `requirements.txt` instalado (ver `README.md`) y `PYTHONUTF8=1` en Windows.
- Los siete `listings_<ciudad>_<fecha>.csv.gz` en `data/raw/` (enlaces en `README.md`).
- **Las cinco tasas del banco central** anotadas en `src/tarifalatam/config.py` (`FX_RATES`), con fecha y enlace. Sin ellas
  solo corren las pruebas y el notebook 02.

## 1. Pruebas (no necesitan los datos reales)

```bash
pytest
```

Esperado: todo en verde, con al menos una prueba por regla (`tests/test_cleaning.py`) y las de partición
(`tests/test_split.py`).

**Comprobación de que la prueba de partición sirve:** cambia temporalmente `split_by_host` para que parta por fila, vuelve a
ejecutar `pytest tests/test_split.py`, verifica que **falla** y deja la función como estaba.

## 2. EDA reproducible

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda.ipynb
```

Esperado: termina sin errores. La última tabla muestra cada cifra de FR-018 con "coincide = sí". La salida no muestra nombres,
fotos, URLs, teléfonos ni correos de anfitriones.

## 3. Limpieza y partición desde cero

Borra `data/processed/` (salvo `.gitkeep`) y ejecuta:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/03_preprocesamiento.ipynb
```

Esperado, en menos de 10 minutos:

- Existen `data/processed/train.csv.gz` y `test.csv.gz`.
- El notebook imprime: anfitriones en común = 0; filas de entrenamiento + prueba = filas antes de partir (menos las quitadas
  por extremos, que el registro muestra por conjunto).
- `reports/03_exclusiones.csv` existe y en cada fila `before − removed = after`.
- El notebook muestra el MAE de la línea base (USD) por pliegue y su promedio.

Si falta una tasa, el notebook se detiene con el mensaje "falta la tasa de cambio de <ciudad>". Es lo esperado.

## 4. Los originales no cambiaron

```bash
git status --short data/
```

Esperado: ninguna línea (`data/raw/` está ignorado y no se escribe en él). Para mayor seguridad, compara el tamaño y la fecha de
los siete archivos antes y después del paso 3.

## 5. Revisión antes de cerrar

- Subagente `auditor-de-fuga` sobre `src/tarifalatam/data/` y los notebooks 02 y 03.
- Subagente `revisor-de-codigo-ia` y `material-del-curso/kit/checklist-revision-ia.md`.
- Copiar a `reports/01_eda.md` las cifras confirmadas y el MAE de la línea base.
