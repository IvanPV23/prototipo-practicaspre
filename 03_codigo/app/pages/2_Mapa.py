"""Mapa: microzonas coloreadas por nivel estimado sobre OpenStreetMap (diseño §3.2)."""

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
for _ruta in (_APP, _APP.parent / "src"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import folium
import streamlit as st
from componentes.avisos import aviso_uso_responsable, etiqueta_nivel, mostrar_error, sin_predicciones
from componentes.contexto import TTL_CACHE_S, barra_lateral, config, configurar_pagina, servicios
from streamlit_folium import st_folium
from tema import COLOR, NIVEL_COLOR, OPACIDAD_MICROZONA

from seguridad_ciudadana.formato import fecha_larga, fmt
from seguridad_ciudadana.servicios.priorizacion import SinPredicciones

TOP_ETIQUETAS = 10
ATRIBUCION_OSM = '© <a href="https://www.openstreetmap.org/copyright">colaboradores de OpenStreetMap</a>'
ATRIBUCION_TEXTO = "© colaboradores de OpenStreetMap"
ALTO_MAPA_PX = 620
ZOOM_INICIAL = 13
OPACIDAD_SIN_DATOS = 0.2

configurar_pagina("Mapa")
sel = barra_lateral()
cfg = config()
st.title("Mapa de nivel estimado por microzona")
st.caption(f"{fecha_larga(sel.fecha)} · turno {sel.turno}")


@st.cache_data(ttl=TTL_CACHE_S, show_spinner="Preparando el mapa…")
def datos_mapa(fecha: str, turno: str, pesos: tuple[float, float, float]) -> dict:
    return servicios()[0].mapa(fecha, turno, dict(zip(("w1", "w2", "w3"), pesos)))


@st.cache_data(ttl=TTL_CACHE_S, show_spinner=False)
def limite() -> dict:
    return servicios()[0].limite_geojson()


try:
    capa = datos_mapa(sel.fecha, sel.turno, sel.pesos_tupla)
except SinPredicciones as error:
    sin_predicciones(error.fecha, error.turno, error.disponibles)
    st.stop()
except Exception as error:  # noqa: BLE001
    mostrar_error("No se pudo preparar el mapa.", error)
    st.stop()

mostrar_puntos = st.toggle("Incidencias históricas (puntos)", value=False,
                           help=f"Incidencias registradas en los {cfg.app['dias_puntos_mapa']} días anteriores a la fecha.")  # fmt: skip


def estilo(feature: dict) -> dict:
    nivel = feature["properties"]["nivel"]
    if nivel not in NIVEL_COLOR:  # celda sin registros: gris claro con borde punteado para no confundirla con Bajo
        return {"fillColor": COLOR["sin_datos"], "color": "#8C8C8C", "weight": 0.5, "dashArray": "3",
                "fillOpacity": OPACIDAD_SIN_DATOS}  # fmt: skip
    return {"fillColor": NIVEL_COLOR[nivel], "color": "#5A5A5A", "weight": 0.6, "fillOpacity": OPACIDAD_MICROZONA}


centro = [sum(f["centro"][0] for f in capa["features"]) / len(capa["features"]),
          sum(f["centro"][1] for f in capa["features"]) / len(capa["features"])]  # fmt: skip
mapa = folium.Map(location=centro, zoom_start=13, tiles=None, control_scale=True)
lats = [f["centro"][0] for f in capa["features"]]
lons = [f["centro"][1] for f in capa["features"]]
mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])  # encuadre al distrito
folium.TileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", attr=ATRIBUCION_OSM, name="OpenStreetMap",
                 max_zoom=19).add_to(mapa)  # fmt: skip
folium.GeoJson(limite(), name="Límite distrital", style_function=lambda _: {"color": COLOR["primario"], "weight": 2.5,
               "fillOpacity": 0}).add_to(mapa)  # fmt: skip
geo = {"type": "FeatureCollection",
       "features": [{k: v for k, v in f.items() if k != "centro"} for f in capa["features"]]}  # fmt: skip
folium.GeoJson(
    geo, name="Microzonas", style_function=estilo,
    highlight_function=lambda _: {"weight": 2.5, "color": COLOR["primario"]},
    tooltip=folium.GeoJsonTooltip(fields=["id", "nivel", "p_texto", "sector"],
                                  aliases=["Microzona", "Nivel estimado", "Prioridad P", "Sector"]),
).add_to(mapa)  # fmt: skip
for f in capa["features"]:
    pos = f["properties"].get("posicion")
    if pos is not None and pos <= TOP_ETIQUETAS:
        folium.Marker(
            f["centro"],
            icon=folium.DivIcon(html=f'<div style="background:{COLOR["primario"]};color:#fff;border-radius:10px;'
                                     f'width:22px;height:22px;text-align:center;font:600 12px sans-serif;'
                                     f'line-height:22px;border:1px solid #fff">{pos}</div>',
                                icon_size=(22, 22), icon_anchor=(11, 11)),
            tooltip=f"#{pos} {f['properties']['id']}",
        ).add_to(mapa)  # fmt: skip
if mostrar_puntos:
    puntos = servicios()[0].puntos_recientes(sel.fecha)
    grupo = folium.FeatureGroup(name="Incidencias históricas")
    for p in puntos.itertuples(index=False):
        folium.CircleMarker([p.lat, p.lon], radius=2.5, color="#3F3F3F", weight=0.5, fill=True, fill_opacity=0.7,
                            tooltip=f"{p.fecha} · {p.turno} · {p.tipo_corto}").add_to(grupo)  # fmt: skip
    grupo.add_to(mapa)

salida = st_folium(
    mapa, height=ALTO_MAPA_PX, use_container_width=True, returned_objects=["last_active_drawing"],
    center=centro, zoom=ZOOM_INICIAL, key="mapa_microzonas",
)  # fmt: skip
st.caption(f"Mapa base: {ATRIBUCION_TEXTO} (openstreetmap.org/copyright). Límite distrital: INEI.")

leyenda = (
    "".join(f'<span class="caja" style="background:{NIVEL_COLOR[n]}"></span>{n}' for n in ("Bajo", "Medio", "Alto"))
    + f'<span class="caja" style="background:{COLOR["sin_datos"]}"></span>Sin registros en el periodo'
)
st.markdown(f'<div class="leyenda"><strong>Nivel estimado:</strong>{leyenda} · Los números indican las '
            f'{TOP_ETIQUETAS} primeras posiciones del ranking.</div>', unsafe_allow_html=True)  # fmt: skip

elegida = (salida or {}).get("last_active_drawing") or {}
props = elegida.get("properties") or {}
if props.get("id", "").startswith(cfg.microzona["prefijo_activa"]):
    st.session_state["microzona_sel"] = props["id"]
    st.markdown(
        f"Seleccionada: **{props['id']}** · {props.get('sector')} · {etiqueta_nivel(props.get('nivel'))} · "
        f"P = {props.get('p_texto')}",
        unsafe_allow_html=True,
    )
    if st.button("Ver detalle", type="primary"):
        st.switch_page("pages/3_Detalle_de_microzona.py")
elif props:
    st.info("Esa celda no tuvo registros en entrenamiento; no tiene estimación.")
else:
    st.caption("Haga clic en una microzona para seleccionarla y abrir su ficha.")

n_alto = sum(1 for f in capa["features"] if f["properties"]["nivel"] == "Alto")
n_activas = sum(1 for f in capa["features"] if f["properties"]["activa"])
st.caption(f"Resumen: {fmt(n_alto)} microzonas en nivel estimado Alto de {fmt(n_activas)} evaluadas.")
aviso_uso_responsable()
