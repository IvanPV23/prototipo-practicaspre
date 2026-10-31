"""Fase 1 · Paso 4: perfil de los conjuntos candidatos (opción C) con la misma tabla de criterios.

Uso:
    python 04_perfilar_candidatos.py

Lee los crudos de datos/raw/cand_*/<fecha>/ (descargados por 01_descargar.py) y el perfil del dataset
principal (datos/procesados/perfil_canonico.json). Escribe datos/procesados/matriz_candidatos.csv.
Los candidatos solo se perfilan: ninguno entra al canónico.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, shape
from shapely.prepared import prep

BASE = Path(__file__).resolve().parents[1]
RAIZ = BASE.parents[1]
PROC = BASE / "datos" / "procesados"
MANIFEST = BASE / "datos" / "manifest.json"


def ruta(manifest: dict, id_fuente: str, archivo: str) -> Path | None:
    c = [a for a in manifest["archivos"] if a["id_fuente"] == id_fuente and a["archivo"] == archivo and a.get("sha256")]
    return RAIZ / max(c, key=lambda a: a["fecha_descarga"])["ruta"] if c else None


def racha(fechas: pd.Series) -> int:
    dias = sorted(set(fechas.dropna().dt.normalize()))
    mejor = actual = 0
    previo = None
    for d in dias:
        actual = actual + 1 if previo is not None and (d - previo).days == 1 else 1
        mejor, previo = max(mejor, actual), d
    return mejor


def estabilidad(fechas: pd.Series) -> tuple[float | None, str]:
    f = fechas.dropna()
    m = f.dt.to_period("M")
    t = pd.DataFrame({"m": m, "d": f.dt.normalize()}).groupby("m").agg(n=("d", "size"), dias=("d", "nunique"))
    t = t[t["dias"] >= 7]  # meses con al menos una semana de datos
    rpd = (t["n"] / t["dias"]).tolist()
    cambios = [abs(b - a) / a * 100 for a, b in zip(rpd, rpd[1:]) if a > 0]
    return (round(max(cambios), 1) if cambios else None), f"{len(t)} meses; rango {min(rpd):.0f}–{max(rpd):.0f}/día" if rpd else ""


def fila(nombre, distrito, ubigeo, en_lima, inst, url, licencia, df_fechas, pct_geo, pct_hora, tipo, n,
         pct_dentro, personales, nota):
    rmax, desc = estabilidad(df_fechas) if df_fechas is not None else (None, "")
    dias = racha(df_fechas) if df_fechas is not None else 0
    rango = (f"{df_fechas.min():%Y-%m-%d} a {df_fechas.max():%Y-%m-%d}" if df_fechas is not None and df_fechas.notna().any()
             else "")
    c = {
        "c1_geo_ge90": pct_geo is not None and pct_geo >= 90,
        "c2_fecha_hora_100": pct_hora is not None and pct_hora >= 99.99,
        "c3_tipo": bool(tipo),
        "c4_dias_ge42": dias >= 42,
        "c5_volumen_ge2000": n >= 2000,
        "c6_estable": rmax is not None and rmax <= 50,
        "c7_licencia_abierta": licencia.lower().startswith("open data commons") or "odc" in licencia.lower(),
        "c8_dentro_ge90": pct_dentro is not None and pct_dentro >= 90,
        "c9_sin_personales": not personales,
    }
    return {
        "candidato": nombre, "distrito": distrito, "ubigeo_inei": ubigeo, "provincia_lima": en_lima,
        "institucion": inst, "url": url, "licencia": licencia, "registros": n, "periodo": rango,
        "max_dias_consecutivos": dias,
        "pct_georreferenciado": None if pct_geo is None else round(pct_geo, 1),
        "pct_fecha_hora": None if pct_hora is None else round(pct_hora, 1),
        "tipo_subtipo": tipo, "max_cambio_mensual_registros_dia_pct": rmax, "estabilidad_detalle": desc,
        "pct_dentro_limite": None if pct_dentro is None else round(pct_dentro, 1),
        "datos_personales": personales, **c, "criterios_minimos_cumplidos": sum(c.values()), "nota": nota,
    }


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    filas = []

    # 0. Dataset principal (SJM) desde su perfil
    p = json.loads((PROC / "perfil_canonico.json").read_text(encoding="utf-8"))
    canon = pd.read_csv(PROC / "incidencias_canonico.csv", dtype=str)
    filas.append(fila("SJM – CCO MDSJM (dataset del alcance)", "San Juan de Miraflores", "150133", True,
                      "Municipalidad Distrital de San Juan de Miraflores",
                      "https://www.datosabiertos.gob.pe/dataset/relaci%C3%B3n-de-incidencias-atendidas-por-el-centro-de-control-de-operaciones-cco-municipalidad",
                      "Open Data Commons Attribution License (ODC-By 1.0)", pd.to_datetime(canon["fecha"]),
                      p["pct_georreferenciado"], 100.0, "tipo/subtipo/modalidad (7/23/79)", p["registros"],
                      p["pct_dentro_distrito"], False, "Único extracto publicado (corte 2026-06-10)."))

    # 1. Callao – Municipalidad Provincial del Callao (central de monitoreo de cámaras)
    # Para SJM el criterio 6 se toma del perfil (incluye cambios entre semanas completas: solo hay 2 meses)
    c6 = next(c["cumple"] for c in p["criterios_viabilidad"] if c["criterio"].startswith("6."))
    filas[0]["c6_estable"] = c6
    filas[0]["criterios_minimos_cumplidos"] = sum(v for k, v in filas[0].items() if k.startswith("c") and k[1].isdigit())
    filas[0]["nota"] += " Criterio 6 evaluado también por semanas (+77 % entre la 1.ª y 2.ª semana completa)."

    r = ruta(manifest, "cand_callao_mpc", "REGISTRO_TOTAL_INCIDENCIAS_CAMARAS_CALLAO_MPC.csv")
    if r:
        d = pd.read_csv(r, sep=";", dtype=str, encoding="utf-8-sig", low_memory=False)
        f = pd.to_datetime(d["FECHA DEL CASO"], format="%Y%m%d", errors="coerce")
        hora_ok = d["HORA DEL CASO"].str.fullmatch(r"\d{4}").fillna(False)
        lat = pd.to_numeric(d["LATITUD"].str.replace(",", "."), errors="coerce")
        lon = pd.to_numeric(d["LONGITUD"].str.replace(",", "."), errors="coerce")
        geo = lat.between(-90, 90) & lon.between(-180, 180) & lat.ne(0) & lon.ne(0)
        rl = ruta(manifest, "cand_callao_mpc", "limite_070101_callao.geojson")
        dentro = None
        if rl:
            g = prep(shape(json.loads(rl.read_text(encoding="utf-8"))["features"][0]["geometry"]))
            muestra = d[geo].sample(min(50000, int(geo.sum())), random_state=0).index
            dentro = 100 * sum(g.contains(Point(x, y)) for x, y in zip(lon[muestra], lat[muestra])) / len(muestra)
        # subconjunto georreferenciado estable (desde julio de 2024)
        desde = f >= "2024-07-01"
        filas.append(fila("Callao – Central de monitoreo de cámaras (MPC)", "Callao", "070101", False,
                          "Municipalidad Provincial del Callao",
                          "https://www.datosabiertos.gob.pe/dataset/incidencias-observadas-mediante-c%C3%A1maras-de-videovigilancia-municipalidad-provincial-del",
                          "Open Data Commons Attribution License", f, 100 * geo.mean(), 100 * (f.notna() & hora_ok).mean(),
                          f"solo TIPO DE CASO ({d['TIPO DE CASO'].nunique()} categorías; 44 % tránsito, 24 % ambientales, "
                          f"3 % seguridad ciudadana); sin subtipo", len(d), dentro, False,
                          f"Provincia Constitucional del Callao, no Lima. Coordenadas solo desde jun-2024 "
                          f"({100 * geo[desde].mean():.1f} % desde jul-2024; 0 % antes). Volumen mensual muy variable "
                          f"(784–4 300/día en 2025). Corte 2025-11-16; sin actualización posterior. "
                          f"% dentro del límite calculado sobre muestra de 50 000 puntos."))

    # 2. San Isidro – Seguridad ciudadana 2026 (apoyo por seguridad)
    r = ruta(manifest, "cand_san_isidro_2026", "SC-APOYO_POR_SEGURIDAD_2026.xls")
    if r:
        d = pd.read_excel(r, dtype=str)
        f = pd.to_datetime(d["FECHA"], format="%d/%m/%Y %H:%M", errors="coerce")
        lat, lon = pd.to_numeric(d["LATITUD"], errors="coerce"), pd.to_numeric(d["LONGITUD"], errors="coerce")
        filas.append(fila("San Isidro – Seguridad Ciudadana 2026 (apoyo por seguridad)", "San Isidro", "150131", True,
                          "Municipalidad Distrital de San Isidro",
                          "https://www.datosabiertos.gob.pe/dataset/mdsi-seguridad-ciudadana-tr%C3%A1nsito-y-gesti%C3%B3n-del-riesgo-de-desastres",
                          "Open Data Commons Public Domain Dedication and Licence (PDDL)", f,
                          100 * lat.notna().mean(), 100 * f.notna().mean(),
                          f"TIPO ({d['TIPO'].nunique()} categorías), MODALIDAD 22 % completa", len(d), None, False,
                          "Columnas LATITUD/LONGITUD vacías: solo dirección textual y sector; exigiría geocodificar "
                          "~39 000 direcciones (dato derivado, no publicado). Ene–abr 2026."))

    # 3. San Martín de Porres – Incidencias 1er semestre 2026
    r = ruta(manifest, "cand_smp_2026", "DATA_BASE_INCIDENCIAS_1ER_SEMESTRE.xlsx")
    if r:
        d = pd.read_excel(r, dtype=str)
        f = pd.to_datetime(d["FECHA"], errors="coerce")
        filas.append(fila("San Martín de Porres – Incidencias 1er semestre", "San Martín de Porres", "150135", True,
                          "Municipalidad Distrital de San Martín de Porres",
                          "https://www.datosabiertos.gob.pe/dataset/incidencias-en-el-distrito-de-san-martin-de-porres",
                          "No especificada", f, 0.0, 100 * f.notna().mean(),
                          "tipo/subtipo/modalidad (mismo catálogo nacional que SJM)", len(d), None, False,
                          "Sin coordenadas ni dirección: solo jurisdicción policial (comisaría) y hora redondeada."))

    # 4. Jesús María – Incidencia delictiva
    r = ruta(manifest, "cand_jesus_maria", "dataset_vf_5.csv")
    if r:
        d = pd.read_csv(r, dtype=str, sep=";")
        f = pd.to_datetime(d["FECHA_OCURRENCIA"], format="%Y%m%d", errors="coerce")
        filas.append(fila("Jesús María – Incidencia delictiva", "Jesús María", "150113", True,
                          "Municipalidad Distrital de Jesús María",
                          "https://www.datosabiertos.gob.pe/dataset/informaci%C3%B3n-estad%C3%ADstica-de-incidencia-delictiva-de-la-municipalidad-distrital-de-jes%C3%BAs-mar%C3%ADa",
                          "Open Data Commons Attribution License", f, 0.0, 0.0, "TIPO_DELITO", len(d), None, False,
                          "Sin coordenadas ni hora."))

    # 5. Gobierno Regional del Callao – Hechos delictivos (feb-2024)
    r = ruta(manifest, "cand_gore_callao", "DATASET_SEGURIDAD_CALLAO_FEBRERO2024_0.csv")
    if r:
        d = pd.read_csv(r, dtype=str, encoding="utf-8-sig", sep=None, engine="python")
        f = pd.to_datetime(d["FECHA_HECHO"], format="%Y%m%d", errors="coerce")
        lat, lon = pd.to_numeric(d["LATITUD"], errors="coerce"), pd.to_numeric(d["LONGITUD"], errors="coerce")
        filas.append(fila("GORE Callao – Hechos delictivos (feb-2024)", "Provincia del Callao (varios)", "07", False,
                          "Gobierno Regional del Callao",
                          "https://www.datosabiertos.gob.pe/dataset/registros-de-hechos-delictivos-en-la-provincia-constitucional-del-callao-gobierno-regional",
                          "Open Data Commons Attribution License", f, 100 * (lat.notna() & lon.notna()).mean(),
                          100 * (f.notna() & d["HORA_HECHO"].notna()).mean(), "tipo/subtipo/modalidad", len(d), None, True,
                          "Un solo mes; incluye fecha de nacimiento, edad, sexo, estado civil y ocupación de la persona "
                          "(datos personales). Provincia del Callao."))

    # 6. Miraflores – Emergencias atendidas (agregado mensual)
    r = ruta(manifest, "cand_miraflores", "4_Atencion_de_emergencia_II_2021.xlsx")
    if r:
        d = pd.read_excel(r, dtype=str)
        filas.append(fila("Miraflores – Emergencias atendidas", "Miraflores", "150122", True,
                          "Municipalidad Distrital de Miraflores",
                          "https://www.datosabiertos.gob.pe/dataset/emergencias-atendidas-por-la-municipalidad-de-miraflores",
                          "Open Data Commons Attribution License", None, None, None, "conteos por categoría", len(d),
                          None, False, "Conteos mensuales agregados (2020-2021), no registros individuales."))

    m = pd.DataFrame(filas)
    m.to_csv(PROC / "matriz_candidatos.csv", index=False, encoding="utf-8")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(m[["candidato", "registros", "periodo", "max_dias_consecutivos", "pct_georreferenciado",
                 "max_cambio_mensual_registros_dia_pct", "pct_dentro_limite", "criterios_minimos_cumplidos"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
