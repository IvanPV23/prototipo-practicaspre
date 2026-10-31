"""Línea base de persistencia: repite el nivel del mismo turno del día anterior (nivel_lag1_turno)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..dominio import NIVELES


def predecir_persistencia(tabla: pd.DataFrame) -> np.ndarray:
    """Códigos 0–2. nivel_lag1_turno ya está codificado y nunca es nulo en las fechas objetivo."""
    codigos = tabla["nivel_lag1_turno"].astype(float)
    if codigos.isna().any():
        raise ValueError("nivel_lag1_turno tiene nulos: la persistencia no puede predecir esas filas")
    return codigos.astype(int).to_numpy()


def probabilidades_persistencia(tabla: pd.DataFrame) -> np.ndarray:
    """Probabilidad degenerada (1 en el nivel repetido) para poder priorizar con la misma interfaz."""
    codigos = predecir_persistencia(tabla)
    return np.eye(len(NIVELES))[codigos]
