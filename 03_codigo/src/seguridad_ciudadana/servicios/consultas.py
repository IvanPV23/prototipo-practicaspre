"""Consultas de solo lectura para Inicio, Mapa, Detalle, Tablero y Metodología."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from ..config import Config
from ..db import BaseDatos
from ..db.repositorios import ejecuciones, incidencias, microzonas, modelos, predicciones
from ..dominio import MODELOS, NOMBRE_LEGIBLE_MODELO, TURNOS
from ..espacial.geometria import leer_limite
from .dto import DetalleMicrozona, EstadoSistema, Metadatos
from .priorizacion import ServicioPriorizacion, SinPredicciones, sector_legible

DOCUMENTOS = {"model_card": "model_card.md", "data_card": "data_card.md", "pipeline_ml": "pipeline_ml.md"}
NOMBRES_DIA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def calle_sin_numero(direccion: str | None) -> str:
    """Trunca la dirección a la calle (sin número ni distrito): la ficha no debe identificar domicilios."""
    if not direccion or (isinstance(direccion, float) and direccion != direccion):
        return "—"
    calle = str(direccion).split(",")[0]
    calle = re.sub(r"\b(N[°º]\s*)?\d+[A-Za-z]?\b", "", calle)
    calle = re.sub(r"\s{2,}", " ", calle).strip(" -/")
    return calle or "—"


class ServicioConsultas:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.bd = BaseDatos(cfg.rutas.base_datos)
        self.priorizacion = ServicioPriorizacion(cfg)

    # ------------------------------------------------------------------ estado y metadatos
    def estado(self) -> EstadoSistema:
        if not self.bd.existe():
            return EstadoSistema(False, "Aún no se ha creado la base de datos local.")
        try:
            with self.bd.lectura() as con:
                vigente = modelos.modelo_vigente(con)
                prio = ejecuciones.ultima_exitosa(con, "priorizar")
        except Exception as error:  # base corrupta o esquema antiguo
            return EstadoSistema(False, f"No se pudo leer la base de datos ({error}).")
        if vigente is None or prio is None:
            return EstadoSistema(False, "El pipeline no se ha ejecutado completo (falta modelo o priorización).")
        return EstadoSistema(True, "Listo")

    def metadatos(self) -> Metadatos:
        with self.bd.lectura() as con:
            vigente = modelos.modelo_vigente(con) or {}
            activas = len(microzonas.leer_microzonas(con, solo_activas=True))
        nombre = vigente.get("nombre", "—")
        return Metadatos(
            distrito=self.cfg.proyecto["distrito"],
            fecha_corte_datos=self.cfg.ultimo_dia_completo,
            fecha_corte_fuente=self.cfg.datos["fecha_corte_fuente"],
            fecha_operativa=self.cfg.fecha_operativa,
            modelo_nombre=nombre,
            modelo_nombre_legible=NOMBRE_LEGIBLE_MODELO.get(nombre, nombre),
            modelo_version=vigente.get("version", "—"),
            macro_f1_test=vigente.get("macro_f1_test"),
            macro_f1_valid=vigente.get("macro_f1_valid"),
            pesos_por_defecto=self.priorizacion.pesos_por_defecto(),
            total_microzonas_activas=activas,
        )

    # ------------------------------------------------------------------ mapa
    def limite_geojson(self) -> dict[str, Any]:
        from shapely.geometry import mapping

        return {"type": "Feature", "properties": {"nombre": self.cfg.proyecto["distrito"]},
                "geometry": mapping(leer_limite(self.cfg.rutas.limite))}  # fmt: skip

    def mapa(self, fecha: str, turno: str, pesos: Mapping[str, float] | None = None) -> dict[str, Any]:
        """FeatureCollection con todas las celdas del distrito; las activas llevan nivel, P y posición."""
        ranking = self.priorizacion.ranking_df(fecha, turno, pesos).set_index("microzona_id")
        with self.bd.lectura() as con:
            mz = microzonas.leer_microzonas(con)
        features = []
        for fila in mz.itertuples(index=False):
            props: dict[str, Any] = {
                "id": fila.id,
                "sector": sector_legible(fila.sector_ref),
                "activa": int(fila.activa),
            }
            if fila.id in ranking.index:
                r = ranking.loc[fila.id]
                props |= {"nivel": r.nivel, "p": round(float(r.p), 3), "posicion": int(r.posicion),
                          "p_texto": f"{r.p:.2f}".replace(".", ",")}  # fmt: skip
            else:
                props |= {"nivel": "Sin registros en el periodo", "p": None, "posicion": None, "p_texto": "—"}
            features.append({"type": "Feature", "properties": props, "geometry": json.loads(fila.geojson),
                             "centro": [fila.centro_lat, fila.centro_lon]})  # fmt: skip
        return {"type": "FeatureCollection", "features": features}

    def puntos_recientes(self, fecha: str) -> pd.DataFrame:
        dias = int(self.cfg.app["dias_puntos_mapa"])
        desde = (date.fromisoformat(fecha) - timedelta(days=dias)).isoformat()
        hasta = min(fecha, (date.fromisoformat(self.cfg.ultimo_dia_completo) + timedelta(days=1)).isoformat())
        with self.bd.lectura() as con:
            return incidencias.puntos_en_ventana(con, desde, hasta)

    # ------------------------------------------------------------------ detalle
    def microzonas_activas(self) -> list[str]:
        with self.bd.lectura() as con:
            return microzonas.leer_microzonas(con, solo_activas=True).id.tolist()

    def detalle(
        self, microzona_id: str, fecha: str, turno: str, pesos: Mapping[str, float] | None = None
    ) -> DetalleMicrozona:
        ranking = self.priorizacion.ranking_df(fecha, turno, pesos)
        with self.bd.lectura() as con:
            mz = microzonas.obtener_microzona(con, microzona_id)
            if mz is None:
                raise KeyError(f"No existe la microzona {microzona_id}")
            hist = incidencias.incidencias_de_microzona(con, microzona_id, fecha)
            obs = predicciones.observado(con, fecha, turno)
        fila = ranking[ranking.microzona_id == microzona_id]
        det = DetalleMicrozona(
            microzona_id=microzona_id, sector=sector_legible(mz["sector_ref"]), fecha=fecha, turno=turno,
            nivel=None, posicion=None, total=len(ranking), p=None,
            centro=(mz["centro_lat"], mz["centro_lon"]), geojson=mz["geojson"],
        )  # fmt: skip
        if not fila.empty:
            r = fila.iloc[0]
            det.nivel, det.posicion, det.p = r.nivel, int(r.posicion), float(r.p)
            det.componentes = [
                {"componente": "R", "nombre": "Nivel estimado", "valor": float(r.r), "peso": float(r.w1), "aporte": float(r.aporte_r)},
                {"componente": "G", "nombre": "Gravedad histórica", "valor": float(r.g), "peso": float(r.w2), "aporte": float(r.aporte_g)},
                {"componente": "F", "nombre": "Frecuencia reciente", "valor": float(r.f), "peso": float(r.w3), "aporte": float(r.aporte_f)},
            ]  # fmt: skip
            det.probabilidades = {"Bajo": float(r.p_bajo), "Medio": float(r.p_medio), "Alto": float(r.p_alto)}
        o = obs[obs.microzona_id == microzona_id]
        if not o.empty and pd.notna(o.iloc[0].nivel_observado):
            det.nivel_observado = o.iloc[0].nivel_observado
            det.conteo_observado = int(o.iloc[0].conteo)
        det.serie_diaria = self._serie_diaria(hist, fecha)
        det.por_turno = (
            hist.groupby("turno").size().reindex(list(TURNOS), fill_value=0).rename("incidencias").reset_index()
        )
        det.por_tipo = (
            hist.groupby("tipo_corto").size().sort_values(ascending=False).head(7).rename("incidencias").reset_index()
            .rename(columns={"tipo_corto": "tipo"})
        )  # fmt: skip
        ultimas = hist.head(int(self.cfg.app["ultimas_incidencias"])).copy()
        ultimas["calle"] = [calle_sin_numero(d) for d in ultimas.direccion]
        det.ultimas = ultimas[["fecha", "hora", "turno", "tipo_corto", "subtipo", "calle"]].rename(
            columns={"tipo_corto": "tipo"}
        )
        return det

    def _serie_diaria(self, hist: pd.DataFrame, fecha: str) -> pd.DataFrame:
        dias = int(self.cfg.app["dias_serie_detalle"])
        fin = min(date.fromisoformat(fecha) - timedelta(days=1), date.fromisoformat(self.cfg.ultimo_dia_completo))
        inicio = max(fin - timedelta(days=dias - 1), date.fromisoformat(self.cfg.datos["fecha_inicio_historia"]))
        rango = [(inicio + timedelta(days=i)).isoformat() for i in range((fin - inicio).days + 1)]
        conteo = hist.groupby("fecha").size().reindex(rango, fill_value=0)
        return conteo.rename("incidencias").rename_axis("fecha").reset_index()

    # ------------------------------------------------------------------ tablero
    def tablero(self) -> dict[str, Any]:
        with self.bd.lectura() as con:
            inc = incidencias.leer_incidencias(con, solo_limpias=True)
            regs = {m["nombre"]: m for m in modelos.ultimos_por_nombre(con)}
            vigente = modelos.modelo_vigente(con)
            mz = microzonas.leer_microzonas(con, solo_activas=False)
        total_fuente = len(inc)
        dias = inc.fecha.nunique()
        serie = inc.groupby("fecha").size().rename("incidencias").reset_index()
        serie["periodo"] = [self._rotulo_periodo(f) for f in serie.fecha]
        estable = inc[inc.periodo == "estable"].copy()
        estable["dia"] = pd.to_datetime(estable.fecha).dt.dayofweek
        n_dias = estable.groupby("dia").fecha.nunique()
        calor = (
            estable.groupby(["dia", "turno"]).size().unstack(fill_value=0).reindex(columns=list(TURNOS), fill_value=0)
        )
        calor = calor.div(n_dias, axis=0).reindex(range(7)).fillna(0)
        calor.index = [NOMBRES_DIA[i] for i in calor.index]
        por_tipo = inc.groupby("tipo_corto").size().sort_values().rename("incidencias").reset_index()
        concentracion = self._curva_concentracion(inc, mz)
        modelos_tabla = pd.DataFrame(
            [{"modelo": NOMBRE_LEGIBLE_MODELO[n], "clave": n, "macro_f1_valid": regs[n]["macro_f1_valid"],
              "macro_f1_test": regs[n]["macro_f1_test"], "vigente": bool(regs[n]["vigente"])}
             for n in MODELOS if n in regs]
        )  # fmt: skip
        met = vigente["metricas"] if vigente else {}
        return {
            "kpis": {
                "total": total_fuente,
                "promedio_diario": total_fuente / dias if dias else 0.0,
                "pct_sin_sector": 100 * float(inc.sector.isna().mean()) if total_fuente else 0.0,
                "dias": int(dias),
            },
            "serie": serie,
            "particion": self.cfg.particion.como_dict(),
            "calor": calor,
            "por_tipo": por_tipo,
            "concentracion": concentracion,
            "modelos": modelos_tabla,
            "vigente": None if vigente is None else NOMBRE_LEGIBLE_MODELO[vigente["nombre"]],
            "matriz_test": met.get("test", {}).get("matriz_confusion"),
            "metricas_vigente": met,
            "importancia": met.get("importancia"),
        }

    def _rotulo_periodo(self, fecha: str) -> str:
        if fecha in set(self.cfg.datos["fechas_censuradas"]):
            return "Censurado (no usado)"
        if fecha <= self.cfg.datos["fin_arranque"]:
            return "Arranque (solo historial)"
        return {"train": "Entrenamiento", "valid": "Validación", "test": "Prueba"}.get(
            self.cfg.particion.de_fecha(fecha) or "", "Otro"
        )

    def _curva_concentracion(self, inc: pd.DataFrame, mz: pd.DataFrame) -> pd.DataFrame:
        """% de celdas del distrito (orden descendente) vs % acumulado de incidencias, train + valid (como en HE2)."""
        ini, fin = self.cfg.particion.train[0], self.cfg.particion.valid[1]
        sub = inc[(inc.fecha >= ini) & (inc.fecha <= fin)]
        conteo = sub.groupby("microzona_id").size().reindex(mz.id, fill_value=0).sort_values(ascending=False)
        acumulado = np.concatenate([[0], np.cumsum(conteo.to_numpy())]) / max(conteo.sum(), 1)
        pct_celdas = np.arange(len(conteo) + 1) / len(conteo)
        return pd.DataFrame({"pct_celdas": 100 * pct_celdas, "pct_incidencias": 100 * acumulado})

    # ------------------------------------------------------------------ metodología
    def metodologia(self) -> dict[str, Any]:
        with self.bd.lectura() as con:
            regs = {m["nombre"]: m for m in modelos.ultimos_por_nombre(con)}
            fuente = con.execute("SELECT * FROM fuente_datos LIMIT 1").fetchone()
        filas_metricas = []
        for n in MODELOS:
            if n not in regs:
                continue
            met = regs[n]["metricas"]
            for p, rot in (("valid", "Validación"), ("test", "Prueba")):
                m = met.get(p, {})
                ic = m.get("bootstrap", {}).get("global_por_bloques_de_dia", {})
                filas_metricas.append({
                    "modelo": NOMBRE_LEGIBLE_MODELO[n], "particion": rot, "macro_f1": m.get("macro_f1"),
                    "ic_inf": ic.get("ic_inf"), "ic_sup": ic.get("ic_sup"), "exactitud": m.get("exactitud"),
                    **{f"f1_{c}": m.get("por_clase", {}).get(c, {}).get("f1") for c in ("Bajo", "Medio", "Alto")},
                })  # fmt: skip
        por_dia = []
        for n in MODELOS:
            if n not in regs:
                continue
            for p, rot in (("valid", "Validación"), ("test", "Prueba")):
                b = regs[n]["metricas"].get(p, {}).get("bootstrap", {}).get("por_dia_filas", {})
                for d, v in b.items():
                    por_dia.append({"modelo": NOMBRE_LEGIBLE_MODELO[n], "particion": rot, "fecha": d, **v})
        por_turno = []
        for n in MODELOS:
            if n not in regs:
                continue
            for p, rot in (("valid", "Validación"), ("test", "Prueba")):
                for t, v in regs[n]["metricas"].get(p, {}).get("por_turno", {}).items():
                    por_turno.append({"modelo": NOMBRE_LEGIBLE_MODELO[n], "particion": rot, "turno": t, "macro_f1": v})
        return {
            "fuente": dict(fuente) if fuente else {},
            "particion": self.cfg.particion.como_dict(),
            "microzona": self.cfg.microzona,
            "pesos": self.priorizacion.pesos_por_defecto(),
            "valor_nivel": self.cfg.priorizacion["valor_nivel"],
            "metricas": pd.DataFrame(filas_metricas),
            "por_dia": pd.DataFrame(por_dia),
            "por_turno": pd.DataFrame(por_turno),
            "features": self.cfg.features_modelo,
            "excluidas_modelo": self.cfg.features.get("excluidas_modelo", []),
            "fecha_operativa": self.cfg.fecha_operativa,
            "ultimo_dia_completo": self.cfg.ultimo_dia_completo,
        }

    def documento(self, nombre: str) -> str:
        """Contenido de un documento de docs/ (model card, data card) para mostrarlo en la app."""
        archivo = DOCUMENTOS.get(nombre)
        if archivo is None:
            raise KeyError(f"Documento desconocido: {nombre}")
        ruta = self.cfg.rutas.docs / archivo
        return ruta.read_text(encoding="utf-8") if ruta.exists() else f"*No se encontró {ruta.name}.*"


__all__ = ["ServicioConsultas", "SinPredicciones", "calle_sin_numero"]
