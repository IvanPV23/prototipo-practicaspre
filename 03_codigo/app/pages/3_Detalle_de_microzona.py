"""Detalle de microzona: ficha explicable de la prioridad sugerida (diseño §3.3)."""

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
for _ruta in (_APP, _APP.parent / "src"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from componentes.avisos import aviso_uso_responsable, etiqueta_nivel, mostrar_error, sin_predicciones
from componentes.contexto import barra_lateral, config, configurar_pagina, ranking_df, servicios
from componentes.graficos import barras_componentes, barras_probabilidad, grafico
from tema import COLOR, fuente_pie

from seguridad_ciudadana.formato import fecha_larga, fmt
from seguridad_ciudadana.servicios.priorizacion import SinPredicciones

configurar_pagina("Detalle de microzona")
sel = barra_lateral()
cfg = config()
consultas = servicios()[0]
st.title("Detalle de microzona")

try:
    ranking = ranking_df(sel.fecha, sel.turno, sel.pesos_tupla)
except SinPredicciones as error:
    sin_predicciones(error.fecha, error.turno, error.disponibles)
    st.stop()

opciones = ranking.microzona_id.tolist()  # en orden de prioridad
if st.session_state.get("microzona_sel") not in opciones:
    st.session_state["microzona_sel"] = opciones[0]
st.session_state["microzona_sel"] = st.session_state["microzona_sel"]
etiquetas = {m: f"#{p} · {m} · {s}" for m, p, s in zip(ranking.microzona_id, ranking.posicion, ranking.sector)}
microzona = st.selectbox("Microzona (ordenadas por prioridad)", opciones, key="microzona_sel",
                         format_func=lambda m: etiquetas[m])  # fmt: skip

try:
    with st.spinner("Cargando ficha…"):
        det = consultas.detalle(microzona, sel.fecha, sel.turno, sel.pesos)
except Exception as error:  # noqa: BLE001
    mostrar_error("No se pudo cargar la ficha de la microzona.", error)
    st.stop()

st.markdown(
    f"### {det.microzona_id} · {det.sector} · Nivel estimado: {etiqueta_nivel(det.nivel)} · "
    f"Prioridad P = {fmt(det.p, 2)} (#{det.posicion} de {det.total})",
    unsafe_allow_html=True,
)
st.caption(f"{fecha_larga(det.fecha)} · turno {det.turno}. Celda de 500 m; el sector es referencial.")
aviso_uso_responsable(compacto=True)

c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("#### ¿Por qué esta prioridad?")
    filas = [
        {"Componente": f"{c['componente']} ({c['nombre'].lower()})", "Valor": fmt(c["valor"], 2),
         "Peso": fmt(c["peso"], 2), "Aporte = valor × peso": fmt(c["aporte"], 3)}
        for c in det.componentes
    ]  # fmt: skip
    filas.append(
        {"Componente": "P (prioridad sugerida)", "Valor": "", "Peso": "", "Aporte = valor × peso": fmt(det.p, 3)}
    )
    st.table(pd.DataFrame(filas).set_index("Componente"))
    grafico(barras_componentes(det.componentes), key="det_comp")
    p = det.probabilidades
    st.caption(
        f"Probabilidades del modelo: Bajo {fmt(p['Bajo'], 2)} · Medio {fmt(p['Medio'], 2)} · Alto {fmt(p['Alto'], 2)}. "
        "R = 0·Bajo + 0,5·Medio + 1·Alto."
    )
with c2:
    grafico(barras_probabilidad(det.probabilidades), key="det_prob")
    if det.nivel_observado is not None:
        st.info(
            f"Demostración: en esta fecha y turno el CCO registró {det.conteo_observado} incidencia(s) en la microzona "
            f"(nivel observado {det.nivel_observado}). La estimación se hizo sin conocer ese dato."
        )
    else:
        st.caption("Fecha operativa: aún no hay registros para comparar.")

st.markdown("#### Historial de la microzona (antes de la fecha objetivo)")
serie = det.serie_diaria
fig = go.Figure(go.Scatter(x=serie.fecha, y=serie.incidencias, mode="lines+markers", line_color=COLOR["primario"]))
fig.update_layout(title=f"Incidencias registradas por día, últimos {len(serie)} días", yaxis_title="Incidencias por día",
                  height=300)  # fmt: skip
grafico(fig, key="det_serie")
st.caption(f"Total en el periodo mostrado: {fmt(int(serie.incidencias.sum()))} incidencias registradas. "
           f"{fuente_pie(cfg.proyecto['fuente_cita'])}")  # fmt: skip

b1, b2 = st.columns(2)
with b1:
    f1 = go.Figure(go.Bar(x=det.por_turno.turno, y=det.por_turno.incidencias, marker_color=COLOR["primario"]))
    f1.update_layout(title="Incidencias por turno (todo el historial previo)", yaxis_title="Incidencias", height=300)
    grafico(f1, key="det_turno")
with b2:
    tipos = det.por_tipo.iloc[::-1]
    f2 = go.Figure(go.Bar(y=tipos.tipo, x=tipos.incidencias, orientation="h", marker_color="#6A8EAE"))
    f2.update_layout(title="Tipos más frecuentes", xaxis_title="Incidencias", height=300)
    grafico(f2, key="det_tipo")

st.markdown(f"#### Últimas {len(det.ultimas)} incidencias registradas")
if det.ultimas.empty:
    st.info("La microzona no tiene incidencias registradas antes de esta fecha.")
else:
    st.dataframe(det.ultimas.rename(columns={"fecha": "Fecha", "hora": "Hora", "turno": "Turno", "tipo": "Tipo",
                                             "subtipo": "Subtipo", "calle": "Calle (sin número)"}),
                 hide_index=True)  # fmt: skip
    st.caption("Sin datos personales: la dirección se recorta a la calle, sin numeración.")
