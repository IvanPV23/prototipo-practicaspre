"""Capa de persistencia: único lugar del sistema con SQL."""

from .conexion import BaseDatos, ErrorBaseDatos, inicializar_esquema

__all__ = ["BaseDatos", "ErrorBaseDatos", "inicializar_esquema"]
