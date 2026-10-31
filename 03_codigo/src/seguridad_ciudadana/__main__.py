"""CLI: python -m seguridad_ciudadana <comando> [--config RUTA]."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .config import ErrorConfiguracion, cargar_config
from .logging_conf import configurar_logging
from .servicios.pipeline import PASOS, ejecutar

LOG = logging.getLogger("seguridad_ciudadana")
AYUDA = {
    "init-db": "crea o actualiza el esquema de la base SQLite",
    "ingestar": "carga el CSV canónico (verifica su sha256 contra el handoff de la Fase 1)",
    "construir": "microzonas, observaciones con ceros, objetivo y variables",
    "entrenar": "línea base, regresión logística, Random Forest y Gradient Boosting; evalúa y registra",
    "predecir": "predicciones del modelo vigente (fechas de prueba y fecha operativa)",
    "priorizar": "calcula R, G, F y P con los pesos por defecto",
    "todo": "ejecuta todos los pasos en orden (idempotente) y escribe reportes/resultado_fase3.json",
}


def main(argv: list[str] | None = None) -> int:
    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("--config", default=None, help="ruta a config.yaml (por defecto config/config.yaml)")
    comun.add_argument("-v", "--verbose", action="store_true", help="más detalle en el log")
    parser = argparse.ArgumentParser(prog="python -m seguridad_ciudadana", description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True, metavar="comando")
    for comando in [*PASOS, "todo"]:
        sub.add_parser(comando, help=AYUDA[comando], parents=[comun])
    args = parser.parse_args(argv)
    configurar_logging(logging.DEBUG if args.verbose else logging.INFO)
    try:
        cfg = cargar_config(args.config)
        resumen = ejecutar(cfg, args.comando)
    except (ErrorConfiguracion, RuntimeError, FileNotFoundError, ValueError) as error:
        LOG.error("%s", error)
        return 1
    LOG.info("Resumen: %s", json.dumps(resumen, ensure_ascii=False, default=str)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
