"""Configuración de página, servicios cacheados y barra lateral global (fecha, turno, pesos)."""

from __future__ import annotations

import traceback
from dataclasses import dataclass

import streamlit as st
from tema import COMPONENTE_NOMBRE, CSS, registrar_plantilla

from componentes.avisos import mostrar_error, sin_base_de_datos
from seguridad_ciudadana.config import Config, cargar_config
from seguridad_ciudadana.dominio import TURNOS
from seguridad_ciudadana.formato import fecha_larga, fmt
from seguridad_ciudadana.priorizacion.calculo import normalizar_pesos
from seguridad_ciudadana.servicios.consultas import ServicioConsultas
from seguridad_ciudadana.servicios.priorizacion import ServicioPriorizacion
from seguridad_ciudadana.servicios.recursos import ServicioRecursos

CLAVES_PESO = ("w1", "w2", "w3")
TTL_CACHE_S = 300


@dataclass(frozen=True)
class Seleccion:
    fecha: str
    turno: str
    pesos: dict[str, float]

    @property
    def pesos_tupla(self) -> tuple[float, float, float]:
        return tuple(round(self.pesos[k], 4) for k in CLAVES_PESO)  # type: ignore[return-value]


@st.cache_resource(show_spinner=False)
def config() -> Config:
    return cargar_config()


@st.cache_resource(show_spinner=False)
def servicios() -> tuple[ServicioConsultas, ServicioPriorizacion, ServicioRecursos]:
    cfg = config()
    return ServicioConsultas(cfg), ServicioPriorizacion(cfg), ServicioRecursos(cfg)


def configurar_pagina(titulo: str) -> None:
    st.set_page_config(page_title=f"{titulo} · Priorización preventiva", page_icon="🗺️", layout="wide")
    registrar_plantilla()
    st.markdown(CSS, unsafe_allow_html=True)


def verificar_estado() -> bool:
    """Si falta la base o el pipeline, muestra el comando exacto y detiene la página."""
    try:
        estado = servicios()[0].estado()
    except Exception as error:  # noqa: BLE001 - se muestra al usuario en lenguaje llano
        mostrar_error("No se pudo abrir la configuración o la base de datos.", error)
        st.stop()
    if not estado.listo:
        sin_base_de_datos(estado.mensaje, estado.comando)
        st.stop()
    return True


@st.cache_data(ttl=TTL_CACHE_S, show_spinner=False)
def fechas_disponibles() -> dict[str, list[str]]:
    return servicios()[1].fechas_disponibles()


def _persistir_widgets() -> None:
    """Streamlit borra el estado de un widget al cambiar de página; reasignarlo lo conserva entre páginas."""
    for clave in ("fecha_sel", "turno_sel", *CLAVES_PESO):
        if clave in st.session_state:
            st.session_state[clave] = st.session_state[clave]


def _restablecer_pesos() -> None:
    for k, v in config().priorizacion["pesos"].items():
        st.session_state[k] = float(v)


def barra_lateral() -> Seleccion:
    """Controles globales del diseño §2: fecha, turno, pesos y pie con corte de datos y modelo vigente."""
    verificar_estado()
    cfg = config()
    consultas = servicios()[0]
    meta = consultas.metadatos()
    fechas = fechas_disponibles()
    _persistir_widgets()
    if st.session_state.get("fecha_sel") not in fechas:
        st.session_state["fecha_sel"] = meta.fecha_operativa if meta.fecha_operativa in fechas else max(fechas)
    if st.session_state.get("turno_sel") not in TURNOS:
        st.session_state["turno_sel"] = TURNOS[0]
    for k, v in cfg.priorizacion["pesos"].items():
        st.session_state.setdefault(k, float(v))

    with st.sidebar:
        st.markdown("### Planificación")

        def rotulo(f: str) -> str:
            tipo = "próximo día (operativa)" if f == meta.fecha_operativa else "demostración con datos de prueba"
            return f"{fecha_larga(f)} · {tipo}"

        st.selectbox("Fecha objetivo", list(fechas), key="fecha_sel", format_func=rotulo,
                     help="Solo se listan fechas con estimaciones del modelo vigente.")  # fmt: skip
        st.selectbox("Turno", list(TURNOS), key="turno_sel")
        st.markdown("**Pesos de la prioridad sugerida**")
        for k, comp in zip(CLAVES_PESO, ("R", "G", "F")):
            st.slider(f"{k} · {COMPONENTE_NOMBRE[comp]}", 0.0, 1.0, step=0.05, key=k)
        crudos = {k: float(st.session_state[k]) for k in CLAVES_PESO}
        if sum(crudos.values()) <= 0:
            st.warning("Todos los pesos están en 0; se usan los valores por defecto.")
            pesos = meta.pesos_por_defecto
        else:
            pesos = normalizar_pesos(crudos)
        st.caption("Pesos normalizados (suman 1): " + " · ".join(f"{k} = {fmt(v, 2)}" for k, v in pesos.items()))
        st.button("Restablecer pesos", on_click=_restablecer_pesos, width="stretch")
        st.divider()
        f1 = "—" if meta.macro_f1_test is None else fmt(meta.macro_f1_test, 3)
        st.caption(
            f"Datos hasta: {fecha_larga(meta.fecha_corte_datos)} · Modelo: {meta.modelo_nombre_legible} "
            f"v{meta.modelo_version} · Macro F1 (prueba): {f1}"
        )
    return Seleccion(st.session_state["fecha_sel"], st.session_state["turno_sel"], pesos)


@st.cache_data(ttl=TTL_CACHE_S, show_spinner="Calculando ranking…")
def ranking_df(fecha: str, turno: str, pesos: tuple[float, float, float]):
    return servicios()[1].ranking_df(fecha, turno, dict(zip(CLAVES_PESO, pesos)))


def detalle_tecnico(error: BaseException) -> str:
    return "".join(traceback.format_exception(type(error), error, error.__traceback__))
