"""Reglas de asignación de recursos (segundo nivel; datos ilustrativos)."""

from __future__ import annotations


class ErrorAsignacion(ValueError):
    """La asignación no respeta la disponibilidad; el mensaje es apto para mostrar al operador."""


def validar_cantidad(cantidad: int) -> None:
    if int(cantidad) <= 0:
        raise ErrorAsignacion("La cantidad a asignar debe ser mayor que 0.")


def validar_asignacion(disponible: int, ya_asignado: int, solicitado: int, tipo: str) -> None:
    """No se puede asignar más de lo declarado para el tipo, fecha y turno."""
    validar_cantidad(solicitado)
    restante = int(disponible) - int(ya_asignado)
    if solicitado > restante:
        raise ErrorAsignacion(f"Solo quedan {max(restante, 0)} {tipo} disponibles para este turno.")


def validar_disponibilidad(nueva_cantidad: int, ya_asignado: int, tipo: str) -> None:
    if int(nueva_cantidad) < 0:
        raise ErrorAsignacion("La cantidad disponible no puede ser negativa.")
    if int(nueva_cantidad) < int(ya_asignado):
        raise ErrorAsignacion(
            f"Ya hay {ya_asignado} {tipo} asignados en este turno; quite asignaciones antes de reducir a {nueva_cantidad}."
        )
