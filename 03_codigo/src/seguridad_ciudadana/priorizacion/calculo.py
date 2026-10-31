"""Prioridad explicable P = w1·R + w2·G + w3·F con componentes normalizados en [0, 1].

R (nivel estimado) = valor esperado del nivel: 0·p_bajo + 0,5·p_medio + 1·p_alto. Se prefiere a p_alto sola
porque conserva el orden ordinal y no descarta la masa de 'Medio'.
G (gravedad histórica) = gravedad media (1–5) de la microzona en d−7…d−1, normalizada (G−1)/4; 0 sin registros.
F (frecuencia reciente) = incidencias de la microzona en d−7…d−1 / máximo de entrenamiento, recortado a 1.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

PESOS = ("w1", "w2", "w3")


class ErrorPesos(ValueError):
    """Pesos inválidos (negativos o todos cero)."""


def normalizar_pesos(pesos: Mapping[str, float]) -> dict[str, float]:
    """Pesos no negativos reescalados para sumar 1 (lo que se muestra en la barra lateral)."""
    valores = {k: float(pesos.get(k, 0.0)) for k in PESOS}
    if any(v < 0 for v in valores.values()):
        raise ErrorPesos("Los pesos no pueden ser negativos.")
    total = sum(valores.values())
    if total <= 0:
        raise ErrorPesos("Al menos un peso debe ser mayor que 0.")
    return {k: v / total for k, v in valores.items()}


def componente_r(
    p_bajo: np.ndarray, p_medio: np.ndarray, p_alto: np.ndarray, valor_nivel: Mapping[str, float]
) -> np.ndarray:
    r = valor_nivel["Bajo"] * np.asarray(p_bajo) + valor_nivel["Medio"] * np.asarray(p_medio)
    r = r + valor_nivel["Alto"] * np.asarray(p_alto)
    return np.clip(r, 0.0, 1.0)


def componente_g(gravedad_media: np.ndarray, g_min: float, g_max: float) -> np.ndarray:
    g = np.asarray(gravedad_media, dtype=float)
    return np.where(g > 0, np.clip((g - g_min) / (g_max - g_min), 0.0, 1.0), 0.0)


def componente_f(suma7: np.ndarray, maximo_train: float) -> np.ndarray:
    if maximo_train <= 0:
        return np.zeros_like(np.asarray(suma7, dtype=float))
    return np.clip(np.asarray(suma7, dtype=float) / maximo_train, 0.0, 1.0)


def calcular_p(r: np.ndarray, g: np.ndarray, f: np.ndarray, pesos: Mapping[str, float]) -> np.ndarray:
    w = normalizar_pesos(pesos)
    return np.clip(w["w1"] * np.asarray(r) + w["w2"] * np.asarray(g) + w["w3"] * np.asarray(f), 0.0, 1.0)


def rankear(df: pd.DataFrame, pesos: Mapping[str, float]) -> pd.DataFrame:
    """Recalcula P con los pesos dados y ordena. Desempates: R, luego id de microzona (orden estable)."""
    w = normalizar_pesos(pesos)
    out = df.copy()
    out["w1"], out["w2"], out["w3"] = w["w1"], w["w2"], w["w3"]
    out["aporte_r"] = w["w1"] * out.r
    out["aporte_g"] = w["w2"] * out.g
    out["aporte_f"] = w["w3"] * out.f
    out["p"] = calcular_p(out.r, out.g, out.f, w)
    out = out.sort_values(["p", "r", "microzona_id"], ascending=[False, False, True]).reset_index(drop=True)
    out["posicion"] = np.arange(1, len(out) + 1)
    return out
