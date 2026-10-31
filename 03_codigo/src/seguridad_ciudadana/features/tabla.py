"""Tabla de modelado microzona × fecha × turno, objetivo y variables sin fuga.

Principio de no fuga: las variables de una fila con fecha objetivo d se calculan solo con incidencias de fechas
estrictamente anteriores a d (información disponible al cierre de d−1). Reimplementa la especificación de la
Fase 2 (`especificacion_modelado.md` §3–§5); la equivalencia fila a fila se verifica en los tests.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from ..config import fechas_rango
from ..dominio import CODIGO_NIVEL, CODIGO_TURNO, NIVELES, TURNOS

ENTERAS = [
    "lag1_turno", "lag7_turno", "suma3_turno", "lag1_celda", "suma7_celda", "vecinos_lag1_turno", "vecinos_suma7",
    "distrito_lag1_turno", "distrito_lag1",
]  # fmt: skip
DECIMALES = ["media7_turno", "gravedad_media7_celda", "distrito_media7"]
DECIMALES_REDONDEO = 4
# La variable `turno` se guarda como código numérico en una columna aparte para no pisar el texto del turno.
COLUMNA_DE_FEATURE = {"turno": "turno_cod"}


def columna_de(feature: str) -> str:
    """Nombre de la columna de la tabla ancha que contiene la variable codificada."""
    return COLUMNA_DE_FEATURE.get(feature, feature)


def _matrices(hist: pd.DataFrame, microzonas: pd.DataFrame, fechas_hist: list[str]) -> dict:
    """Cubos de conteo y gravedad por (col, fila, día, turno) sobre todas las celdas con registros."""
    pos_fecha = {f: i for i, f in enumerate(fechas_hist)}
    h = hist[hist.fecha.isin(pos_fecha)]
    cols = np.concatenate([h.mz_col.to_numpy(), microzonas.col.to_numpy()])
    fils = np.concatenate([h.mz_fila.to_numpy(), microzonas.fila.to_numpy()])
    cmin, fmin = int(cols.min()) - 1, int(fils.min()) - 1
    nc, nf, nd = int(cols.max()) + 2 - cmin, int(fils.max()) + 2 - fmin, len(fechas_hist)
    C = np.zeros((nc, nf, nd, len(TURNOS)))
    G = np.zeros_like(C)
    indices = (
        (h.mz_col - cmin).to_numpy(),
        (h.mz_fila - fmin).to_numpy(),
        h.fecha.map(pos_fecha).to_numpy(),
        h.turno.map(CODIGO_TURNO).to_numpy(),
    )
    np.add.at(C, indices, 1)
    np.add.at(G, indices, h.gravedad.to_numpy(dtype=float))
    V = np.zeros_like(C)  # suma de las 8 celdas vecinas (queen), sin la propia
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            V[max(dx, 0) : nc + min(dx, 0), max(dy, 0) : nf + min(dy, 0)] += C[
                max(-dx, 0) : nc - max(dx, 0), max(-dy, 0) : nf - max(dy, 0)
            ]
    Dturno = C.sum(axis=(0, 1))
    return {
        "C": C, "G": G, "V": V, "Cdia": C.sum(axis=3), "Gdia": G.sum(axis=3), "Vdia": V.sum(axis=3),
        "Dturno": Dturno, "Ddia": Dturno.sum(axis=1), "cmin": cmin, "fmin": fmin, "pos_fecha": pos_fecha,
    }  # fmt: skip


def construir_tabla(
    hist: pd.DataFrame,
    microzonas: pd.DataFrame,
    fechas_objetivo: list[str],
    fecha_inicio_historia: str,
    feriados: Iterable[str],
    tope_dias_desde_ultima: int,
) -> pd.DataFrame:
    """hist: incidencias limpias (fecha, turno, mz_col, mz_fila, gravedad). microzonas: id, col, fila (activas).

    Devuelve una fila por microzona × fecha objetivo × turno con las 18 variables y `conteo` (que solo sirve para
    construir el objetivo; en fechas sin datos observados el conteo carece de sentido y se anula fuera)."""
    feriados = set(feriados)
    fechas_hist = fechas_rango(fecha_inicio_historia, max(fechas_objetivo))
    m = _matrices(hist, microzonas, fechas_hist)
    C, Cdia, G_dia, V, Vdia = m["C"], m["Cdia"], m["Gdia"], m["V"], m["Vdia"]
    filas = []
    for mz in microzonas.itertuples(index=False):
        i, j = int(mz.col) - m["cmin"], int(mz.fila) - m["fmin"]
        for fecha in fechas_objetivo:
            k = m["pos_fecha"][fecha]
            w7, w3 = slice(max(k - 7, 0), k), slice(max(k - 3, 0), k)
            n7 = k - max(k - 7, 0)
            previos = np.nonzero(Cdia[i, j, :k] > 0)[0]
            dias_ult = min(k - previos[-1], tope_dias_desde_ultima) if len(previos) else tope_dias_desde_ultima
            n_inc7 = Cdia[i, j, w7].sum()
            dia = pd.Timestamp(fecha)
            for t, turno in enumerate(TURNOS):
                filas.append(
                    {
                        "microzona_id": mz.id, "mz_col": int(mz.col), "mz_fila": int(mz.fila),
                        "fecha": fecha, "turno": turno,
                        "lag1_turno": C[i, j, k - 1, t] if k >= 1 else np.nan,
                        "lag7_turno": C[i, j, k - 7, t] if k >= 7 else np.nan,
                        "suma3_turno": C[i, j, w3, t].sum(),
                        "media7_turno": C[i, j, w7, t].sum() / n7 if n7 else np.nan,
                        "lag1_celda": Cdia[i, j, k - 1] if k >= 1 else np.nan,
                        "suma7_celda": Cdia[i, j, w7].sum(),
                        "dias_desde_ultima": dias_ult,
                        "gravedad_media7_celda": G_dia[i, j, w7].sum() / n_inc7 if n_inc7 else 0.0,
                        "vecinos_lag1_turno": V[i, j, k - 1, t] if k >= 1 else np.nan,
                        "vecinos_suma7": Vdia[i, j, w7].sum(),
                        "dia_semana": dia.dayofweek,
                        "fin_de_semana": int(dia.dayofweek >= 5),
                        "feriado": int(fecha in feriados),
                        "distrito_lag1_turno": m["Dturno"][k - 1, t] if k >= 1 else np.nan,
                        "distrito_lag1": m["Ddia"][k - 1] if k >= 1 else np.nan,
                        "distrito_media7": m["Ddia"][w7].sum() / n7 if n7 else np.nan,
                        "conteo": C[i, j, k, t],
                    }
                )  # fmt: skip
    tabla = pd.DataFrame(filas)
    for c in DECIMALES:
        tabla[c] = tabla[c].astype(float).round(DECIMALES_REDONDEO)
    return tabla


def umbral_b(conteos_train: pd.Series) -> float:
    """b = mediana de los conteos > 0 de entrenamiento (umbral Medio/Alto, fijo para valid y test)."""
    positivos = conteos_train[conteos_train > 0]
    if positivos.empty:
        raise ValueError("No hay conteos positivos en entrenamiento: no se puede fijar el umbral b")
    return float(positivos.median())


def nivel_vectorial(conteo: pd.Series, b: float) -> pd.Series:
    c = pd.Series(conteo, dtype="float")
    salida = pd.Series(np.where(c == 0, "Bajo", np.where(c <= b, "Medio", "Alto")), index=c.index, dtype="object")
    salida[c.isna()] = None
    return salida


def anadir_objetivo(tabla: pd.DataFrame, b: float, fechas_sin_objetivo: Iterable[str]) -> pd.DataFrame:
    """nivel (objetivo) y nivel_lag1_turno (variable) con el mismo b. En fechas futuras el objetivo es nulo."""
    out = tabla.copy()
    sin_objetivo = out.fecha.isin(set(fechas_sin_objetivo))
    out.loc[sin_objetivo, "conteo"] = np.nan
    out["nivel"] = nivel_vectorial(out.conteo, b)
    out["nivel_lag1_turno"] = nivel_vectorial(out.lag1_turno, b)
    return out


def codificar(tabla: pd.DataFrame) -> pd.DataFrame:
    """Categorías -> códigos ordinales para guardarlas como números (turno 0–2, nivel_lag1_turno 0–2)."""
    out = tabla.copy()
    out["turno_cod"] = out.turno.map(CODIGO_TURNO)
    out["nivel_lag1_turno"] = out.nivel_lag1_turno.map(CODIGO_NIVEL)
    return out


def matriz_modelo(tabla: pd.DataFrame, features: list[str], imputar_lag7_con: str | None) -> pd.DataFrame:
    """X para los estimadores a partir de la tabla ancha (turno y nivel_lag1_turno ya en códigos).

    lag7_turno solo es nulo el primer día objetivo (22 may); se imputa fila a fila con media7_turno, que también
    usa solo días previos, por lo que la imputación no introduce fuga ni depende de estadísticos de otras filas."""
    X = pd.DataFrame({f: tabla[columna_de(f)].astype(float) for f in features}, index=tabla.index)
    if imputar_lag7_con and "lag7_turno" in X:
        X["lag7_turno"] = X["lag7_turno"].fillna(tabla[imputar_lag7_con].astype(float))
    return X


def niveles_a_codigo(niveles: pd.Series) -> np.ndarray:
    return niveles.map(CODIGO_NIVEL).to_numpy(dtype=int)


def codigo_a_nivel(codigos: Iterable[int]) -> list[str]:
    return [NIVELES[int(c)] for c in codigos]
