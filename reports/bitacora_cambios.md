# Bitácora de cambios — TarifaLatam

**Responsable de los próximos cambios:** Dulce Vargas
**Última actualización:** 2026-11-06 · **Rama local:** `feature/estudiantes`

Este documento deja constancia de **qué había**, **qué cambió** y **qué se agregó** al alinear este equipo con el
repositorio real del grupo (`https://github.com/Rony0218/tarifalatam`), siguiendo `LEEME-PRIMERO.md` y
`material-del-curso/guias/montaje-proyecto.md`.

---

## 1. Qué se tenía antes (commit local `248ff25`)

Era la **plantilla base del curso** (rama `feature/estudiantes`), sin el trabajo del grupo:

- Paquete genérico `src/proyecto/` (con `inference/` y `tracking/` de ejemplo).
- Especificación, `README.md`, constitución y reportes **de plantilla** (sin el caso TarifaLatam).
- Sin `src/tarifalatam/`, sin `specs/`, sin `pytest.ini`.
- Sin entorno de Python, sin `.env` y sin datos en `data/raw/`.

## 2. Qué se cambió: sincronización con el remoto del grupo

**Decisión (Dulce Vargas, 2026-11-06):** *«lo que está en el git remoto es la información real que debo tener»*. Se
clonó `Rony0218/tarifalatam` (último commit `b96efc4`, «Une la validación, el registro del modelo y la app local (PR #7)»)
y se **sobrescribió** el contenido local con él.

- Se comprobó archivo por archivo: los **255 archivos** del remoto quedaron idénticos en el equipo (0 diferencias).
- Se conservaron `.git` (historial y rama local) y `.env` (secretos).
- **Eliminado de la plantilla:** `src/proyecto/` completo (9 archivos). Lo reemplaza `src/tarifalatam/`.
- **Reemplazado por la versión del grupo:** `CLAUDE.md`, `README.md`, `especificacion-proyecto.md`, `.gitignore`,
  constitución, `especificaciones/`, los 9 notebooks, `reports/`, `app/streamlit_app.py`, `presentacion/ejecutiva.md`
  y `tests/`.
- **Agregado por el remoto:** `src/tarifalatam/`, `specs/001…003`, `pytest.ini`, `models/model.joblib`,
  `models/input_schema.json` y los reportes 00 a 09 con sus tablas.
- Los cambios están **sin commit** en el árbol de trabajo (se pueden revisar con `git status`).

Lo que el grupo ya había completado (contexto, no se tocó): caso de negocio y datos (Inside Airbnb, 7 ciudades, Buenos
Aires excluida desde 2026-10-31), problema de **regresión** sobre `price` en logaritmo, etapas 1 a 9 hechas (EDA, limpieza,
features, torneo, optimización, validación con prueba abierta una vez, registro del modelo y app local).

## 3. Qué se agregó para dejar el equipo listo (pasos de `LEEME-PRIMERO.md`)

| Paso de la guía | Estado | Qué se hizo |
|---|---|---|
| 1–2. Repo del grupo y clonar la base | Ya hecho por el grupo | El repo es `Rony0218/tarifalatam`; se clonó su contenido (sección 2) |
| 3. Nombre del paquete | Ya hecho | `src/tarifalatam/`; `CLAUDE.md` no menciona `src/proyecto/` |
| 4. Entorno de Python | **Hecho hoy** | `.venv` con Python 3.12.16 y `requirements.txt` instalado |
| 5. `.env` | **Hecho hoy** | Creado con `PYTHONUTF8=1` y `MLFLOW_FORCE_LOCAL=1`; sin credenciales; Git lo ignora |
| 6. Carpeta de Databricks | **Pendiente** | Requiere cuenta/token de Dulce (ver sección 5) |
| 7. Especificación | Ya hecho | Secciones 1 a 6 completas |
| 8. Revisar `CLAUDE.md` | Ya hecho | Usa `src/tarifalatam/` |
| 9. Datos en `data/raw/` | **Hecho hoy** | 7 archivos `listings_*.csv.gz` descargados con los enlaces del `README.md`; íntegros (`gzip -t`) y fuera de Git |
| 10. Verificar entorno | **Hecho hoy** | `verificar_entorno.py`: 8 OK · 1 aviso (Databricks sin configurar) · 1 FALTA (el remoto `origin`, ver sección 5) |
| 11. Primer commit y push | **Pendiente** | Requiere decisión de Dulce (ver sección 5) |
| 12. Entorno de IA | Ya hecho | Constitución ajustada (principios I a VII), 9 skills `/speckit-…` y 3 subagentes en `.claude/agents/` |

**Pruebas:** `pytest` → **288 aprobadas, 1 omitida, 0 fallidas** (4 min 43 s), con el entorno nuevo.

## 4. Riesgos y avisos

- **Datos personales:** los `listings` traen datos de anfitriones. Están en `data/raw/` y `.gitignore` los protege; no
  subirlos. `data/processed/` conserva `host_id` y tampoco se sube.
- **No se inventó ningún dato ni métrica.** Las cifras del proyecto vienen de los reportes del grupo.
- **Sin Databricks:** el seguimiento corre en MLflow local (`mlflow_local.db`, ignorado por Git). Los resultados de
  Databricks del grupo no se reprodujeron aquí.
- **Roles provisionales:** se asignaron al azar (sección 6); el informe técnico y la presentación aún tienen secciones `TODO`
  que dependen del grupo.

## 5. Pendientes de Dulce Vargas

1. **Apuntar `origin` al repo del grupo.** Hoy `origin` sigue en el repo del curso
   (`palenciaronald/ab-casos-avanzados2026v2`). Comando: `git remote set-url origin https://github.com/Rony0218/tarifalatam.git`.
   Con eso, `verificar_entorno.py` quedaría en 0 por arreglar.
2. **Decidir cómo entregar los cambios.** Esta rama local diverge del remoto del grupo. Lo seguro es crear una rama
   propia, hacer commit y abrir un PR; **no** hacer `push --force` sobre `main`.
3. **Databricks (opcional hasta la clase 4):** crear carpeta `curso_tarifalatam`, generar token, completar `.env` y
   probar con `python scripts/check_databricks.py`.
4. **Con el grupo:** confirmar o cambiar los roles sorteados (ver sección 6) y llenar los `TODO` restantes del informe técnico.
5. **Antes del hito H3:** borrar `material-del-curso/` y `LEEME-PRIMERO.md` (`git rm -r material-del-curso`).

## 6. Roles y estado de la app (2026-11-06)

A pedido de Dulce Vargas, los roles que estaban en «Por definir» se asignaron **por sorteo aleatorio**. Son cinco personas
para cuatro roles, así que *app* tiene dos. **Es provisional:** el grupo debe confirmarlo o cambiarlo.

| Integrante | Rol sorteado |
|---|---|
| Rony Guerrero | app |
| Carolina Jiménez | modelado |
| Jesica Tarazona | app |
| Dulce Vargas | datos |
| Rafael Jaramillo | negocio |

Cambios hechos: tabla de la sección 1 y dos filas nuevas en la sección 7 de `especificacion-proyecto.md`; tabla de roles en
`README.md`; línea de grupo en `reports/informe_tecnico.md`. Dulce Vargas también confirmó que **la app no está
desplegada** (H3 pendiente): el informe técnico lo dice así en lugar de `TODO`.

## 7. Presentación e informe técnico (2026-11-06)

A pedido de Dulce Vargas se completaron los documentos que estaban en plantilla. **No se inventó ninguna cifra**: todas salen de
`reports/07_validacion.md`, `05_torneo.md`, `06_optimizacion.md`, `08_registro.md`, `01_eda.md` y `especificacion-proyecto.md`.

| Archivo | Antes | Ahora |
|---|---|---|
| `presentacion/ejecutiva.md` | Plantilla con `TODO` | 5 diapositivas completas: problema, enfoque, resultado (41,40 frente a 57,44 USD por noche), demo y riesgos |
| `reports/informe_tecnico.md` | Esqueleto con 12 `TODO` | Las 9 secciones y el anexo de reproducción, cada decisión con su motivo |
| `reports/09_despliegue.md` | Plantilla en blanco | Estado real (no desplegada), decisiones de despliegue, pruebas locales y **plan de despliegue escrito** |

Lo que quedó **pendiente a propósito**, porque depende de hechos que aún no existen: el enlace público de la app, las pruebas en ventana
privada, la captura de pantalla (plan B), el ensayo cronometrado de 10 minutos y quién habla de qué. En la diapositiva 4 y en el
informe se dice abiertamente que la app no está desplegada. La diapositiva 3 no usa «decisiones al mes» porque no hay un volumen real
en los datos; usa anuncios con error mayor a la mitad del precio (31,0 % frente a 18,7 %).

## 9. Rama de trabajo y cambio de base (2026-11-06)

**Qué pasó.** Al apuntar `origin` al repo del grupo y hacer `git fetch`, se vio que `main` de `Rony0218/tarifalatam` ya había avanzado
**después** de la copia que habíamos tomado (`b96efc4`): Rony Guerrero fusionó el rediseño de la app con mapa de precios (PR #8), la
preparación del despliegue en Streamlit Cloud (PR #9: `app/requirements.txt`, `packages.txt`, `.streamlit/config.toml`), el contexto
del notebook 01 (PR #10) y los controles de métrica, el alcance del inversionista y la meta (PR #5). Crear la rama desde la copia
anterior habría **revertido ese trabajo** en el PR.

**Qué se hizo (esto reemplaza los puntos 1 y 2 de la sección 5).**
- `origin` apunta ahora a `https://github.com/Rony0218/tarifalatam.git`.
- Se creó la rama **`dulce/presentacion-informe-despliegue`** desde `origin/main` (`3f92789`).
- El estado anterior de la carpeta quedó guardado en `stash@{0}` (recuperable con `git stash list`) y los archivos propios en un respaldo.
- Se volvieron a aplicar solo los cambios de Dulce Vargas: `README.md`, `especificacion-proyecto.md` (merge de tres vías: conserva lo de
  Rony y agrega los roles), `presentacion/ejecutiva.md`, `reports/informe_tecnico.md`, `reports/09_despliegue.md`,
  `reports/bitacora_cambios.md` y el PDF de la presentación. Nada de `app/`, `src/` ni `tests/` se tocó.
- Se alineó el texto del inversionista con la decisión del grupo (2026-10-31): recibe el precio como insumo; el modelo no dice si un
  inmueble se paga.
- Se repitieron los casos de la app sobre la **app rediseñada**: normal 41 USD (rango 32 a 48), límite en Belice 279 USD (rango 207 a
  377) con aviso, «No sé» 52 USD; sin errores. `tests/test_inference.py`: 19 aprobadas, 1 omitida.

**Consecuencia para el despliegue.** El código de la app ya está en `main`: se puede crear la app en Streamlit Cloud **sin esperar** este
PR. Este PR solo agrega documentos.

## 10. Registro de cambios futuros

| Fecha | Responsable | Cambio | Motivo |
|---|---|---|---|
| 2026-11-06 | Dulce Vargas | Sincronización con `Rony0218/tarifalatam` (255 archivos) | El remoto del grupo es la información real |
| 2026-11-06 | Dulce Vargas | Entorno `.venv`, `.env` local, datos en `data/raw/`, bitácora | Pasos 4, 5, 9 y 10 de `LEEME-PRIMERO.md` |
| 2026-11-06 | Dulce Vargas | Roles sorteados al azar y estado de la app (no desplegada) en especificación, README e informe | Los roles estaban «Por definir»; provisional hasta confirmar con el grupo |
| 2026-11-06 | Dulce Vargas | Presentación ejecutiva, informe técnico completo y plan de despliegue (`09_despliegue.md`) | Estaban en plantilla; se llenaron con cifras de los reportes |
| 2026-11-06 | Dulce Vargas | PDF de la presentación en `presentacion/TarifaLatam_presentacion_ejecutiva.pdf` (5 páginas); verificación de la app local según la guía de validación, registro y app (normal 41 USD, rango 32 a 48; Belice con aviso; «No sé» sin error; 17 pruebas de inferencia en verde) | Se corrigió un solapamiento del pie en la diapositiva 3. No se reabrió la prueba |
| 2026-11-06 | Dulce Vargas | `origin` apunta a `Rony0218/tarifalatam`; rama `dulce/presentacion-informe-despliegue` desde `origin/main`; cambios propios reaplicados sobre la base nueva | `main` ya tenía la app rediseñada y la preparación del despliegue; la copia anterior los habría revertido |
