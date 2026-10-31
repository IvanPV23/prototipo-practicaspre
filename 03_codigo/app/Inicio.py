"""Inicio: qué es, cómo usarlo, aviso de uso responsable y accesos (diseño §3.0)."""

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parent
for _ruta in (_APP, _APP.parent / "src"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

import streamlit as st
from componentes.avisos import aviso_uso_responsable
from componentes.contexto import barra_lateral, configurar_pagina, servicios

from seguridad_ciudadana.formato import fecha_larga, fmt

configurar_pagina("Inicio")
sel = barra_lateral()
meta = servicios()[0].metadatos()

st.title(f"Priorización preventiva — {meta.distrito}")
st.markdown(
    "Apoyo a la decisión de patrullaje a partir de registros del Centro de Control de Operaciones (CCO). "
    f"Datos hasta **{fecha_larga(meta.fecha_corte_datos)}** (último día completo del extracto con corte "
    f"{fecha_larga(meta.fecha_corte_fuente)})."
)
aviso_uso_responsable()

c1, c2 = st.columns(2)
c1.page_link("pages/1_Ranking.py", label="Ver ranking del próximo turno", icon="📋")
c2.page_link("pages/2_Mapa.py", label="Abrir mapa", icon="🗺️")

st.subheader("Cómo leer la prioridad sugerida")
st.markdown(
    f"Cada microzona (celda de 500 m) recibe una prioridad **P = w1·R + w2·G + w3·F** entre 0 y 1. "
    f"Pesos actuales: w1 = {fmt(sel.pesos['w1'], 2)}, w2 = {fmt(sel.pesos['w2'], 2)}, w3 = {fmt(sel.pesos['w3'], 2)} "
    "(ajustables en la barra lateral)."
)
t1, t2, t3 = st.columns(3)
tarjetas = [
    (t1, "R · Nivel estimado", "Lo que el modelo espera para la fecha y turno: Bajo (0 incidencias), Medio (1) o "
     "Alto (2 o más), resumido como 0·p(Bajo) + 0,5·p(Medio) + 1·p(Alto)."),
    (t2, "G · Gravedad histórica", "Gravedad media (escala 1–5 por tipo de incidencia) de lo registrado en la "
     "microzona en los 7 días previos. Es un supuesto de diseño, revisable."),
    (t3, "F · Frecuencia reciente", "Incidencias registradas en la microzona en los 7 días previos, en relación "
     "con el máximo observado en entrenamiento."),
]  # fmt: skip
for col, titulo, texto in tarjetas:
    col.markdown(f'<div class="tarjeta"><h4>{titulo}</h4>{texto}</div>', unsafe_allow_html=True)

st.subheader("Cómo usarlo")
st.markdown(
    f"""
1. Elija **fecha y turno** en la barra lateral. La fecha por defecto es la operativa
   ({fecha_larga(meta.fecha_operativa)}), el día siguiente al último dato completo; las fechas del periodo de prueba se
   ofrecen como demostración porque para ellas se conoce lo que realmente se registró.
2. Revise el **Ranking** y el **Mapa**; abra la **Ficha de detalle** para ver por qué una zona tiene esa prioridad.
3. Consulte el **Tablero** para el panorama general y la **Metodología** para saber qué tan confiable es el modelo
   ({meta.modelo_nombre_legible}, Macro F1 en prueba {fmt(meta.macro_f1_test, 3)}).
4. Opcional: registre recursos ilustrativos y asígnelos en **Recursos**.
"""
)
