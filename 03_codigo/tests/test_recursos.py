"""Recursos: no se puede asignar más de lo disponible (servicio y base de datos)."""

import sqlite3

import pytest

from seguridad_ciudadana.db import BaseDatos
from seguridad_ciudadana.recursos.asignacion import ErrorAsignacion, validar_asignacion
from seguridad_ciudadana.servicios.recursos import ServicioRecursos

FECHA, TURNO = "2026-06-09", "Noche"


@pytest.fixture
def servicio(cfg_tmp):
    s = ServicioRecursos(cfg_tmp)
    with BaseDatos(cfg_tmp.rutas.base_datos).transaccion() as con:
        con.execute("DELETE FROM asignacion")
        con.execute("DELETE FROM recurso_disponible")
    return s


def test_regla_pura():
    validar_asignacion(3, 1, 2, "Camioneta")
    with pytest.raises(ErrorAsignacion, match="Solo quedan 2 Camioneta disponibles para este turno."):
        validar_asignacion(3, 1, 3, "Camioneta")
    with pytest.raises(ErrorAsignacion):
        validar_asignacion(3, 0, 0, "Camioneta")


def test_no_asigna_mas_de_lo_disponible(servicio):
    servicio.registrar_disponibilidad(FECHA, TURNO, "Camioneta", 2)
    servicio.asignar(FECHA, TURNO, "Camioneta", "MZ-0001", 1)
    servicio.asignar(FECHA, TURNO, "Camioneta", "MZ-0002", 1)
    with pytest.raises(ErrorAsignacion, match="Solo quedan 0 Camioneta"):
        servicio.asignar(FECHA, TURNO, "Camioneta", "MZ-0003", 1)
    disp = servicio.disponibilidad(FECHA, TURNO)
    assert disp.loc[disp.tipo == "Camioneta", "restante"].item() == 0


def test_sin_disponibilidad_registrada(servicio):
    with pytest.raises(ErrorAsignacion, match="Solo quedan 0 Motocicleta"):
        servicio.asignar(FECHA, TURNO, "Motocicleta", "MZ-0001", 1)


def test_no_reduce_disponibilidad_por_debajo_de_lo_asignado(servicio):
    servicio.registrar_disponibilidad(FECHA, TURNO, "A pie", 4)
    servicio.asignar(FECHA, TURNO, "A pie", "MZ-0001", 3)
    with pytest.raises(ErrorAsignacion):
        servicio.registrar_disponibilidad(FECHA, TURNO, "A pie", 2)


def test_quitar_libera_cupo(servicio):
    servicio.registrar_disponibilidad(FECHA, TURNO, "Otro", 1)
    aid = servicio.asignar(FECHA, TURNO, "Otro", "MZ-0001", 1)
    assert servicio.quitar(aid)
    servicio.asignar(FECHA, TURNO, "Otro", "MZ-0005", 1)
    assert len(servicio.asignaciones(FECHA, TURNO)) == 1


def test_trigger_de_la_base_impide_exceder(servicio, cfg_tmp):
    rid = servicio.registrar_disponibilidad(FECHA, TURNO, "Motocicleta", 1)
    with pytest.raises(sqlite3.IntegrityError), BaseDatos(cfg_tmp.rutas.base_datos).transaccion() as con:
        con.execute(
            "INSERT INTO asignacion (recurso_id, microzona_id, cantidad, creado) VALUES (?, 'MZ-0001', 2, 'x')", (rid,)
        )
