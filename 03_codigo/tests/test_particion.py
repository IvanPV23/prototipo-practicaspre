"""Partición temporal: contigua, sin solapamiento e igual al handoff; arranque y censura fuera del objetivo."""

import json
from datetime import date

import pytest

from seguridad_ciudadana.config import ErrorConfiguracion, Particion, _validar
from seguridad_ciudadana.db import BaseDatos


def test_igual_al_handoff(cfg):
    h2 = json.loads(cfg.rutas.handoff_fase2.read_text(encoding="utf-8"))
    for nombre, tramo in cfg.particion.como_dict().items():
        assert list(tramo) == h2["particion_temporal"][nombre]


def test_contigua_y_sin_solapamiento(cfg):
    tramos = [tuple(date.fromisoformat(x) for x in t) for t in cfg.particion.como_dict().values()]
    for (_, fin), (ini, _) in zip(tramos, tramos[1:]):
        assert (ini - fin).days == 1
    assert all(a <= b for a, b in tramos)


def test_fechas_en_bd_por_particion(cfg_tmp):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        filas = con.execute("SELECT particion, MIN(fecha), MAX(fecha) FROM observacion GROUP BY particion").fetchall()
    rangos = {r[0]: (r[1], r[2]) for r in filas}
    for nombre, tramo in cfg_tmp.particion.como_dict().items():
        assert rangos[nombre] == tuple(tramo)
    assert rangos["operativa"] == (cfg_tmp.fecha_operativa, cfg_tmp.fecha_operativa)


def test_arranque_y_censura_no_son_objetivo(cfg_tmp):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        fechas = {r[0] for r in con.execute("SELECT DISTINCT fecha FROM observacion WHERE particion != 'operativa'")}
    assert min(fechas) == "2026-05-22"
    assert not fechas & {"2026-05-16", "2026-05-21", "2026-06-09", "2026-06-10"}


def test_configuracion_rechaza_particion_con_hueco(cfg):
    from dataclasses import replace

    mala = replace(cfg, particion=Particion(("2026-05-22", "2026-05-30"), ("2026-06-01", "2026-06-04"),
                                            ("2026-06-05", "2026-06-08")))  # fmt: skip
    with pytest.raises(ErrorConfiguracion):
        _validar(mala)
