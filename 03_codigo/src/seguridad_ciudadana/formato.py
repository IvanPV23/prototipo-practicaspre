"""Formato numérico del design system: coma decimal y espacio fino de miles (§4.4)."""

from __future__ import annotations

import math

ESPACIO_MILES = "\u202f"


def fmt(valor: float | int | None, decimales: int = 0) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ESPACIO_MILES)


def pct(valor: float | None, decimales: int = 1) -> str:
    return "—" if valor is None else f"{fmt(valor, decimales)} %"


def fecha_larga(fecha_iso: str) -> str:
    """'2026-06-09' -> 'mar 9 jun 2026' (sin depender del locale del sistema)."""
    from datetime import date

    dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    d = date.fromisoformat(fecha_iso)
    return f"{dias[d.weekday()]} {d.day} {meses[d.month - 1]} {d.year}"
