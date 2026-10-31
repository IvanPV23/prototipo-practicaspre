"""Conexión a SQLite con claves foráneas activas y transacciones explícitas."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

LOG = logging.getLogger(__name__)
RUTA_ESQUEMA = Path(__file__).with_name("schema.sql")
VERSION_ESQUEMA = 1


class ErrorBaseDatos(RuntimeError):
    """Problema de la base local; el mensaje indica el comando que lo resuelve."""


class BaseDatos:
    """Punto de acceso a la base. Abre una conexión por operación (seguro con los hilos de Streamlit)."""

    def __init__(self, ruta: Path) -> None:
        self.ruta = Path(ruta)

    def existe(self) -> bool:
        return self.ruta.exists() and self.ruta.stat().st_size > 0

    def _abrir(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.ruta, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    @contextmanager
    def lectura(self) -> Iterator[sqlite3.Connection]:
        if not self.existe():
            raise ErrorBaseDatos(f"No existe la base de datos {self.ruta}. Ejecute: python -m seguridad_ciudadana todo")
        con = self._abrir()
        try:
            yield con
        finally:
            con.close()

    @contextmanager
    def transaccion(self) -> Iterator[sqlite3.Connection]:
        """Escritura atómica: confirma al salir sin error y deshace ante cualquier excepción."""
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        con = self._abrir()
        try:
            con.execute("BEGIN")
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def inicializar_esquema(bd: BaseDatos) -> int:
    """Crea o actualiza el esquema (idempotente). Devuelve la versión resultante."""
    bd.ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(bd.ruta)
    try:
        version = con.execute("PRAGMA user_version").fetchone()[0]
        if version > VERSION_ESQUEMA:
            raise ErrorBaseDatos(
                f"La base {bd.ruta} tiene esquema v{version}, más nuevo que el del código (v{VERSION_ESQUEMA})."
            )
        con.executescript(RUTA_ESQUEMA.read_text(encoding="utf-8"))
        con.commit()
        version = con.execute("PRAGMA user_version").fetchone()[0]
    finally:
        con.close()
    LOG.info("Esquema de base de datos v%s listo en %s", version, bd.ruta)
    return version


def tablas(bd: BaseDatos) -> list[str]:
    with bd.lectura() as con:
        filas = con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    return [f["name"] for f in filas]
