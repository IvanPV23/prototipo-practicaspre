"""Priorización: R, G, F y P en [0, 1]; pesos normalizados; orden correcto en un caso construido a mano."""

import numpy as np
import pandas as pd
import pytest

from seguridad_ciudadana.priorizacion.calculo import (
    ErrorPesos,
    calcular_p,
    componente_f,
    componente_g,
    componente_r,
    normalizar_pesos,
    rankear,
)
from seguridad_ciudadana.servicios.priorizacion import ServicioPriorizacion

VALOR_NIVEL = {"Bajo": 0.0, "Medio": 0.5, "Alto": 1.0}


def test_normalizar_pesos_suma_uno():
    w = normalizar_pesos({"w1": 2, "w2": 1, "w3": 1})
    assert w == pytest.approx({"w1": 0.5, "w2": 0.25, "w3": 0.25})
    assert sum(w.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("pesos", [{"w1": 0, "w2": 0, "w3": 0}, {"w1": -0.1, "w2": 1, "w3": 0}])
def test_pesos_invalidos(pesos):
    with pytest.raises(ErrorPesos):
        normalizar_pesos(pesos)


def test_componentes_en_rango():
    r = componente_r(np.array([1, 0, 0.2]), np.array([0, 0, 0.3]), np.array([0, 1, 0.5]), VALOR_NIVEL)
    assert r == pytest.approx([0.0, 1.0, 0.65])
    g = componente_g(np.array([0.0, 1.0, 3.0, 5.0, 7.0]), 1.0, 5.0)
    assert g == pytest.approx([0.0, 0.0, 0.5, 1.0, 1.0])
    f = componente_f(np.array([0, 30, 61, 90]), 61.0)
    assert f.min() >= 0 and f.max() <= 1 and f[1] == pytest.approx(30 / 61)
    p = calcular_p(r, g[:3], f[:3], {"w1": 1, "w2": 1, "w3": 1})
    assert ((p >= 0) & (p <= 1)).all()


def test_orden_caso_a_mano():
    df = pd.DataFrame({
        "microzona_id": ["MZ-A", "MZ-B", "MZ-C", "MZ-D"],
        "r": [0.9, 0.2, 0.5, 0.5],
        "g": [0.1, 1.0, 0.5, 0.5],
        "f": [0.2, 0.9, 0.5, 0.5],
    })  # fmt: skip
    # Con w1 = 1 manda R: A primero; C y D empatan en P y R -> orden por id.
    solo_r = rankear(df, {"w1": 1, "w2": 0, "w3": 0})
    assert solo_r.microzona_id.tolist() == ["MZ-A", "MZ-C", "MZ-D", "MZ-B"]
    # Con w2 = w3 = 0,5 manda la historia: B primero (0,95), luego C, D (0,5) y A (0,15).
    historia = rankear(df, {"w1": 0, "w2": 0.5, "w3": 0.5})
    assert historia.microzona_id.tolist() == ["MZ-B", "MZ-C", "MZ-D", "MZ-A"]
    assert historia.posicion.tolist() == [1, 2, 3, 4]
    assert historia.p.tolist() == pytest.approx([0.95, 0.5, 0.5, 0.15])
    assert (historia.aporte_r + historia.aporte_g + historia.aporte_f).to_numpy() == pytest.approx(
        historia.p.to_numpy()
    )


def test_componentes_guardados_en_rango(bd_real):
    s = ServicioPriorizacion(bd_real)
    for fecha, turnos in s.fechas_disponibles().items():
        for turno in turnos:
            df = s.ranking_df(fecha, turno)
            for col in ("r", "g", "f", "p"):
                assert df[col].between(0, 1).all(), (fecha, turno, col)
            assert df.p.is_monotonic_decreasing
