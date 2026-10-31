"""Avisos y estados de interfaz (§3.7) con el microcopy del diseño (§4.6)."""

from __future__ import annotations

import html
import traceback

import streamlit as st
from tema import AVISO, NIVEL_COLOR, NIVEL_TEXTO


def aviso_uso_responsable(compacto: bool = False) -> None:
    texto = AVISO if not compacto else f"ℹ️ {AVISO}"
    st.markdown(f'<div class="aviso" role="note">{html.escape(texto)}</div>', unsafe_allow_html=True)


def sin_base_de_datos(mensaje: str, comando: str) -> None:
    st.warning(f"{mensaje} Ejecute en la carpeta 03_codigo:")
    st.code(comando, language="bash")
    st.caption("Luego recargue esta página.")


def sin_predicciones(fecha: str, turno: str, disponibles: list[str]) -> None:
    st.info(f"No hay estimaciones para {fecha} {turno}. Fechas disponibles: {', '.join(disponibles)}")


def sin_resultados(clave_limpiar: str, al_limpiar) -> None:
    st.info("Ningún resultado con estos filtros.")
    st.button("Limpiar filtros", key=clave_limpiar, on_click=al_limpiar)


def mostrar_error(mensaje: str, error: BaseException) -> None:
    st.error(mensaje)
    with st.expander("Detalle técnico"):
        st.code("".join(traceback.format_exception(type(error), error, error.__traceback__)))


def etiqueta_nivel(nivel: str | None) -> str:
    """Nivel siempre como texto + color (nunca solo color)."""
    if nivel not in NIVEL_COLOR:
        return '<span class="nivel" style="background:#D9D9D9;color:#1A1A1A">Sin estimación</span>'
    return f'<span class="nivel" style="background:{NIVEL_COLOR[nivel]};color:{NIVEL_TEXTO[nivel]}">{nivel}</span>'
