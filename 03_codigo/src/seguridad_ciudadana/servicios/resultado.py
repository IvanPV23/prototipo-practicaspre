"""Escritura de `reportes/resultado_fase3.json` (contrato §4 de contratos_handoff.md) con números reales."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import Config
from ..db import BaseDatos
from ..db.conexion import tablas
from ..db.repositorios import modelos
from ..dominio import MODELOS
from ..formato import pct

ARCHIVO_TESTS = "tests_resumen.json"
ARCHIVO_RESULTADO = "resultado_fase3.json"
COMANDOS = {
    "instalar": (
        "python -m venv .venv && .venv\\Scripts\\python -m pip install -r requirements.txt -r requirements-dev.txt"
        " && .venv\\Scripts\\python -m pip install -e . --no-deps"
    ),
    "pipeline": "python -m seguridad_ciudadana todo",
    "app": "streamlit run app/Inicio.py",
    "tests": "pytest",
}


def _ruta_raiz_relativa(cfg: Config, ruta: Path) -> str:
    """Ruta relativa a RAIZ (carpeta que contiene 03_codigo) con '/'."""
    raiz = cfg.ruta_archivo.parent.parent.parent
    try:
        return Path(ruta).resolve().relative_to(raiz.resolve()).as_posix()
    except ValueError:
        return Path(ruta).resolve().as_posix()


def leer_resumen_tests(cfg: Config) -> dict[str, int]:
    ruta = cfg.rutas.reportes / ARCHIVO_TESTS
    if not ruta.exists():
        return {"total": 0, "pasados": 0, "fallidos": 0}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return {k: int(datos.get(k, 0)) for k in ("total", "pasados", "fallidos")}


def advertencias(cfg: Config, metricas: dict[str, Any], verificacion: dict[str, Any]) -> list[str]:
    sel = metricas["seleccionado"]
    m = metricas["modelos"]
    lista = [
        "Periodo muy corto (18 días utilizables: 10 train / 4 valid / 4 test): métricas exploratorias y de alta "
        "varianza; ver Macro F1 por día y por turno e intervalos bootstrap en reportes/metricas_por_dia_turno.json.",
        f"IC 95 % (bootstrap por bloques de día) del Macro F1 en prueba del modelo seleccionado: "
        f"[{m[sel]['test']['bootstrap']['global_por_bloques_de_dia']['ic_inf']:.3f}, "
        f"{m[sel]['test']['bootstrap']['global_por_bloques_de_dia']['ic_sup']:.3f}].",
        "Desplazamiento de distribución: la proporción de Alto sube de 9,4 % (train) a 10,1 % (valid) y 13,8 % (test); "
        "validación no tiene fin de semana y prueba incluye sábado, domingo y el feriado del 7 jun.",
        "9 y 10 jun están censurados en la fuente: la fecha operativa (9 jun) se predice con historia hasta el 8 jun "
        "y no puede evaluarse; las fechas de prueba se muestran en la app como demostración.",
        "lag7_turno nulo solo el 22 may (258 filas): imputado fila a fila con media7_turno (sin fuga).",
        "feriado es constante en train y valid: se conserva en la tabla y en la BD pero no entra al estimador.",
        "El objetivo mide incidencias registradas por el CCO (≈3/4 por cámaras), no delitos; no usar para etiquetar zonas.",
        "Los recursos del módulo de segundo nivel son ilustrativos (ingresados a mano), no datos de la municipalidad.",
        "El modelo vigente se ajustó solo con train y se calibró solo con valid (no se reentrenó con train+valid) "
        "para que la cifra de prueba corresponda exactamente al artefacto publicado.",
    ]
    if cfg.calibracion.get("activa", False) and "sin_calibrar" in m[sel]:
        crudo = m[sel]["sin_calibrar"]
        lista.append(
            f"Calibración posterior con validación (ADR 0007): la proporción de Alto predicha en prueba pasa de "
            f"{pct(100 * crudo['test']['proporcion_predicha']['Alto'])} sin calibrar a "
            f"{pct(100 * m[sel]['test']['proporcion_predicha']['Alto'])} "
            f"(observada {pct(100 * m[sel]['test']['proporcion_observada']['Alto'])}). "
            "La calibración se decidió solo con validación, pero la prueba ya se había leído una vez con v1.0.0: "
            "esta es su segunda lectura y debe interpretarse con esa cautela."
        )
    if cfg.calibracion.get("activa", False):
        lista.append(
            "El Macro F1 de validación de los modelos calibrados se calcula dejando un día fuera (cada día con un "
            "calibrador ajustado en los otros tres), para no premiar el ajuste en la misma validación que elige el modelo."
        )
    persist_valid = m["persistencia"]["valid"]["macro_f1"]
    if m[sel]["valid"]["macro_f1"] <= persist_valid:
        lista.append(
            f"Ningún modelo de ML supera a la persistencia en validación ({persist_valid:.3f}); se usa el mejor de ML "
            "porque la priorización necesita probabilidades."
        )
    persist_test = m["persistencia"]["test"]["macro_f1"]
    if m[sel]["test"]["macro_f1"] <= persist_test:
        lista.append(
            f"El modelo seleccionado por validación ({sel}, Macro F1 prueba {m[sel]['test']['macro_f1']:.3f}) no supera "
            f"a la persistencia en prueba ({persist_test:.3f}); los intervalos bootstrap se solapan. No se cambió la "
            "selección para no elegir con prueba; la priorización combina R con G y F y el operador decide."
        )
    if not verificacion.get("coincide_con_handoff", False):
        lista.append(
            "La reconstrucción no coincide en todo con el handoff de la Fase 2: ver verificacion_construccion.json"
        )
    return lista


def escribir_resultado(cfg: Config) -> Path:
    bd = BaseDatos(cfg.rutas.base_datos)
    rep = cfg.rutas.reportes
    metricas = json.loads((rep / "metricas_modelos.json").read_text(encoding="utf-8"))
    verificacion = json.loads((rep / "verificacion_construccion.json").read_text(encoding="utf-8"))
    with bd.lectura() as con:
        registrados = {m["nombre"]: m for m in modelos.ultimos_por_nombre(con)}
        vigente = modelos.modelo_vigente(con)
    resultado = {
        "version": 1,
        "generado": datetime.now().astimezone().isoformat(timespec="seconds"),
        "modelos": [
            {
                "nombre": n,
                "macro_f1_valid": registrados[n]["macro_f1_valid"],
                "macro_f1_test": registrados[n]["macro_f1_test"],
                "hiperparametros": registrados[n]["hiperparametros"],
                "version": registrados[n]["version"],
            }
            for n in MODELOS
        ],
        "modelo_seleccionado": {
            "nombre": vigente["nombre"],
            "criterio": "Mejor Macro F1 en validación",
            "ruta_artefacto": f"03_codigo/{vigente['ruta_artefacto']}",
            "version": vigente["version"],
        },
        "hipotesis": metricas["hipotesis"],
        "verificacion_fase2": {
            k: v
            for k, v in verificacion.items()
            if k
            in (
                "incidencias_limpias",
                "microzonas_activas",
                "filas_tabla",
                "macro_f1_persistencia_valid",
                "coincide_con_handoff",
            )
        },  # fmt: skip
        "base_datos": {"ruta": _ruta_raiz_relativa(cfg, cfg.rutas.base_datos), "tablas": tablas(bd)},
        "tests": leer_resumen_tests(cfg),
        "comandos": COMANDOS,
        "fecha_operativa": cfg.fecha_operativa,
        "reportes": sorted(p.name for p in rep.glob("*.json") if p.name != ARCHIVO_RESULTADO),
        "advertencias": advertencias(cfg, metricas, verificacion),
    }
    ruta = rep / ARCHIVO_RESULTADO
    ruta.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def actualizar_tests(cfg: Config, total: int, pasados: int, fallidos: int) -> None:
    """Llamado desde conftest al terminar pytest: guarda el resumen y lo refleja en resultado_fase3.json."""
    rep = cfg.rutas.reportes
    rep.mkdir(parents=True, exist_ok=True)
    resumen = {"total": total, "pasados": pasados, "fallidos": fallidos,
               "fecha": datetime.now().astimezone().isoformat(timespec="seconds")}  # fmt: skip
    (rep / ARCHIVO_TESTS).write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    ruta = rep / ARCHIVO_RESULTADO
    if ruta.exists():
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos["tests"] = {"total": total, "pasados": pasados, "fallidos": fallidos}
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
