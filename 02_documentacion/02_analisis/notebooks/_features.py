"""Construcción de la tabla de modelado microzona × fecha × turno (implementación de referencia).

Principio de no fuga: todas las variables de una fila con fecha objetivo `d` se calculan exclusivamente con incidencias
registradas en fechas **estrictamente anteriores** a `d` (información disponible al cierre del día d-1).
La prueba programática está en 04_preparacion_modelado.ipynb (recalcular cada fecha con la historia truncada en d).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from _comun import FECHA_INICIO_DATOS, FERIADOS, NIVELES, TURNOS, fechas_rango

FEATURES = [
    # historial de la propia microzona
    "lag1_turno", "lag7_turno", "suma3_turno", "media7_turno", "lag1_celda", "suma7_celda",
    "dias_desde_ultima", "gravedad_media7_celda", "nivel_lag1_turno",
    # espacial (vecinos, rezagados)
    "vecinos_lag1_turno", "vecinos_suma7",
    # calendario
    "dia_semana", "fin_de_semana", "feriado", "turno",
    # contexto del distrito (rezagado)
    "distrito_lag1_turno", "distrito_lag1", "distrito_media7",
]
TOPE_DIAS_DESDE_ULTIMA = 14


def nivel_desde_conteo(conteo, b: float):
    """Bajo = 0; Medio = 1..b; Alto > b. NaN se conserva."""
    c = pd.Series(conteo, dtype="float")
    salida = pd.Series(np.where(c == 0, "Bajo", np.where(c <= b, "Medio", "Alto")), index=c.index, dtype="object")
    salida[c.isna()] = np.nan
    return salida


def construir_tabla(hist: pd.DataFrame, microzonas: pd.DataFrame, fechas_objetivo: list[str], b: float | None,
                    incluir_objetivo: bool = True) -> pd.DataFrame:
    """hist: incidencias limpias con columnas fecha, turno, mz_col, mz_fila, gravedad.
    microzonas: id_microzona, col, fila (activas). b: umbral Medio/Alto (None -> sin nivel_lag1_turno).
    Solo se usan filas de hist con fecha < fecha objetivo para las variables; el conteo objetivo usa la propia fecha.
    """
    fechas_hist = fechas_rango(FECHA_INICIO_DATOS, max(fechas_objetivo))
    pos_fecha = {f: i for i, f in enumerate(fechas_hist)}
    h = hist[hist.fecha.isin(pos_fecha)].copy()
    cmin = int(min(h.mz_col.min() if len(h) else 0, microzonas.col.min())) - 1
    fmin = int(min(h.mz_fila.min() if len(h) else 0, microzonas.fila.min())) - 1
    cmax = int(max(h.mz_col.max() if len(h) else 0, microzonas.col.max())) + 1
    fmax = int(max(h.mz_fila.max() if len(h) else 0, microzonas.fila.max())) + 1
    nc, nf, nd = cmax - cmin + 1, fmax - fmin + 1, len(fechas_hist)
    C = np.zeros((nc, nf, nd, 3))          # conteos
    G = np.zeros((nc, nf, nd, 3))          # suma de gravedad
    ic = (h.mz_col - cmin).to_numpy(); jf = (h.mz_fila - fmin).to_numpy()
    kd = h.fecha.map(pos_fecha).to_numpy(); tt = h.turno.map({t: i for i, t in enumerate(TURNOS)}).to_numpy()
    np.add.at(C, (ic, jf, kd, tt), 1)
    np.add.at(G, (ic, jf, kd, tt), h.gravedad.to_numpy(dtype=float))
    Cdia = C.sum(axis=3)
    Gdia = G.sum(axis=3)
    # suma de los 8 vecinos (queen), sin la propia celda
    V = np.zeros_like(C)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            V[max(dx, 0):nc + min(dx, 0), max(dy, 0):nf + min(dy, 0)] += C[max(-dx, 0):nc - max(dx, 0), max(-dy, 0):nf - max(dy, 0)]
    Vdia = V.sum(axis=3)
    Dturno = C.sum(axis=(0, 1))             # (nd, 3)
    Ddia = Dturno.sum(axis=1)               # (nd,)

    filas = []
    for _, mz in microzonas.iterrows():
        i, j = int(mz.col) - cmin, int(mz.fila) - fmin
        for fecha in fechas_objetivo:
            k = pos_fecha[fecha]
            w7 = slice(max(k - 7, 0), k); w3 = slice(max(k - 3, 0), k)
            n7 = k - max(k - 7, 0)
            previos = np.nonzero(Cdia[i, j, :k] > 0)[0]
            dias_ult = min(k - previos[-1], TOPE_DIAS_DESDE_ULTIMA) if len(previos) else TOPE_DIAS_DESDE_ULTIMA
            n_inc7 = Cdia[i, j, w7].sum()
            fd = pd.Timestamp(fecha)
            for t_idx, turno in enumerate(TURNOS):
                fila = {
                    "id_microzona": mz.id_microzona, "mz_col": int(mz.col), "mz_fila": int(mz.fila),
                    "fecha": fecha, "turno": turno,
                    "lag1_turno": C[i, j, k - 1, t_idx] if k >= 1 else np.nan,
                    "lag7_turno": C[i, j, k - 7, t_idx] if k >= 7 else np.nan,
                    "suma3_turno": C[i, j, w3, t_idx].sum(),
                    "media7_turno": C[i, j, w7, t_idx].sum() / n7 if n7 else np.nan,
                    "lag1_celda": Cdia[i, j, k - 1] if k >= 1 else np.nan,
                    "suma7_celda": Cdia[i, j, w7].sum(),
                    "dias_desde_ultima": dias_ult,
                    "gravedad_media7_celda": Gdia[i, j, w7].sum() / n_inc7 if n_inc7 else 0.0,
                    "vecinos_lag1_turno": V[i, j, k - 1, t_idx] if k >= 1 else np.nan,
                    "vecinos_suma7": Vdia[i, j, w7].sum(),
                    "dia_semana": fd.dayofweek, "fin_de_semana": int(fd.dayofweek >= 5), "feriado": int(fecha in FERIADOS),
                    "distrito_lag1_turno": Dturno[k - 1, t_idx] if k >= 1 else np.nan,
                    "distrito_lag1": Ddia[k - 1] if k >= 1 else np.nan,
                    "distrito_media7": Ddia[w7].sum() / n7 if n7 else np.nan,
                }
                if incluir_objetivo:
                    fila["conteo"] = C[i, j, k, t_idx]
                filas.append(fila)
    tabla = pd.DataFrame(filas)
    tabla["nivel_lag1_turno"] = nivel_desde_conteo(tabla.lag1_turno, b) if b is not None else np.nan
    if incluir_objetivo and b is not None:
        tabla["nivel"] = nivel_desde_conteo(tabla.conteo, b)
    enteros = ["lag1_turno", "lag7_turno", "suma3_turno", "lag1_celda", "suma7_celda", "vecinos_lag1_turno", "vecinos_suma7",
               "distrito_lag1_turno", "distrito_lag1", "conteo"]
    for c in enteros:
        if c in tabla:
            tabla[c] = tabla[c].astype("Int64") if tabla[c].isna().any() else tabla[c].astype(int)
    for c in ["media7_turno", "gravedad_media7_celda", "distrito_media7"]:
        tabla[c] = tabla[c].astype(float).round(4)
    return tabla
