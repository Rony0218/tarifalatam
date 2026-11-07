# Despliegue de la app

> Despliegue del 2026-11-06 (clase 5). Guía: `material-del-curso/guias/streamlit-despliegue.md` y
> `material-del-curso/kit/guia-despliegue-y-presentacion.md`. La sección 5 (ensayo) la completa el grupo.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | **https://tarifalatam-unaula.streamlit.app** |
| Plataforma | Streamlit Community Cloud |
| Repo, rama y archivo principal | `Rony0218/tarifalatam`, rama `main`, `app/streamlit_app.py` |
| Versión de Python elegida | ☒ 3.12 (3.12.16 en la nube; Streamlit proponía 3.14 por defecto y se cambió)  ☐ otra |
| ¿Se comprobó en una **ventana privada**? | ☒ sí: en un navegador sin la sesión de Streamlit ni de GitHub (2026-11-06)  ☐ no |
| ¿Se desplegó? | ☒ sí  ☐ no |

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | No hay credenciales en la nube y la app no depende de la cuota de ninguna plataforma. El archivo se exportó desde la versión `champion` del registro y da en la prueba el mismo MAE que se evaluó (`reports/08_registro.md`) |
| Versiones fijadas en `app/requirements.txt` (además del `requirements.txt` de la raíz) | Streamlit Cloud lee primero el archivo que está junto a `app/streamlit_app.py`. Solo trae lo que la app carga (streamlit, pydeck, pandas, numpy, scipy, scikit-learn, lightgbm, joblib), con las mismas versiones con que se guardó el modelo: otra versión de scikit-learn o LightGBM puede fallar al cargarlo o predecir distinto. Sin MLflow, Optuna, SHAP ni Databricks la instalación tarda menos de un minuto |
| `packages.txt` con `libgomp1` | Es la librería del sistema que necesita LightGBM en Linux |
| Qué NO se subió al repo (y por qué) | `.env` (credenciales), `data/` (datos crudos y procesados: tienen `host_id` y licencia de terceros; se regeneran con el notebook 03), `mlflow_local.db` y `mlruns/` (registro local) y `models/final_pipeline.joblib` (intermedio). La app no los necesita |
| Subdominio `tarifalatam-unaula` | `tarifalatam.streamlit.app` ya estaba ocupado |
| Mapa con Carto y fuente de Google Fonts | Se cargan de internet sin token. Sin conexión la app funciona, pero sin el fondo del mapa |

## 3. Pruebas del enlace público

> **Local (2026-11-05):** con `streamlit.testing` sobre `app/streamlit_app.py`. **Enlace público (2026-11-06):** en
> https://tarifalatam-unaula.streamlit.app, desde un navegador sin sesión, con los valores por defecto del formulario
> (3 huéspedes, 1 habitación, 2 camas, 1 baño, vivienda entera, *Entire rental unit*). El modelo es el mismo; los datos de
> cada columna son los que dice la tabla.

| Caso | Datos usados | Resultado esperado | Resultado real |
|---|---|---|---|
| Normal | Local: Bogotá, Antonio Nariño, 2 huéspedes. Público: Río de Janeiro, Copacabana, valores por defecto | precio y rango en USD | local: 41 USD, rango 32 a 48 USD · **público: 80 USD, rango 58 a 102 USD**, sin advertencias (el mismo resultado que en local con esos datos) |
| Límite (cambia la decisión) | Belice, la ciudad donde el modelo falla más. Local: Belize Islands, 4 huéspedes. Público: barrio y valores por defecto | precio, rango y aviso de error alto | local: 279 USD, rango 207 a 377 USD · **público: 254 USD, rango 189 a 344 USD**, y en los dos el aviso de Belice (246 USD de error medio en la prueba) |
| Inválido (debe rechazarse con un mensaje claro) | 40 huéspedes | no da precio y dice qué corregir | local y **público: el campo de huéspedes solo admite de 1 a 16**; con `predict_price` (notebook 09) responde «Huéspedes (accommodates): debe estar entre 1 y 16» |
| Con un campo en «No sé» | Local: el caso normal con «No sé» en baños, camas y tipo de propiedad. Público: Belice con «No sé» en baños | precio sin error | local: 52 USD, rango 41 a 60 USD · **público: 263 USD**, sin errores (solo el aviso de Belice) |

## 4. Problemas encontrados y plan B

- **Errores de despliegue que aparecieron y cómo se resolvieron:** ninguno al instalar ni al arrancar. Antes de desplegar
  hubo tres ajustes: (1) Streamlit pidió conectar la cuenta de GitHub; la autorizó el dueño del repo, confirmando el acceso
  con el código que llegó a su correo; (2) el subdominio `tarifalatam` estaba ocupado y se usó `tarifalatam-unaula`;
  (3) Python venía en 3.14 por defecto y se eligió 3.12. El registro solo avisó que el repo tiene más de un archivo de
  requisitos (es lo esperado: se usa el de `app/`). Instaló con Python 3.12.16 y arrancó en menos de dos minutos.
- **Plan B** (si la app falla en vivo): captura con fecha y repo → `reports/09_captura_app_2026-11-06.jpg` (el enlace
  público funcionando el 2026-11-06); app en local → `streamlit run app/streamlit_app.py` desde la raíz del repo; y una
  copia en el servidor propio de Rony Guerrero (pendiente de configurar).

## 5. Ensayo cronometrado (clase 5)

| Parte | Tiempo previsto | Tiempo real |
|---|---|---|
| Caso de negocio | 2 min | |
| App (demo en vivo) | 4 min | |
| Resultados | 3 min | |
| Cierre | 1 min | |
| **Total** | **10 min** | |

- ¿Se pasó de 10 minutos? ☐ no  ☐ sí → qué se recortó: _______________
- Retroalimentación recibida (lo mejor y la corrección que propusieron): _______________
- **Corrección concreta que hicimos por ella:** _______________
- Quién habla de qué y quién responde las preguntas técnicas: _______________
