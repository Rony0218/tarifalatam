"""App de TarifaLatam: sugiere el precio por noche de un inmueble de Airbnb, con su rango típico y un mapa de precios.

- Carga `models/model.joblib` y `models/input_schema.json` desde ESTE repositorio. NO consulta Databricks ni MLflow: no
  hay credenciales en la nube y la app no depende de la cuota de ninguna plataforma.
- Valida las entradas: si un dato es imposible, explica qué corregir en vez de responder cualquier cosa.
- El mapa colorea cada barrio por la mediana del precio por noche del ENTRENAMIENTO (solo barrios con 30 anuncios o
  más) y marca el inmueble. No muestra anuncios individuales.
- Diseño: tablero de tres columnas (inmueble · resultado · mapa), con el tema de `.streamlit/config.toml`.

Ejecutar en local (desde la raíz del repo):  streamlit run app/streamlit_app.py
"""
import html
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "model.joblib"
SCHEMA_PATH = ROOT / "models" / "input_schema.json"
UNKNOWN = "(no sé)"

sys.path.insert(0, str(ROOT / "src"))
from tarifalatam.inference.predict import InputValidationError, load_model, predict_price  # noqa: E402
from tarifalatam.inference.schema import load_schema  # noqa: E402

# Colores del tablero (lavanda, azul, amarillo, verde y coral suaves): (fondo de la tarjeta, miniatura)
PALETTE = {
    "lavender": ("#EEEEFE", "#A5A8F5"),
    "blue": ("#E6F0FD", "#7EB6F7"),
    "yellow": ("#FEF6E4", "#F5C76B"),
    "green": ("#E7F6EC", "#7FCB95"),
    "coral": ("#FDECEC", "#F28B82"),
}
# Escala del mapa: de barrios baratos (claro) a caros (oscuro), en RGB
MAP_SCALE = [(224, 231, 255), (165, 180, 252), (129, 140, 248), (99, 102, 241), (67, 56, 202)]
HOME_COLOR = (242, 114, 107)

CSS = """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1450px;}
[class*="st-key-card_"] {
  background: #FFFFFF; border: 1px solid #EEF0F7 !important; border-radius: 22px; box-shadow: 0 10px 30px rgba(45, 49, 66, .06);
  padding: 1.1rem 1.1rem 1.2rem 1.1rem;
}
div[data-testid="stForm"] {border: none; padding: 0;}
.tl-header {display: flex; align-items: center; gap: 14px; margin-bottom: 1.1rem;}
.tl-logo {width: 46px; height: 46px; border-radius: 14px; background: #7C83FD; color: #fff; display: flex;
  align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 6px 16px rgba(124, 131, 253, .35);}
.tl-brand {font-size: 1.45rem; font-weight: 800; line-height: 1.1;}
.tl-tag {color: #8A8FA8; font-size: .92rem;}
.tl-badge {margin-left: auto; background: #FFFFFF; border: 1px solid #EEF0F7; border-radius: 999px; padding: 6px 14px;
  color: #6B7090; font-size: .82rem; font-weight: 600;}
.tl-section {font-weight: 800; font-size: 1.05rem; margin: 0 0 .2rem 0;}
.tl-muted {color: #8A8FA8; font-size: .85rem;}
.tl-price-box {display: flex; align-items: center; justify-content: space-between; background: #F7F7FE; border-radius: 16px;
  padding: 14px 16px; margin: .4rem 0 .9rem 0;}
.tl-price-label {font-weight: 700;}
.tl-pill {background: #8E92F7; color: #FFFFFF; font-weight: 800; font-size: 1.65rem; border-radius: 14px; padding: 6px 16px;
  white-space: nowrap;
  box-shadow: 0 6px 16px rgba(142, 146, 247, .35);}
.tl-range {margin: .2rem 0 1rem 0;}
.tl-range-track {position: relative; height: 10px; border-radius: 999px;
  background: linear-gradient(90deg, #E0E7FF, #A5B4FC 50%, #E0E7FF);}
.tl-range-dot {position: absolute; top: -5px; width: 20px; height: 20px; margin-left: -10px; border-radius: 50%;
  background: #F2726B; border: 3px solid #FFFFFF; box-shadow: 0 2px 6px rgba(0, 0, 0, .2);}
.tl-range-labels {display: flex; justify-content: space-between; color: #6B7090; font-size: .82rem; margin-top: 6px;}
.tl-item {display: flex; align-items: center; gap: 14px; border-radius: 18px; padding: 12px; margin-bottom: 10px;}
.tl-thumb {width: 58px; height: 58px; min-width: 58px; border-radius: 14px; display: flex; align-items: center;
  justify-content: center; font-size: 28px;}
.tl-body {flex: 1;}
.tl-title {font-weight: 800;}
.tl-sub {color: #7C83FD; font-size: .78rem; font-weight: 700;}
.tl-meta {color: #6B7090; font-size: .8rem;}
.tl-value {font-weight: 800; color: #4B4F6B; white-space: nowrap;}
.tl-legend {display: flex; align-items: center; gap: 8px; color: #6B7090; font-size: .8rem; margin-top: 8px;}
.tl-legend-bar {flex: 1; height: 8px; border-radius: 999px;
  background: linear-gradient(90deg, rgb(224,231,255), rgb(129,140,248), rgb(67,56,202));}
.tl-home {display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: rgb(242,114,107);
  border: 2px solid #fff; box-shadow: 0 0 0 1px rgba(0,0,0,.15);}
</style>
"""


@st.cache_resource
def get_model():
    return load_model(MODEL_PATH)


@st.cache_data
def get_schema() -> dict:
    return load_schema(SCHEMA_PATH)


def label(schema: dict, column: str) -> str:
    return schema.get("labels", {}).get(column, column)


def usd(value: float) -> str:
    """Un monto en dólares con punto de miles, como se escribe en español: 1.234 USD."""
    return f"{value:,.0f} USD".replace(",", ".")


def numeric_field(schema: dict, column: str, default: float | None = None, key: str | None = None):
    """Campo numérico limitado al rango POSIBLE, con una casilla «No sé» que deja el dato vacío."""
    low, high = schema["valid_range"].get(column) or schema["observed_range"][column]
    value = schema["median"][column] if default is None else default
    value = min(max(value, low), high)
    key = key or f"num_{column}"
    if st.checkbox(f"No sé: {label(schema, column).lower()}", key=f"unk_{key}"):
        return np.nan
    if column in schema.get("integer_columns", []):
        return st.number_input(label(schema, column), min_value=int(low), max_value=int(high), value=int(round(value)),
                               step=1, key=key)
    decimals = "%.5f" if column in ("latitude", "longitude") else "%.1f"
    return st.number_input(label(schema, column), min_value=float(low), max_value=float(high), value=float(value),
                           format=decimals, key=key)


def category_field(schema: dict, column: str):
    options = schema["categories"][column] + [UNKNOWN]
    default = schema.get("most_frequent", {}).get(column)
    index = options.index(default) if default in options else 0
    choice = st.selectbox(label(schema, column), options, index=index, key=f"cat_{column}")
    return np.nan if choice == UNKNOWN else choice


def item_card(color: str, emoji: str, title: str, sub: str, meta: str, value: str = "") -> str:
    """Una tarjeta de color con miniatura, como las de la lista del tablero (todo el texto se escapa)."""
    background, thumb = PALETTE[color]
    esc = html.escape
    return (
        f'<div class="tl-item" style="background:{background}"><div class="tl-thumb" style="background:{thumb}">{emoji}</div>'
        f'<div class="tl-body"><div class="tl-title">{esc(title)}</div><div class="tl-sub">{esc(sub)}</div>'
        f'<div class="tl-meta">{esc(meta)}</div></div><div class="tl-value">{esc(value)}</div></div>'
    )


def range_bar(price: int, low: int, high: int) -> str:
    """Barra del rango típico con un punto en el precio sugerido (si queda fuera del rango, el punto va al borde)."""
    share = 50.0 if high <= low else min(max((price - low) / (high - low) * 100, 0), 100)
    return (
        f'<div class="tl-range"><div class="tl-range-track"><div class="tl-range-dot" style="left:{share:.1f}%"></div></div>'
        f'<div class="tl-range-labels"><span>{usd(low)}</span><span>rango típico</span><span>{usd(high)}</span></div></div>'
    )


def _scale_color(value: float, low: float, high: float) -> list:
    share = 0.0 if high <= low else min(max((value - low) / (high - low), 0.0), 1.0)
    return list(MAP_SCALE[min(int(share * len(MAP_SCALE)), len(MAP_SCALE) - 1)]) + [200]


def price_map(schema: dict, city: str, home: tuple[float, float], home_text: str) -> tuple[pdk.Deck, float, float]:
    """Mapa de la ciudad: barrios coloreados por la mediana del precio (entrenamiento) y el inmueble en coral.

    Devuelve (mapa, precio del extremo claro, precio del extremo oscuro) para la leyenda. Los extremos son los percentiles
    5 y 95 de las medianas de la ciudad, para que un barrio muy caro no deje a todos los demás del mismo color.
    """
    coords = schema["neighbourhood_coords"].get(city, {})
    prices = schema.get("neighbourhood_price", {}).get(city, {})
    rows = [
        {"lat": coords[b][0], "lon": coords[b][1], "barrio": b, "mediana": m, "n": n}
        for b, (m, n) in prices.items() if b in coords
    ]
    barrios = pd.DataFrame(rows, columns=["lat", "lon", "barrio", "mediana", "n"])
    low = float(barrios["mediana"].quantile(0.05)) if len(barrios) else 0.0
    high = float(barrios["mediana"].quantile(0.95)) if len(barrios) else 1.0
    if len(barrios):
        barrios["color"] = [_scale_color(v, low, high) for v in barrios["mediana"]]
        barrios["radius"] = np.minimum(90 + 9 * np.sqrt(barrios["n"]), 900)  # más anuncios, círculo más grande
        barrios["titulo"] = barrios["barrio"]
        barrios["detalle"] = [f"Mediana: {usd(m)} por noche · {n} anuncios" for m, n in zip(barrios["mediana"], barrios["n"])]
    home_df = pd.DataFrame([{"lat": home[0], "lon": home[1], "titulo": "Tu inmueble", "detalle": home_text}])

    lats = [c[0] for c in coords.values()] or [home[0]]
    lons = [c[1] for c in coords.values()] or [home[1]]
    span = max(np.percentile(lats, 95) - np.percentile(lats, 5), np.percentile(lons, 95) - np.percentile(lons, 5), 0.05)
    zoom = float(np.clip(math.log2(360 / span) + 1.0, 7, 13))
    layers = [
        pdk.Layer("ScatterplotLayer", barrios, get_position="[lon, lat]", get_fill_color="color", get_radius="radius",
                  pickable=True, stroked=True, get_line_color=[255, 255, 255, 230], line_width_min_pixels=1),
        pdk.Layer("ScatterplotLayer", home_df, get_position="[lon, lat]", get_fill_color=list(HOME_COLOR) + [255],
                  get_radius=260, radius_min_pixels=8, pickable=True, stroked=True, get_line_color=[255, 255, 255],
                  line_width_min_pixels=3),
    ]
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=home[0], longitude=home[1], zoom=zoom, pitch=0),
        map_provider="carto",
        map_style=pdk.map_styles.CARTO_LIGHT,  # mapa base de Carto: no necesita token
        tooltip={"html": "<b>{titulo}</b><br/>{detalle}",
                 "style": {"backgroundColor": "#2D3142", "color": "white", "borderRadius": "10px", "fontSize": "13px"}},
    )
    return deck, low, high


def main() -> None:
    st.set_page_config(page_title="TarifaLatam", page_icon="🏠", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    if not MODEL_PATH.exists() or not SCHEMA_PATH.exists():
        st.title("TarifaLatam")
        st.error("Falta `models/model.joblib` o `models/input_schema.json`. Ejecuta `notebooks/09_inferencia.ipynb` para generarlos.")
        st.stop()

    model, schema = get_model(), get_schema()
    city_names = schema.get("city_labels", {})
    st.markdown(
        '<div class="tl-header"><div class="tl-logo">🏠</div><div><div class="tl-brand">TarifaLatam</div>'
        '<div class="tl-tag">Precio sugerido por noche para inmuebles de Airbnb en seis ciudades de América Latina</div></div>'
        '<div class="tl-badge">Modelo v1 · Inside Airbnb, septiembre de 2026</div></div>',
        unsafe_allow_html=True,
    )

    col_form, col_result, col_map = st.columns([1.05, 0.95, 1.4], gap="medium")

    # --- 1. El inmueble ---------------------------------------------------------------------------------------------
    with col_form:
        with st.container(border=True, key="card_form"):
            st.markdown('<p class="tl-section">Tu inmueble</p><p class="tl-muted">Marca «No sé» en lo que no conozcas.</p>',
                        unsafe_allow_html=True)
            cities = schema["categories"]["city"]
            first = schema.get("most_frequent", {}).get("city")
            city = st.selectbox(label(schema, "city"), cities, index=cities.index(first) if first in cities else 0,
                                format_func=lambda c: city_names.get(c, c))
            barrios = schema["neighbourhoods_by_city"].get(city, [])
            # por defecto, el barrio con más anuncios de la ciudad (tiene mediana en el mapa)
            counts = {b: v[1] for b, v in schema.get("neighbourhood_price", {}).get(city, {}).items()}
            busiest = max(counts, key=counts.get) if counts else None
            barrio = st.selectbox(label(schema, "neighbourhood_cleansed"), barrios + [UNKNOWN],
                                  index=barrios.index(busiest) if busiest in barrios else 0)
            barrio = np.nan if barrio == UNKNOWN else barrio
            box = schema["city_box"][city]
            center = [(box[0] + box[1]) / 2, (box[2] + box[3]) / 2]
            lat0, lon0 = schema["neighbourhood_coords"].get(city, {}).get(barrio, center) if isinstance(barrio, str) else center

            with st.form("inmueble"):
                room_type = category_field(schema, "room_type")
                property_type = category_field(schema, "property_type")
                row = {}
                left, right = st.columns(2)
                for i, column in enumerate(["accommodates", "bedrooms", "beds", "bathrooms_count", "minimum_nights", "maximum_nights"]):
                    with (left if i % 2 == 0 else right):
                        row[column] = numeric_field(schema, column)
                shared = st.radio(label(schema, "bathroom_shared"), ["No", "Sí", UNKNOWN], horizontal=True)
                with st.expander("📍 Ubicación exacta (por defecto, el centro del barrio)"):
                    row["latitude"] = numeric_field(schema, "latitude", lat0, key=f"lat_{city}_{barrio}")
                    row["longitude"] = numeric_field(schema, "longitude", lon0, key=f"lon_{city}_{barrio}")
                submitted = st.form_submit_button("Sugerir precio", type="primary", use_container_width=True)

    name = city_names.get(city, city)
    home = (float(lat0), float(lon0))
    result, error = None, None
    if submitted:
        row.update({
            "city": city, "neighbourhood_cleansed": barrio, "room_type": room_type, "property_type": property_type,
            "bathroom_shared": {"No": 0, "Sí": 1}.get(shared, np.nan),
        })
        if not (pd.isna(row["latitude"]) or pd.isna(row["longitude"])):
            home = (float(row["latitude"]), float(row["longitude"]))
        try:
            result = predict_price(pd.DataFrame([row]), model, schema)
        except InputValidationError as exc:
            error = str(exc)

    # --- 2. El resultado --------------------------------------------------------------------------------------------
    with col_result:
        with st.container(border=True, key="card_result"):
            st.markdown('<p class="tl-section">Precio sugerido</p>', unsafe_allow_html=True)
            if error:
                st.error(f"Revisa los datos: {error}")
            elif result is None:
                st.markdown(
                    '<div class="tl-price-box"><span class="tl-price-label">Precio por noche</span>'
                    '<span class="tl-pill" style="background:#C9CBF9">— USD</span></div>'
                    '<p class="tl-muted">Completa los datos y pulsa <b>Sugerir precio</b>.</p>',
                    unsafe_allow_html=True,
                )
            else:
                first_row = result.iloc[0]
                price, low, high = int(first_row["price_usd"]), int(first_row["low_usd"]), int(first_row["high_usd"])
                st.markdown(
                    f'<div class="tl-price-box"><span class="tl-price-label">Precio por noche</span>'
                    f'<span class="tl-pill">{usd(price)}</span></div>{range_bar(price, low, high)}'
                    f'<p class="tl-muted"><b>Rango típico en {html.escape(name)}:</b> de {usd(low)} a {usd(high)} por noche. '
                    'En anfitriones que el modelo no vio, la mitad de los anuncios de esta ciudad tenía su precio real dentro '
                    'de ese rango.</p>',
                    unsafe_allow_html=True,
                )
                for message in result.attrs.get("warnings", []):
                    st.warning(message)

            cards = []
            barrio_price = schema.get("neighbourhood_price", {}).get(city, {}).get(barrio) if isinstance(barrio, str) else None
            if barrio_price:
                cards.append(item_card("lavender", "📍", barrio, name, f"{barrio_price[1]:,} anuncios en el barrio".replace(",", "."),
                                       usd(barrio_price[0])))
            else:
                cards.append(item_card("lavender", "📍", barrio if isinstance(barrio, str) else "Barrio sin indicar", name,
                                       "Pocos anuncios para dar una mediana confiable", "—"))
            city_price = schema.get("city_price", {}).get(city)
            if city_price:
                cards.append(item_card("blue", "🏙️", name, "Mediana de la ciudad",
                                       f"{city_price[1]:,} anuncios".replace(",", "."), usd(city_price[0])))
            mae = schema.get("city_mae", {}).get(city)
            if mae is not None:
                cards.append(item_card("yellow", "🎯", "Error típico aquí", "Medido en anuncios nunca vistos",
                                       "Cuánto se equivoca, en promedio, el precio sugerido", f"± {usd(mae)}"))
            if submitted and not error:
                details = [str(v) for v in (room_type, property_type) if isinstance(v, str)]
                facts = [f"{int(row[c])} {t}" for c, t in (("accommodates", "huéspedes"), ("bedrooms", "habitaciones"))
                         if not pd.isna(row[c])]
                cards.append(item_card("green", "🛏️", " · ".join(details) or "Tu inmueble", "Lo que describiste",
                                       " · ".join(facts) or "Sin capacidad indicada"))
            st.markdown('<p class="tl-muted" style="margin-top:.6rem">Referencias (precio por noche)</p>' + "".join(cards),
                        unsafe_allow_html=True)

    # --- 3. El mapa -------------------------------------------------------------------------------------------------
    with col_map:
        with st.container(border=True, key="card_map"):
            st.markdown(f'<p class="tl-section">Precio típico por barrio · {html.escape(name)}</p>'
                        '<p class="tl-muted">Mediana del precio por noche en el entrenamiento (barrios con 30 anuncios o más). '
                        'Pasa el cursor sobre un barrio para ver su cifra.</p>', unsafe_allow_html=True)
            home_text = f"{usd(int(result.iloc[0]['price_usd']))} por noche (sugerido)" if result is not None else "Aún sin precio"
            deck, low, high = price_map(schema, city, home, home_text)
            st.pydeck_chart(deck, height=560)
            st.markdown(
                f'<div class="tl-legend"><span>{usd(low)}</span><div class="tl-legend-bar"></div><span>{usd(high)}</span>'
                f'<span style="margin-left:10px"><span class="tl-home"></span> tu inmueble</span></div>',
                unsafe_allow_html=True,
            )

    with st.expander("Uso responsable"):
        st.markdown(schema.get("responsible_use", ""))


if __name__ == "__main__":  # `streamlit run` ejecuta el archivo como programa principal
    main()
