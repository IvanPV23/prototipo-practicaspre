"""Fixtures compartidas.

- `cfg`: configuración real (config/config.yaml).
- `bd_real`: garantiza que la base real tenga el pipeline completo (lo ejecuta si falta); la usan servicios y app.
- `cfg_tmp`: copia de la configuración que escribe en una carpeta temporal (ingesta + construcción).
Al terminar una corrida completa, el resumen se guarda en reportes/ y en resultado_fase3.json.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ_CODIGO = Path(__file__).resolve().parents[1]
for ruta in (RAIZ_CODIGO / "src", RAIZ_CODIGO / "app"):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

from seguridad_ciudadana.config import cargar_config, con_base_datos
from seguridad_ciudadana.servicios import pipeline
from seguridad_ciudadana.servicios.consultas import ServicioConsultas


@pytest.fixture(scope="session")
def cfg():
    return cargar_config(RAIZ_CODIGO / "config" / "config.yaml")


@pytest.fixture(scope="session")
def bd_real(cfg):
    if not ServicioConsultas(cfg).estado().listo:
        pipeline.todo(cfg)
    return cfg


@pytest.fixture(scope="session")
def cfg_tmp(cfg, tmp_path_factory):
    """Base temporal con init-db, ingestar y construir (sin entrenar: es rápido)."""
    destino = tmp_path_factory.mktemp("bd") / "seguridad.db"
    c = con_base_datos(cfg, destino)
    for paso in ("init-db", "ingestar", "construir"):
        pipeline.ejecutar(c, paso)
    return c


def pytest_terminal_summary(terminalreporter, exitstatus, config):  # noqa: ARG001
    """Solo una corrida completa (sin argumentos ni filtros) actualiza el resultado de la Fase 3."""
    if config.args_source != pytest.Config.ArgsSource.TESTPATHS or config.getoption("keyword"):
        return
    stats = terminalreporter.stats
    pasados = len(stats.get("passed", []))
    fallidos = len(stats.get("failed", [])) + len(stats.get("error", []))
    total = pasados + fallidos + len(stats.get("skipped", []))
    from seguridad_ciudadana.servicios.resultado import actualizar_tests

    actualizar_tests(cargar_config(RAIZ_CODIGO / "config" / "config.yaml"), total, pasados, fallidos)
