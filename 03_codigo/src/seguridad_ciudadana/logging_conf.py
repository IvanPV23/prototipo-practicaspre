"""Configuración única de logging para CLI y app (mensajes en español, sin print)."""

from __future__ import annotations

import logging

FORMATO = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configurar_logging(nivel: int = logging.INFO) -> None:
    """Idempotente: no duplica handlers si se llama varias veces (Streamlit relanza scripts)."""
    raiz = logging.getLogger()
    if not any(getattr(h, "_seguridad", False) for h in raiz.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(FORMATO, datefmt="%H:%M:%S"))
        handler._seguridad = True  # type: ignore[attr-defined]
        raiz.addHandler(handler)
    raiz.setLevel(nivel)
    for ruidoso in ("matplotlib", "PIL", "urllib3", "fsspec"):
        logging.getLogger(ruidoso).setLevel(logging.WARNING)
