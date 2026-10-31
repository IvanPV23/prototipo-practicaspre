"""Recursos (segundo nivel): disponibilidad ilustrativa y asignación validada a microzonas (diseño §3.5)."""

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
for _ruta in (_APP, _APP.parent / "src"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import streamlit as st
from componentes.avisos import mostrar_error, sin_predicciones
from componentes.contexto import barra_lateral, configurar_pagina, ranking_df, servicios

from seguridad_ciudadana.formato import fecha_larga
from seguridad_ciudadana.recursos.asignacion import ErrorAsignacion
from seguridad_ciudadana.servicios.priorizacion import SinPredicciones
from seguridad_ciudadana.servicios.recursos import AVISO_ILUSTRATIVO

configurar_pagina("Recursos")
sel = barra_lateral()
servicio = servicios()[2]
st.title("Recursos de patrullaje (segundo nivel)")
st.warning(AVISO_ILUSTRATIVO, icon="⚠️")
st.caption(f"{fecha_larga(sel.fecha)} · turno {sel.turno}")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("#### Disponibilidad del turno")
    with st.form("form_disponibilidad", clear_on_submit=False):
        tipo = st.selectbox("Tipo de recurso", servicio.tipos(), key="disp_tipo")
        cantidad = st.number_input("Cantidad disponible", min_value=0, max_value=500, value=0, step=1, key="disp_cant")
        if st.form_submit_button("Guardar disponibilidad", type="primary"):
            try:
                servicio.registrar_disponibilidad(sel.fecha, sel.turno, tipo, int(cantidad))
                st.success(f"Disponibilidad guardada: {int(cantidad)} {tipo}.")
            except ErrorAsignacion as error:
                st.error(str(error))
            except Exception as error:  # noqa: BLE001
                mostrar_error("No se pudo guardar la disponibilidad.", error)
    disp = servicio.disponibilidad(sel.fecha, sel.turno)
    if disp.empty:
        st.info("Aún no hay recursos registrados para esta fecha y turno.")
    else:
        st.dataframe(disp.rename(columns={"tipo": "Tipo", "cantidad": "Disponible", "asignado": "Asignado",
                                          "restante": "Restante"})[["Tipo", "Disponible", "Asignado", "Restante"]],
                     hide_index=True)  # fmt: skip

with col_b:
    st.markdown("#### Asignar a una microzona")
    try:
        ranking = ranking_df(sel.fecha, sel.turno, sel.pesos_tupla)
    except SinPredicciones as error:
        sin_predicciones(error.fecha, error.turno, error.disponibles)
        st.stop()
    etiquetas = {m: f"#{p} · {m} · {n}" for m, p, n in zip(ranking.microzona_id, ranking.posicion, ranking.nivel)}
    with st.form("form_asignacion"):
        mz = st.selectbox("Microzona (por defecto, las primeras del ranking)", ranking.microzona_id.tolist(),
                          format_func=lambda m: etiquetas[m])  # fmt: skip
        tipo_a = st.selectbox("Tipo de recurso", servicio.tipos(), key="asig_tipo")
        cant_a = st.number_input("Cantidad", min_value=1, max_value=500, value=1, step=1, key="asig_cant")
        if st.form_submit_button("Asignar", type="primary"):
            try:
                servicio.asignar(sel.fecha, sel.turno, tipo_a, mz, int(cant_a))
                st.success(f"Asignado: {int(cant_a)} {tipo_a} a {mz}.")
            except ErrorAsignacion as error:
                st.error(str(error))
            except Exception as error:  # noqa: BLE001
                mostrar_error("No se pudo registrar la asignación.", error)

st.markdown("#### Asignaciones del turno")
asig = servicio.asignaciones(sel.fecha, sel.turno)
if asig.empty:
    st.info("No hay asignaciones registradas para esta fecha y turno.")
else:
    for fila in asig.itertuples(index=False):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        c1.write(fila.microzona_id)
        c2.write(fila.tipo)
        c3.write(str(fila.cantidad))
        if c4.button("Quitar", key=f"quitar_{fila.id}"):
            servicio.quitar(int(fila.id))
            st.rerun()
