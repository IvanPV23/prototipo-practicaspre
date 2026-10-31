"""Orquestación del pipeline por lotes: init-db → ingestar → construir → entrenar → predecir → priorizar.

Cada paso lee de SQLite lo que dejó el anterior, escribe en una transacción y deja constancia en
`ejecucion_pipeline`. Todos los pasos son idempotentes: repetirlos con el mismo dato y config da el mismo estado.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import Config
from ..db import BaseDatos, inicializar_esquema
from ..db.conexion import tablas
from ..db.repositorios import ejecuciones, fuentes, incidencias, microzonas, modelos, observaciones, predicciones
from ..dominio import MODELOS, NIVELES, NOMBRE_LEGIBLE_MODELO, PARTICION_OPERATIVA
from ..espacial.geometria import limite_metrico
from ..espacial.grilla import celdas_que_intersecan, construir_microzonas
from ..features.tabla import (
    anadir_objetivo,
    codificar,
    codigo_a_nivel,
    columna_de,
    construir_tabla,
    matriz_modelo,
    niveles_a_codigo,
    umbral_b,
)
from ..ingesta.canonico import leer_canonico, leer_gravedad, preparar_incidencias, verificar_canonico
from ..modelos import evaluacion, figuras
from ..modelos.calibracion import (
    ModeloCalibrado,
    ajustar_calibrador,
    predecir_dejando_un_dia_fuera,
    rejilla_desde_config,
)
from ..modelos.entrenamiento import MODELOS_ML, buscar
from ..modelos.linea_base import predecir_persistencia
from ..modelos.registro import cargar_artefacto, guardar_artefacto, version_modelo
from ..priorizacion.calculo import componente_f, componente_g, componente_r, rankear

LOG = logging.getLogger(__name__)


class ErrorPipeline(RuntimeError):
    """Paso del pipeline sin sus prerrequisitos; el mensaje indica el comando a ejecutar."""


def _ahora() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _bd(cfg: Config) -> BaseDatos:
    return BaseDatos(cfg.rutas.base_datos)


def _escribir_json(ruta: Path, datos: Any) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    return ruta


def _handoff_fase2(cfg: Config) -> dict:
    return json.loads(cfg.rutas.handoff_fase2.read_text(encoding="utf-8"))


def _registrar(cfg: Config, comando: str, paso: Callable[[Config], dict]) -> dict:
    """Ejecuta un paso dejando constancia en ejecucion_pipeline (también si falla)."""
    bd = _bd(cfg)
    inicializar_esquema(bd)
    with bd.transaccion() as con:
        eid = ejecuciones.iniciar(con, comando, _ahora())
    t0 = time.perf_counter()
    try:
        resumen = paso(cfg)
    except Exception as error:
        with bd.transaccion() as con:
            ejecuciones.finalizar(con, eid, _ahora(), "error", f"{type(error).__name__}: {error}")
        raise
    resumen["segundos"] = round(time.perf_counter() - t0, 1)
    with bd.transaccion() as con:
        ejecuciones.finalizar(con, eid, _ahora(), "ok", json.dumps(resumen, ensure_ascii=False, default=str))
    LOG.info("Paso '%s' terminado en %.1f s", comando, resumen["segundos"])
    return resumen


# ------------------------------------------------------------------------------------------------ pasos
def paso_init_db(cfg: Config) -> dict:
    version = inicializar_esquema(_bd(cfg))
    return {"version_esquema": version, "tablas": tablas(_bd(cfg))}


def paso_ingestar(cfg: Config) -> dict:
    sha, handoff1 = verificar_canonico(cfg)
    crudo = leer_canonico(cfg.rutas.canonico)
    esperado = int(handoff1["dataset_principal"]["registros"])
    if len(crudo) != esperado:
        raise ErrorPipeline(f"El canónico tiene {len(crudo)} filas y el handoff declara {esperado}.")
    gravedad = leer_gravedad(cfg.rutas.gravedad)
    df = preparar_incidencias(crudo, gravedad, cfg)
    fuente = next(f for f in handoff1["fuentes"] if f["id"] == cfg.datos["fuente_id"])
    with _bd(cfg).transaccion() as con:
        fuentes.guardar_fuente(
            con,
            {
                "id": fuente["id"], "nombre": fuente["nombre"], "institucion": fuente.get("institucion"),
                "url": fuente.get("url"), "licencia": fuente.get("licencia"), "sha256": sha,
                "fecha_descarga": fuente.get("fecha_descarga"), "registros": len(df),
            },
        )  # fmt: skip
        ids_tipo = fuentes.guardar_tipos(con, gravedad)
        df = df.rename(columns={"id_incidencia": "id"})
        df["fuente_id"] = cfg.datos["fuente_id"]
        df["tipo_id"] = [ids_tipo[(t, s)] for t, s in zip(df.tipo, df.subtipo)]
        df["microzona_id"] = None
        incidencias.reemplazar_incidencias(con, df)
        conteo = incidencias.contar(con)
    limpias_esperadas = int(_handoff_fase2(cfg)["dataset_limpio"]["registros"])
    if conteo["limpias"] != limpias_esperadas:
        LOG.warning("Incidencias limpias %s ≠ %s del handoff de la Fase 2", conteo["limpias"], limpias_esperadas)
    LOG.info("Ingesta: %s registros, %s limpios (%s excluidos a > %s m del límite)", conteo["total"],
             conteo["limpias"], conteo["total"] - conteo["limpias"], cfg.datos["tolerancia_borde_m"])  # fmt: skip
    return {"registros": conteo["total"], "limpias": conteo["limpias"], "sha256": sha,
            "limpias_handoff": limpias_esperadas}  # fmt: skip


def _sector_referencial(limpias: pd.DataFrame) -> dict[tuple[int, int], str]:
    """Sector más frecuente de la celda (solo referencia: el 21 % de registros no tiene sector)."""
    con_sector = limpias.dropna(subset=["sector"])
    modas = con_sector.groupby(["mz_col", "mz_fila"]).sector.agg(lambda s: s.value_counts().sort_index().idxmax())
    return modas.to_dict()


def paso_construir(cfg: Config) -> dict:
    bd = _bd(cfg)
    with bd.lectura() as con:
        limpias = incidencias.leer_incidencias(con, solo_limpias=True)
    if limpias.empty:
        raise ErrorPipeline("No hay incidencias cargadas. Ejecute: python -m seguridad_ciudadana ingestar")
    mz_cfg = cfg.microzona
    poligono = limite_metrico(cfg.rutas.limite, mz_cfg["crs_metrico"])
    celdas = celdas_que_intersecan(float(mz_cfg["tamano_m"]), tuple(mz_cfg["origen"]), poligono)
    ini, fin = cfg.particion.train
    en_train = limpias[(limpias.fecha >= ini) & (limpias.fecha <= fin)]
    mz = construir_microzonas(
        celdas, set(zip(en_train.mz_col, en_train.mz_fila)), mz_cfg["crs_metrico"],
        mz_cfg["prefijo_activa"], mz_cfg["prefijo_inactiva"],
    )  # fmt: skip
    historia = limpias[limpias.fecha <= cfg.ultimo_dia_completo]  # 9–10 jun censurados: fuera de la historia
    sectores = _sector_referencial(historia)
    mz["sector_ref"] = [sectores.get((c, f)) for c, f in zip(mz.col, mz.fila)]
    activas = mz[mz.activa == 1][["id", "col", "fila"]]

    fechas = cfg.particion.fechas_objetivo() + [cfg.fecha_operativa]
    tabla = construir_tabla(
        historia, activas, fechas, cfg.datos["fecha_inicio_historia"], cfg.datos["feriados"],
        int(cfg.features["tope_dias_desde_ultima"]),
    )  # fmt: skip
    tabla["particion"] = [cfg.particion.de_fecha(f) or PARTICION_OPERATIVA for f in tabla.fecha]
    b = umbral_b(tabla.loc[tabla.particion == "train", "conteo"])
    tabla = anadir_objetivo(tabla, b, [cfg.fecha_operativa])
    tabla = codificar(tabla)
    columnas = {f: columna_de(f) for f in cfg.features["lista"]}

    id_por_celda = {(c, f): i for i, c, f in zip(mz.id, mz.col, mz.fila)}
    with bd.transaccion() as con:
        microzonas.guardar_microzonas(con, mz)
        todas = incidencias.leer_incidencias(con, solo_limpias=False)
        incidencias.asignar_microzonas(
            con, [(id_por_celda.get((c, f)), i) for i, c, f in zip(todas.id, todas.mz_col, todas.mz_fila)]
        )
        observaciones.reemplazar_observaciones(con, tabla, columnas)
        conteo_inc = incidencias.contar(con)

    objetivo = tabla[tabla.particion != PARTICION_OPERATIVA]
    distribucion = {
        p: {n: int((g.nivel == n).sum()) for n in NIVELES} for p, g in objetivo.groupby("particion", sort=False)
    }
    persist_valid = evaluacion.macro_f1(
        niveles_a_codigo(objetivo.loc[objetivo.particion == "valid", "nivel"]),
        objetivo.loc[objetivo.particion == "valid", "nivel_lag1_turno"].astype(int).to_numpy(),
    )
    h2 = _handoff_fase2(cfg)
    celdas_activas = set(zip(activas.col, activas.fila))
    estables = historia[historia.periodo == "estable"]
    verificacion = {
        "incidencias_limpias": {"obtenido": conteo_inc["limpias"], "handoff": h2["dataset_limpio"]["registros"]},
        "microzonas_activas": {"obtenido": int(mz.activa.sum()), "handoff": h2["microzona"]["n_microzonas_activas"]},
        "celdas_distrito": {"obtenido": len(mz)},
        "filas_tabla": {"obtenido": len(objetivo), "handoff": h2["tabla_modelado"]["filas"]},
        "filas_operativas": {"obtenido": int((tabla.particion == PARTICION_OPERATIVA).sum())},
        "umbral_b": {"obtenido": b, "handoff": float(cfg.objetivo["umbral_b_esperado"])},
        "distribucion_por_particion": {"obtenido": distribucion, "handoff": h2["objetivo"]["distribucion_por_particion"]},
        "macro_f1_persistencia_valid": {"obtenido": round(persist_valid, 3), "handoff": h2["linea_base"]["macro_f1_valid"]},
        "pct_ceros": round(100 * float((objetivo.conteo == 0).mean()), 1),
        "incidencias_estables_fuera_de_activas": int(
            sum((c, f) not in celdas_activas for c, f in zip(estables.mz_col, estables.mz_fila))
        ),
    }  # fmt: skip
    for clave, valor in verificacion.items():
        if isinstance(valor, dict) and "handoff" in valor and valor["obtenido"] != valor["handoff"]:
            LOG.warning("Verificación '%s': obtenido %s ≠ handoff %s", clave, valor["obtenido"], valor["handoff"])
    verificacion["coincide_con_handoff"] = all(
        v["obtenido"] == v["handoff"] for v in verificacion.values() if isinstance(v, dict) and "handoff" in v
    )
    _escribir_json(cfg.rutas.reportes / "verificacion_construccion.json", verificacion)
    LOG.info("Construcción: %s microzonas activas, %s filas objetivo, b = %s, coincide con handoff: %s",
             int(mz.activa.sum()), len(objetivo), b, verificacion["coincide_con_handoff"])  # fmt: skip
    return {"microzonas_activas": int(mz.activa.sum()), "filas": len(objetivo), "b": b,
            "coincide_con_handoff": verificacion["coincide_con_handoff"]}  # fmt: skip


def _particiones(cfg: Config) -> dict[str, pd.DataFrame]:
    with _bd(cfg).lectura() as con:
        tabla = observaciones.leer_tabla_modelado(con)
    if tabla.empty:
        raise ErrorPipeline("No hay tabla de modelado. Ejecute: python -m seguridad_ciudadana construir")
    return {p: g.reset_index(drop=True) for p, g in tabla.groupby("particion")}


def _evaluar(cfg: Config, datos: pd.DataFrame, y: np.ndarray, yhat: np.ndarray) -> dict[str, Any]:
    m = evaluacion.metricas(y, yhat)
    m.update(evaluacion.por_grupo(datos.fecha, datos.turno, y, yhat))
    m["proporcion_predicha"] = {n: round(float(np.mean(yhat == i)), 4) for i, n in enumerate(NIVELES)}
    m["proporcion_observada"] = {n: round(float(np.mean(y == i)), 4) for i, n in enumerate(NIVELES)}
    m["bootstrap"] = evaluacion.bootstrap(
        datos.fecha, y, yhat, int(cfg.modelado["repeticiones_bootstrap"]), cfg.semilla,
        float(cfg.modelado["nivel_confianza"]),
    )  # fmt: skip
    return m


def _hipotesis(f1_test: dict[str, float], importancia: dict[str, Any], seleccionado: str) -> dict[str, Any]:
    ensambles = {k: f1_test[k] for k in ("random_forest", "gradient_boosting")}
    mejor = max(ensambles, key=ensambles.get)
    supera = ensambles[mejor] > f1_test["regresion_logistica"] and ensambles[mejor] > f1_test["persistencia"]
    h1 = {
        "resultado": "se_sostiene" if supera else "no_se_sostiene",
        "evidencia": (
            f"Macro F1 en prueba (evaluación única, modelos ajustados con train y elegidos con valid): "
            f"persistencia {f1_test['persistencia']:.3f}, regresión logística {f1_test['regresion_logistica']:.3f}, "
            f"Random Forest {f1_test['random_forest']:.3f}, Gradient Boosting {f1_test['gradient_boosting']:.3f}. "
            f"El mejor ensamble ({NOMBRE_LEGIBLE_MODELO[mejor]}) "
            + ("supera" if supera else "no supera")
            + " a la regresión logística y a la persistencia. Exploratorio: 4 días de prueba (1 032 filas)."
        ),
    }
    grupos = importancia[seleccionado]["por_grupo"]
    hist, cal = grupos["historial"]["media"], grupos["calendario"]["media"]
    otros = {g: v["media"] for g, v in grupos.items()}
    if hist > cal and hist > 2 * max(grupos["historial"]["desv"], grupos["calendario"]["desv"], 1e-9):
        resultado_he1 = "se_sostiene"
    elif cal >= hist:
        resultado_he1 = "no_se_sostiene"
    else:
        resultado_he1 = "no_concluyente"
    coincidencias = [
        m
        for m, imp in importancia.items()
        if imp["por_grupo"]["historial"]["media"] > imp["por_grupo"]["calendario"]["media"]
    ]
    he1 = {
        "resultado": resultado_he1,
        "evidencia": (
            f"Importancia por permutación sobre validación del modelo seleccionado ({NOMBRE_LEGIBLE_MODELO[seleccionado]}), "
            f"permutando cada grupo completo: caída media del Macro F1 historial {hist:.3f} vs calendario {cal:.3f} "
            f"(espacial {otros.get('espacial', 0):.3f}, contexto {otros.get('contexto', 0):.3f}). "
            f"El historial supera al calendario en {len(coincidencias)} de {len(importancia)} modelos ML."
        ),
    }
    return {"H1": h1, "HE1": he1}


def paso_entrenar(cfg: Config) -> dict:
    partes = _particiones(cfg)
    features = cfg.features_modelo
    categoricas = list(cfg.features["categoricas"])
    imput = cfg.features.get("imputacion_lag7_con")
    X = {p: matriz_modelo(partes[p], features, imput) for p in ("train", "valid", "test")}
    y = {p: niveles_a_codigo(partes[p].nivel) for p in ("train", "valid", "test")}
    with _bd(cfg).lectura() as con:
        sha_datos = fuentes.obtener_fuente(con, cfg.datos["fuente_id"])["sha256"]

    # 1) Ajuste con train y selección con valid (test no se toca)
    ajustados: dict[str, Any] = {}
    busquedas: dict[str, Any] = {}
    for nombre in MODELOS_ML:
        LOG.info("Búsqueda de hiperparámetros: %s", nombre)
        res = buscar(nombre, cfg.modelado["grillas"][nombre], X["train"], y["train"], X["valid"], y["valid"],
                     categoricas, cfg.semilla)  # fmt: skip
        ajustados[nombre] = res
        busquedas[nombre] = {"mejores_parametros": res.mejores_parametros, "candidatos": res.candidatos,
                             "mejor_macro_f1_valid": round(res.mejor_macro_f1_valid, 4)}  # fmt: skip
    pred_valid = {"persistencia": predecir_persistencia(partes["valid"])}
    pred_valid |= {n: r.estimador.predict(X["valid"]) for n, r in ajustados.items()}

    # 1b) Calibración posterior con validación (ADR 0007). Las métricas de validación de los modelos calibrados
    # salen de la predicción dejando un día fuera, para que elegir con validación no premie el ajuste en ella.
    sin_calibrar: dict[str, Any] = {}
    if cfg.calibracion.get("activa", False):
        rejilla = rejilla_desde_config(cfg.calibracion)
        for n, r in ajustados.items():
            if list(r.estimador.classes_) != list(range(len(NIVELES))):
                raise ErrorPipeline(f"{n}: el entrenamiento no vio las tres clases; no se puede calibrar.")
            P = r.estimador.predict_proba(X["valid"])
            cal = ajustar_calibrador(P, y["valid"], rejilla)
            sin_calibrar[n] = {"base": r.estimador,
                               "valid": _evaluar(cfg, partes["valid"], y["valid"], pred_valid[n])}  # fmt: skip
            pred_valid[n] = predecir_dejando_un_dia_fuera(P, y["valid"], partes["valid"].fecha, rejilla)
            r.estimador = ModeloCalibrado(r.estimador, cal)
            busquedas[n]["calibracion"] = cal.como_dict()
            LOG.info("Calibración %s: T=%.3f sesgo=%s desplazamiento=%s", n, cal.temperatura,
                     np.round(cal.sesgo, 3).tolist(), cal.desplazamiento)  # fmt: skip
    metricas = {n: {"valid": _evaluar(cfg, partes["valid"], y["valid"], p)} for n, p in pred_valid.items()}
    seleccionado = max(MODELOS_ML, key=lambda n: metricas[n]["valid"]["macro_f1"])
    LOG.info("Modelo seleccionado por Macro F1 en validación: %s (%.4f)", seleccionado,
             metricas[seleccionado]["valid"]["macro_f1"])  # fmt: skip

    # 2) Importancia por permutación (validación) para H E1
    grupos = {g: [v for v in vs if v in features] for g, vs in cfg.features["grupos"].items()}
    importancia = {
        n: evaluacion.importancia_por_permutacion(
            r.estimador, X["valid"], y["valid"], grupos, int(cfg.modelado["repeticiones_permutacion"]), cfg.semilla
        )
        for n, r in ajustados.items()
    }

    # 3) Evaluación única en prueba, después de cerrar la selección
    pred_test = {"persistencia": predecir_persistencia(partes["test"])}
    pred_test |= {n: r.estimador.predict(X["test"]) for n, r in ajustados.items()}
    for n, p in pred_test.items():
        metricas[n]["test"] = _evaluar(cfg, partes["test"], y["test"], p)
    for n, s in sin_calibrar.items():
        metricas[n]["sin_calibrar"] = {
            "valid": s["valid"], "test": _evaluar(cfg, partes["test"], y["test"], s["base"].predict(X["test"])),
        }  # fmt: skip

    # 4) Registro (BD + joblib) y reportes
    ejecutado = _ahora()
    registros = {}
    with _bd(cfg).transaccion() as con:
        for n in MODELOS:
            params = busquedas.get(n, {}).get("mejores_parametros", {"regla": "nivel_lag1_turno"})
            if "calibracion" in busquedas.get(n, {}):
                params = params | {"calibracion": busquedas[n]["calibracion"]}
            version = version_modelo(n, params, sha_datos, cfg.hash())
            ruta = None
            if n in ajustados:
                ruta = guardar_artefacto(
                    cfg.rutas.modelos, n, version,
                    {"estimador": ajustados[n].estimador, "features": features, "clases": list(NIVELES),
                     "imputacion_lag7_con": imput, "version": version, "nombre": n},
                )  # fmt: skip
            metricas_modelo = dict(metricas[n])
            if n in importancia:
                metricas_modelo["importancia"] = importancia[n]
            registros[n] = modelos.registrar_modelo(
                con,
                {
                    "nombre": n, "version": version, "hiperparametros": params, "sha256_datos": sha_datos,
                    "config_hash": cfg.hash(), "config": cfg.crudo, "metricas": metricas_modelo,
                    "macro_f1_valid": metricas[n]["valid"]["macro_f1"], "macro_f1_test": metricas[n]["test"]["macro_f1"],
                    "ruta_artefacto": None if ruta is None else _relativa(cfg, ruta), "creado": ejecutado,
                    "ejecucion_id": None,
                },
            )  # fmt: skip
        modelos.marcar_vigente(con, registros[seleccionado])

    f1_test = {n: metricas[n]["test"]["macro_f1"] for n in MODELOS}
    hipotesis = _hipotesis(f1_test, importancia, seleccionado)
    rep = cfg.rutas.reportes
    _escribir_json(rep / "busqueda_hiperparametros.json", busquedas)
    _escribir_json(rep / "importancia_permutacion.json", importancia)
    _escribir_json(rep / "metricas_modelos.json", {
        "seleccionado": seleccionado, "criterio": "Mejor Macro F1 en validación (entre los modelos de ML)",
        "features_modelo": features, "modelos": metricas, "hipotesis": hipotesis,
    })  # fmt: skip
    _escribir_json(rep / "metricas_por_dia_turno.json", {
        n: {p: {"por_dia": metricas[n][p]["por_dia"], "por_turno": metricas[n][p]["por_turno"],
                "bootstrap": metricas[n][p]["bootstrap"]} for p in ("valid", "test")}
        for n in MODELOS
    })  # fmt: skip
    _figuras(cfg, metricas, importancia, seleccionado)
    return {"seleccionado": seleccionado, "macro_f1_valid": {n: metricas[n]["valid"]["macro_f1"] for n in MODELOS},
            "macro_f1_test": f1_test, "hipotesis": {k: v["resultado"] for k, v in hipotesis.items()}}  # fmt: skip


def _relativa(cfg: Config, ruta: Path) -> str:
    base = cfg.ruta_archivo.parent.parent
    try:
        return Path(ruta).resolve().relative_to(base).as_posix()
    except ValueError:
        return Path(ruta).resolve().as_posix()


def _absoluta(cfg: Config, ruta: str) -> Path:
    p = Path(ruta)
    return p if p.is_absolute() else cfg.ruta_archivo.parent.parent / p


def _figuras(cfg: Config, metricas: dict, importancia: dict, seleccionado: str) -> None:
    carpeta = cfg.rutas.reportes / "figuras"
    carpeta.mkdir(parents=True, exist_ok=True)
    fuente = cfg.proyecto["fuente_cita"]
    figuras.matrices_confusion(
        {n: metricas[n]["valid"] for n in MODELOS}, "Matrices de confusión en validación (1–4 jun)",
        carpeta / "matrices_confusion_valid.png", fuente,
    )  # fmt: skip
    figuras.matrices_confusion(
        {n: metricas[n]["test"] for n in MODELOS}, "Matrices de confusión en prueba (5–8 jun, evaluación única)",
        carpeta / "matrices_confusion_test.png", fuente,
    )  # fmt: skip
    for p, rotulo in (("valid", "validación"), ("test", "prueba")):
        figuras.f1_por_dia(
            {n: metricas[n][p]["bootstrap"] for n in MODELOS},
            f"Macro F1 por día en {rotulo}, con intervalo bootstrap del 95 %", carpeta / f"f1_por_dia_{p}.png", fuente,
        )  # fmt: skip
    figuras.importancia(
        importancia[seleccionado],
        f"Importancia por permutación en validación — {NOMBRE_LEGIBLE_MODELO[seleccionado]}",
        carpeta / "importancia_permutacion.png", fuente,
    )  # fmt: skip


def paso_predecir(cfg: Config) -> dict:
    """Predicciones del modelo vigente para las fechas de prueba (demostración) y la fecha operativa."""
    with _bd(cfg).lectura() as con:
        vigente = modelos.modelo_vigente(con)
        tabla = observaciones.leer_tabla_modelado(con, ["test", PARTICION_OPERATIVA])
    if vigente is None:
        raise ErrorPipeline("No hay modelo vigente. Ejecute: python -m seguridad_ciudadana entrenar")
    artefacto = cargar_artefacto(_absoluta(cfg, vigente["ruta_artefacto"]))
    X = matriz_modelo(tabla, artefacto["features"], artefacto["imputacion_lag7_con"])
    proba = artefacto["estimador"].predict_proba(X)
    clases = list(artefacto["estimador"].classes_)
    p = np.zeros((len(X), len(NIVELES)))
    for j, c in enumerate(clases):
        p[:, int(c)] = proba[:, j]
    pred = pd.DataFrame({
        "microzona_id": tabla.microzona_id, "fecha": tabla.fecha, "turno": tabla.turno,
        # El nivel sale de predict: con calibración incluye los desplazamientos de decisión (no es el argmax de p).
        "nivel": codigo_a_nivel(artefacto["estimador"].predict(X).astype(int)), "p_bajo": p[:, 0].round(6), "p_medio": p[:, 1].round(6),
        "p_alto": p[:, 2].round(6),
        "tipo_fecha": np.where(tabla.particion == PARTICION_OPERATIVA, "operativa", "demostracion"),
    })  # fmt: skip
    with _bd(cfg).transaccion() as con:
        n = predicciones.reemplazar_predicciones(con, vigente["id"], pred)
    LOG.info("Predicciones: %s filas con %s v%s (%s fechas)", n, vigente["nombre"], vigente["version"],
             pred.fecha.nunique())  # fmt: skip
    return {"filas": n, "modelo": vigente["nombre"], "fechas": sorted(pred.fecha.unique().tolist())}


def paso_priorizar(cfg: Config) -> dict:
    with _bd(cfg).lectura() as con:
        pred = predicciones.leer_predicciones(con)
        tabla = observaciones.leer_tabla_modelado(con)
    if pred.empty:
        raise ErrorPipeline("No hay predicciones. Ejecute: python -m seguridad_ciudadana predecir")
    pc = cfg.priorizacion
    maximo_f = float(tabla.loc[tabla.particion == "train", "suma7_celda"].max())
    base = pred.merge(
        tabla[["microzona_id", "fecha", "turno", "gravedad_media7_celda", "suma7_celda"]],
        on=["microzona_id", "fecha", "turno"], how="left", validate="1:1",
    )  # fmt: skip
    base["r"] = componente_r(base.p_bajo, base.p_medio, base.p_alto, pc["valor_nivel"])
    base["g"] = componente_g(base.gravedad_media7_celda, float(pc["gravedad_min"]), float(pc["gravedad_max"]))
    base["f"] = componente_f(base.suma7_celda, maximo_f)
    base = base.rename(columns={"id": "prediccion_id"})
    filas = [rankear(g, pc["pesos"]) for _, g in base.groupby(["fecha", "turno"], sort=True)]
    prio = pd.concat(filas, ignore_index=True)
    with _bd(cfg).transaccion() as con:
        n = predicciones.reemplazar_prioridades(con, prio)
    LOG.info("Priorización: %s filas, pesos %s, F normalizada con máximo de train = %s", n, pc["pesos"], maximo_f)
    return {"filas": n, "pesos": pc["pesos"], "maximo_f_train": maximo_f}


PASOS: dict[str, Callable[[Config], dict]] = {
    "init-db": paso_init_db,
    "ingestar": paso_ingestar,
    "construir": paso_construir,
    "entrenar": paso_entrenar,
    "predecir": paso_predecir,
    "priorizar": paso_priorizar,
}


def ejecutar(cfg: Config, comando: str) -> dict:
    if comando == "todo":
        return todo(cfg)
    if comando not in PASOS:
        raise ErrorPipeline(f"Comando desconocido '{comando}'. Opciones: {', '.join([*PASOS, 'todo'])}")
    return _registrar(cfg, comando, PASOS[comando])


def todo(cfg: Config) -> dict:
    """Pipeline completo en orden; al final escribe reportes/resultado_fase3.json."""
    resumen = {nombre: _registrar(cfg, nombre, paso) for nombre, paso in PASOS.items()}
    from .resultado import escribir_resultado

    escribir_resultado(cfg)
    return resumen
