# Especificación · Etapas 7 a 9 · Validación, registro del modelo y app local

> Se llena **antes de abrir la prueba**: el modelo final, la corrección del logaritmo, la forma de entregar el precio y la
> meta de éxito se escriben aquí y no se cambian después de ver un resultado. Es la entrada de `/speckit-specify` para la
> pieza `specs/003-validacion-registro-app/`. Los resultados van a `reports/07_validacion.md`, `08_registro.md`,
> `models/ficha_modelo.md` y a la app.
> Guía: `material-del-curso/kit/guia-validacion-registro-y-app.md` · El instructor todavía no publicó la especificación
> de estas etapas (la rama base `feature/estudiantes` sigue en `248ff25`), así que esta la arma el grupo con la forma de
> `04-features-torneo-optimizacion.md`.

**Grupo:** TarifaLatam   **Fecha:** 2026-11-05   **Estado:** ☐ borrador  ☒ aprobada por el grupo (2026-11-05)  ☐ cerrada (falta la revisión del grupo: T020, T038 y T039)

> **Cómo se llenó este borrador.** Sale de `especificacion-proyecto.md` (secciones 4 y 7), la constitución (versión
> 0.3.0), `reports/06_best_params.json`, `reports/03_exclusiones.csv` y la guía de la clase 4. **No hay cifras nuevas: la
> prueba no se abrió** (no existe `reports/prueba_abierta.txt`). **El grupo aprobó el borrador completo el 2026-11-05**
> (lo registró Rony Guerrero); las propuestas quedan como decisiones.
> Las tres preguntas de la sección 10 se respondieron el 2026-11-05 (lo registró Rony Guerrero).

## 0. Datos de entrada

- **Entrenamiento:** `data/processed/train.csv.gz`, 118.513 anuncios de 53.385 anfitriones (se lee con `load_train()`).
- **Prueba:** `data/processed/test.csv.gz`, **29.721 anuncios** de seis ciudades (Río 8.246 · São Paulo 8.283 · Ciudad de
  México 5.388 · Bogotá 3.552 · Santiago 3.399 · Belice 853). Ya excluye **86 anuncios** con precio fuera de
  [0,1 ×; 20 ×] la mediana de su ciudad en el entrenamiento (`reports/03_exclusiones.csv`, filas `price_outlier,test`).
  Antes del filtro eran 29.807.
- **`ID_COL` = `host_id`**, **`TARGET` = `log_price_usd`**. El error se mide en USD con `exp(predicción)`.
- **Las plantillas de los notebooks 07 a 09 son de clasificación** (`predict_proba`, calibración, matriz de costos,
  `train.joblib`). Este proyecto es de **regresión**: se adaptan como dice cada sección; no se crea `train.joblib` ni
  `test.joblib` (se usan los `.csv.gz`, como en las etapas 4 a 6).
- **La prueba se abre una sola vez**, en la sección 3 del notebook 07 y con la sección 1 ya congelada (principio III).

## 1. Decisiones congeladas (antes de abrir la prueba)

| Decisión | Valor | Cómo se decidió |
|---|---|---|
| Modelo final | **LightGBM** con las 13 columnas de la referencia (`config.STAGE7_MODEL`) | Etapa 6. Es una **excepción a la regla escrita, decidida después de ver el resultado** (T047): la regla elegía el bosque aleatorio. Se declara en el informe |
| Parámetros | Los **optimizados** (`reports/06_best_params.json`, ensayo 30) | En los anfitriones reservados la mejora fue distinguible del ruido: MAE de 38,86 a 38,52 USD, intervalo de la diferencia [−0,64; −0,01] |
| Corrección al volver del logaritmo | **No**, salvo que la comprobación de la sección 2 la justifique *(aprobado por el grupo el 2026-11-05)* | Ya aprobado el 2026-10-31 (especificación 04, sección 0): `exp` de la predicción se acerca a la mediana, que es lo que premia el MAE |
| Métrica principal | MAE en USD por noche | `especificacion-proyecto.md`, sección 4 |
| Métricas de control | MAPE, R² sobre el logaritmo, RMSE, sesgo medio, sesgo por ciudad y **costo 2 a 1** (con 1,5 a 1 y 3 a 1 como sensibilidad) | Las del torneo, más el control que propuso Rafael en el PR #5 (respuesta 1) |
| Forma de entregar el precio | Precio puntual redondeado al dólar **y un rango típico de su ciudad**: el precio sugerido multiplicado por los percentiles 25 y 75 de la razón *precio real / precio sugerido* en los anfitriones **reservados** de esa ciudad | Respuesta 2 del grupo (2026-11-05). El rango se mide sin la prueba |
| Meta de éxito | Se cumple si **las tres** condiciones se dan en la prueba: (a) MAE del modelo al menos **20 % menor** que el de la línea base; (b) el intervalo del 95 % de la diferencia (modelo − línea base) queda **entero bajo cero**; (c) en **ninguna ciudad** el MAE del modelo es mayor que el de la línea base | Respuesta 1 del grupo (2026-11-05): la meta del PR #5 de Rafael Jaramillo, copiada tal cual |
| Fecha y hora en que se congelan | **2026-11-05 17:42 (UTC−5)** | Aprobación de esta especificación por el grupo; la prueba seguía cerrada |

## 2. Corrección al volver del logaritmo (con los anfitriones reservados, nunca con la prueba)

En regresión no hay probabilidades que calibrar. El equivalente es revisar si `exp(predicción)` se queda corto de forma
sistemática y si conviene multiplicarlo por un factor (el de Duan, el promedio de `exp(residuo)`).

- **Datos:** los mismos 75 % de búsqueda / 25 % de anfitriones reservados de la etapa 6 (`reserve_hosts`, semilla 7).
- **Cómo:** se ajusta LightGBM optimizado con la búsqueda; el factor se calcula con los residuos de la búsqueda; se
  compara el MAE en los reservados con y sin el factor, con intervalo por anfitrión (1.000 remuestreos, semilla 42).
- **Regla (escrita antes de medir) *(aprobado por el grupo el 2026-11-05)*:** se usa el factor **solo si todo el intervalo de la diferencia de MAE
  (con factor − sin factor) queda por debajo de cero**. Si no, se mantiene la decisión aprobada: sin corrección.

## 3. La prueba, abierta una sola vez

1. Se entrena el modelo final con **todo** el entrenamiento y se guarda entero en `models/final_pipeline.joblib` (en
   `.gitignore`: es intermedio).
2. El notebook abre `test.csv.gz` y deja la marca `reports/prueba_abierta.txt` con la fecha y la hora. Si la marca ya
   existe, avisa y lo declara.
3. Se calculan, en la misma prueba: el MAE (y las de control) del modelo y de la **línea base** (mediana de `price_usd`
   por `city` × `room_type`, ajustada con todo el entrenamiento). Incluye el **costo 2 a 1**:
   `promedio de [2 × máx(sugerido − real, 0) + 1 × máx(real − sugerido, 0)]`, repetido con 1,5 a 1 y 3 a 1. El 2 a 1 es
   un supuesto del grupo, no una medición: es un control y no cambia la elección del modelo.
4. Se evalúa la **meta** (sección 1) y se escribe el veredicto, se cumpla o no.
5. **Intervalo del 95 %** del MAE del modelo, del de la línea base y de su **diferencia**, remuestreando **anfitriones
   completos** (1.000 remuestreos, semilla 42), no filas.
6. **Sensibilidad, una sola vez y sin usarla para decidir:** el MAE en la prueba **sin** el filtro de precios extremos
   (29.807 anuncios), porque la app no filtra nada.
7. Se guardan las cifras en `reports/07_metricas_test.json` y se completa `reports/07_validacion.md`.
8. **Si algo no gusta, no se vuelve a abrir la prueba para arreglarlo:** se anota como límite del modelo.

## 4. Errores por segmento

- **Segmentos:** ciudad (las seis) y `room_type`. Por segmento: anuncios, MAE, MAPE, sesgo medio y el **% de anuncios
  en que el modelo sobrestima** (para el inversionista sobrestimar es el error caro).
- **Carga de trabajo:** no aplica tal cual (el modelo no prioriza revisiones humanas). Su equivalente aquí: cuántos
  anuncios quedan con un error mayor a la mitad de su precio, por ciudad. Se reporta, no se usa para decidir.
- **Belice** ya concentraba el error en el torneo (MAE de unos 205 USD y sesgo de −73 a −83 USD): se vigila y se escribe.

## 5. Interpretación

- **Importancia global:** valores SHAP (`shap` 0.54.1 ya está en `requirements.txt`) sobre una muestra de 2.000
  anuncios del **entrenamiento**, y **dos anuncios concretos de la prueba**: uno bien predicho y uno mal predicho. Es
  explicación, no decisión: no cambia nada del modelo.
- **Límites que se escriben:** explican al modelo, no al mundo; las variables correlacionadas (latitud, longitud, barrio,
  ciudad) se reparten el crédito; una importancia alta no es causa.
- **Atributos sensibles:** el modelo no usa datos del anfitrión. Usa la **ubicación** (coordenadas y barrio): se declara
  que el precio sugerido refleja el precio de mercado del barrio, con sus desigualdades.

## 6. Registro del modelo

- **Dónde:** **MLflow local** (`mlflow_local.db`), el mismo de la etapa 6 (respuesta 3 del grupo, 2026-11-05). Motivo: no
  hay `.env` con Databricks y el seguimiento de la etapa 6 ya está ahí; la guía acepta el local como respaldo. Como
  `CLAUDE.md` (regla 7) pide Databricks, la excepción se anota en `especificacion-proyecto.md`, sección 7. El experimento se llama `tarifalatam-modelo-final`; el modelo registrado,
  `tarifalatam_precio_noche`, con alias `champion`.
- **Qué se registra:** tipo de modelo y parámetros; métricas de la prueba (con su intervalo); firma y ejemplo de entrada
  (5 filas del entrenamiento, solo las 13 columnas); etiquetas: etapa, fecha de los datos (septiembre de 2026), las seis
  ciudades y la excepción T047. Formato `cloudpickle` (el formato por defecto rechaza un `Pipeline`).
- **Ida y vuelta:** se recupera `models:/tarifalatam_precio_noche@champion` y debe predecir **igual** que el original en
  200 filas del entrenamiento.
- **Constancia:** `reports/08_registro.json` y `reports/08_registro.md`.
- **Si es local:** el MLflow de la etapa 6 (`mlflow_local.db` y `mlruns/`, 60 ejecuciones) quedó **solo en el worktree**
  `.claude/worktrees/002-…`. Se copia al checkout principal antes de registrar, para que el seguimiento y el registro
  queden juntos, y el worktree no se borra hasta comprobar la copia.

## 7. Exportación y esquema de entrada

- `models/model.joblib` se exporta **desde la versión `champion` del registro** (el registro es la fuente de verdad) y
  se sube al repositorio. Se comprueba que con él el MAE en la prueba es **idéntico** al de `07_metricas_test.json`.
- `models/input_schema.json`: las 13 columnas, sus categorías conocidas y dos tipos de rango:
  - **Rango posible** (conocimiento del grupo; fuera de él, `predict` **se niega**) *(aprobado por el grupo el 2026-11-05)*:

    | Columna | Posible | Motivo |
    |---|---|---|
    | `accommodates` | 1 a 16 | Airbnb no permite anunciar más de 16 huéspedes |
    | `bedrooms` | 0 a 10 | 0 = estudio; más de 10 se marcó como imposible en la limpieza (`MAX_BEDROOMS`) |
    | `beds` | 0 a 50 | Un inmueble para 16 huéspedes no necesita más; un valor mayor es un error de digitación |
    | `bathrooms_count` | 0 a 20 | Ídem |
    | `minimum_nights` | 1 a 29 | 30 o más es arriendo mensual y se excluyó del modelo |
    | `maximum_nights` | 1 a 1.125 | 1.125 es el máximo de Airbnb (`MAX_NIGHTS_CAP`) |
    | `latitude` / `longitude` | −90 a 90 / −180 a 180 | Lo imposible en el planeta; fuera de la ciudad es solo advertencia |

  - **Rango observado** en el entrenamiento: fuera de él, solo una **advertencia**.
  - **Barrio y ciudad deben coincidir**: un barrio de otra ciudad es un error, no una advertencia.

## 8. Predicción y app local

- `src/tarifalatam/inference/` se adapta a **regresión**: `predict_price` devuelve el precio sugerido en USD por noche,
  redondeado al dólar, su rango típico (sección 1) y las advertencias; con un dato imposible lanza `InputValidationError` con un
  mensaje que dice qué corregir. Lo de clasificación (probabilidades, matriz de costos, "revisar") se retira.
- La app (`app/streamlit_app.py`) carga `models/model.joblib` y el esquema desde el repositorio, **no consulta
  Databricks**, pide primero la ciudad y ofrece solo los barrios de esa ciudad, tiene casilla «No sé» en cada campo,
  muestra el precio con su rango y un **aviso de uso responsable** (es un precio de referencia: la tarifa la fija el
  anfitrión, y el modelo no dice si un inmueble se paga), y avisa cuando la ciudad es Belice (el error ahí es mucho mayor).
- **Hoy la app solo corre en local.** Para mañana se comprueba que `requirements.txt` está en la raíz y que
  `models/model.joblib` y `models/input_schema.json` no están en `.gitignore`.

## 9. Pruebas automáticas que deben existir

- ☒ `predict_price` **rechaza** un dato imposible (p. ej. `accommodates = 40`) con un mensaje claro.
- ☒ `predict_price` **acepta** una fila incompleta («No sé»: un número vacío y una categoría desconocida).
- ☒ `predict_price` rechaza un barrio que no pertenece a la ciudad.
- ☒ `build_schema` guarda y recarga lo mismo (columnas, categorías, rangos, barrios por ciudad).
- ☒ Una prueba con **una fila real** del entrenamiento y el modelo exportado (se salta si `models/model.joblib` no existe).
- ☒ Intervalo por anfitrión de la prueba: remuestrea anfitriones, no filas (ya existe para la etapa 6; se reutiliza).
- ☒ El factor de corrección del logaritmo: con residuos nulos vale 1.
- ☒ El costo 2 a 1: un caso calculado a mano (sobrestimar 10 USD cuesta 20; subestimar 10 USD cuesta 10).
- ☒ El rango típico: con razones conocidas devuelve sus percentiles 25 y 75, y el precio sugerido queda dentro del rango.
- ☒ La meta: un caso que cumple las tres condiciones y uno que falla cada una.
- ☒ Ninguna función de `src/` abre la prueba salvo la de la etapa 7 (se ajusta `tests/test_no_test_set.py`).
- ☒ `pytest` en verde desde la raíz (281 pruebas el 2026-11-05).

## 10. Respuestas del grupo (2026-11-05)

1. **Meta de éxito:** la del PR #5 de Rafael Jaramillo (sección 1), con el costo 2 a 1 como control. El PR #5 sigue
   abierto con conflictos; aquí se copia la meta y el PR se resuelve aparte.
2. **Forma de entregar el precio:** precio puntual redondeado al dólar y rango típico de su ciudad (percentiles 25 y 75,
   medidos en los anfitriones reservados).
3. **Registro:** MLflow local, el mismo de la etapa 6.
4. **Quién implementa:** se reparte al aprobar `tasks.md`. *Pendiente.*

## 11. Entradas y salidas

| | Ruta |
|---|---|
| Entradas | `data/processed/train.csv.gz`, `data/processed/test.csv.gz` (una vez), `reports/06_best_params.json` |
| Validación y prueba | `src/tarifalatam/models/` (evaluación, intervalo, factor del logaritmo) → `notebooks/07_validacion_interpretacion.ipynb` |
| Registro | `src/tarifalatam/tracking/mlflow_utils.py` → `notebooks/08_registro_modelo.ipynb` |
| Inferencia | `src/tarifalatam/inference/` (`schema.py`, `predict.py`) → `notebooks/09_inferencia.ipynb` |
| App | `app/streamlit_app.py` |
| Salidas | `reports/prueba_abierta.txt`, `07_metricas_test.json`, `07_validacion.md`, `08_registro.json`, `08_registro.md`; `models/model.joblib`, `models/input_schema.json`, `models/ficha_modelo.md` |

**Fuera de alcance:** el despliegue en Streamlit Community Cloud y la presentación (pieza 004, hito H3, viernes 6 de
noviembre); el informe técnico (H4); volver a medir variables, modelos o parámetros.

## 12. Criterios de cierre (hito H2)

- ☒ Decisiones congeladas escritas (sección 1) **antes** de abrir la prueba, con fecha y hora. *(Congeladas a las 17:42;
  `reports/07_decisiones.json` escrito a las 18:09:30; apertura a las 18:09:33.)*
- ☒ Prueba abierta una sola vez (`reports/prueba_abierta.txt`), con intervalo por anfitrión y comparación con la línea base.
  *(MAE 41,40 [38,29; 45,01] frente a 57,44; diferencia −16,04 [−17,84; −14,36]; la meta se cumple. La segunda línea de la
  marca es la comprobación del archivo exportado, que no decide nada.)*
- ☒ Error por ciudad y por tipo de habitación, e interpretación con sus límites, en `reports/07_validacion.md`.
- ☒ Modelo registrado con versión y alias `champion`, con la ida y vuelta comprobada (`reports/08_registro.md`). *(Versión 1;
  200 de 200 iguales.)*
- ☒ `models/model.joblib` exportado desde el `champion` y con el mismo MAE en la prueba. *(41,399173 USD en los dos; 10,3 MB.)*
- ☒ `models/ficha_modelo.md` completada a mano con cifras medidas.
- ☒ `pytest` en verde. *(281 pruebas.)*
- ☒ La app corre en local: responde con datos normales, con «No sé» y se niega con un dato imposible. *(Probada con
  `streamlit.testing`; casos en `reports/09_despliegue.md`, sección 3. Falta que el grupo la abra con `streamlit run`.)*
- ☒ Revisión con `auditor-de-fuga` y `revisor-de-codigo-ia` antes de cerrar. *(2026-11-05: sin fuga; "aceptar con cambios",
  cambios atendidos en `reports/07_validacion.md`, sección "Revisión de los subagentes".)*
- ☒ Toda cifra de los informes sale de un notebook ejecutado (ninguna inventada).
