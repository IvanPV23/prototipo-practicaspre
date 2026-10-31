"""No fuga: las variables de una fecha-turno solo usan datos anteriores; ninguna columna [POST] llega al modelo.

Repite la prueba de la Fase 2: para cada fecha d se recalculan las variables con la historia truncada en d y con
incidencias falsas inyectadas en d y después; las variables de d no deben cambiar.
"""

import json

import numpy as np
import pandas as pd
import pytest

from seguridad_ciudadana.db import BaseDatos
from seguridad_ciudadana.db.repositorios import incidencias, microzonas
from seguridad_ciudadana.features.tabla import construir_tabla
from seguridad_ciudadana.modelos.registro import cargar_artefacto

FECHAS_PRUEBA = ["2026-05-22", "2026-05-27", "2026-06-01", "2026-06-05", "2026-06-08"]
N_FALSAS = 50


@pytest.fixture(scope="module")
def insumos(cfg_tmp):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        limpias = incidencias.leer_incidencias(con)
        activas = microzonas.leer_microzonas(con, solo_activas=True)[["id", "col", "fila"]]
    historia = limpias[limpias.fecha <= cfg_tmp.ultimo_dia_completo]
    return historia, activas


def _tabla(cfg, hist, activas, fechas):
    return construir_tabla(hist, activas, fechas, cfg.datos["fecha_inicio_historia"], cfg.datos["feriados"],
                           int(cfg.features["tope_dias_desde_ultima"]))  # fmt: skip


@pytest.mark.parametrize("fecha", FECHAS_PRUEBA)
def test_variables_no_cambian_con_datos_de_d_o_posteriores(cfg_tmp, insumos, fecha):
    historia, activas = insumos
    completa = _tabla(cfg_tmp, historia, activas, [fecha])
    truncada = historia[historia.fecha < fecha].copy()
    rng = np.random.default_rng(0)
    fila_mz = activas.sample(N_FALSAS, replace=True, random_state=0)
    falsas = pd.DataFrame({
        "fecha": rng.choice([fecha, cfg_tmp.ultimo_dia_completo], N_FALSAS),
        "turno": rng.choice(["Mañana", "Tarde", "Noche"], N_FALSAS),
        "mz_col": fila_mz.col.to_numpy(), "mz_fila": fila_mz.fila.to_numpy(), "gravedad": 5.0,
    })  # fmt: skip
    contaminada = _tabla(cfg_tmp, pd.concat([truncada, falsas], ignore_index=True), activas, [fecha])
    variables = [f for f in cfg_tmp.features["lista"] if f not in ("nivel_lag1_turno",)]
    for v in variables:
        if completa[v].dtype == object:
            assert (completa[v] == contaminada[v]).all(), v
        else:
            assert np.allclose(completa[v].astype(float), contaminada[v].astype(float), equal_nan=True), v
    # control: el conteo objetivo de d sí cambia con las incidencias falsas (la prueba tiene poder)
    assert contaminada.conteo.sum() > completa.conteo.sum() - historia[historia.fecha == fecha].shape[0]


def test_lista_de_variables_es_la_del_handoff_y_sin_prohibidas(cfg):
    h2 = json.loads(cfg.rutas.handoff_fase2.read_text(encoding="utf-8"))
    assert cfg.features["lista"] == [f["nombre"] for f in h2["features"]]
    prohibidas = set(h2["excluidas_por_fuga"]) | {"estado_final", "fecha_hora_cierre", "tiempo_respuesta_min"}
    assert not prohibidas & set(cfg.features_modelo)


def test_el_modelo_vigente_no_recibe_columnas_post(bd_real):
    from seguridad_ciudadana.db.repositorios import modelos

    with BaseDatos(bd_real.rutas.base_datos).lectura() as con:
        vigente = modelos.modelo_vigente(con)
    artefacto = cargar_artefacto(bd_real.ruta_archivo.parent.parent / vigente["ruta_artefacto"])
    usadas = set(artefacto["features"])
    assert not usadas & {"estado_final", "fecha_hora_cierre", "tiempo_respuesta_min", "NIVEL", "conteo", "nivel"}
    assert usadas == set(bd_real.features_modelo)
