"""Carga del CSV canónico de la Fase 1 y reglas de limpieza de la Fase 2 (R1–R5, R10).

El sistema reconstruye todo desde el canónico: no lee los CSV intermedios del analista.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..espacial.geometria import distancia_al_limite, limite_metrico, proyectar
from ..espacial.grilla import celda_de

LOG = logging.getLogger(__name__)
# R1: columnas de texto que pandas convertiría en números (ubigeo con ceros, ids hexadecimales como '0e12')
COLUMNAS_TEXTO = {"id_incidencia": str, "ubigeo_inei": str, "zona": str, "sector": str}
COLUMNAS_POST = ("estado_final", "fecha_hora_cierre", "tiempo_respuesta_min")


class ErrorIngesta(RuntimeError):
    """El dato de entrada no es el esperado; el mensaje explica cómo resolverlo."""


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_handoff_fase1(cfg: Config) -> dict:
    return json.loads(cfg.rutas.handoff_fase1.read_text(encoding="utf-8"))


def verificar_canonico(cfg: Config) -> tuple[str, dict]:
    """Compara el sha256 del CSV con el del handoff de la Fase 1; si difiere, se detiene."""
    if not cfg.rutas.canonico.exists():
        raise ErrorIngesta(f"No se encuentra el CSV canónico en {cfg.rutas.canonico}. Revise rutas.canonico.")
    handoff = leer_handoff_fase1(cfg)
    esperado = handoff["dataset_principal"]["sha256"]
    obtenido = sha256_archivo(cfg.rutas.canonico)
    if obtenido != esperado:
        raise ErrorIngesta(
            f"El sha256 del CSV canónico ({obtenido[:12]}…) no coincide con el handoff de la Fase 1 "
            f"({esperado[:12]}…). Vuelva a generar el canónico con los scripts de la Fase 1."
        )
    return obtenido, handoff


def leer_canonico(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, dtype=COLUMNAS_TEXTO, encoding="utf-8")
    # R7: las columnas [POST] no pasan del punto de ingesta (se conocen después del evento)
    return df.drop(columns=[c for c in COLUMNAS_POST if c in df.columns])


def leer_gravedad(ruta: Path) -> pd.DataFrame:
    tabla = pd.read_csv(ruta, encoding="utf-8")
    faltan = {"tipo", "tipo_corto", "subtipo", "subtipo_norm", "gravedad", "justificacion"} - set(tabla.columns)
    if faltan:
        raise ErrorIngesta(f"La tabla de gravedad {ruta} no tiene las columnas {sorted(faltan)}")
    return tabla


def periodo_de(fechas: pd.Series, cfg: Config) -> pd.Series:
    """R4/R5: arranque (solo historial), censurado (fuera de la tabla) o estable."""
    censuradas = set(cfg.datos["fechas_censuradas"])
    return pd.Series(
        np.where(
            fechas <= cfg.datos["fin_arranque"], "arranque", np.where(fechas.isin(censuradas), "censurado", "estable")
        ),
        index=fechas.index,
    )


def preparar_incidencias(df: pd.DataFrame, gravedad: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Añade proyección, distancia al límite, exclusión (R2), periodo (R4–R5), celda (R10) y gravedad."""
    mz = cfg.microzona
    out = df.copy()
    x, y = proyectar(out.lon.to_numpy(), out.lat.to_numpy(), mz["crs_metrico"])
    out["x_utm"], out["y_utm"] = np.round(x, 2), np.round(y, 2)
    poligono = limite_metrico(cfg.rutas.limite, mz["crs_metrico"])
    out["dist_limite_m"] = np.round(distancia_al_limite(x, y, poligono), 2)
    out["excluida"] = (out.dist_limite_m > float(cfg.datos["tolerancia_borde_m"])).astype(int)
    out["periodo"] = periodo_de(out.fecha, cfg)
    col, fila = celda_de(x, y, float(mz["tamano_m"]), tuple(mz["origen"]))
    out["mz_col"], out["mz_fila"] = col, fila
    out = out.merge(gravedad[["tipo", "subtipo", "gravedad"]], on=["tipo", "subtipo"], how="left", validate="m:1")
    sin_gravedad = out.gravedad.isna().sum()
    if sin_gravedad:
        raise ErrorIngesta(
            f"{sin_gravedad} incidencias no tienen gravedad: añada su (tipo, subtipo) a {cfg.rutas.gravedad}"
        )
    return out
