"""Métricas de clasificación, desagregación por día y turno, bootstrap e importancia por permutación.

Con 4 días por partición la varianza es alta: además del Macro F1 global se reportan el Macro F1 por día y por
turno y dos intervalos bootstrap (por bloques de día y, dentro de cada día, por filas).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support

from ..dominio import NIVELES, TURNOS

ETIQUETAS = list(range(len(NIVELES)))
DECIMALES = 4


def _r(x: float) -> float:
    return round(float(x), DECIMALES)


def macro_f1(y: np.ndarray, yhat: np.ndarray) -> float:
    return float(f1_score(y, yhat, labels=ETIQUETAS, average="macro", zero_division=0))


def metricas(y: np.ndarray, yhat: np.ndarray) -> dict[str, Any]:
    """Macro F1 (principal), exactitud, precisión/recall/F1/soporte por clase y matriz de confusión."""
    p, r, f, s = precision_recall_fscore_support(y, yhat, labels=ETIQUETAS, zero_division=0)
    return {
        "macro_f1": _r(macro_f1(y, yhat)),
        "exactitud": _r(accuracy_score(y, yhat)),
        "por_clase": {
            n: {"precision": _r(p[i]), "recall": _r(r[i]), "f1": _r(f[i]), "soporte": int(s[i])}
            for i, n in enumerate(NIVELES)
        },
        "matriz_confusion": confusion_matrix(y, yhat, labels=ETIQUETAS).tolist(),
        "etiquetas": list(NIVELES),
        "n": int(len(y)),
    }


def por_grupo(fechas: pd.Series, turnos: pd.Series, y: np.ndarray, yhat: np.ndarray) -> dict[str, dict[str, float]]:
    df = pd.DataFrame({"fecha": fechas.to_numpy(), "turno": turnos.to_numpy(), "y": y, "yhat": yhat})
    return {
        "por_dia": {f: _r(macro_f1(g.y, g.yhat)) for f, g in df.groupby("fecha")},
        "por_turno": {t: _r(macro_f1(df[df.turno == t].y, df[df.turno == t].yhat)) for t in TURNOS},
    }


def _matriz(y: np.ndarray, yhat: np.ndarray) -> np.ndarray:
    k = len(ETIQUETAS)
    return np.bincount(np.asarray(y, dtype=int) * k + np.asarray(yhat, dtype=int), minlength=k * k).reshape(k, k)


def _macro_f1_desde_matriz(cm: np.ndarray) -> float:
    """Igual que f1_score(average='macro', zero_division=0) pero sobre una matriz ya sumada (rápido)."""
    tp = np.diag(cm).astype(float)
    denom = cm.sum(axis=0) + cm.sum(axis=1)
    f1 = np.divide(2 * tp, denom, out=np.zeros_like(tp), where=denom > 0)
    return float(f1.mean())


def bootstrap(
    fechas: pd.Series, y: np.ndarray, yhat: np.ndarray, repeticiones: int, semilla: int, confianza: float
) -> dict[str, Any]:
    """(a) IC del Macro F1 global remuestreando días completos (bloques) y (b) IC por día remuestreando filas."""
    rng = np.random.default_rng(semilla)
    fechas = pd.Series(fechas).to_numpy()
    y, yhat = np.asarray(y, dtype=int), np.asarray(yhat, dtype=int)
    alfa = (1 - confianza) / 2
    dias = sorted(set(fechas))
    matrices = np.stack([_matriz(y[fechas == d], yhat[fechas == d]) for d in dias])
    elegidos = rng.integers(0, len(dias), size=(repeticiones, len(dias)))
    globales = [_macro_f1_desde_matriz(matrices[fila].sum(axis=0)) for fila in elegidos]
    por_dia = {}
    for d in dias:
        yv, pv = y[fechas == d], yhat[fechas == d]
        idx = rng.integers(0, len(yv), size=(repeticiones, len(yv)))
        valores = [_macro_f1_desde_matriz(_matriz(yv[i], pv[i])) for i in idx]
        por_dia[str(d)] = {
            "macro_f1": _r(macro_f1(yv, pv)),
            "ic_inf": _r(np.quantile(valores, alfa)),
            "ic_sup": _r(np.quantile(valores, 1 - alfa)),
        }
    return {
        "metodo": f"bootstrap percentil, {repeticiones} réplicas, confianza {confianza:.0%}",
        "global_por_bloques_de_dia": {
            "ic_inf": _r(np.quantile(globales, alfa)),
            "ic_sup": _r(np.quantile(globales, 1 - alfa)),
        },
        "por_dia_filas": por_dia,
    }


def importancia_por_permutacion(
    estimador, X: pd.DataFrame, y: np.ndarray, grupos: dict[str, list[str]], repeticiones: int, semilla: int
) -> dict[str, Any]:
    """Caída del Macro F1 en validación al permutar (a) cada variable y (b) cada grupo completo a la vez.

    El permutado por grupo evita que variables correlacionadas del mismo grupo (p. ej. lag1 y suma3) se
    'cubran' entre sí y subestimen la importancia del grupo."""
    base = macro_f1(y, estimador.predict(X))
    individual = permutation_importance(
        estimador, X, y, scoring="f1_macro", n_repeats=repeticiones, random_state=semilla, n_jobs=1
    )
    por_variable = {
        c: {"media": _r(individual.importances_mean[i]), "desv": _r(individual.importances_std[i])}
        for i, c in enumerate(X.columns)
    }
    rng = np.random.default_rng(semilla)
    por_grupo_res = {}
    for nombre, columnas in grupos.items():
        columnas = [c for c in columnas if c in X.columns]
        if not columnas:
            continue
        caidas = []
        for _ in range(repeticiones):
            Xp = X.copy()
            orden = rng.permutation(len(X))
            Xp[columnas] = X[columnas].to_numpy()[orden]
            caidas.append(base - macro_f1(y, estimador.predict(Xp)))
        por_grupo_res[nombre] = {
            "media": _r(np.mean(caidas)),
            "desv": _r(np.std(caidas)),
            "suma_individual": _r(sum(por_variable[c]["media"] for c in columnas)),
            "variables": columnas,
        }
    return {"macro_f1_base_valid": _r(base), "por_variable": por_variable, "por_grupo": por_grupo_res}
