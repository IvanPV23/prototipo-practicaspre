"""Calibración posterior con validación: probabilidades honestas y una regla de decisión que no infla 'Alto'.

Por qué: class_weight='balanced' compensa el desbalance al entrenar, pero infla p(Medio) y p(Alto). En v1.0.0 la
regresión logística marcaba Alto en el 20 % de validación (observado: 10 %) y hasta el 44 % de un día de prueba.
Se corrige en dos pasos, ambos ajustados solo con validación (ADR 0007):

1. Escalado de temperatura con sesgo por clase (3 parámetros) por máxima verosimilitud: la probabilidad media de
   cada nivel pasa a coincidir con su frecuencia observada. Estas probabilidades alimentan R en la priorización.
2. Desplazamientos aditivos sobre las log-probabilidades de Medio y Alto, elegidos en una rejilla por Macro F1:
   es la regla que decide el nivel que se muestra.

Como validación también se usa para elegir el modelo, sus métricas se calculan dejando un día fuera: cada día se
predice con un calibrador ajustado en los otros días, así el Macro F1 de validación no es optimista.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.base import BaseEstimator, ClassifierMixin

EPS = 1e-12
N_CLASES = 3


def _log_proba(P: np.ndarray) -> np.ndarray:
    return np.log(np.clip(np.asarray(P, dtype=float), EPS, 1.0))


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def macro_f1_rapido(y: np.ndarray, pred: np.ndarray) -> float:
    """Macro F1 con conteos de NumPy (misma definición que sklearn con zero_division=0); la rejilla lo llama miles de veces."""
    matriz = np.bincount(np.asarray(y) * N_CLASES + np.asarray(pred), minlength=N_CLASES**2).reshape(N_CLASES, -1)
    vp = np.diag(matriz).astype(float)
    denominador = matriz.sum(axis=0) + matriz.sum(axis=1)
    f1 = np.divide(2 * vp, denominador, out=np.zeros(N_CLASES), where=denominador > 0)
    return float(f1.mean())


@dataclass(frozen=True)
class Calibrador:
    temperatura: float
    sesgo: tuple[float, float, float]
    desplazamiento: tuple[float, float, float]

    def proba(self, P: np.ndarray) -> np.ndarray:
        return _softmax(_log_proba(P) / self.temperatura + np.asarray(self.sesgo))

    def decidir(self, Q: np.ndarray) -> np.ndarray:
        """Índice de clase sobre probabilidades ya calibradas."""
        return (_log_proba(Q) + np.asarray(self.desplazamiento)).argmax(axis=1)

    def como_dict(self) -> dict[str, float | list[float]]:
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in asdict(self).items()}


def ajustar_escala(P: np.ndarray, y: np.ndarray) -> tuple[float, tuple[float, float, float]]:
    """Temperatura y sesgo por clase (el de Bajo fijo en 0) que minimizan la log-pérdida."""
    L, y = _log_proba(P), np.asarray(y)

    def nll(theta: np.ndarray) -> float:
        Q = _softmax(L / np.exp(theta[0]) + np.r_[0.0, theta[1:]])
        return float(-np.log(Q[np.arange(len(y)), y] + EPS).mean())

    res = minimize(nll, np.zeros(N_CLASES), method="L-BFGS-B")
    return float(np.exp(res.x[0])), (0.0, float(res.x[1]), float(res.x[2]))


def ajustar_desplazamiento(Q: np.ndarray, y: np.ndarray, rejilla: np.ndarray) -> tuple[float, float, float]:
    """Desplazamientos de Medio y Alto que maximizan el Macro F1. Empates: el menor desplazamiento (más conservador)."""
    L, y = _log_proba(Q), np.asarray(y)
    mejor, mejor_f1 = (0.0, 0.0, 0.0), -1.0
    for dm in rejilla:
        for da in rejilla:
            f1 = macro_f1_rapido(y, (L + np.array([0.0, dm, da])).argmax(axis=1))
            if f1 > mejor_f1 + 1e-12:
                mejor, mejor_f1 = (0.0, float(dm), float(da)), f1
    return mejor


def ajustar_calibrador(P: np.ndarray, y: np.ndarray, rejilla: np.ndarray) -> Calibrador:
    temperatura, sesgo = ajustar_escala(P, y)
    previo = Calibrador(temperatura, sesgo, (0.0, 0.0, 0.0))
    return Calibrador(temperatura, sesgo, ajustar_desplazamiento(previo.proba(P), y, rejilla))


def predecir_dejando_un_dia_fuera(P: np.ndarray, y: np.ndarray, fechas: pd.Series, rejilla: np.ndarray) -> np.ndarray:
    """Predicción de validación sin optimismo: cada día con un calibrador ajustado en los demás días."""
    fechas = np.asarray(fechas)
    pred = np.empty(len(y), dtype=int)
    for dia in np.unique(fechas):
        dentro = fechas == dia
        cal = ajustar_calibrador(P[~dentro], np.asarray(y)[~dentro], rejilla)
        pred[dentro] = cal.decidir(cal.proba(P[dentro]))
    return pred


def rejilla_desde_config(calibracion: dict) -> np.ndarray:
    paso = float(calibracion["desplazamiento_paso"])
    return np.round(np.arange(0.0, float(calibracion["desplazamiento_max"]) + paso / 2, paso), 6)


class ModeloCalibrado(ClassifierMixin, BaseEstimator):
    """Envuelve un clasificador ya ajustado: misma interfaz (predict, predict_proba, classes_), salida calibrada.

    Se guarda tal cual en el artefacto joblib, de modo que predecir y la importancia por permutación lo usan
    sin cambios."""

    def __init__(self, base=None, calibrador: Calibrador | None = None) -> None:
        self.base = base
        self.calibrador = calibrador

    @property
    def classes_(self) -> np.ndarray:
        return self.base.classes_

    def fit(self, X, y):
        raise NotImplementedError("El modelo base se ajusta con train y el calibrador con validación (ver ADR 0007).")

    def predict_proba(self, X) -> np.ndarray:
        return self.calibrador.proba(self.base.predict_proba(X))

    def predict(self, X) -> np.ndarray:
        return self.classes_[self.calibrador.decidir(self.predict_proba(X))]
