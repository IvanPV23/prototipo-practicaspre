"""Observaciones microzona × fecha × turno y sus variables (formato largo)."""

from __future__ import annotations

import sqlite3

import pandas as pd


def reemplazar_observaciones(con: sqlite3.Connection, tabla: pd.DataFrame, columnas: dict[str, str]) -> int:
    """Borra y reinserta la tabla de modelado. `tabla` trae microzona_id, fecha, turno, conteo, nivel,
    particion y las variables ya codificadas como números; `columnas` = {nombre_variable: columna_de_tabla}."""
    features = list(columnas)
    con.execute("DELETE FROM feature")
    con.execute("DELETE FROM observacion")
    obs = [
        (
            f.microzona_id,
            f.fecha,
            f.turno,
            None if pd.isna(f.conteo) else int(f.conteo),
            None if pd.isna(f.nivel) else f.nivel,
            f.particion,
        )
        for f in tabla.itertuples(index=False)
    ]
    con.executemany(
        "INSERT INTO observacion (microzona_id, fecha, turno, conteo, nivel, particion) VALUES (?, ?, ?, ?, ?, ?)",
        obs,
    )
    ids = {
        (r["microzona_id"], r["fecha"], r["turno"]): r["id"]
        for r in con.execute("SELECT id, microzona_id, fecha, turno FROM observacion").fetchall()
    }
    valores = []
    origen = [columnas[n] for n in features]
    for f in tabla[["microzona_id", "fecha", "turno", *origen]].itertuples(index=False, name=None):
        oid = ids[(f[0], f[1], f[2])]
        for nombre, v in zip(features, f[3:]):
            valores.append((oid, nombre, None if pd.isna(v) else float(v)))
    con.executemany("INSERT INTO feature (observacion_id, nombre, valor) VALUES (?, ?, ?)", valores)
    return len(obs)


def leer_tabla_modelado(con: sqlite3.Connection, particiones: list[str] | None = None) -> pd.DataFrame:
    """Tabla ancha (una fila por observación, una columna por variable)."""
    filtro, params = "", ()
    if particiones:
        filtro = f"WHERE o.particion IN ({', '.join('?' for _ in particiones)})"
        params = tuple(particiones)
    largo = pd.read_sql_query(
        f"""SELECT o.id AS observacion_id, o.microzona_id, o.fecha, o.turno, o.conteo, o.nivel, o.particion,
                   f.nombre, f.valor
            FROM observacion o JOIN feature f ON f.observacion_id = o.id {filtro}""",
        con,
        params=params,
    )
    if largo.empty:
        return largo
    claves = ["observacion_id", "microzona_id", "fecha", "turno", "particion"]
    largo["nombre"] = [f"{n}_cod" if n in claves else n for n in largo.nombre]  # p. ej. turno -> turno_cod
    ancho = largo.pivot(index=claves, columns="nombre", values="valor").reset_index()
    ancho.columns.name = None
    objetivo = largo.drop_duplicates("observacion_id").set_index("observacion_id")[["conteo", "nivel"]]
    ancho = ancho.join(objetivo, on="observacion_id")
    return ancho.sort_values(["fecha", "microzona_id", "observacion_id"]).reset_index(drop=True)


def contar_por_particion(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT particion, nivel, COUNT(*) AS n FROM observacion GROUP BY particion, nivel", con)
