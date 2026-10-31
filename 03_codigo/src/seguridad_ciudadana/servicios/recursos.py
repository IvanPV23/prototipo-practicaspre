"""ServicioRecursos (segundo nivel): disponibilidad ilustrativa por fecha y turno, y asignación validada."""

from __future__ import annotations

import sqlite3
from datetime import datetime

import pandas as pd

from ..config import Config
from ..db import BaseDatos
from ..db.repositorios import microzonas, recursos
from ..dominio import TURNOS
from ..recursos.asignacion import ErrorAsignacion, validar_asignacion, validar_disponibilidad

AVISO_ILUSTRATIVO = "Datos ilustrativos ingresados manualmente; no provienen de la municipalidad."


class ServicioRecursos:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.bd = BaseDatos(cfg.rutas.base_datos)

    def tipos(self) -> list[str]:
        return list(self.cfg.recursos["tipos"])

    def _validar_clave(self, turno: str, tipo: str) -> None:
        if turno not in TURNOS:
            raise ErrorAsignacion(f"Turno inválido: {turno}")
        if tipo not in self.tipos():
            raise ErrorAsignacion(f"Tipo de recurso inválido: {tipo}. Opciones: {', '.join(self.tipos())}")

    def registrar_disponibilidad(self, fecha: str, turno: str, tipo: str, cantidad: int) -> int:
        self._validar_clave(turno, tipo)
        with self.bd.transaccion() as con:
            actual = recursos.obtener_recurso(con, fecha, turno, tipo)
            validar_disponibilidad(int(cantidad), int(actual["asignado"]) if actual else 0, tipo)
            return recursos.guardar_disponibilidad(con, fecha, turno, tipo, int(cantidad))

    def disponibilidad(self, fecha: str, turno: str) -> pd.DataFrame:
        with self.bd.lectura() as con:
            df = recursos.listar_disponibilidad(con, fecha, turno)
        df["restante"] = df.cantidad - df.asignado
        return df

    def asignar(self, fecha: str, turno: str, tipo: str, microzona_id: str, cantidad: int) -> int:
        """Valida en el servicio (mensaje para el operador); la BD lo vuelve a impedir con un trigger."""
        self._validar_clave(turno, tipo)
        with self.bd.transaccion() as con:
            if microzonas.obtener_microzona(con, microzona_id) is None:
                raise ErrorAsignacion(f"No existe la microzona {microzona_id}.")
            recurso = recursos.obtener_recurso(con, fecha, turno, tipo)
            if recurso is None:
                raise ErrorAsignacion(f"Solo quedan 0 {tipo} disponibles para este turno.")
            validar_asignacion(int(recurso["cantidad"]), int(recurso["asignado"]), int(cantidad), tipo)
            try:
                return recursos.insertar_asignacion(
                    con, int(recurso["id"]), microzona_id, int(cantidad), datetime.now().isoformat(timespec="seconds")
                )
            except sqlite3.IntegrityError as error:  # carrera entre dos sesiones: el trigger tiene la última palabra
                raise ErrorAsignacion(f"No se pudo asignar: {error}") from error

    def asignaciones(self, fecha: str, turno: str) -> pd.DataFrame:
        with self.bd.lectura() as con:
            return recursos.listar_asignaciones(con, fecha, turno)

    def quitar(self, asignacion_id: int) -> bool:
        with self.bd.transaccion() as con:
            return recursos.eliminar_asignacion(con, int(asignacion_id)) > 0
