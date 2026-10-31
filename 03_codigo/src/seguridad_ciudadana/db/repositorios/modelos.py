"""Registro de modelos (trazabilidad: versión, datos, config, métricas, artefacto, vigente)."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def registrar_modelo(con: sqlite3.Connection, registro: dict[str, Any]) -> int:
    """Upsert por (nombre, version): reentrenar con los mismos datos y config no duplica filas."""
    datos = dict(registro)
    for clave in ("hiperparametros", "config", "metricas"):
        if not isinstance(datos[clave], str):
            datos[clave] = json.dumps(datos[clave], ensure_ascii=False, sort_keys=True, default=float)
    con.execute(
        """INSERT INTO modelo (nombre, version, hiperparametros, sha256_datos, config_hash, config, metricas,
                               macro_f1_valid, macro_f1_test, ruta_artefacto, vigente, creado, ejecucion_id)
           VALUES (:nombre, :version, :hiperparametros, :sha256_datos, :config_hash, :config, :metricas,
                   :macro_f1_valid, :macro_f1_test, :ruta_artefacto, 0, :creado, :ejecucion_id)
           ON CONFLICT (nombre, version) DO UPDATE SET hiperparametros = excluded.hiperparametros,
             sha256_datos = excluded.sha256_datos, config_hash = excluded.config_hash, config = excluded.config,
             metricas = excluded.metricas, macro_f1_valid = excluded.macro_f1_valid,
             macro_f1_test = excluded.macro_f1_test, ruta_artefacto = excluded.ruta_artefacto,
             creado = excluded.creado, ejecucion_id = excluded.ejecucion_id""",
        datos,
    )
    fila = con.execute(
        "SELECT id FROM modelo WHERE nombre = ? AND version = ?", (datos["nombre"], datos["version"])
    ).fetchone()
    return int(fila["id"])


def marcar_vigente(con: sqlite3.Connection, modelo_id: int) -> None:
    con.execute("UPDATE modelo SET vigente = 0 WHERE vigente = 1")
    con.execute("UPDATE modelo SET vigente = 1 WHERE id = ?", (modelo_id,))


def _decodificar(fila: sqlite3.Row) -> dict[str, Any]:
    d = dict(fila)
    for clave in ("hiperparametros", "config", "metricas"):
        d[clave] = json.loads(d[clave]) if d.get(clave) else {}
    return d


def modelo_vigente(con: sqlite3.Connection) -> dict[str, Any] | None:
    fila = con.execute("SELECT * FROM modelo WHERE vigente = 1").fetchone()
    return _decodificar(fila) if fila else None


def ultimos_por_nombre(con: sqlite3.Connection) -> list[dict[str, Any]]:
    """La versión más reciente de cada modelo (la que corresponde a la última ejecución de `entrenar`)."""
    filas = con.execute(
        """SELECT m.* FROM modelo m
           JOIN (SELECT nombre, MAX(id) AS id FROM modelo GROUP BY nombre) u ON u.id = m.id
           ORDER BY m.id"""
    ).fetchall()
    return [_decodificar(f) for f in filas]


def contar_modelos(con: sqlite3.Connection) -> int:
    return int(con.execute("SELECT COUNT(*) FROM modelo").fetchone()[0])
