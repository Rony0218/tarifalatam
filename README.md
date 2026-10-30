# TarifaLatam

> Sugiere a anfitriones e inversionistas de Airbnb en América Latina cuánto cobrar por noche, según las
> características del inmueble, su barrio y su ciudad.

**App desplegada:** _enlace público de Streamlit (se completa en la clase 5)_

## Qué contiene
Estructura obligatoria del curso. Cada carpeta tiene un propósito:

| Carpeta | Contenido |
|---|---|
| `.specify/` y `.claude/` | Entorno de IA: constitución del proyecto, Spec Kit (`/speckit-…`) y subagentes |
| `specs/` | Lo que genera Spec Kit: `spec.md`, `plan.md`, `tasks.md` de cada pieza (aparece al usarlo) |
| `especificaciones/` | Guías que se llenan **antes** de programar cada etapa |
| `data/raw/` | Datos originales, intocables |
| `data/processed/` | Datos limpios generados por el código |
| `notebooks/` | Un notebook por etapa; solo orquestan |
| `src/tarifalatam/` | Código reutilizable (data, features, models, tracking, inference) |
| `tests/` | Pruebas con `pytest` |
| `models/` | `model.joblib` y `ficha_modelo.md` |
| `app/` | `streamlit_app.py` |
| `reports/` | Una sección por hito e `informe_tecnico.md` |
| `presentacion/` | `ejecutiva.md` (máximo 5 diapositivas) |

## Datos

Fuente: [Inside Airbnb](https://insideairbnb.com/get-the-data/), licencia
[Creative Commons Atribución 4.0](https://creativecommons.org/licenses/by/4.0/). Los archivos **no se suben
al repo** (traen datos personales de los anfitriones): cada integrante los descarga y los guarda en
`data/raw/` con el nombre de la tabla, sin descomprimirlos.

| Guardar como | Ciudad | Descarga |
|---|---|---|
| `listings_rio-de-janeiro_2026-09-22.csv.gz` | Río de Janeiro | [listings.csv.gz](https://data.insideairbnb.com/brazil/rj/rio-de-janeiro/2026-09-22/data/listings.csv.gz) |
| `listings_sao-paulo_2026-09-14.csv.gz` | São Paulo | [listings.csv.gz](https://data.insideairbnb.com/brazil/sp/s%C3%A3o-paulo/2026-09-14/data/listings.csv.gz) |
| `listings_mexico-city_2026-09-23.csv.gz` | Ciudad de México | [listings.csv.gz](https://data.insideairbnb.com/mexico/df/mexico-city/2026-09-23/data/listings.csv.gz) |
| `listings_buenos-aires_2026-09-23.csv.gz` | Buenos Aires | [listings.csv.gz](https://data.insideairbnb.com/argentina/ciudad-aut%C3%B3noma-de-buenos-aires/buenos-aires/2026-09-23/data/listings.csv.gz) |
| `listings_bogota_2026-09-14.csv.gz` | Bogotá | [listings.csv.gz](https://data.insideairbnb.com/colombia/dc/bogot%C3%A1/2026-09-14/data/listings.csv.gz) |
| `listings_santiago_2026-09-23.csv.gz` | Santiago | [listings.csv.gz](https://data.insideairbnb.com/chile/rm/santiago/2026-09-23/data/listings.csv.gz) |
| `listings_belize_2026-09-25.csv.gz` | Belice | [listings.csv.gz](https://data.insideairbnb.com/belize/bz/belize/2026-09-25/data/listings.csv.gz) |

Inside Airbnb solo deja descargar gratis los cortes del último año: si estos enlaces dejan de funcionar,
pídanle los archivos a un compañero del grupo.

## Cómo ejecutarlo
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # en Mac/Linux: .venv/bin/python
cp .env.example .env     # completa PROFILE o DATABRICKS_HOST y DATABRICKS_TOKEN
python scripts/check_databricks.py
pytest
streamlit run app/streamlit_app.py
```

## De dónde viene este repositorio
Nació de la rama `feature/estudiantes` del repositorio del curso (ver `LEEME-PRIMERO.md`): una persona del grupo la clonó con
`git clone --branch feature/estudiantes --single-branch …`, la apuntó a este repo con `git remote set-url origin …` y hizo `push`. Los demás integrantes
clonan **este** repositorio. Para arrancar, sigue `material-del-curso/guias/montaje-proyecto.md`.

## Equipo
| Integrante | Rol |
|---|---|
| Rony Guerrero | Por definir |
| Carolina Jiménez | Por definir |
| Jesica Tarazona | Por definir |
| Dulce Vargas | Por definir |
| Rafael Jaramillo | Por definir |

Especificación del proyecto: [`especificacion-proyecto.md`](especificacion-proyecto.md) · Especificaciones por etapa: [`especificaciones/`](especificaciones/)
