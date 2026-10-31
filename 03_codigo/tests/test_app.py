"""App: prueba de humo con streamlit.testing.v1.AppTest para cada página (carga sin excepción)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
PAGINAS = [APP / "Inicio.py", *sorted((APP / "pages").glob("*.py"))]
TIEMPO_MAX_S = 120


@pytest.mark.parametrize("pagina", PAGINAS, ids=[p.stem for p in PAGINAS])
def test_pagina_carga_sin_excepcion(bd_real, pagina):
    at = AppTest.from_file(str(pagina), default_timeout=TIEMPO_MAX_S).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.body for e in at.error]


def test_seis_paginas_mas_inicio():
    assert len(PAGINAS) == 7


def test_ranking_cambia_con_el_turno(bd_real):
    at = AppTest.from_file(str(APP / "pages" / "1_Ranking.py"), default_timeout=TIEMPO_MAX_S).run()
    at.sidebar.selectbox(key="turno_sel").set_value("Noche").run()
    assert not at.exception
    assert any("Noche" in m.value for m in at.metric)


def test_aviso_visible_en_ranking_y_mapa(bd_real):
    for nombre in ("1_Ranking.py", "2_Mapa.py"):
        at = AppTest.from_file(str(APP / "pages" / nombre), default_timeout=TIEMPO_MAX_S).run()
        textos = " ".join(m.value for m in at.markdown)
        assert "no delitos ni una condición permanente de la zona" in textos, nombre
