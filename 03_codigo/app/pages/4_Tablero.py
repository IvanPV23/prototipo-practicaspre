"""Tablero: panorama histórico y desempeño del modelo (diseño §3.4)."""

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
for _ruta in (_APP, _APP.parent / "src"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from componentes.avisos import mostrar_error
from componentes.contexto import TTL_CACHE_S, barra_lateral, config, configurar_pagina, servicios
from componentes.graficos import grafico
from tema import COLOR, PARTICION_COLOR, fuente_pie

from seguridad_ciudadana.dominio import NIVELES
from seguridad_ciudadana.formato import fmt, pct

configurar_pagina("Tablero")
barra_lateral()
cfg = config()
FUENTE = fuente_pie(cfg.proyecto["fuente_cita"])
st.title("Tablero: panorama de incidencias registradas y desempeño del modelo")


@st.cache_data(ttl=TTL_CACHE_S, show_spinner="Calculando indicadores…")
def datos() -> dict:
    return servicios()[0].tablero()


try:
    t = datos()
except Exception as error:  # noqa: BLE001
    mostrar_error("No se pudo calcular el tablero.", error)
    st.stop()

k = t["kpis"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Incidencias registradas (limpias)", fmt(k["total"]))
c2.metric("Promedio diario", fmt(k["promedio_diario"], 1))
c3.metric("Sin sector asignado", pct(k["pct_sin_sector"]))
c4.metric("Días cubiertos", fmt(k["dias"]))

# Serie diaria con la división temporal
serie = t["serie"]
fig = go.Figure()
for periodo, g in serie.groupby("periodo", sort=False):
    fig.add_bar(x=g.fecha, y=g.incidencias, name=periodo, marker_color=PARTICION_COLOR.get(periodo, COLOR["primario"]))
fig.update_layout(title="El registro diario crece desde el arranque; la prueba (5–8 jun) es el tramo más alto",
                  yaxis_title="Incidencias por día", barmode="overlay", height=360)  # fmt: skip
grafico(fig, key="tab_serie")
p = t["particion"]
st.caption(f"Entrenamiento {p['train'][0]} a {p['train'][1]} · validación {p['valid'][0]} a {p['valid'][1]} · prueba "
           f"{p['test'][0]} a {p['test'][1]}. 9 y 10 jun están incompletos en la fuente (censura) y no se usan. {FUENTE}")  # fmt: skip

a, b = st.columns(2)
with a:
    calor = t["calor"]
    fh = go.Figure(go.Heatmap(z=calor.values, x=list(calor.columns), y=list(calor.index), colorscale="Purples",
                              colorbar={"title": "Media/día"}, hovertemplate="%{y} · %{x}: %{z:.1f}<extra></extra>"))  # fmt: skip
    fh.update_layout(title="La mañana concentra más registros", height=380,
                     yaxis={"autorange": "reversed"})  # fmt: skip
    grafico(fh, key="tab_calor")
    st.caption(f"Promedio de incidencias por día según día de la semana y turno (22 may–8 jun). {FUENTE}")
with b:
    tipos = t["por_tipo"]
    ft = go.Figure(go.Bar(y=tipos.tipo_corto, x=tipos.incidencias, orientation="h", marker_color=COLOR["primario"]))
    ft.update_layout(title="Predominan infracciones y faltas", xaxis_title="Incidencias", height=380)
    grafico(ft, key="tab_tipos")
    st.caption(
        f"Incidencias por tipo (todo el extracto limpio). Solo una fracción pequeña es presuntamente delictiva. {FUENTE}"
    )

c = t["concentracion"]
fc = go.Figure()
fc.add_scatter(x=c.pct_celdas, y=c.pct_incidencias, mode="lines", line_color=COLOR["primario"], name="Observado")
fc.add_scatter(x=[0, 100], y=[0, 100], mode="lines", line={"dash": "dot", "color": "#8C8C8C"}, name="Reparto uniforme")
mitad = c[c.pct_incidencias >= 50].pct_celdas.min()
fc.update_layout(title=f"Concentración (HE2): el {fmt(mitad, 1)} % de las celdas reúne la mitad de los registros",
                 xaxis_title="% de celdas del distrito (de mayor a menor registro)",
                 yaxis_title="% acumulado de incidencias", height=380)  # fmt: skip
grafico(fc, key="tab_conc")
st.caption(
    f"Curva de concentración sobre 22 may–4 jun (entrenamiento + validación). Concentración del registro, no del delito. {FUENTE}"
)

st.subheader("Desempeño de los modelos")
mod = t["modelos"].copy()
mod["Macro F1 validación"] = [fmt(v, 3) for v in mod.macro_f1_valid]
mod["Macro F1 prueba"] = [fmt(v, 3) for v in mod.macro_f1_test]
mod["Vigente"] = ["Sí" if v else "" for v in mod.vigente]
st.dataframe(mod[["modelo", "Macro F1 validación", "Macro F1 prueba", "Vigente"]].rename(columns={"modelo": "Modelo"}),
             hide_index=True)  # fmt: skip
st.caption("El modelo vigente se eligió con validación; prueba se evaluó una sola vez y se muestra para comparar (H1).")

m1, m2 = st.columns(2)
with m1:
    cm = t["matriz_test"]
    if cm:
        fm = go.Figure(go.Heatmap(z=cm, x=list(NIVELES), y=list(NIVELES), colorscale="Purples", showscale=False,
                                  text=[[fmt(v) for v in fila] for fila in cm], texttemplate="%{text}"))  # fmt: skip
        fm.update_layout(title=f"Confusión en prueba · {t['vigente']}", xaxis_title="Nivel estimado",
                         yaxis_title="Nivel observado", yaxis={"autorange": "reversed"}, height=380)  # fmt: skip
        grafico(fm, key="tab_cm")
        total = sum(map(sum, cm))
        aciertos = sum(cm[i][i] for i in range(len(cm)))
        st.caption(f"Aciertos: {fmt(aciertos)} de {fmt(total)} observaciones ({pct(100 * aciertos / total)}).")
with m2:
    imp = t["importancia"]
    if imp:
        grupos = pd.DataFrame(
            [{"grupo": g, "media": v["media"], "desv": v["desv"]} for g, v in imp["por_grupo"].items()]
        )
        grupos = grupos.sort_values("media")
        fi = go.Figure(go.Bar(y=grupos.grupo, x=grupos.media, orientation="h", marker_color=COLOR["primario"],
                              error_x={"type": "data", "array": grupos.desv}))  # fmt: skip
        fi.update_layout(title="Importancia por grupo (HE1)", xaxis_title="Caída del Macro F1 al permutar",
                         height=380)  # fmt: skip
        grafico(fi, key="tab_imp")
        st.caption("Permutación sobre validación: cuánto empeora el modelo si se desordena cada grupo.")
        with st.expander("Importancia por variable"):
            pv = pd.DataFrame([{"Variable": k2, "Caída media del Macro F1": fmt(v["media"], 4)}
                               for k2, v in sorted(imp["por_variable"].items(), key=lambda kv: -kv[1]["media"])])  # fmt: skip
            st.dataframe(pv, hide_index=True)
