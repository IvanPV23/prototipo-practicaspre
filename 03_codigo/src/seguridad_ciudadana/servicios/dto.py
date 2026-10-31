"""Objetos de transferencia que la interfaz recibe de los servicios (sin SQL ni detalles de la BD)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class FilaRanking:
    posicion: int
    microzona_id: str
    sector: str
    nivel: str
    p_bajo: float
    p_medio: float
    p_alto: float
    r: float
    g: float
    f: float
    w1: float
    w2: float
    w3: float
    aporte_r: float
    aporte_g: float
    aporte_f: float
    p: float

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Metadatos:
    distrito: str
    fecha_corte_datos: str  # último día completo usado como historia
    fecha_corte_fuente: str
    fecha_operativa: str
    modelo_nombre: str
    modelo_nombre_legible: str
    modelo_version: str
    macro_f1_test: float | None
    macro_f1_valid: float | None
    pesos_por_defecto: dict[str, float]
    total_microzonas_activas: int


@dataclass(frozen=True)
class EstadoSistema:
    listo: bool
    mensaje: str
    comando: str = "python -m seguridad_ciudadana todo"


@dataclass
class DetalleMicrozona:
    microzona_id: str
    sector: str
    fecha: str
    turno: str
    nivel: str | None
    posicion: int | None
    total: int
    p: float | None
    componentes: list[dict[str, Any]] = field(default_factory=list)
    probabilidades: dict[str, float] = field(default_factory=dict)
    nivel_observado: str | None = None
    conteo_observado: int | None = None
    serie_diaria: Any = None  # DataFrame fecha, incidencias
    por_turno: Any = None  # DataFrame turno, incidencias
    por_tipo: Any = None  # DataFrame tipo, incidencias
    ultimas: Any = None  # DataFrame últimas incidencias (sin datos personales)
    centro: tuple[float, float] | None = None
    geojson: str | None = None
