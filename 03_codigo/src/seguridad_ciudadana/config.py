"""Carga y validación de `config/config.yaml`.

Toda constante del dominio (distrito, rutas, partición, pesos, semillas) vive en el YAML para que adaptar el
sistema a otro distrito sea cambiar configuración y datos, no código.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

VARIABLE_ENTORNO_CONFIG = "SEGURIDAD_CONFIG"
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_CONFIG_POR_DEFECTO = RAIZ_PROYECTO / "config" / "config.yaml"


class ErrorConfiguracion(ValueError):
    """La configuración no es coherente; el mensaje dice qué corregir en config.yaml."""


@dataclass(frozen=True)
class Rutas:
    canonico: Path
    handoff_fase1: Path
    handoff_fase2: Path
    limite: Path
    gravedad: Path
    tabla_referencia_fase2: Path
    informe_fase1: Path
    informe_fase2: Path
    base_datos: Path
    modelos: Path
    reportes: Path
    docs: Path


@dataclass(frozen=True)
class Particion:
    train: tuple[str, str]
    valid: tuple[str, str]
    test: tuple[str, str]

    def como_dict(self) -> dict[str, tuple[str, str]]:
        return {"train": self.train, "valid": self.valid, "test": self.test}

    def de_fecha(self, fecha: str) -> str | None:
        for nombre, (ini, fin) in self.como_dict().items():
            if ini <= fecha <= fin:
                return nombre
        return None

    def fechas_objetivo(self) -> list[str]:
        return fechas_rango(self.train[0], self.test[1])


@dataclass(frozen=True)
class Config:
    proyecto: dict[str, Any]
    rutas: Rutas
    datos: dict[str, Any]
    microzona: dict[str, Any]
    particion: Particion
    objetivo: dict[str, Any]
    features: dict[str, Any]
    modelado: dict[str, Any]
    prediccion: dict[str, Any]
    priorizacion: dict[str, Any]
    recursos: dict[str, Any]
    app: dict[str, Any]
    calibracion: dict[str, Any]
    ruta_archivo: Path
    crudo: dict[str, Any] = field(repr=False, default_factory=dict)

    # ------------------------------------------------------------------ derivados
    @property
    def semilla(self) -> int:
        return int(self.modelado["semilla"])

    @property
    def features_modelo(self) -> list[str]:
        """Variables que entran al estimador (las 18 del handoff menos las excluidas con justificación)."""
        excluidas = set(self.features.get("excluidas_modelo", []))
        return [f for f in self.features["lista"] if f not in excluidas]

    @property
    def ultimo_dia_completo(self) -> str:
        return self.particion.test[1]

    @property
    def fecha_operativa(self) -> str:
        """Día siguiente al último día completo: la fecha que el operador planifica (ver ADR 0003)."""
        return (date.fromisoformat(self.ultimo_dia_completo) + timedelta(days=1)).isoformat()

    def hash(self) -> str:
        """Huella de la configuración (trazabilidad del registro de modelos)."""
        texto = json.dumps(self.crudo, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def fechas_rango(inicio: str, fin: str) -> list[str]:
    """Fechas ISO consecutivas entre inicio y fin, ambos incluidos."""
    d0, d1 = date.fromisoformat(inicio), date.fromisoformat(fin)
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


def _resolver(base: Path, valor: str) -> Path:
    ruta = Path(valor)
    return ruta if ruta.is_absolute() else (base / ruta).resolve()


def _validar(cfg: Config) -> None:
    tramos = [cfg.particion.train, cfg.particion.valid, cfg.particion.test]
    for ini, fin in tramos:
        if ini > fin:
            raise ErrorConfiguracion(f"Partición con inicio posterior al fin: {ini} > {fin}")
    for (_, fin_a), (ini_b, _) in zip(tramos, tramos[1:]):
        if (date.fromisoformat(ini_b) - date.fromisoformat(fin_a)).days != 1:
            raise ErrorConfiguracion("La partición temporal debe ser contigua y sin solapamiento (revise 'particion').")
    pesos = cfg.priorizacion["pesos"]
    if any(float(v) < 0 for v in pesos.values()) or sum(float(v) for v in pesos.values()) <= 0:
        raise ErrorConfiguracion("Los pesos de priorización deben ser no negativos y sumar más que 0.")
    prohibidas = set(cfg.features.get("prohibidas", []))
    if prohibidas & set(cfg.features["lista"]):
        raise ErrorConfiguracion(
            f"Hay variables prohibidas por fuga en features.lista: {prohibidas & set(cfg.features['lista'])}"
        )


def cargar_config(ruta: str | Path | None = None) -> Config:
    """Lee el YAML (ruta explícita, variable SEGURIDAD_CONFIG o config/config.yaml) y resuelve rutas."""
    ruta = Path(ruta or os.environ.get(VARIABLE_ENTORNO_CONFIG) or RUTA_CONFIG_POR_DEFECTO).resolve()
    if not ruta.exists():
        raise ErrorConfiguracion(f"No existe el archivo de configuración {ruta}")
    crudo = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    base = ruta.parent.parent
    rutas = Rutas(**{k: _resolver(base, v) for k, v in crudo["rutas"].items()})
    p = crudo["particion"]
    cfg = Config(
        proyecto=crudo["proyecto"],
        rutas=rutas,
        datos=crudo["datos"],
        microzona=crudo["microzona"],
        particion=Particion(train=tuple(p["train"]), valid=tuple(p["valid"]), test=tuple(p["test"])),
        objetivo=crudo["objetivo"],
        features=crudo["features"],
        modelado=crudo["modelado"],
        prediccion=crudo["prediccion"],
        priorizacion=crudo["priorizacion"],
        recursos=crudo["recursos"],
        app=crudo["app"],
        calibracion=crudo.get("calibracion", {"activa": False}),
        ruta_archivo=ruta,
        crudo=crudo,
    )
    _validar(cfg)
    return cfg


def con_base_datos(cfg: Config, ruta_bd: Path) -> Config:
    """Copia de la configuración apuntando a otra base de datos y carpetas (útil en tests)."""
    from dataclasses import replace

    base = ruta_bd.parent
    rutas = replace(cfg.rutas, base_datos=ruta_bd, modelos=base / "modelos", reportes=base / "reportes")
    return replace(cfg, rutas=rutas)
