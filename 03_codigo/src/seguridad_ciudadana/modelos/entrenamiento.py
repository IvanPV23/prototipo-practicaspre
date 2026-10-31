"""Estimadores, búsqueda pequeña de hiperparámetros con validación temporal y ajuste reproducible.

Regla: se ajusta con train y se elige con Macro F1 en valid. Test no participa en ninguna decisión.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

LOG = logging.getLogger(__name__)
MAX_ITER_LOGISTICA = 5000
MODELOS_ML = ("regresion_logistica", "random_forest", "gradient_boosting")


@dataclass
class ResultadoBusqueda:
    nombre: str
    mejores_parametros: dict[str, Any]
    mejor_macro_f1_valid: float
    estimador: Any
    candidatos: list[dict[str, Any]] = field(default_factory=list)


def construir_estimador(nombre: str, params: dict[str, Any], features: list[str], categoricas: list[str], semilla: int):
    """Desbalance ~7,7:1: class_weight='balanced' en LR y RF; en GB se pasa sample_weight balanceado al ajustar."""
    if nombre == "regresion_logistica":
        cat = [f for f in features if f in categoricas]
        num = [f for f in features if f not in categoricas]
        prepro = ColumnTransformer(
            [
                ("categoricas", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
                ("numericas", StandardScaler(), num),
            ]
        )
        clf = LogisticRegression(
            C=float(params["C"]), class_weight="balanced", max_iter=MAX_ITER_LOGISTICA, random_state=semilla
        )
        return Pipeline([("preprocesamiento", prepro), ("clasificador", clf)])
    if nombre == "random_forest":
        return RandomForestClassifier(
            n_estimators=int(params["n_estimators"]),
            max_depth=None if params["max_depth"] is None else int(params["max_depth"]),
            min_samples_leaf=int(params["min_samples_leaf"]),
            class_weight="balanced",
            random_state=semilla,
            n_jobs=1,  # un hilo: probabilidades idénticas bit a bit entre corridas (reproducibilidad)
        )
    if nombre == "gradient_boosting":
        return GradientBoostingClassifier(
            n_estimators=int(params["n_estimators"]),
            learning_rate=float(params["learning_rate"]),
            max_depth=int(params["max_depth"]),
            random_state=semilla,
        )
    raise ValueError(f"Modelo desconocido: {nombre}. Opciones: {MODELOS_ML}")


def ajustar(nombre: str, estimador, X: pd.DataFrame, y: np.ndarray):
    if nombre == "gradient_boosting":
        return estimador.fit(X, y, sample_weight=compute_sample_weight("balanced", y))
    return estimador.fit(X, y)


def expandir_grilla(grilla: dict[str, list[Any]]) -> list[dict[str, Any]]:
    claves = list(grilla)
    return [dict(zip(claves, valores)) for valores in itertools.product(*(grilla[c] for c in claves))]


def buscar(
    nombre: str,
    grilla: dict[str, list[Any]],
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_valid: pd.DataFrame,
    y_valid: np.ndarray,
    categoricas: list[str],
    semilla: int,
) -> ResultadoBusqueda:
    """Ajusta cada combinación con train y la puntúa en valid. Empates: gana la primera de la grilla."""
    features = list(X_train.columns)
    mejor: ResultadoBusqueda | None = None
    candidatos = []
    for params in expandir_grilla(grilla):
        est = ajustar(nombre, construir_estimador(nombre, params, features, categoricas, semilla), X_train, y_train)
        f1 = float(f1_score(y_valid, est.predict(X_valid), average="macro"))
        candidatos.append({"parametros": params, "macro_f1_valid": round(f1, 6)})
        LOG.info("  %s %s -> Macro F1 valid %.4f", nombre, params, f1)
        if mejor is None or f1 > mejor.mejor_macro_f1_valid:
            mejor = ResultadoBusqueda(nombre, params, f1, est)
    assert mejor is not None
    mejor.candidatos = candidatos
    return mejor
