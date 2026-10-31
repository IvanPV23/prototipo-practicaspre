"""Proyección de coordenadas y operaciones con el límite distrital (Shapely + pyproj, sin GeoPandas)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

CRS_GEOGRAFICO = "EPSG:4326"


@lru_cache(maxsize=4)
def _transformador(origen: str, destino: str) -> Transformer:
    return Transformer.from_crs(origen, destino, always_xy=True)


def proyectar(lon: np.ndarray, lat: np.ndarray, crs_metrico: str) -> tuple[np.ndarray, np.ndarray]:
    """WGS84 -> CRS métrico (UTM) para medir en metros."""
    t = _transformador(CRS_GEOGRAFICO, crs_metrico)
    return t.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))


def a_wgs84(geom: BaseGeometry, crs_metrico: str) -> BaseGeometry:
    return transform(_transformador(crs_metrico, CRS_GEOGRAFICO).transform, geom)


def leer_limite(ruta: Path) -> BaseGeometry:
    """Primer polígono del GeoJSON del límite distrital (WGS84)."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if not datos.get("features"):
        raise ValueError(f"El GeoJSON {ruta} no tiene features; revise rutas.limite en config.yaml")
    return shape(datos["features"][0]["geometry"])


def limite_metrico(ruta: Path, crs_metrico: str) -> BaseGeometry:
    return transform(_transformador(CRS_GEOGRAFICO, crs_metrico).transform, leer_limite(ruta))


def distancia_al_limite(x: np.ndarray, y: np.ndarray, poligono: BaseGeometry) -> np.ndarray:
    """0 si el punto está dentro; si no, distancia en metros al polígono."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    dentro = shapely.contains_xy(poligono, x, y)
    puntos = shapely.points(x, y)
    distancia = shapely.distance(poligono, puntos)
    return np.where(dentro, 0.0, distancia)
