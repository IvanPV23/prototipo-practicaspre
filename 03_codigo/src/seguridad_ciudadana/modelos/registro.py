"""Artefactos joblib versionados y huella de versión reproducible."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib

VERSION_BASE = "1.1.0"


def version_modelo(nombre: str, parametros: dict[str, Any], sha256_datos: str, config_hash: str) -> str:
    """Misma combinación de datos, config y parámetros => misma versión (reentrenar no duplica el registro)."""
    texto = json.dumps([nombre, parametros, sha256_datos, config_hash], sort_keys=True, default=str)
    return f"{VERSION_BASE}+{hashlib.sha256(texto.encode('utf-8')).hexdigest()[:10]}"


def guardar_artefacto(carpeta: Path, nombre: str, version: str, contenido: dict[str, Any]) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}-{version.replace('+', '_')}.joblib"
    joblib.dump(contenido, ruta)
    return ruta


def cargar_artefacto(ruta: Path) -> dict[str, Any]:
    if not Path(ruta).exists():
        raise FileNotFoundError(f"No existe el artefacto {ruta}. Ejecute: python -m seguridad_ciudadana entrenar")
    return joblib.load(ruta)
