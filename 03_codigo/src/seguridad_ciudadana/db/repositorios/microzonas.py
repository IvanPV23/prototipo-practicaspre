"""Microzonas (celdas de la grilla que intersecan el distrito)."""

from __future__ import annotations

import sqlite3

import pandas as pd

COLUMNAS = ["id", "col", "fila", "geojson", "centro_lat", "centro_lon", "frac_dentro", "sector_ref", "activa"]


def _limpio(v: object) -> object:
    if v is None or v is pd.NA or (isinstance(v, float) and v != v):
        return None
    return v.item() if hasattr(v, "item") else v


def guardar_microzonas(con: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Upsert por id: conserva las referencias de asignaciones existentes."""
    columnas = ", ".join(COLUMNAS)
    marcadores = ", ".join("?" for _ in COLUMNAS)
    con.executemany(
        f"""INSERT INTO microzona ({columnas}) VALUES ({marcadores})
            ON CONFLICT (id) DO UPDATE SET col = excluded.col, fila = excluded.fila, geojson = excluded.geojson,
              centro_lat = excluded.centro_lat, centro_lon = excluded.centro_lon,
              frac_dentro = excluded.frac_dentro, sector_ref = excluded.sector_ref, activa = excluded.activa""",
        [tuple(_limpio(v) for v in f) for f in df[COLUMNAS].itertuples(index=False, name=None)],
    )
    return len(df)


def leer_microzonas(con: sqlite3.Connection, solo_activas: bool = False) -> pd.DataFrame:
    filtro = "WHERE activa = 1" if solo_activas else ""
    return pd.read_sql_query(f"SELECT * FROM microzona {filtro} ORDER BY activa DESC, id", con)


def obtener_microzona(con: sqlite3.Connection, microzona_id: str) -> dict | None:
    fila = con.execute("SELECT * FROM microzona WHERE id = ?", (microzona_id,)).fetchone()
    return dict(fila) if fila else None
