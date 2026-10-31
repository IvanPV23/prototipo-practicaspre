"""Grilla regular de microzonas (500 m en EPSG:32718 con el origen del handoff de la Fase 2)."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from shapely.geometry import box, mapping
from shapely.geometry.base import BaseGeometry

from .geometria import a_wgs84


def celda_de(
    x: np.ndarray, y: np.ndarray, tamano_m: float, origen: tuple[float, float]
) -> tuple[np.ndarray, np.ndarray]:
    """Índices (col, fila) de la celda que contiene cada punto proyectado."""
    col = np.floor((np.asarray(x, dtype=float) - origen[0]) / tamano_m).astype(int)
    fila = np.floor((np.asarray(y, dtype=float) - origen[1]) / tamano_m).astype(int)
    return col, fila


def celdas_que_intersecan(tamano_m: float, origen: tuple[float, float], poligono: BaseGeometry) -> pd.DataFrame:
    """Todas las celdas de la grilla que tocan el polígono del distrito, con la fracción de área dentro."""
    _, _, maxx, maxy = poligono.bounds
    ncol = int(np.ceil((maxx - origen[0]) / tamano_m))
    nfil = int(np.ceil((maxy - origen[1]) / tamano_m))
    filas = []
    for c in range(ncol):
        for f in range(nfil):
            celda = box(
                origen[0] + c * tamano_m, origen[1] + f * tamano_m,
                origen[0] + (c + 1) * tamano_m, origen[1] + (f + 1) * tamano_m,
            )  # fmt: skip
            if celda.intersects(poligono):
                filas.append(
                    {"col": c, "fila": f, "geom": celda, "frac_dentro": celda.intersection(poligono).area / celda.area}
                )
    return pd.DataFrame(filas)


def construir_microzonas(
    celdas: pd.DataFrame,
    celdas_con_registro_train: set[tuple[int, int]],
    crs_metrico: str,
    prefijo_activa: str,
    prefijo_inactiva: str,
) -> pd.DataFrame:
    """Activa = celda del distrito con >= 1 incidencia en entrenamiento. Ids ordenados por fila desc, col asc
    (mismo orden que la Fase 2: MZ-0001 es la celda activa más al norte y al oeste)."""
    mz = celdas.copy()
    mz["activa"] = [int((c, f) in celdas_con_registro_train) for c, f in zip(mz.col, mz.fila)]
    mz = mz.sort_values(["fila", "col"], ascending=[False, True]).reset_index(drop=True)
    ids: list[str] = []
    contador = {1: 0, 0: 0}
    for activa in mz.activa:
        contador[activa] += 1
        prefijo = prefijo_activa if activa else prefijo_inactiva
        ids.append(f"{prefijo}{contador[activa]:04d}")
    mz["id"] = ids
    geoms = [a_wgs84(g, crs_metrico) for g in mz.geom]
    mz["geojson"] = [json.dumps(mapping(g)) for g in geoms]
    mz["centro_lat"] = [g.centroid.y for g in geoms]
    mz["centro_lon"] = [g.centroid.x for g in geoms]
    mz["frac_dentro"] = mz.frac_dentro.clip(0, 1).round(6)
    return mz.drop(columns="geom")
