"""App de TarifaLatam: sugiere el precio por noche de un inmueble de Airbnb, con su rango típico.

- Carga `models/model.joblib` y `models/input_schema.json` desde ESTE repositorio. NO consulta Databricks ni MLflow: no
  hay credenciales en la nube y la app no depende de la cuota de ninguna plataforma.
- Valida las entradas: si un dato es imposible, explica qué corregir en vez de responder cualquier cosa.
- Ciudad y barrio se eligen fuera del formulario (un formulario de Streamlit no se actualiza al cambiar un campo), para
  que la lista de barrios y las coordenadas correspondan a la ciudad elegida.

Ejecutar en local (desde la raíz del repo):  streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "model.joblib"
SCHEMA_PATH = ROOT / "models" / "input_schema.json"
UNKNOWN = "(no sé)"

sys.path.insert(0, str(ROOT / "src"))
from tarifalatam.inference.predict import InputValidationError, load_model, predict_price  # noqa: E402
from tarifalatam.inference.schema import load_schema  # noqa: E402

FORM_NUMBERS = ["accommodates", "bedrooms", "beds", "bathrooms_count", "minimum_nights", "maximum_nights"]


@st.cache_resource
def get_model():
    return load_model(MODEL_PATH)


@st.cache_data
def get_schema() -> dict:
    return load_schema(SCHEMA_PATH)


def label(schema: dict, column: str) -> str:
    return schema.get("labels", {}).get(column, column)


def numeric_field(schema: dict, column: str, default: float | None = None, key: str | None = None):
    """Campo numérico limitado al rango POSIBLE, con una casilla «No sé» que deja el dato vacío."""
    low, high = schema["valid_range"].get(column) or schema["observed_range"][column]
    value = schema["median"][column] if default is None else default
    value = min(max(value, low), high)
    key = key or f"num_{column}"
    if st.checkbox(f"No sé: {label(schema, column).lower()}", key=f"unk_{key}"):
        return np.nan
    if column in schema.get("integer_columns", []):
        return st.number_input(label(schema, column), min_value=int(low), max_value=int(high), value=int(round(value)), step=1, key=key)
    decimals = "%.5f" if column in ("latitude", "longitude") else "%.1f"
    return st.number_input(label(schema, column), min_value=float(low), max_value=float(high), value=float(value), format=decimals, key=key)


def category_field(schema: dict, column: str):
    options = schema["categories"][column] + [UNKNOWN]
    default = schema.get("most_frequent", {}).get(column)
    index = options.index(default) if default in options else 0
    choice = st.selectbox(label(schema, column), options, index=index, key=f"cat_{column}")
    return np.nan if choice == UNKNOWN else choice


def main() -> None:
    st.set_page_config(page_title="TarifaLatam", page_icon="🏠", layout="wide")

    if not MODEL_PATH.exists() or not SCHEMA_PATH.exists():
        st.title("TarifaLatam")
        st.error("Falta `models/model.joblib` o `models/input_schema.json`. Ejecuta `notebooks/09_inferencia.ipynb` para generarlos.")
        st.stop()

    model, schema = get_model(), get_schema()
    city_names = schema.get("city_labels", {})
    st.title(schema.get("app_title", "TarifaLatam"))
    st.caption("Herramienta de apoyo: sugiere un precio de referencia. **La tarifa la decide el anfitrión.**")

    left, right = st.columns(2)
    with left:
        cities = schema["categories"]["city"]
        first = schema.get("most_frequent", {}).get("city")
        city = st.selectbox(label(schema, "city"), cities, index=cities.index(first) if first in cities else 0,
                            format_func=lambda c: city_names.get(c, c))
    with right:
        barrios = schema["neighbourhoods_by_city"].get(city, [])
        barrio = st.selectbox(label(schema, "neighbourhood_cleansed"), barrios + [UNKNOWN])
    barrio = np.nan if barrio == UNKNOWN else barrio
    box = schema["city_box"][city]
    lat0, lon0 = schema["neighbourhood_coords"].get(city, {}).get(barrio, [(box[0] + box[1]) / 2, (box[2] + box[3]) / 2]) \
        if isinstance(barrio, str) else [(box[0] + box[1]) / 2, (box[2] + box[3]) / 2]

    with st.form("inmueble"):
        cols = st.columns(3)
        with cols[0]:
            room_type = category_field(schema, "room_type")
            property_type = category_field(schema, "property_type")
            shared = st.radio(label(schema, "bathroom_shared"), ["No", "Sí", UNKNOWN], horizontal=True)
        row = {}
        for i, column in enumerate(FORM_NUMBERS):
            with cols[1 + i % 2]:
                row[column] = numeric_field(schema, column)
        with st.expander("Ubicación exacta (por defecto, el centro del barrio)"):
            row["latitude"] = numeric_field(schema, "latitude", lat0, key=f"lat_{city}_{barrio}")
            row["longitude"] = numeric_field(schema, "longitude", lon0, key=f"lon_{city}_{barrio}")
        submitted = st.form_submit_button("Sugerir precio", type="primary")

    if not submitted:
        st.info("Completa los datos y pulsa **Sugerir precio**. Marca *No sé* en lo que no conozcas.")
        with st.expander("Uso responsable"):
            st.markdown(schema.get("responsible_use", ""))
        return

    row.update({
        "city": city, "neighbourhood_cleansed": barrio, "room_type": room_type, "property_type": property_type,
        "bathroom_shared": {"No": 0, "Sí": 1}.get(shared, np.nan),
    })
    try:
        result = predict_price(pd.DataFrame([row]), model, schema)
    except InputValidationError as error:
        st.error(f"Revisa los datos: {error}")
        return

    first = result.iloc[0]
    name = city_names.get(city, city)
    st.metric("Precio sugerido por noche", f"{first['price_usd']:,} USD")
    st.write(f"**Rango típico en {name}:** de {first['low_usd']:,} a {first['high_usd']:,} USD por noche.")
    st.caption(
        "En anfitriones que el modelo no vio, la mitad de los anuncios de esta ciudad tenía su precio real dentro de ese "
        "rango (la otra mitad quedó por fuera, arriba o abajo)."
    )
    for message in result.attrs.get("warnings", []):
        st.warning(message)
    with st.expander("Uso responsable"):
        st.markdown(schema.get("responsible_use", ""))


if __name__ == "__main__":  # `streamlit run` ejecuta el archivo como programa principal
    main()
