"""Esquema: la base se crea con las tablas y restricciones esperadas."""

import sqlite3

import pytest

from seguridad_ciudadana.db import BaseDatos, inicializar_esquema
from seguridad_ciudadana.db.conexion import tablas

TABLAS = {
    "fuente_datos", "tipo_incidencia", "microzona", "incidencia", "observacion", "feature", "modelo", "prediccion",
    "prioridad", "recurso_disponible", "asignacion", "ejecucion_pipeline",
}  # fmt: skip


@pytest.fixture
def bd(tmp_path):
    b = BaseDatos(tmp_path / "s.db")
    inicializar_esquema(b)
    return b


def test_crea_todas_las_tablas(bd):
    assert set(tablas(bd)) >= TABLAS


def test_esquema_idempotente_y_versionado(bd):
    assert inicializar_esquema(bd) == 1
    with bd.lectura() as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1


def test_claves_foraneas_activas(bd):
    with bd.lectura() as con:
        assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError), bd.transaccion() as con:
        con.execute(
            "INSERT INTO observacion (microzona_id, fecha, turno, conteo, nivel, particion) "
            "VALUES ('NO-EXISTE', '2026-06-01', 'Mañana', 0, 'Bajo', 'train')"
        )


def _microzona(con, mid="MZ-0001"):
    con.execute(
        "INSERT INTO microzona (id, col, fila, geojson, centro_lat, centro_lon, frac_dentro, activa) "
        "VALUES (?, 1, 1, '{}', -12.1, -76.9, 1.0, 1)",
        (mid,),
    )


def test_check_turno_y_unique_observacion(bd):
    with bd.transaccion() as con:
        _microzona(con)
    with pytest.raises(sqlite3.IntegrityError), bd.transaccion() as con:
        con.execute(
            "INSERT INTO observacion (microzona_id, fecha, turno, particion) VALUES ('MZ-0001', '2026-06-01', 'Madrugada', 'train')"
        )
    with pytest.raises(sqlite3.IntegrityError), bd.transaccion() as con:
        for _ in range(2):
            con.execute(
                "INSERT INTO observacion (microzona_id, fecha, turno, particion) VALUES ('MZ-0001', '2026-06-01', 'Tarde', 'train')"
            )


def test_cantidad_no_negativa(bd):
    with pytest.raises(sqlite3.IntegrityError), bd.transaccion() as con:
        con.execute(
            "INSERT INTO recurso_disponible (fecha, turno, tipo, cantidad) VALUES ('2026-06-09', 'Mañana', 'A pie', -1)"
        )


def test_un_solo_modelo_vigente(bd):
    fila = ("x", "{}", "sha", "h", "{}", "{}", 0.5, "2026-10-31")
    with pytest.raises(sqlite3.IntegrityError), bd.transaccion() as con:
        for i in range(2):
            con.execute(
                "INSERT INTO modelo (nombre, version, hiperparametros, sha256_datos, config_hash, config, metricas, "
                "macro_f1_valid, creado, vigente) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (fila[0], f"v{i}", *fila[1:]),
            )
