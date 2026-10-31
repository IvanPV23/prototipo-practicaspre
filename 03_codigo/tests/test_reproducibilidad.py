"""Reproducibilidad: dos entrenamientos con la misma semilla dan las mismas métricas y predicciones."""

import numpy as np
import pytest

from seguridad_ciudadana.db import BaseDatos
from seguridad_ciudadana.db.repositorios import observaciones
from seguridad_ciudadana.features.tabla import matriz_modelo, niveles_a_codigo
from seguridad_ciudadana.modelos.entrenamiento import ajustar, construir_estimador
from seguridad_ciudadana.modelos.evaluacion import metricas

PARAMETROS = {
    "regresion_logistica": {"C": 1.0},
    "random_forest": {"n_estimators": 60, "max_depth": 6, "min_samples_leaf": 5},
    "gradient_boosting": {"n_estimators": 40, "learning_rate": 0.1, "max_depth": 2},
}


@pytest.fixture(scope="module")
def datos(cfg_tmp):
    with BaseDatos(cfg_tmp.rutas.base_datos).lectura() as con:
        tabla = observaciones.leer_tabla_modelado(con, ["train", "valid"])
    imput = cfg_tmp.features["imputacion_lag7_con"]
    partes = {p: tabla[tabla.particion == p] for p in ("train", "valid")}
    X = {p: matriz_modelo(g, cfg_tmp.features_modelo, imput) for p, g in partes.items()}
    y = {p: niveles_a_codigo(g.nivel) for p, g in partes.items()}
    return X, y


def _entrenar(cfg, nombre, X, y):
    est = construir_estimador(
        nombre, PARAMETROS[nombre], list(X["train"].columns), cfg.features["categoricas"], cfg.semilla
    )
    est = ajustar(nombre, est, X["train"], y["train"])
    pred = est.predict(X["valid"])
    return metricas(y["valid"], pred), est.predict_proba(X["valid"])


@pytest.mark.parametrize("nombre", list(PARAMETROS))
def test_misma_semilla_mismas_metricas(cfg_tmp, datos, nombre):
    X, y = datos
    m1, p1 = _entrenar(cfg_tmp, nombre, X, y)
    m2, p2 = _entrenar(cfg_tmp, nombre, X, y)
    assert m1 == m2
    assert np.array_equal(p1, p2)


def test_sin_nulos_tras_imputar(datos):
    X, _ = datos
    assert not X["train"].isna().any().any()
    assert not X["valid"].isna().any().any()
