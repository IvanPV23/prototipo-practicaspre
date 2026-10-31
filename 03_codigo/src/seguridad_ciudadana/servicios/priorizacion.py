"""ServicioPriorizacion: ranking(fecha, turno, pesos) con desglose explicable de P."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from ..config import Config
from ..db import BaseDatos
from ..db.repositorios import predicciones
from ..dominio import TURNOS
from ..priorizacion.calculo import normalizar_pesos, rankear
from .dto import FilaRanking

SIN_SECTOR = "Sin sector"


class SinPredicciones(LookupError):
    """No hay estimaciones para la fecha y turno pedidos."""

    def __init__(self, fecha: str, turno: str, disponibles: list[str]) -> None:
        self.fecha, self.turno, self.disponibles = fecha, turno, disponibles
        super().__init__(f"No hay estimaciones para {fecha} {turno}. Fechas disponibles: {', '.join(disponibles)}")


def sector_legible(sector: str | None) -> str:
    """'SECTOR II' -> 'Sector II'; nulo -> 'Sin sector' (el sector es referencial)."""
    if sector is None or (isinstance(sector, float) and sector != sector) or not str(sector).strip():
        return SIN_SECTOR
    palabras = str(sector).strip().split()
    return " ".join([palabras[0].capitalize(), *palabras[1:]])


class ServicioPriorizacion:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.bd = BaseDatos(cfg.rutas.base_datos)

    def pesos_por_defecto(self) -> dict[str, float]:
        return normalizar_pesos(self.cfg.priorizacion["pesos"])

    def fechas_disponibles(self) -> dict[str, list[str]]:
        """{fecha: [turnos]} solo con fechas que tienen predicciones del modelo vigente."""
        with self.bd.lectura() as con:
            df = predicciones.fechas_disponibles(con)
        salida: dict[str, list[str]] = {}
        for fecha, g in df.groupby("fecha", sort=True):
            salida[fecha] = [t for t in TURNOS if t in set(g.turno)]
        return salida

    def tipo_de_fecha(self, fecha: str) -> str:
        return "operativa" if fecha == self.cfg.fecha_operativa else "demostracion"

    def ranking_df(self, fecha: str, turno: str, pesos: Mapping[str, float] | None = None) -> pd.DataFrame:
        with self.bd.lectura() as con:
            df = predicciones.leer_componentes(con, fecha, turno)
        if df.empty:
            raise SinPredicciones(fecha, turno, list(self.fechas_disponibles()))
        df = rankear(df.drop(columns=["w1", "w2", "w3", "p", "posicion"]), pesos or self.cfg.priorizacion["pesos"])
        df["sector"] = [sector_legible(s) for s in df.sector_ref]
        return df

    def ranking(self, fecha: str, turno: str, pesos: Mapping[str, float] | None = None) -> list[FilaRanking]:
        """Lista ordenada por P descendente; cada fila trae R, G, F, pesos normalizados y aportes w·componente."""
        df = self.ranking_df(fecha, turno, pesos)
        campos = FilaRanking.__dataclass_fields__
        return [FilaRanking(**{k: fila[k] for k in campos}) for fila in df.to_dict("records")]
