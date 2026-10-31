"""Incidencias del CCO (una fila por registro de la fuente, con marcas de limpieza)."""

from __future__ import annotations

import sqlite3

import pandas as pd

COLUMNAS = [
    "id", "fuente_id", "tipo_id", "microzona_id", "fecha", "hora", "turno", "lat", "lon", "x_utm", "y_utm",
    "mz_col", "mz_fila", "sector", "zona", "canal_reporte", "tipo_reportante", "direccion", "dist_limite_m",
    "periodo", "excluida", "gravedad",
]  # fmt: skip


def _valor(v: object) -> object:
    if v is None or v is pd.NA or (isinstance(v, float) and v != v):
        return None
    return v.item() if hasattr(v, "item") else v


def reemplazar_incidencias(con: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Carga idempotente: borra y vuelve a insertar (ninguna otra tabla referencia incidencia)."""
    con.execute("DELETE FROM incidencia")
    filas = [tuple(_valor(v) for v in fila) for fila in df[COLUMNAS].itertuples(index=False, name=None)]
    marcadores = ", ".join("?" for _ in COLUMNAS)
    con.executemany(f"INSERT INTO incidencia ({', '.join(COLUMNAS)}) VALUES ({marcadores})", filas)
    return len(filas)


def asignar_microzonas(con: sqlite3.Connection, asignacion: list[tuple[str | None, str]]) -> None:
    """asignacion: [(microzona_id, incidencia_id)]."""
    con.execute("UPDATE incidencia SET microzona_id = NULL")
    con.executemany("UPDATE incidencia SET microzona_id = ? WHERE id = ?", asignacion)


def leer_incidencias(con: sqlite3.Connection, solo_limpias: bool = True) -> pd.DataFrame:
    """Incidencias con su tipo y gravedad. Limpias = dentro del límite o a <= tolerancia (no excluidas)."""
    filtro = "WHERE i.excluida = 0" if solo_limpias else ""
    return pd.read_sql_query(
        f"""SELECT i.*, t.tipo, t.tipo_corto, t.subtipo, t.subtipo_norm
            FROM incidencia i LEFT JOIN tipo_incidencia t ON t.id = i.tipo_id
            {filtro}
            ORDER BY i.fecha, i.hora, i.id""",
        con,
    )


def contar(con: sqlite3.Connection) -> dict[str, int]:
    fila = con.execute(
        """SELECT COUNT(*) AS total, SUM(excluida = 0) AS limpias, COUNT(DISTINCT id) AS ids,
                  SUM(excluida = 0 AND microzona_id IN (SELECT id FROM microzona WHERE activa = 1)) AS en_activas
           FROM incidencia"""
    ).fetchone()
    return {k: int(fila[k] or 0) for k in fila.keys()}  # noqa: SIM118 - sqlite3.Row


def incidencias_de_microzona(con: sqlite3.Connection, microzona_id: str, hasta_fecha: str) -> pd.DataFrame:
    """Incidencias limpias de una microzona con fecha estrictamente anterior a `hasta_fecha`."""
    return pd.read_sql_query(
        """SELECT i.id, i.fecha, i.hora, i.turno, t.tipo_corto, t.subtipo_norm AS subtipo, i.direccion,
                  i.sector, i.gravedad, i.periodo
           FROM incidencia i LEFT JOIN tipo_incidencia t ON t.id = i.tipo_id
           WHERE i.excluida = 0 AND i.microzona_id = ? AND i.fecha < ?
           ORDER BY i.fecha DESC, i.hora DESC""",
        con,
        params=(microzona_id, hasta_fecha),
    )


def puntos_en_ventana(con: sqlite3.Connection, desde: str, hasta_excl: str) -> pd.DataFrame:
    return pd.read_sql_query(
        """SELECT i.lat, i.lon, i.fecha, i.turno, t.tipo_corto
           FROM incidencia i LEFT JOIN tipo_incidencia t ON t.id = i.tipo_id
           WHERE i.excluida = 0 AND i.fecha >= ? AND i.fecha < ?""",
        con,
        params=(desde, hasta_excl),
    )
