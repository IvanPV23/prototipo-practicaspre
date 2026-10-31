"""Bitácora de ejecuciones del pipeline."""

from __future__ import annotations

import sqlite3


def iniciar(con: sqlite3.Connection, comando: str, inicio: str) -> int:
    cursor = con.execute(
        "INSERT INTO ejecucion_pipeline (comando, inicio, estado) VALUES (?, ?, 'en_curso')", (comando, inicio)
    )
    return int(cursor.lastrowid)


def finalizar(con: sqlite3.Connection, ejecucion_id: int, fin: str, estado: str, detalle: str) -> None:
    con.execute(
        "UPDATE ejecucion_pipeline SET fin = ?, estado = ?, detalle = ? WHERE id = ?",
        (fin, estado, detalle, ejecucion_id),
    )


def ultima_exitosa(con: sqlite3.Connection, comando: str) -> dict | None:
    fila = con.execute(
        "SELECT * FROM ejecucion_pipeline WHERE comando = ? AND estado = 'ok' ORDER BY id DESC LIMIT 1", (comando,)
    ).fetchone()
    return dict(fila) if fila else None
