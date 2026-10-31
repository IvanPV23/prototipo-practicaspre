"""Fuentes de datos y catálogo de tipos de incidencia."""

from __future__ import annotations

import sqlite3
from typing import Any

import pandas as pd


def guardar_fuente(con: sqlite3.Connection, fuente: dict[str, Any]) -> None:
    con.execute(
        """INSERT INTO fuente_datos (id, nombre, institucion, url, licencia, sha256, fecha_descarga, registros)
           VALUES (:id, :nombre, :institucion, :url, :licencia, :sha256, :fecha_descarga, :registros)
           ON CONFLICT (id) DO UPDATE SET nombre = excluded.nombre, institucion = excluded.institucion,
             url = excluded.url, licencia = excluded.licencia, sha256 = excluded.sha256,
             fecha_descarga = excluded.fecha_descarga, registros = excluded.registros""",
        fuente,
    )


def obtener_fuente(con: sqlite3.Connection, fuente_id: str) -> dict[str, Any] | None:
    fila = con.execute("SELECT * FROM fuente_datos WHERE id = ?", (fuente_id,)).fetchone()
    return dict(fila) if fila else None


def guardar_tipos(con: sqlite3.Connection, tipos: pd.DataFrame) -> dict[tuple[str, str], int]:
    """Inserta o actualiza el catálogo (tipo, subtipo, gravedad) y devuelve {(tipo, subtipo): id}."""
    columnas = ["tipo", "tipo_corto", "subtipo", "subtipo_norm", "gravedad", "justificacion"]
    con.executemany(
        """INSERT INTO tipo_incidencia (tipo, tipo_corto, subtipo, subtipo_norm, gravedad, justificacion)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT (tipo, subtipo) DO UPDATE SET tipo_corto = excluded.tipo_corto,
             subtipo_norm = excluded.subtipo_norm, gravedad = excluded.gravedad,
             justificacion = excluded.justificacion""",
        list(tipos[columnas].itertuples(index=False, name=None)),
    )
    filas = con.execute("SELECT id, tipo, subtipo FROM tipo_incidencia").fetchall()
    return {(f["tipo"], f["subtipo"]): f["id"] for f in filas}


def leer_tipos(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM tipo_incidencia ORDER BY gravedad DESC, tipo_corto, subtipo", con)
