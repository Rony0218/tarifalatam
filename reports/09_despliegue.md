# Despliegue de la app

> **Estado al 2026-11-06: la app NO está desplegada** (confirmado por Dulce Vargas). Este informe registra lo que sí se hizo
> (pruebas en local) y deja el **plan de despliegue escrito** (apartado 4). Los campos del enlace público quedan en blanco a propósito:
> no se inventan. Se completan cuando se despliegue.
> Guía paso a paso: `material-del-curso/guias/streamlit-despliegue.md` y `material-del-curso/kit/guia-despliegue-y-presentacion.md`.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | **Ninguno todavía** (no desplegada) |
| Plataforma | Streamlit Community Cloud |
| Repo, rama y archivo principal | Previstos: `Rony0218/tarifalatam`, rama `main`, `app/streamlit_app.py` (por confirmar al desplegar) |
| Versión de Python elegida | ☒ 3.12 (prevista; es la del curso y la de `requirements.txt`) |
| ¿Se comprobó en una **ventana privada**? | ☐ sí  ☒ no (no hay enlace aún) |
| ¿Se desplegó? | ☐ sí  ☒ no → **plan B** (apartado 4) |

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | La app pública no debe llevar credenciales ni depender de una cuenta personal; además el registro del modelo es local (`reports/08_registro.md`). Regla 8 de `CLAUDE.md` |
| Versiones fijadas en `app/requirements.txt` (solo lo que usa la app) y en `requirements.txt` (todo el proyecto) | Streamlit Community Cloud lee primero el archivo que está junto a `streamlit_app.py`; el modelo debe cargarse con las mismas versiones con que se entrenó (`scikit-learn==1.9.1`, `lightgbm==4.7.0`, `streamlit==1.66.0`). La app no necesita MLflow, Optuna, SHAP ni Databricks. Preparado por Rony Guerrero (PR #9) |
| `packages.txt` con `libgomp1` y `.streamlit/config.toml` | LightGBM necesita la librería del sistema `libgomp1` en el servidor de Streamlit; el archivo `config.toml` fija el tema de la app. Preparados por Rony Guerrero (PR #9) |
| Qué NO se subió al repo (y por qué) | `.env` (credenciales), `data/raw/` y `data/processed/` (datos de anfitriones; el repo es público), `mlflow_local.db` y `mlruns/` (registro local), `models/final_pipeline.joblib` (pesado e innecesario para la app). Todo está en `.gitignore` |
| `models/model.joblib` (10 MB) **sí** se sube y no está ignorado | Es lo único que la app necesita para predecir; se comprobó con `git check-ignore` que `.gitignore` no lo cubre |
| La app valida las entradas y muestra «Uso responsable» y avisos por ciudad | Regla 8 de `CLAUDE.md`; el modelo falla más en Belice y debe decirse en la propia app |

## 3. Pruebas del enlace público

> **En local, con `streamlit.testing`:** los cuatro casos se probaron el 2026-11-05 sobre la primera versión de la app y se
> **repitieron el 2026-11-06 sobre la app rediseñada de `main` (tablero con mapa, PR #8): los resultados fueron los mismos.** Falta
> repetirlos en el enlace público y agregar la columna de ese resultado.

| Caso | Datos usados | Resultado esperado | Resultado real |
|---|---|---|---|
| Normal | Bogotá, barrio Antonio Nariño, vivienda entera (*Entire rental unit*), 2 huéspedes; lo demás con sus valores por defecto | precio y rango en USD | local: 41 USD por noche, rango típico 32 a 48 USD, sin advertencias |
| Límite (cambia la decisión) | Belice, barrio Belize Islands, vivienda entera, 4 huéspedes (la ciudad donde el modelo falla más) | precio, rango y aviso de error alto | local: 279 USD, rango 207 a 377 USD y el aviso de Belice (246 USD de error medio en la prueba) |
| Inválido (debe rechazarse con un mensaje claro) | 40 huéspedes | no da precio y dice qué corregir | local: el campo de huéspedes solo admite de 1 a 16; con `predict_price` (notebook 09) responde «Huéspedes (accommodates): debe estar entre 1 y 16» |
| Con un campo en «No sé» | el caso normal con «No sé» en baños, camas y tipo de propiedad | precio sin error | local: 52 USD, sin errores (2026-11-06; el rango no se volvió a leer en la app nueva) |

## 4. Problemas encontrados y plan B

- Errores de despliegue que aparecieron y cómo se resolvieron: **ninguno registrado, porque todavía no se intentó desplegar.**
- **Plan B** (si la app falla en vivo): captura de pantalla de la app con fecha (**pendiente de tomar**) y la app en local con
  `streamlit run app/streamlit_app.py` (comprobado en local el 2026-11-05).
- **Plan de despliegue escrito** (la app no se desplegó; no hubo error que reportar, solo falta ejecutar estos pasos):
  1. **Repositorio público con los archivos correctos.** Ya está: `main` de `Rony0218/tarifalatam` trae la app rediseñada
     (PR #8) y la preparación del despliegue (PR #9: `app/requirements.txt`, `packages.txt`, `.streamlit/config.toml`). Para
     desplegar **no hace falta** esperar los documentos de este informe (van en otro PR). Comprobar en el navegador que aparecen
     `app/streamlit_app.py`, `app/requirements.txt`, `models/model.joblib`, `models/input_schema.json` y `src/tarifalatam/`.
  2. **Cuenta en Streamlit Community Cloud** conectada al GitHub de quien tenga el repo (el repo debe ser público).
  3. **Crear la app:** repo `Rony0218/tarifalatam`, rama `main`, archivo principal `app/streamlit_app.py`, Python 3.12, *Deploy*.
  4. **Si falla:** leer los registros de abajo hacia arriba. Causas más probables según la guía: falta una librería en
     `requirements.txt` (`ModuleNotFoundError`) o versiones distintas de scikit-learn o LightGBM (`InconsistentVersionWarning`).
  5. **Probar en ventana privada** los cuatro casos del apartado 3 y agregar la columna con el resultado del enlace público.
  6. **Pegar el enlace** en `README.md`, en `reports/informe_tecnico.md` (sección 8) y en `presentacion/ejecutiva.md` (diapositiva 4).
  - **Riesgo a vigilar:** la app importa `src/tarifalatam/`; Streamlit Cloud debe poder encontrarla (la app añade `src/` al
    `sys.path`). Si el modelo exige otra librería no listada, hay que añadirla a `requirements.txt` y volver a subir.

## 5. Ensayo cronometrado (clase 5)

| Parte | Tiempo previsto | Tiempo real |
|---|---|---|
| Caso de negocio | 2 min | |
| App (demo en vivo) | 4 min | |
| Resultados | 3 min | |
| Cierre | 1 min | |
| **Total** | **10 min** | |

> **El ensayo no se ha hecho** (no hay tiempos reales ni retroalimentación). Estos campos se llenan con el ensayo, no antes.

- ¿Se pasó de 10 minutos? **Pendiente** (falta el ensayo)
- Retroalimentación recibida (lo mejor y la corrección que propusieron): **pendiente**
- **Corrección concreta que hicimos por ella:** **pendiente**
- Quién habla de qué y quién responde las preguntas técnicas: **por acordar en el grupo.** Los roles sorteados (`especificacion-proyecto.md`,
  sección 1) pueden servir de punto de partida: negocio (Rafael) para el caso, app (Rony y Jesica) para la demo, modelado (Carolina)
  para resultados y datos (Dulce) para las preguntas sobre la limpieza.
