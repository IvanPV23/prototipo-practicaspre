"""Ranking: microzonas ordenadas por prioridad sugerida P para la fecha y turno elegidos (diseño §3.1)."""

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
for _ruta in (_APP, _APP.parent / "src"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import streamlit as st
from componentes.avisos import aviso_uso_responsable, mostrar_error, sin_predicciones, sin_resultados
from componentes.contexto import barra_lateral, config, configurar_pagina, ranking_df
from componentes.graficos import barra_composicion, grafico
from tema import NIVEL_COLOR, NIVEL_TEXTO, fuente_pie

from seguridad_ciudadana.formato import fecha_larga, fmt
from seguridad_ciudadana.servicios.priorizacion import SinPredicciones

configurar_pagina("Ranking")
sel = barra_lateral()
cfg = config()
st.title("Prioridad sugerida por microzona")

try:
    df = ranking_df(sel.fecha, sel.turno, sel.pesos_tupla)
except SinPredicciones as error:
    sin_predicciones(error.fecha, error.turno, error.disponibles)
    st.stop()
except Exception as error:  # noqa: BLE001
    mostrar_error("No se pudo calcular el ranking.", error)
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Microzonas evaluadas", fmt(len(df)))
k2.metric("En nivel Alto", fmt(int((df.nivel == "Alto").sum())))
k3.metric("Fecha · Turno", f"{fecha_larga(sel.fecha)[4:-5]} · {sel.turno}", help=fecha_larga(sel.fecha))
aviso_uso_responsable(compacto=True)
if sel.fecha != cfg.fecha_operativa:
    st.caption(
        "Fecha de demostración (periodo de prueba): la estimación se calculó solo con datos anteriores a ese día."
    )

opciones_top = [int(x) for x in cfg.app["opciones_top"]] + [len(df)]
sectores = ["Todos", *sorted(df.sector.unique())]


def _limpiar_filtros() -> None:
    st.session_state["filtro_sector"] = "Todos"


f1, f2, f3 = st.columns([1, 1, 1])
top = f1.selectbox("Mostrar top", opciones_top, index=opciones_top.index(int(cfg.app["top_por_defecto"])),
                   format_func=lambda n: "Todas" if n == len(df) else str(n))  # fmt: skip
sector = f2.selectbox("Filtrar por sector", sectores, key="filtro_sector")
filtrado = df if sector == "Todos" else df[df.sector == sector]
vista = filtrado.head(top)

csv = vista.assign(fecha=sel.fecha, turno=sel.turno)[
    ["posicion", "microzona_id", "sector", "nivel", "p_bajo", "p_medio", "p_alto", "r", "g", "f", "w1", "w2", "w3", "p",
     "fecha", "turno"]
].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")  # fmt: skip
f3.download_button("Descargar CSV", csv, file_name=f"ranking_{sel.fecha}_{sel.turno}.csv", mime="text/csv",
                   width="stretch")  # fmt: skip

if vista.empty:
    sin_resultados("limpiar_ranking", _limpiar_filtros)
    st.stop()

tabla = vista.assign(
    **{
        "#": vista.posicion,
        "Microzona": vista.microzona_id,
        "Sector": vista.sector,
        "Nivel estimado": vista.nivel,
        "R": [fmt(v, 2) for v in vista.r],
        "G": [fmt(v, 2) for v in vista.g],
        "F": [fmt(v, 2) for v in vista.f],
        "P": [fmt(v, 2) for v in vista.p],
    }
)[["#", "Microzona", "Sector", "Nivel estimado", "R", "G", "F", "P"]]
estilo = tabla.style.map(
    lambda n: f"background-color: {NIVEL_COLOR.get(n, '#D9D9D9')}; color: {NIVEL_TEXTO.get(n, '#1A1A1A')}",
    subset=["Nivel estimado"],
)
st.caption("Seleccione una fila para abrir su ficha de detalle.")
evento = st.dataframe(estilo, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_ranking")
filas = evento.selection.rows if evento and hasattr(evento, "selection") else []
if filas:
    elegido = vista.iloc[filas[0]].microzona_id
    st.session_state["microzona_sel"] = elegido
    if st.button(f"Ver detalle de {elegido}", type="primary"):
        st.switch_page("pages/3_Detalle_de_microzona.py")

grafico(barra_composicion(vista, "Composición de la prioridad: cuánto aporta cada componente"), key="comp")
lider = vista.iloc[0]
st.caption(
    f"Resumen: la primera posición es {lider.microzona_id} (P = {fmt(lider.p, 2)}; R aporta {fmt(lider.aporte_r, 2)}, "
    f"G {fmt(lider.aporte_g, 2)} y F {fmt(lider.aporte_f, 2)}). {fuente_pie(cfg.proyecto['fuente_cita'])}"
)
