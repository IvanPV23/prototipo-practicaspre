"""Calibración posterior (ADR 0007): probabilidades alineadas con las frecuencias, decisión coherente y sin usar prueba."""

import pickle

import numpy as np
import pytest
from sklearn.metrics import f1_score

from seguridad_ciudadana.db import BaseDatos
from seguridad_ciudadana.db.repositorios import modelos
from seguridad_ciudadana.modelos.calibracion import (
    Calibrador,
    ModeloCalibrado,
    ajustar_calibrador,
    macro_f1_rapido,
    predecir_dejando_un_dia_fuera,
)

REJILLA = np.round(np.arange(0.0, 3.05, 0.1), 6)


@pytest.fixture(scope="module")
def inflado():
    """Probabilidades que sobrestiman Medio/Alto, como hace class_weight='balanced'."""
    rng = np.random.default_rng(0)
    y = rng.choice(3, size=1200, p=[0.72, 0.18, 0.10])
    logits = rng.normal(0, 1, size=(1200, 3)) + 1.5 * np.eye(3)[y] + np.array([0.0, 0.6, 0.6])
    e = np.exp(logits)
    return e / e.sum(axis=1, keepdims=True), y


class _BaseFija:
    classes_ = np.array([0, 1, 2])

    def __init__(self, P):
        self.P = P

    def predict_proba(self, X):
        return self.P[np.asarray(X).ravel().astype(int)]


def test_macro_f1_rapido_igual_a_sklearn(inflado):
    P, y = inflado
    pred = P.argmax(axis=1)
    assert macro_f1_rapido(y, pred) == pytest.approx(f1_score(y, pred, average="macro", zero_division=0))


def test_probabilidad_media_coincide_con_la_frecuencia(inflado):
    P, y = inflado
    cal = ajustar_calibrador(P, y, REJILLA)
    observada = np.bincount(y, minlength=3) / len(y)
    assert np.abs(P.mean(axis=0) - observada).max() > 0.05  # sin calibrar está desalineada
    assert cal.proba(P).mean(axis=0) == pytest.approx(observada, abs=0.01)


def test_reduce_la_sobrestimacion_de_alto(inflado):
    P, y = inflado
    cal = ajustar_calibrador(P, y, REJILLA)
    antes = np.mean(P.argmax(axis=1) == 2)
    despues = np.mean(cal.decidir(cal.proba(P)) == 2)
    assert despues < antes
    assert macro_f1_rapido(y, cal.decidir(cal.proba(P))) >= macro_f1_rapido(y, P.argmax(axis=1)) - 1e-9


def test_dejando_un_dia_fuera_no_usa_el_dia_predicho(inflado):
    P, y = inflado
    dias = np.repeat(["d1", "d2", "d3", "d4"], 300)
    base = predecir_dejando_un_dia_fuera(P, y, dias, REJILLA)
    y_alterado = y.copy()
    y_alterado[dias == "d1"] = 2  # cambiar las etiquetas de d1 no puede cambiar su propia predicción
    assert np.array_equal(predecir_dejando_un_dia_fuera(P, y_alterado, dias, REJILLA)[dias == "d1"], base[dias == "d1"])


def test_modelo_calibrado_coherente_y_serializable(inflado):
    P, _ = inflado
    cal = Calibrador(1.3, (0.0, -1.0, -1.5), (0.0, 1.0, 1.2))
    modelo = ModeloCalibrado(_BaseFija(P), cal)
    X = np.arange(len(P)).reshape(-1, 1)
    Q = modelo.predict_proba(X)
    assert np.allclose(Q.sum(axis=1), 1.0)
    assert np.array_equal(modelo.predict(X), cal.decidir(Q))
    copia = pickle.loads(pickle.dumps(modelo))
    assert np.array_equal(copia.predict(X), modelo.predict(X))


def test_vigente_calibrado_y_predicciones_coherentes(bd_real):
    with BaseDatos(bd_real.rutas.base_datos).lectura() as con:
        vigente = modelos.modelo_vigente(con)
        filas = con.execute(
            "SELECT nivel, p_bajo, p_medio, p_alto FROM prediccion WHERE modelo_id = ?", (vigente["id"],)
        ).fetchall()
    assert "calibracion" in vigente["hiperparametros"]
    alto_predicho = np.mean([f[0] == "Alto" for f in filas])
    p_alto_media = np.mean([f[3] for f in filas])
    assert alto_predicho < 0.30  # v1.0.0 llegaba al 44 % en un día de prueba
    assert 0.05 < p_alto_media < 0.25  # probabilidades en el rango de la frecuencia observada (9–14 %)
