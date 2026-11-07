# Informe técnico — TarifaLatam

> Esqueleto. Aquí **ensamblas** las secciones que ya escribiste en `reports/`; no las reescribas desde cero: tómalas, ordénalas
> y cuenta una historia coherente. **Se entrega el domingo 15 de noviembre** (hito H4).

> **Regla del informe:** **cada decisión va con su motivo.** Un resultado sin la razón de la decisión que lo produjo es solo un número.

**Grupo:** Rony Guerrero, Carolina Jiménez, Jesica Tarazona, Dulce Vargas, Rafael Jaramillo (roles asignados al azar el 2026-11-06, por confirmar: app, Rony Guerrero y Jesica Tarazona; modelado, Carolina Jiménez; datos, Dulce Vargas; negocio, Rafael Jaramillo) · **Repositorio:** <https://github.com/Rony0218/tarifalatam> · **App:** aún no desplegada (solo corre en local)

## Resumen ejecutivo

**TarifaLatam sirve como precio de referencia por noche para un anfitrión de Airbnb en cinco ciudades grandes de América
Latina, siempre con su rango típico y con la decisión final en manos del anfitrión.** En 29.721 anuncios de 13.345 anfitriones
que el modelo nunca vio, el precio sugerido se equivoca en promedio **41,40 USD por noche** frente a **57,44 USD** de una
regla simple (mediana por ciudad y tipo de habitación): **16,04 USD menos (27,9 %)**, con intervalo del 95 % de 14,36 a 17,84 USD,
y las seis ciudades mejoran. Los anuncios con un error mayor a la mitad de su precio bajan de 31,0 % a 18,7 %. El límite
principal es **Belice** (error de 246 USD por noche), además de las habitaciones de hotel y las compartidas. El modelo predice
el precio **publicado**, no el cobrado, y no responde si un inmueble se paga. **La app está desplegada** en https://tarifalatam-unaula.streamlit.app
(Streamlit Community Cloud, 2026-11-06).

## 1. Caso de negocio

> Fuente: `reports/00_caso.md` (ficha de caso aprobada).

- **Quién decide y qué:** el **anfitrión** fija su tarifa por noche (conserva la decisión final); el **inversionista** recibe ese
  precio por noche como un insumo más de sus cuentas. El modelo **no dice si un inmueble se paga**: la ocupación confiable, los
  costos y el valor de compra no están en los datos (decisión del grupo, 2026-10-31).
- **Con qué información:** las 13 características que el anfitrión conoce al publicar (ciudad, barrio, tipo de propiedad y de
  habitación, ubicación, huéspedes, habitaciones, camas, baños y noches mínima y máxima).
- **Qué cuesta equivocarse:** un precio **muy bajo** pierde ingreso cada noche reservada; uno **muy alto** deja el inmueble vacío y
  la plataforma lo baja en las búsquedas. Para el inversionista, **sobrestimar** es peor. Por eso se midió también un costo
  asimétrico 2 a 1 (subestimar cuesta el doble) con 1,5 a 1 y 3 a 1 como sensibilidad.
- **Cómo se midió el éxito:** MAE en USD por noche (se lee directo en dinero), con MAPE y R² como apoyo, contra la línea base. La
  **meta**, escrita antes de abrir la prueba (propuesta de Rafael Jaramillo, PR #5): MAE al menos 20 % menor que la línea base,
  intervalo del 95 % de la diferencia entero bajo cero y ninguna ciudad peor que la línea base.

## 2. Datos y limpieza

> Fuente: `reports/01_eda.md` y `src/tarifalatam/data/`.

- **Unidad de análisis y partición** (y por qué respeta la entidad que se repite): la unidad es **un anuncio en la fecha de
  corte de su ciudad**, pero un **anfitrión** (`host_id`) puede tener muchos anuncios (89.964 anfitriones; el 31 % de los anuncios
  es de anfitriones con 10 o más). Partir por fila pondría anuncios casi iguales del mismo anfitrión a ambos lados y inflaría la
  métrica. Por eso la partición y la validación cruzada son **por anfitrión** (`GroupShuffleSplit` y `GroupKFold`), con una prueba
  automática que verifica que ningún anfitrión cae en dos particiones. Resultado: 118.513 anuncios de entrenamiento (53.385
  anfitriones) y 29.721 de prueba (13.345 anfitriones).
- **Hallazgos y decisiones** (cada una con su motivo): se partió de 194.628 anuncios de siete ciudades (90 columnas) y quedaron
  148.234 de seis. Las 11 decisiones del EDA, aprobadas por el grupo el 2026-10-31, están completas en `reports/01_eda.md`. Las
  principales:

  | Decisión | Motivo |
  |---|---|
  | `price` es texto en seis monedas: convertir a USD con la tasa oficial del día del corte y modelar `log(price_usd)` | Una sola escala; el logaritmo reduce la asimetría de 23–160 a 0,5–2,1 |
  | Excluir los 11.642 anuncios sin precio (6,0 %) | Son anuncios inactivos; imputar el objetivo sería inventarlo |
  | Eliminar `price_quote_*` y `estimated_revenue_l365d` | Contienen el precio: fuga de información |
  | Excluir arriendos con `minimum_nights` de 30 o más (6.103) | Son arriendos mensuales, fuera del caso |
  | Excluir precios fuera de [0,1 ×; 20 ×] la mediana de su ciudad (umbral calculado en entrenamiento) | Errores de captura que dominarían el error |
  | **Excluir Buenos Aires** (2026-10-31) | El 38,6 % de sus precios son múltiplos de 764,41 ARS, una tasa sin explicación verificable, más la inflación argentina |
  | Eliminar la columna `license` | Solo existe en Bogotá: delata la ciudad y es un número de registro que identifica la propiedad |

- **Datos personales o sensibles y cómo se trataron:** los datos traen datos de anfitriones (nombres, fotos, descripciones con 91
  teléfonos y 9 correos). Se eliminan al cargar: `host_name`, `host_about`, `host_location`, `host_url`, `host_profile_url`,
  `host_profile_id`, `host_picture_url`, `host_thumbnail_url`, `listing_url`, `picture_url` y el texto libre. `host_id` se conserva
  **solo para partir** y nunca es variable del modelo. Los datos crudos y los procesados no se suben al repositorio público
  (`.gitignore`). Licencia de los datos: CC BY 4.0 (fuente: Inside Airbnb).

## 3. Variables

> Fuente: `reports/04_features.md`.

- **Referencia:** las 13 columnas conocidas al decidir, con LightGBM fijo: MAE de 39,90 ± 1,73 USD en 5 pliegues por anfitrión.
- **Ideas probadas (cinco):** cada una se aceptaba solo si la mejora superaba el ruido de la validación (mejora / ruido mayor
  que 1) y se conocía al predecir. Esa regla se escribió **antes** de medir, para no ajustarla después de ver un resultado.
- **Resultado: se descartaron las cinco** (`config.FINAL_IDEAS = ()`). Las **amenidades** fueron la más cercana: bajaron el MAE
  0,91 USD y ganaron en los 5 pliegues, pero su mejora / ruido fue 0,48. El grupo decidió aplicar la regla sin excepciones; además
  habría sumado 7 preguntas a la app.
- **Columnas prohibidas y sospechosas:** las que contienen el precio o son consecuencia de él (por ejemplo
  `estimated_occupancy_l365d`, la disponibilidad y `host_is_superhost`) no entran. Detalle en `reports/04_features.md`.

## 4. Torneo de modelos

> Fuente: `reports/05_torneo.md`.

- **Validación común:** todos los candidatos con los mismos datos y los mismos 5 pliegues por anfitrión (118.513 anuncios). La
  métrica principal es el MAE en USD; las de control son MAPE, R² sobre el logaritmo, RMSE, sesgo y error por ciudad.
- **Resultados** (media ± ruido entre pliegues):

  | Modelo | MAE (USD) |
  |---|---|
  | Bosque aleatorio | **39,67 ± 1,60** |
  | LightGBM | 39,90 ± 1,73 |
  | Ridge | 43,64 ± 1,88 |
  | Línea base (mediana por ciudad y tipo de habitación) | 55,90 ± 2,55 |

- **Finalistas y motivo:** pasan el **bosque aleatorio y LightGBM**. El bosque le gana a LightGBM en 4 de 5 pliegues, pero la
  diferencia es pequeña frente al ruido (1,13); los dos le ganan a Ridge en los 5 pliegues y a la línea base por unos 16 USD.
  El torneo descarta, no corona: la decisión final se toma tras optimizar.

## 5. Optimización y seguimiento

> Fuente: `reports/06_optimizacion.md`.

- **Método y presupuesto:** Optuna (`TPESampler`, semilla 42), **30 ensayos por finalista (60 en total)**, fijados antes de empezar.
  El espacio de búsqueda (7 parámetros de LightGBM y 3 del bosque, con sus rangos y motivos) está en `reports/06_optimizacion.md`.
- **Comprobación con datos reservados:** la mejor puntuación de una búsqueda es optimista. Por eso se reservó el **25 % de los
  anfitriones del entrenamiento** (13.347 anfitriones, 29.023 anuncios) que la búsqueda nunca vio.
- **¿La mejora fue real?** En los reservados, optimizar bajó el MAE de LightGBM de **38,86 a 38,52 USD** (intervalo de la
  diferencia [−0,64; −0,01], distinguible del ruido) y el del bosque de 38,87 a 38,70. Entre los dos optimizados hubo **empate**
  (intervalo [−0,20; +0,55]).
- **Decisión y excepción declarada:** la regla escrita elegía el bosque (más rápido de ajustar); el grupo eligió **LightGBM
  optimizado** por su MAE menor y por ser más simple de operar en la app. **Es una excepción a la regla, decidida después de ver el
  resultado**, y así queda registrada (`config.STAGE7_MODEL`).
- **Seguimiento:** las 60 ejecuciones quedaron en **MLflow local** (no en Databricks, ver sección 7), cada una con sus
  hiperparámetros, 7 métricas y etiquetas.

## 6. Validación e interpretación

> Fuente: `reports/07_validacion.md`.

- **Decisiones congeladas antes de abrir la prueba** (2026-11-05, 17:42): modelo LightGBM optimizado con las 13 columnas; **sin**
  corrección del logaritmo (con los anfitriones reservados, el factor de Duan empeoraba el MAE en 2,64 USD); entrega del precio
  redondeado al dólar con un rango típico por ciudad (percentiles 25 y 75 de real / sugerido); y la meta de éxito de la sección 1.
- **La prueba se abrió una sola vez** (18:09:33; las otras dos lecturas se declaran en `reports/07_validacion.md` y no cambiaron
  ninguna decisión).
- **Resultado en la prueba** (29.721 anuncios de 13.345 anfitriones):

  | Métrica | Modelo | Línea base |
  |---|---|---|
  | MAE (USD por noche) | **41,40** [38,29; 45,01] | 57,44 [53,18; 62,50] |
  | MAPE (%) | 31,78 | 42,39 |
  | R² (sobre el logaritmo) | 0,67 | 0,33 |
  | Anuncios con error > 50 % del precio | 5.549 (18,7 %) | 9.204 (31,0 %) |

  Diferencia de MAE: **−16,04 USD** (27,9 % menos), intervalo del 95 % por anfitrión [−17,84; −14,36]. **La meta se cumple** en
  sus tres condiciones. Se declara que la prueba excluye 86 anuncios con precio extremo; sin ese filtro el MAE sube a 56,81 USD
  (línea base 73,94).
- **Errores por segmento:** mejora en las seis ciudades. Por ciudad, el MAE va de 21,35 USD en São Paulo, 22,32 en Bogotá y 23,80
  en Santiago a 45,38 en Ciudad de México y 53,25 en Río; **Belice es el límite: 245,96 USD de error y sesgo de −110 USD**. Las
  habitaciones de hotel (76 anuncios) fallan mucho y en las **compartidas** (181) el modelo es **peor que la línea base** (15,42
  frente a 12,98). El sesgo medio es negativo en todas las ciudades: cuando subestima, se equivoca por más dinero (precios altos).
- **Interpretación y su límite:** pesan sobre todo el **tamaño** (`bedrooms`, `accommodates`, `bathrooms_count`) y la **ubicación**
  (coordenadas, barrio, ciudad). Los valores SHAP explican al **modelo**, no al mundo: no prueban causa, y latitud, longitud,
  barrio y ciudad se reparten el crédito.
- **Revisión de los subagentes:** el `auditor-de-fuga` no encontró fuga que invalide la métrica y el `revisor-de-codigo-ia`
  recomendó «aceptar con cambios»; los hallazgos y lo que se hizo están en `reports/07_validacion.md`.

## 7. Registro del modelo

> Fuente: `reports/08_registro.md` y `models/ficha_modelo.md`.

- **Dónde quedó:** modelo `tarifalatam_precio_noche`, **versión 1, alias `champion`**, en **MLflow local** (experimento
  `tarifalatam-modelo-final`). Lo registró Rony Guerrero el 2026-11-05 a las 18:12.
- **Por qué local y no Databricks:** no había conexión configurada y las 60 ejecuciones de la etapa 6 ya estaban en el local. Es una
  **excepción a la regla 7 de `CLAUDE.md`**, decidida por el grupo y anotada en `especificacion-proyecto.md`.
- **Ida y vuelta:** el modelo recuperado con `models:/tarifalatam_precio_noche@champion` predice igual que el local (200 de 200).
- **Exportación y esquema:** `models/model.joblib` (mismo MAE en la prueba) y `models/input_schema.json`, con las 13 columnas
  crudas de entrada; la salida es el logaritmo del precio en USD. Se guarda con `cloudpickle`: **solo se cargan modelos propios**,
  porque un archivo pickle puede ejecutar código al cargarse.
- **Reproducibilidad:** el registro local no se sube a Git; lo que sí está es `models/model.joblib` y la forma de regenerarlo
  (anexo).

## 8. Despliegue

> Fuente: `reports/09_despliegue.md`.

- **Estado: desplegada** el 2026-11-06 en Streamlit Community Cloud: **https://tarifalatam-unaula.streamlit.app** (repo `Rony0218/tarifalatam`, rama
  `main`, `app/streamlit_app.py`, Python 3.12). En local corre con `streamlit run app/streamlit_app.py`.
- **Decisiones de despliegue (ya aplicadas en el código):** la app carga `models/model.joblib` del repositorio y **no consulta
  Databricks**; valida las entradas y muestra un aviso de «Uso responsable».
- **Pruebas hechas (en local, 2026-11-05):** caso normal (Bogotá: 41 USD, rango 32 a 48), caso límite (Belice: 279 USD, rango 207
  a 377, con aviso de error alto), caso inválido (40 huéspedes: se rechaza) y un campo en «No sé» (52 USD, sin error). **En el
  enlace público, sin sesión (2026-11-06):** Río con los valores por defecto, 80 USD (rango 58 a 102); Belice, 254 USD con el
  aviso; «No sé» en baños, 263 USD sin error; el campo de huéspedes no admite más de 16.
- **Plan B:** captura con fecha (`reports/09_captura_app_2026-11-06.jpg`) y la app en local. Cómo se desplegó, los ajustes
  que hubo (subdominio ocupado, Python 3.12 en lugar de 3.14) y el registro están en `reports/09_despliegue.md`.

## 9. Riesgos, límites y siguientes pasos

- **Qué NO hace el modelo:** no predice el precio que se **cobrará**, sino el **publicado**; no responde si un inmueble **se paga**
  (no hay ocupación, costos ni valor de compra); no debe usarse sin revisión en **Belice**, ni para habitaciones de hotel o
  compartidas. La tarifa la decide el anfitrión.
- **Límites de los datos:** una foto de **septiembre de 2026**, sin efecto de temporada; seis ciudades (cinco grandes y Belice), no
  Buenos Aires ni ciudades intermedias como Medellín o Cartagena; hay anuncios con precios extremos.
- **Uso responsable:** el modelo no usa datos del anfitrión, pero sí la **ubicación**, así que el precio refleja las desigualdades de
  cada barrio; antes de producción hay que revisar que no se use para discriminar zonas. La app muestra siempre el rango típico.
- **Mejoras concretas y qué vigilar:** (1) desplegar la app; (2) tratar Belice aparte o restringirlo; (3) en producción, vigilar el
  **error por ciudad** con precios nuevos. Son propuestas de este documento, aún no decididas por el grupo.

## Anexo: cómo reproducir el proyecto

1. **Entorno** (Python 3.12): `uv venv --python 3.12 .venv` y `uv pip install --python .venv/Scripts/python.exe -r requirements.txt`
   (en Mac/Linux, `.venv/bin/python`).
2. **Credenciales:** copiar `.env.example` como `.env`. Sin Databricks, usar `MLFLOW_FORCE_LOCAL=1` y `PYTHONUTF8=1`.
3. **Datos:** descargar los siete `listings.csv.gz` de Inside Airbnb con los enlaces del `README.md` y guardarlos en `data/raw/` con el
   nombre de la tabla, sin descomprimir (Buenos Aires se descarga pero se excluye del modelo).
4. **Notebooks, en orden:** `01` a `09` en `notebooks/` (caso, EDA, preprocesamiento, variables, torneo, optimización, validación,
   registro, inferencia). Los notebooks solo orquestan; la lógica está en `src/tarifalatam/`. El `07` abre la prueba **una sola vez**.
5. **Pruebas:** `pytest` (288 aprobadas y 1 omitida al 2026-11-06).
6. **App:** `streamlit run app/streamlit_app.py`.

---

### Lista de comprobación antes de entregar

- [ ] Las **9 secciones** tienen contenido y **cada decisión lleva su motivo**.
- [ ] Las cifras **coinciden** con `reports/07_validacion.md` y con la presentación.
- [ ] No hay credenciales, `.env` ni datos personales.
- [x] El enlace de la app abre en una ventana privada. *(Comprobado el 2026-11-06 en un navegador sin sesión.)*
- [ ] Un tercero puede reproducir el proyecto con el anexo.
