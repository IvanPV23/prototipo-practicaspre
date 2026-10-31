"""Predicciones del modelo vigente y su priorización."""

from __future__ import annotations

import sqlite3

import pandas as pd


def reemplazar_predicciones(con: sqlite3.Connection, modelo_id: int, df: pd.DataFrame) -> int:
    """Idempotente: elimina todas las predicciones (y sus prioridades en cascada) y vuelve a insertar."""
    con.execute("DELETE FROM prioridad")
    con.execute("DELETE FROM prediccion")
    con.executemany(
        """INSERT INTO prediccion (modelo_id, microzona_id, fecha, turno, nivel, p_bajo, p_medio, p_alto, tipo_fecha)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                modelo_id,
                f.microzona_id,
                f.fecha,
                f.turno,
                f.nivel,
                float(f.p_bajo),
                float(f.p_medio),
                float(f.p_alto),
                f.tipo_fecha,
            )
            for f in df.itertuples(index=False)
        ],
    )
    return len(df)


def leer_predicciones(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM prediccion ORDER BY fecha, turno, microzona_id", con)


def reemplazar_prioridades(con: sqlite3.Connection, df: pd.DataFrame) -> int:
    con.execute("DELETE FROM prioridad")
    con.executemany(
        "INSERT INTO prioridad (prediccion_id, r, g, f, w1, w2, w3, p, posicion) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                int(f.prediccion_id),
                float(f.r),
                float(f.g),
                float(f.f),
                float(f.w1),
                float(f.w2),
                float(f.w3),
                float(f.p),
                int(f.posicion),
            )
            for f in df.itertuples(index=False)
        ],
    )
    return len(df)


def fechas_disponibles(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """SELECT p.fecha, p.turno, p.tipo_fecha, COUNT(*) AS n
           FROM prediccion p JOIN prioridad q ON q.prediccion_id = p.id
           JOIN modelo m ON m.id = p.modelo_id AND m.vigente = 1
           GROUP BY p.fecha, p.turno, p.tipo_fecha ORDER BY p.fecha""",
        con,
    )


def leer_componentes(con: sqlite3.Connection, fecha: str, turno: str) -> pd.DataFrame:
    """Predicción + componentes R, G, F del modelo vigente para una fecha y turno."""
    return pd.read_sql_query(
        """SELECT p.id AS prediccion_id, p.microzona_id, mz.sector_ref, p.fecha, p.turno, p.nivel,
                  p.p_bajo, p.p_medio, p.p_alto, p.tipo_fecha, q.r, q.g, q.f, q.w1, q.w2, q.w3, q.p, q.posicion,
                  mz.centro_lat, mz.centro_lon
           FROM prediccion p
           JOIN prioridad q ON q.prediccion_id = p.id
           JOIN modelo m ON m.id = p.modelo_id AND m.vigente = 1
           JOIN microzona mz ON mz.id = p.microzona_id
           WHERE p.fecha = ? AND p.turno = ?""",
        con,
        params=(fecha, turno),
    )


def observado(con: sqlite3.Connection, fecha: str, turno: str) -> pd.DataFrame:
    """Nivel observado (si existe) para comparar en la ficha; NULL en la fecha operativa."""
    return pd.read_sql_query(
        "SELECT microzona_id, conteo, nivel AS nivel_observado FROM observacion WHERE fecha = ? AND turno = ?",
        con,
        params=(fecha, turno),
    )
