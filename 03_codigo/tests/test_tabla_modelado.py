"""Tabla de modelado: incluye ceros, filas = microzonas × fechas × 3 y coincide con la Fase 2."""

import json

import numpy as np
import pandas as pd
import pytest

from seguridad_ciudadana.db import BaseDatos
from seguridad_ciudadana.db.repositorios import microzonas, observaciones
from seguridad_ciudadana.dominio import CODIGO_NIVEL, CODIGO_TURNO, NIVELES
from seguridad_ciudadana.features.tabla import columna_de
from seguridad_ciudadana.modelos.evaluacion import macro_f1


@pytest.fixture(scope="module")
def tabla(cfg_tmp):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        return observaciones.leer_tabla_modelado(con)


@pytest.fixture(scope="module")
def handoff2(cfg_tmp):
    return json.loads(cfg_tmp.rutas.handoff_fase2.read_text(encoding="utf-8"))


def test_microzonas_activas(cfg_tmp, handoff2):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        mz = microzonas.leer_microzonas(con)
    assert int(mz.activa.sum()) == handoff2["microzona"]["n_microzonas_activas"] == 86
    assert len(mz) == 121  # celdas que intersecan el distrito


def test_filas_y_ceros(tabla, cfg_tmp):
    objetivo = tabla[tabla.particion != "operativa"]
    n_fechas = len(cfg_tmp.particion.fechas_objetivo())
    assert len(objetivo) == 86 * n_fechas * 3 == 4644
    assert (objetivo.conteo == 0).sum() > 0
    assert round(100 * (objetivo.conteo == 0).mean(), 1) == 71.1
    assert objetivo.groupby(["microzona_id", "fecha"]).size().eq(3).all()


def test_distribucion_por_particion(tabla, handoff2):
    objetivo = tabla[tabla.particion != "operativa"]
    esperado = handoff2["objetivo"]["distribucion_por_particion"]
    for particion, conteos in esperado.items():
        obtenido = objetivo[objetivo.particion == particion].nivel.value_counts().to_dict()
        assert obtenido == conteos


def test_fila_operativa_sin_objetivo(tabla, cfg_tmp):
    operativa = tabla[tabla.particion == "operativa"]
    assert len(operativa) == 86 * 3
    assert set(operativa.fecha) == {cfg_tmp.fecha_operativa}
    assert operativa.conteo.isna().all() and operativa.nivel.isna().all()


def test_persistencia_en_validacion_igual_al_handoff(tabla, handoff2):
    v = tabla[tabla.particion == "valid"]
    f1 = macro_f1(v.nivel.map(CODIGO_NIVEL).to_numpy(), v.nivel_lag1_turno.astype(int).to_numpy())
    assert round(f1, 3) == handoff2["linea_base"]["macro_f1_valid"] == 0.439


def test_coincide_fila_a_fila_con_la_tabla_de_fase2(tabla, cfg_tmp):
    ruta = cfg_tmp.rutas.tabla_referencia_fase2
    if not ruta.exists():
        pytest.skip("No está la tabla de referencia de la Fase 2")
    ref = pd.read_csv(ruta).rename(columns={"id_microzona": "microzona_id"})
    ref["turno_cod"] = ref.turno.map(CODIGO_TURNO)
    ref["nivel_lag1_turno"] = ref.nivel_lag1_turno.map(CODIGO_NIVEL)
    propia = tabla[tabla.particion != "operativa"]
    clave = ["microzona_id", "fecha", "turno"]
    ref = ref.sort_values(clave).reset_index(drop=True)
    propia = propia.sort_values(clave).reset_index(drop=True)
    assert (ref[clave].to_numpy() == propia[clave].to_numpy()).all()
    for f in cfg_tmp.features["lista"]:
        col = columna_de(f)
        assert np.allclose(propia[col].astype(float), ref[col].astype(float), equal_nan=True), f
    assert (propia.nivel.to_numpy() == ref.nivel.to_numpy()).all()
    assert set(propia.nivel) == set(NIVELES)
