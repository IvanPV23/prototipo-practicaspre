"""Fase 1 · Paso 3: normalización al esquema canónico, cartografía y perfil con criterios de viabilidad.

Uso:
    python 03_normalizar.py

Entradas: datos/procesados/cco_unificado.csv (02_unificar.py) y el límite distrital descargado en
datos/raw/limite_inei_ana/<fecha>/limite_150133_sjm.geojson.

Salidas:
- datos/cartografia/limite_distrito.geojson          límite oficial (INEI, servido por ANA), WGS84
- datos/procesados/incidencias_canonico.csv          esquema canónico (contratos_handoff.md §1), mismo orden
- datos/procesados/perfil_canonico.json              perfil y evaluación de los 9 criterios de viabilidad
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from shapely.prepared import prep

BASE = Path(__file__).resolve().parents[1]
RAIZ = BASE.parents[1]
PROC = BASE / "datos" / "procesados"
CARTO = BASE / "datos" / "cartografia"
MANIFEST = BASE / "datos" / "manifest.json"

FUENTE_ID = "cco_mdsjm_2026"
DISTRITO = "San Juan de Miraflores"
UBIGEO_INEI = "150133"
COLUMNAS = [
    "id_incidencia", "fuente_dataset", "distrito", "ubigeo_inei", "fecha", "hora", "fecha_hora",
    "turno", "tipo", "subtipo", "modalidad", "zona", "sector", "lat", "lon", "dentro_distrito",
    "canal_reporte", "tipo_reportante", "direccion", "estado_final", "fecha_hora_cierre",
    "tiempo_respuesta_min",
]
OFFSET = "-05:00"  # Lima, sin horario de verano


def texto(s: pd.Series) -> pd.Series:
    """Mayúsculas, sin espacios dobles ni en los extremos; vacío -> nulo."""
    s = s.fillna("").astype(str).str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    return s.replace("", pd.NA)


def turno_por_hora(h: int) -> str:
    # Diccionario de la fuente: Mañana (06–14) / Tarde (14–22) / Noche (22–06)
    if 6 <= h < 14:
        return "Mañana"
    if 14 <= h < 22:
        return "Tarde"
    return "Noche"


def limite() -> tuple[object, dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cand = [a for a in manifest["archivos"] if a["id_fuente"] == "limite_inei_ana"
            and a["archivo"].startswith("limite_") and a.get("sha256")]
    if not cand:
        raise SystemExit("Falta el límite distrital en el manifest (ejecuta 01_descargar.py)")
    a = max(cand, key=lambda a: a["fecha_descarga"])
    gj = json.loads((RAIZ / a["ruta"]).read_text(encoding="utf-8"))
    feats = gj["features"]
    props = feats[0]["properties"]
    if str(props.get("ubigeo")) != UBIGEO_INEI:
        raise SystemExit(f"El límite descargado no es {UBIGEO_INEI}: {props}")
    geom = unary_union([shape(f["geometry"]) for f in feats])
    salida = {
        "type": "FeatureCollection",
        "name": "limite_distrito",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [{
            "type": "Feature",
            "properties": {"ubigeo_inei": UBIGEO_INEI, "distrito": DISTRITO, "provincia": "LIMA",
                           "departamento": "LIMA", "fuente": "INEI (límites censales), servido por ANA – "
                           "geosnirh.ana.gob.pe Hosted/distritos", "url": a["url"],
                           "fecha_descarga": a["fecha_descarga"]},
            "geometry": geom.__geo_interface__,
        }],
    }
    CARTO.mkdir(parents=True, exist_ok=True)
    (CARTO / "limite_distrito.geojson").write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    return geom, a


def main() -> int:
    src = pd.read_csv(PROC / "cco_unificado.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    geom, meta_lim = limite()
    pgeom = prep(geom)

    c = pd.DataFrame(index=src.index)
    c["id_incidencia"] = src["ID_INCIDENCIA"].str.strip()
    c["fuente_dataset"] = FUENTE_ID
    c["distrito"] = DISTRITO
    c["ubigeo_inei"] = UBIGEO_INEI
    f = pd.to_datetime(src["FECHA_REGISTRO"], format="%Y%m%d", errors="coerce")
    h = pd.to_datetime(src["HORA_REGISTRO"].str.strip(), format="%H:%M", errors="coerce")
    c["fecha"] = f.dt.strftime("%Y-%m-%d")
    c["hora"] = h.dt.strftime("%H:%M:%S")
    c["fecha_hora"] = c["fecha"] + "T" + c["hora"] + OFFSET
    turno_fuente = src["TURNO"].str.strip().str.capitalize().replace({"Manana": "Mañana"})
    turno_hora = h.dt.hour.map(turno_por_hora)
    c["turno"] = turno_fuente
    c["tipo"] = texto(src["TIPO"])
    c["subtipo"] = texto(src["SUBTIPO"])
    c["modalidad"] = texto(src["MODALIDAD"])
    c["zona"] = texto(src["ZONA"])
    sector = texto(src["SECTOR"])
    c["sector"] = sector.mask(sector.isin(["SIN ASIGNAR", "SIN SECTOR", "NO ASIGNADO"]))
    lat = pd.to_numeric(src["LATITUD"].str.strip(), errors="coerce")
    lon = pd.to_numeric(src["LONGITUD"].str.strip(), errors="coerce")
    c["lat"], c["lon"] = lat, lon
    geo_ok = lat.between(-90, 90) & lon.between(-180, 180) & lat.ne(0) & lon.ne(0)
    c["dentro_distrito"] = [bool(ok) and pgeom.contains(Point(x, y)) for ok, x, y in zip(geo_ok, lon, lat)]
    c["canal_reporte"] = texto(src["FUENTE"])
    c["tipo_reportante"] = texto(src["TIPO_REPORTANTE"])
    c["direccion"] = src["DIRECCION"].str.replace(r"\s+", " ", regex=True).str.strip().replace("", pd.NA)
    c["estado_final"] = src["ESTADO_FINAL"].str.strip()
    fc = pd.to_datetime(src["FECHA_CIERRE"] + " " + src["HORA_CIERRE"].str.strip(), format="%Y%m%d %H:%M",
                        errors="coerce")
    c["fecha_hora_cierre"] = fc.dt.strftime("%Y-%m-%dT%H:%M:%S") + OFFSET
    c["tiempo_respuesta_min"] = pd.to_numeric(src["TIEMPO_RESPUESTA_MIN"], errors="coerce").astype("Int64")
    c = c[COLUMNAS].sort_values(["fecha_hora", "id_incidencia"]).reset_index(drop=True)

    # --- Validaciones duras -------------------------------------------------------------------
    assert c["id_incidencia"].is_unique, "id_incidencia duplicado"
    assert c["fecha"].notna().all() and c["hora"].notna().all(), "fecha/hora no parseables"
    assert set(c["turno"]) <= {"Mañana", "Tarde", "Noche"}, f"turnos: {set(c['turno'])}"

    c.to_csv(PROC / "incidencias_canonico.csv", index=False, encoding="utf-8", lineterminator="\n")

    # --- Perfil ---------------------------------------------------------------------------------
    n = len(c)
    fechas = pd.to_datetime(c["fecha"])
    por_dia = fechas.value_counts().sort_index()
    rango = pd.date_range(por_dia.index.min(), por_dia.index.max(), freq="D")
    presentes = set(por_dia.index)
    racha = mejor = 0
    for d in rango:
        racha = racha + 1 if d in presentes else 0
        mejor = max(mejor, racha)
    mes = fechas.dt.to_period("M").astype(str)
    por_mes = (pd.DataFrame({"mes": mes, "fecha": fechas}).groupby("mes")
               .agg(registros=("fecha", "size"), dias=("fecha", "nunique")))
    por_mes["registros_por_dia"] = (por_mes["registros"] / por_mes["dias"]).round(1)
    rpd = por_mes["registros_por_dia"].tolist()
    cambios = [round(100 * (b - a) / a, 1) for a, b in zip(rpd, rpd[1:])]
    semana = fechas.dt.to_period("W-SUN")
    por_semana = (pd.DataFrame({"s": semana.astype(str), "f": fechas}).groupby("s")
                  .agg(registros=("f", "size"), dias=("f", "nunique")))
    por_semana["registros_por_dia"] = (por_semana["registros"] / por_semana["dias"]).round(1)
    completas = por_semana[por_semana["dias"] == 7]["registros_por_dia"].tolist()
    cambios_sem = [round(100 * (b - a) / a, 1) for a, b in zip(completas, completas[1:])]

    tipos_por_semana = pd.crosstab(semana.astype(str), c["tipo"]).gt(0)
    tipos_estables = int(tipos_por_semana.all().sum())

    patrones = {
        "posible_dni_8_digitos": r"(?<![\d.])\d{8}(?![\d.])",
        "posible_telefono_9_digitos": r"(?<!\d)9\d{8}(?!\d)",
        "correo": r"[\w.+-]+@[\w-]+\.[\w.]+",
        "posible_placa": r"\b[A-Z]{1,3}\d?-\d{3,4}\b",
        "tratamiento_persona": r"\b(?:SR|SRA|SRTA|DON|DOÑA)\.?\s+[A-ZÁÉÍÓÚÑ]",
    }
    dirs = c["direccion"].fillna("")
    hallazgos = {k: int(dirs.str.contains(p, regex=True, case=False).sum()) for k, p in patrones.items()}

    pct_geo = round(100 * geo_ok.mean(), 2)
    pct_dentro = round(100 * c["dentro_distrito"].mean(), 2)
    fuera = c.loc[~c["dentro_distrito"], ["id_incidencia", "lat", "lon", "direccion"]]
    inconsist_turno = int((turno_fuente != turno_hora).sum())

    # Censura a la derecha: el dataset solo incluye incidencias cerradas a la fecha de corte
    ult = c[c["fecha"] >= (fechas.max() - pd.Timedelta(days=3)).strftime("%Y-%m-%d")]
    censura = (ult.assign(largo=ult["tiempo_respuesta_min"].fillna(0) > 1380)
               .groupby("fecha").agg(registros=("id_incidencia", "size"), pct_cierre_mayor_23h=("largo", "mean")))
    censura["pct_cierre_mayor_23h"] = (100 * censura["pct_cierre_mayor_23h"]).round(1)

    criterios = [
        {"criterio": "1. Georreferenciación a nivel de punto (lat/lon válidas)", "umbral": ">= 90 % (deseable >= 98 %)",
         "valor": f"{pct_geo} %", "cumple": pct_geo >= 90},
        {"criterio": "2. Fecha y hora (o turno) por registro", "umbral": "100 %",
         "valor": f"{round(100 * (c['fecha'].notna() & c['hora'].notna()).mean(), 2)} % con fecha y hora; "
                  f"turno coherente con la hora en {n - inconsist_turno}/{n}",
         "cumple": bool(c["fecha"].notna().all() and c["hora"].notna().all())},
        {"criterio": "3. Tipo/subtipo de incidencia", "umbral": "presente (deseable: catálogo estable)",
         "valor": f"{c['tipo'].nunique()} tipos, {c['subtipo'].nunique()} subtipos, {c['modalidad'].nunique()} "
                  f"modalidades; {tipos_estables}/{c['tipo'].nunique()} tipos presentes en todas las semanas",
         "cumple": bool(c["tipo"].notna().all() and c["subtipo"].notna().all())},
        {"criterio": "4. Días consecutivos cubiertos", "umbral": ">= 42 (deseable >= 90)",
         "valor": f"{mejor} días ({c['fecha'].min()} a {c['fecha'].max()})", "cumple": mejor >= 42},
        {"criterio": "5. Volumen", "umbral": ">= 2 000 registros (deseable >= 50 por día)",
         "valor": f"{n} registros; {round(n / len(rango), 1)} por día en promedio", "cumple": n >= 2000},
        {"criterio": "6. Estabilidad de cobertura (registros/día por mes)",
         "umbral": "sin cambios de nivel > 50 % sin explicar",
         "valor": "; ".join(f"{m}: {r}/día" for m, r in por_mes["registros_por_dia"].items())
                  + f"; cambio entre meses {cambios} % (al límite); entre semanas completas {completas} /día "
                    f"-> cambios {cambios_sem} %. Arranque 16–21 may con {por_dia.iloc[:6].mean():.1f}/día "
                    f"(probable puesta en marcha del sistema, no confirmada por la fuente) y último día "
                    f"censurado por el filtro de incidencias cerradas",
         "cumple": all(abs(x) <= 50 for x in cambios + cambios_sem)},
        {"criterio": "7. Licencia abierta y fuente oficial identificable", "umbral": "sí",
         "valor": "ODC-By 1.0; MDSJM – Gerencia de Seguridad Ciudadana (PNDA)", "cumple": True},
        {"criterio": "8. Puntos dentro del límite distrital", "umbral": ">= 90 % (deseable >= 98 %)",
         "valor": f"{pct_dentro} % ({int(c['dentro_distrito'].sum())}/{n}) dentro del límite INEI 150133",
         "cumple": pct_dentro >= 90},
        {"criterio": "9. Sin datos personales o eliminables", "umbral": "sí",
         "valor": "Fuente anonimizada (sin nombres ni descripción libre); DIRECCION es dirección de vía/lote. "
                  f"Barrido de patrones en direccion: {hallazgos}",
         "cumple": sum(hallazgos.values()) == 0},
    ]

    perfil = {
        "registros": n,
        "fecha_min": c["fecha"].min(), "fecha_max": c["fecha"].max(),
        "dias_rango": len(rango), "dias_con_registros": len(presentes), "max_dias_consecutivos": mejor,
        "pct_georreferenciado": pct_geo, "pct_dentro_distrito": pct_dentro,
        "fuera_del_distrito": fuera.astype(str).to_dict(orient="records"),
        "inconsistencias_turno_hora": inconsist_turno,
        "registros_por_dia": {d.strftime("%Y-%m-%d"): int(v) for d, v in por_dia.items()},
        "registros_por_mes": por_mes.reset_index().to_dict(orient="records"),
        "cambio_registros_dia_entre_meses_pct": cambios,
        "registros_por_semana": por_semana.reset_index().to_dict(orient="records"),
        "censura_ultimos_dias": censura.reset_index().to_dict(orient="records"),
        "turno": c["turno"].value_counts().to_dict(),
        "tipo": c["tipo"].value_counts().to_dict(),
        "subtipo_n": int(c["subtipo"].nunique()), "modalidad_n": int(c["modalidad"].nunique()),
        "sector": c["sector"].fillna("(nulo)").value_counts().to_dict(),
        "zona": c["zona"].fillna("(nulo)").value_counts().to_dict(),
        "canal_reporte": c["canal_reporte"].value_counts().to_dict(),
        "tipo_reportante": c["tipo_reportante"].value_counts().to_dict(),
        "estado_final": c["estado_final"].value_counts().to_dict(),
        "nivel_fuente_no_canonico": src["NIVEL"].replace("", "(vacío)").value_counts().to_dict(),
        "nivel_vacio_por_estado": pd.crosstab(src["NIVEL"].replace("", "(vacío)"), src["ESTADO_FINAL"]).to_dict(),
        "tiempo_respuesta_min": c["tiempo_respuesta_min"].astype(float).describe().round(1).to_dict(),
        "no_atendida_con_cierre_mayor_23h": int(((c["estado_final"] == "No atendida")
                                                  & (c["tiempo_respuesta_min"] > 1380)).sum()),
        "ubigeo_fuente": sorted(src["UBIGEO"].unique().tolist()),
        "limite": {"ruta": (CARTO / "limite_distrito.geojson").relative_to(RAIZ).as_posix(),
                   "url": meta_lim["url"], "area_km2_aprox": None},
        "hallazgos_datos_personales": hallazgos,
        "criterios_viabilidad": criterios,
    }
    # Área aproximada (proyección equirectangular local; solo referencia)
    import math
    k = 111.32 * math.cos(math.radians(-12.16))
    perfil["limite"]["area_km2_aprox"] = round(geom.area * 110.57 * k, 2)
    (PROC / "perfil_canonico.json").write_text(json.dumps(perfil, ensure_ascii=False, indent=2, default=str),
                                               encoding="utf-8")
    print(f"canónico: {n} filas, {c['fecha'].min()} → {c['fecha'].max()}, geo {pct_geo} %, dentro {pct_dentro} %")
    for cr in criterios:
        print(f"  [{'OK ' if cr['cumple'] else 'NO '}] {cr['criterio']}: {cr['valor']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
