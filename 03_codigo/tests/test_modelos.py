"""Registro de modelos: cuatro modelos trazables, uno vigente elegido por validación, artefactos existentes."""

import json

import pytest

from seguridad_ciudadana.db import BaseDatos
from seguridad_ciudadana.db.repositorios import modelos
from seguridad_ciudadana.dominio import MODELOS
from seguridad_ciudadana.modelos.entrenamiento import MODELOS_ML


@pytest.fixture(scope="module")
def registrados(bd_real):
    with BaseDatos(bd_real.rutas.base_datos).lectura() as con:
        return {m["nombre"]: m for m in modelos.ultimos_por_nombre(con)}, modelos.modelo_vigente(con)


def test_cuatro_modelos_con_trazabilidad(registrados, bd_real):
    regs, _ = registrados
    assert set(MODELOS) <= set(regs)
    sha = json.loads(bd_real.rutas.handoff_fase1.read_text(encoding="utf-8"))["dataset_principal"]["sha256"]
    for m in regs.values():
        assert m["sha256_datos"] == sha
        assert m["config_hash"] == bd_real.hash()
        assert {"valid", "test"} <= set(m["metricas"])
        for p in ("valid", "test"):
            assert set(m["metricas"][p]["por_clase"]) == {"Bajo", "Medio", "Alto"}
            assert len(m["metricas"][p]["por_dia"]) == 4
        if m["nombre"] != "persistencia":
            assert (bd_real.ruta_archivo.parent.parent / m["ruta_artefacto"]).exists()


def test_vigente_es_el_mejor_en_validacion(registrados):
    regs, vigente = registrados
    mejor = max(MODELOS_ML, key=lambda n: regs[n]["macro_f1_valid"])
    assert vigente["nombre"] == mejor


def test_persistencia_valid_igual_al_handoff(registrados):
    regs, _ = registrados
    assert regs["persistencia"]["macro_f1_valid"] == pytest.approx(0.439, abs=5e-4)


def test_resultado_fase3_cumple_contrato(bd_real):
    ruta = bd_real.rutas.reportes / "resultado_fase3.json"
    r = json.loads(ruta.read_text(encoding="utf-8"))
    for clave in ("modelos", "modelo_seleccionado", "hipotesis", "base_datos", "tests", "comandos", "advertencias"):
        assert clave in r
    assert {m["nombre"] for m in r["modelos"]} == set(MODELOS)
    assert r["hipotesis"]["H1"]["resultado"] in {"se_sostiene", "no_se_sostiene"}
    assert r["hipotesis"]["HE1"]["resultado"] in {"se_sostiene", "no_se_sostiene", "no_concluyente"}
