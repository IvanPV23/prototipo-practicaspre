"""Servicios: ranking(fecha, turno, pesos) devuelve el contrato esperado; consultas de la app."""

import pytest

from seguridad_ciudadana.servicios.consultas import ServicioConsultas, calle_sin_numero
from seguridad_ciudadana.servicios.dto import FilaRanking
from seguridad_ciudadana.servicios.priorizacion import ServicioPriorizacion, SinPredicciones, sector_legible


@pytest.fixture(scope="module")
def prio(bd_real):
    return ServicioPriorizacion(bd_real)


@pytest.fixture(scope="module")
def consultas(bd_real):
    return ServicioConsultas(bd_real)


def test_ranking_contrato(prio, bd_real):
    filas = prio.ranking(bd_real.fecha_operativa, "Mañana", {"w1": 2, "w2": 1, "w3": 1})
    assert len(filas) == 86
    assert all(isinstance(f, FilaRanking) for f in filas)
    assert [f.posicion for f in filas] == list(range(1, 87))
    assert all(a.p >= b.p for a, b in zip(filas, filas[1:]))
    primera = filas[0]
    assert primera.w1 + primera.w2 + primera.w3 == pytest.approx(1.0)
    assert primera.w1 == pytest.approx(0.5)
    for f in filas:
        assert f.aporte_r + f.aporte_g + f.aporte_f == pytest.approx(f.p)
        assert f.p_bajo + f.p_medio + f.p_alto == pytest.approx(1.0, abs=1e-5)
        assert f.nivel in {"Bajo", "Medio", "Alto"}
        assert f.sector


def test_pesos_cambian_el_orden(prio, bd_real):
    solo_r = [f.microzona_id for f in prio.ranking(bd_real.fecha_operativa, "Noche", {"w1": 1, "w2": 0, "w3": 0})]
    solo_g = [f.microzona_id for f in prio.ranking(bd_real.fecha_operativa, "Noche", {"w1": 0, "w2": 1, "w3": 0})]
    assert solo_r != solo_g


def test_fechas_disponibles_solo_con_predicciones(prio, bd_real):
    fechas = prio.fechas_disponibles()
    esperadas = [*bd_real.particion.fechas_objetivo()[-4:], bd_real.fecha_operativa]
    assert list(fechas) == esperadas
    assert all(t == ["Mañana", "Tarde", "Noche"] for t in fechas.values())


def test_sin_predicciones(prio):
    with pytest.raises(SinPredicciones) as info:
        prio.ranking("2026-05-25", "Tarde")
    assert "2026-06-09" in info.value.disponibles


def test_detalle_y_mapa(consultas, prio, bd_real):
    fecha = bd_real.particion.test[0]
    top = prio.ranking(fecha, "Tarde")[0]
    det = consultas.detalle(top.microzona_id, fecha, "Tarde")
    assert det.posicion == 1 and det.p == pytest.approx(top.p)
    assert [c["componente"] for c in det.componentes] == ["R", "G", "F"]
    assert det.nivel_observado in {"Bajo", "Medio", "Alto"}  # fecha de prueba: hay observado
    assert (det.serie_diaria.fecha < fecha).all()
    assert len(det.ultimas) <= bd_real.app["ultimas_incidencias"]
    mapa = consultas.mapa(fecha, "Tarde")
    assert len(mapa["features"]) == 121
    assert sum(1 for f in mapa["features"] if f["properties"]["posicion"]) == 86


def test_metadatos_y_tablero(consultas, bd_real):
    meta = consultas.metadatos()
    assert meta.fecha_operativa == "2026-06-09" and meta.fecha_corte_datos == "2026-06-08"
    assert meta.macro_f1_test is not None
    t = consultas.tablero()
    assert t["kpis"]["total"] == 2580
    assert len(t["modelos"]) == 4 and t["modelos"].vigente.sum() == 1


def test_utilidades_de_presentacion():
    assert calle_sin_numero("Jesús Morales 221, San Juan de Miraflores 15801, Perú") == "Jesús Morales"
    assert calle_sin_numero(None) == "—"
    assert sector_legible("SECTOR II") == "Sector II"
    assert sector_legible(None) == "Sin sector"
