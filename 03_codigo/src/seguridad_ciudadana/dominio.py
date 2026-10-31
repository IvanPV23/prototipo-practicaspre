"""Constantes y reglas puras del dominio (sin E/S)."""

from __future__ import annotations

TURNOS: tuple[str, ...] = ("Mañana", "Tarde", "Noche")
NIVELES: tuple[str, ...] = ("Bajo", "Medio", "Alto")
CODIGO_TURNO: dict[str, int] = {t: i for i, t in enumerate(TURNOS)}
CODIGO_NIVEL: dict[str, int] = {n: i for i, n in enumerate(NIVELES)}
PARTICIONES: tuple[str, ...] = ("train", "valid", "test")
PARTICION_OPERATIVA = "operativa"
MODELOS: tuple[str, ...] = ("persistencia", "regresion_logistica", "random_forest", "gradient_boosting")
NOMBRE_LEGIBLE_MODELO: dict[str, str] = {
    "persistencia": "Línea base (persistencia)",
    "regresion_logistica": "Regresión logística",
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting",
}


def nivel_desde_conteo(conteo: float | None, b: float) -> str | None:
    """Bajo = 0; Medio = 1..b; Alto > b (umbral b fijado con entrenamiento)."""
    if conteo is None or conteo != conteo:  # NaN
        return None
    if conteo == 0:
        return "Bajo"
    return "Medio" if conteo <= b else "Alto"


def siguiente_turno(turno: str) -> str:
    return TURNOS[(CODIGO_TURNO[turno] + 1) % len(TURNOS)]
