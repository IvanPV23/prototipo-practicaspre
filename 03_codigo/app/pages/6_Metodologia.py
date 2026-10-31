"""Metodología: datos, modelo, métricas y limitaciones (diseño §3.6)."""

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
for _ruta in (_APP, _APP.parent / "src"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import streamlit as st
from componentes.avisos import aviso_uso_responsable, mostrar_error
from componentes.contexto import TTL_CACHE_S, barra_lateral, config, configurar_pagina, servicios

from seguridad_ciudadana.formato import fecha_larga, fmt

configurar_pagina("Metodología")
barra_lateral()
cfg = config()
st.title("Metodología y limitaciones")


@st.cache_data(ttl=TTL_CACHE_S, show_spinner=False)
def datos() -> dict:
    return servicios()[0].metodologia()


try:
    m = datos()
except Exception as error:  # noqa: BLE001
    mostrar_error("No se pudo cargar la metodología.", error)
    st.stop()

f = m["fuente"]
st.header("Fuente de datos")
st.markdown(
    f"- **{f.get('nombre', '—')}** — {f.get('institucion', '')}.\n"
    f"- Licencia: {f.get('licencia', '—')}. Descarga: {f.get('fecha_descarga', '—')}. "
    f"Registros: {fmt(f.get('registros', 0))} (sha256 `{str(f.get('sha256', ''))[:16]}…`).\n"
    f"- Periodo: 16 may–10 jun 2026; se usan como historia hasta el {fecha_larga(m['ultimo_dia_completo'])} "
    "(9 y 10 jun están incompletos porque la fuente solo publica incidencias cerradas).\n"
    f"- URL: {f.get('url', '—')}"
)

st.header("Definiciones")
mz = m["microzona"]
v = m["valor_nivel"]
n_activas = fmt(servicios()[0].metadatos().total_microzonas_activas)
st.markdown(
    f"- **Microzona:** celda de {fmt(mz['tamano_m'])} m en {mz['crs_metrico']} (origen {mz['origen']}); activa si interseca "
    f"el límite distrital y tuvo al menos una incidencia en entrenamiento ({n_activas} celdas).\n"
    "- **Nivel (objetivo):** incidencias registradas en la microzona, fecha y turno. **Bajo** = 0, **Medio** = 1, "
    "**Alto** = 2 o más (umbral fijado con entrenamiento: mediana de los conteos positivos = 1).\n"
    f"- **R (nivel estimado):** {fmt(v['Bajo'], 1)}·p(Bajo) + {fmt(v['Medio'], 1)}·p(Medio) + {fmt(v['Alto'], 1)}·p(Alto).\n"
    "- **G (gravedad histórica):** gravedad media (1–5 por tipo, supuesto de diseño) de la microzona en los 7 días "
    "previos, normalizada (G − 1)/4; 0 si no hubo registros.\n"
    "- **F (frecuencia reciente):** incidencias de la microzona en los 7 días previos / máximo observado en entrenamiento, recortado a 1.\n"
    f"- **P = w1·R + w2·G + w3·F**, con pesos por defecto w1 = {fmt(m['pesos']['w1'], 2)}, w2 = {fmt(m['pesos']['w2'], 2)}, "
    f"w3 = {fmt(m['pesos']['w3'], 2)} (normalizados a suma 1, ajustables en la barra lateral)."
)
st.markdown(
    f"**Variables del modelo ({len(m['features'])}):** {', '.join(m['features'])}. Todas usan solo datos anteriores a la "
    f"fecha objetivo. Excluida del estimador: {', '.join(m['excluidas_modelo'])} (constante en entrenamiento y validación)."
)

st.header("Partición temporal y métricas")
p = m["particion"]
st.markdown(
    f"Entrenamiento {p['train'][0]} → {p['train'][1]} · validación {p['valid'][0]} → {p['valid'][1]} · prueba "
    f"{p['test'][0]} → {p['test'][1]}. Los hiperparámetros y el modelo se eligieron con validación; prueba se evaluó "
    "una sola vez. Intervalos: bootstrap del 95 % remuestreando días completos."
)
met = m["metricas"].copy()
for col in ("macro_f1", "ic_inf", "ic_sup", "exactitud", "f1_Bajo", "f1_Medio", "f1_Alto"):
    met[col] = [fmt(x, 3) for x in met[col]]
met["IC 95 %"] = "[" + met.ic_inf + "; " + met.ic_sup + "]"
st.dataframe(
    met[["modelo", "particion", "macro_f1", "IC 95 %", "exactitud", "f1_Bajo", "f1_Medio", "f1_Alto"]].rename(
        columns={"modelo": "Modelo", "particion": "Partición", "macro_f1": "Macro F1", "exactitud": "Exactitud",
                 "f1_Bajo": "F1 Bajo", "f1_Medio": "F1 Medio", "f1_Alto": "F1 Alto"}
    ),
    hide_index=True,
)  # fmt: skip
with st.expander("Macro F1 por día (con intervalo bootstrap por filas) y por turno"):
    pdia = m["por_dia"].copy()
    for col in ("macro_f1", "ic_inf", "ic_sup"):
        pdia[col] = [fmt(x, 3) for x in pdia[col]]
    st.dataframe(pdia.rename(columns={"modelo": "Modelo", "particion": "Partición", "fecha": "Fecha",
                                      "macro_f1": "Macro F1", "ic_inf": "IC inf.", "ic_sup": "IC sup."}),
                 hide_index=True)  # fmt: skip
    ptur = m["por_turno"].copy()
    ptur["macro_f1"] = [fmt(x, 3) for x in ptur.macro_f1]
    st.dataframe(ptur.rename(columns={"modelo": "Modelo", "particion": "Partición", "turno": "Turno",
                                      "macro_f1": "Macro F1"}), hide_index=True)  # fmt: skip

st.header("Limitaciones")
st.markdown(
    "- **Periodo muy corto** (18 días utilizables): las métricas son exploratorias y varían mucho de un día a otro.\n"
    "- **Desplazamiento:** la proporción de nivel Alto sube de 9,4 % (entrenamiento) a 13,8 % (prueba); la validación no "
    "tiene fines de semana y la prueba incluye sábado, domingo y el feriado del 7 de junio.\n"
    "- **Naturaleza del registro:** son incidencias atendidas por el CCO (≈ 3/4 vistas por cámaras), no delitos; dependen "
    "de dónde hay cámaras y patrullaje.\n"
    "- **Sin datos de exposición** (población o flujo por microzona): los conteos no son tasas.\n"
    "- **Gravedad** por tipo es un supuesto de diseño, no una medición.\n"
    "- **Fecha operativa:** el 9 de junio se estima con datos hasta el 8; no puede evaluarse porque la fuente está "
    "incompleta esos días.\n"
    "- **Recursos** del segundo nivel son ilustrativos.\n"
    "- El sistema **no predice delitos**, no califica zonas como seguras o inseguras y no sustituye el criterio del operador."
)
aviso_uso_responsable()

st.header("Documentos")
for nombre, titulo in (
    ("model_card", "Ficha del modelo (docs/model_card.md)"),
    ("data_card", "Ficha de datos (docs/data_card.md)"),
):
    with st.expander(titulo):
        st.markdown(servicios()[0].documento(nombre))
