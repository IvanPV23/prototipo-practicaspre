"""Ingesta: conteos iguales al handoff, ids únicos, columnas [POST] fuera y verificación del sha256."""

import json
import shutil

import pytest

from seguridad_ciudadana.config import con_base_datos
from seguridad_ciudadana.db import BaseDatos
from seguridad_ciudadana.db.repositorios import incidencias
from seguridad_ciudadana.ingesta.canonico import ErrorIngesta, verificar_canonico
from seguridad_ciudadana.servicios import pipeline


def test_conteo_coincide_con_handoff_y_ids_unicos(cfg_tmp):
    h1 = json.loads(cfg_tmp.rutas.handoff_fase1.read_text(encoding="utf-8"))
    h2 = json.loads(cfg_tmp.rutas.handoff_fase2.read_text(encoding="utf-8"))
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        conteo = incidencias.contar(con)
    assert conteo["total"] == h1["dataset_principal"]["registros"] == 2592
    assert conteo["ids"] == conteo["total"]
    assert conteo["limpias"] == h2["dataset_limpio"]["registros"] == 2580


def test_columnas_post_no_se_guardan(cfg_tmp):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        columnas = {r["name"] for r in con.execute("PRAGMA table_info(incidencia)").fetchall()}
    assert not columnas & {"estado_final", "fecha_hora_cierre", "tiempo_respuesta_min", "nivel"}


def test_todas_las_incidencias_tienen_gravedad_y_tipo(cfg_tmp):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        df = incidencias.leer_incidencias(con, solo_limpias=False)
    assert df.gravedad.between(1, 5).all()
    assert df.tipo_id.notna().all()


def test_ingesta_idempotente(cfg_tmp):
    pipeline.ejecutar(cfg_tmp, "ingestar")
    pipeline.ejecutar(cfg_tmp, "construir")
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        assert incidencias.contar(con)["total"] == 2592
        assert con.execute("SELECT COUNT(*) FROM observacion WHERE particion != 'operativa'").fetchone()[0] == 4644


def test_sha256_distinto_detiene_la_ingesta(cfg, tmp_path):
    copia = tmp_path / "canonico.csv"
    shutil.copy(cfg.rutas.canonico, copia)
    with copia.open("a", encoding="utf-8") as f:
        f.write("\n")
    from dataclasses import replace

    c = con_base_datos(cfg, tmp_path / "s.db")
    c = replace(c, rutas=replace(c.rutas, canonico=copia))
    with pytest.raises(ErrorIngesta, match="sha256"):
        verificar_canonico(c)
