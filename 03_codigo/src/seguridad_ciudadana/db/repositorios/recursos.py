"""Recursos de patrullaje (ilustrativos) y asignaciones a microzonas."""

from __future__ import annotations

import sqlite3

import pandas as pd


def guardar_disponibilidad(con: sqlite3.Connection, fecha: str, turno: str, tipo: str, cantidad: int) -> int:
    con.execute(
        """INSERT INTO recurso_disponible (fecha, turno, tipo, cantidad) VALUES (?, ?, ?, ?)
           ON CONFLICT (fecha, turno, tipo) DO UPDATE SET cantidad = excluded.cantidad""",
        (fecha, turno, tipo, cantidad),
    )
    fila = con.execute(
        "SELECT id FROM recurso_disponible WHERE fecha = ? AND turno = ? AND tipo = ?", (fecha, turno, tipo)
    ).fetchone()
    return int(fila["id"])


def obtener_recurso(con: sqlite3.Connection, fecha: str, turno: str, tipo: str) -> dict | None:
    fila = con.execute(
        """SELECT r.*, COALESCE((SELECT SUM(a.cantidad) FROM asignacion a WHERE a.recurso_id = r.id), 0) AS asignado
           FROM recurso_disponible r WHERE r.fecha = ? AND r.turno = ? AND r.tipo = ?""",
        (fecha, turno, tipo),
    ).fetchone()
    return dict(fila) if fila else None


def listar_disponibilidad(con: sqlite3.Connection, fecha: str, turno: str) -> pd.DataFrame:
    return pd.read_sql_query(
        """SELECT r.id, r.tipo, r.cantidad,
                  COALESCE((SELECT SUM(a.cantidad) FROM asignacion a WHERE a.recurso_id = r.id), 0) AS asignado
           FROM recurso_disponible r WHERE r.fecha = ? AND r.turno = ? ORDER BY r.tipo""",
        con,
        params=(fecha, turno),
    )


def insertar_asignacion(con: sqlite3.Connection, recurso_id: int, microzona_id: str, cantidad: int, creado: str) -> int:
    cursor = con.execute(
        "INSERT INTO asignacion (recurso_id, microzona_id, cantidad, creado) VALUES (?, ?, ?, ?)",
        (recurso_id, microzona_id, cantidad, creado),
    )
    return int(cursor.lastrowid)


def listar_asignaciones(con: sqlite3.Connection, fecha: str, turno: str) -> pd.DataFrame:
    return pd.read_sql_query(
        """SELECT a.id, a.microzona_id, r.tipo, a.cantidad, a.creado
           FROM asignacion a JOIN recurso_disponible r ON r.id = a.recurso_id
           WHERE r.fecha = ? AND r.turno = ? ORDER BY a.id""",
        con,
        params=(fecha, turno),
    )


def eliminar_asignacion(con: sqlite3.Connection, asignacion_id: int) -> int:
    return con.execute("DELETE FROM asignacion WHERE id = ?", (asignacion_id,)).rowcount
