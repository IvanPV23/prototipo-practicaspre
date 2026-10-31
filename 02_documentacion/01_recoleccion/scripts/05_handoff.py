"""Fase 1 · Paso 5: catálogo de fuentes y handoff hacia la Fase 2.

Uso:
    python 05_handoff.py

Construye catalogo_fuentes.csv y handoff_fase1.json a partir de datos/manifest.json,
datos/procesados/perfil_canonico.json y el canónico (cuyo SHA-256 se calcula aquí).
Ejecutar después de 01–04.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAIZ = BASE.parents[1]
PROC = BASE / "datos" / "procesados"
MANIFEST = BASE / "datos" / "manifest.json"
CANON = PROC / "incidencias_canonico.csv"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def rel(p: Path) -> str:
    return p.relative_to(RAIZ).as_posix()


def entrada(manifest: dict, id_fuente: str, archivo: str) -> dict:
    c = [a for a in manifest["archivos"] if a["id_fuente"] == id_fuente and a["archivo"] == archivo and a.get("sha256")]
    if not c:
        raise SystemExit(f"Falta {id_fuente}/{archivo} en el manifest")
    return max(c, key=lambda a: a["fecha_descarga"])


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    perfil = json.loads((PROC / "perfil_canonico.json").read_text(encoding="utf-8"))
    canon = pd.read_csv(CANON, dtype=str)

    e_cco = entrada(manifest, "cco_mdsjm_2026", "incidencias_seguridad_sjm_20260610.csv")
    e_sid = entrada(manifest, "sidpol_mininter", "DATASET_Denuncias_Policiales_Enero_2018_a_Septiembre_2026.csv")
    e_lim = entrada(manifest, "limite_inei_ana", "limite_150133_sjm.geojson")
    e_pob = entrada(manifest, "poblacion_inei_2026", "poblacion_proyectada_distrital_2018_2026.xlsx")

    n_sid = sum(1 for _ in open(RAIZ / e_sid["ruta"], encoding="utf-8-sig")) - 1
    pob = pd.read_excel(RAIZ / e_pob["ruta"], header=None, dtype=str)
    n_dist = int(pob[0].astype(str).str.fullmatch(r"\d{4}(?!00)\d{2}").sum())
    sid_sjm = pd.read_csv(PROC / "sidpol_sjm_mensual.csv")
    ultimo = sid_sjm.sort_values(["anio", "mes"]).iloc[-1]
    periodo_sid = f"{int(sid_sjm.anio.min())}-{int(sid_sjm[sid_sjm.anio == sid_sjm.anio.min()].mes.min()):02d} a " \
                  f"{int(ultimo.anio)}-{int(ultimo.mes):02d}"

    fuentes = [
        {"id": "cco_mdsjm_2026",
         "nombre": "Relación de incidencias atendidas por el Centro de Control de Operaciones (CCO) - "
                   "Municipalidad Distrital de San Juan de Miraflores (v1.0, corte 2026-06-10)",
         "institucion": "Municipalidad Distrital de San Juan de Miraflores – Gerencia de Seguridad Ciudadana",
         "url": "https://www.datosabiertos.gob.pe/dataset/relaci%C3%B3n-de-incidencias-atendidas-por-el-centro-de-"
                "control-de-operaciones-cco-municipalidad",
         "licencia": "Open Data Commons Attribution License (ODC-By 1.0)",
         "fecha_descarga": e_cco["fecha_descarga"], "ruta_raw": e_cco["ruta"], "sha256": e_cco["sha256"],
         "registros": int(len(pd.read_csv(RAIZ / e_cco["ruta"], dtype=str, encoding="utf-8-sig"))),
         "uso": "entrenamiento"},
        {"id": "sidpol_mininter",
         "nombre": "Denuncias policiales registradas a nivel nacional (SIDPOL), enero 2018 a septiembre 2026",
         "institucion": "Ministerio del Interior (MININTER)",
         "url": "https://www.datosabiertos.gob.pe/dataset/denuncias-policiales-registradas-nivel-nacional-mininter",
         "licencia": "Open Data Commons Attribution License (ODC-By)",
         "fecha_descarga": e_sid["fecha_descarga"], "ruta_raw": e_sid["ruta"], "sha256": e_sid["sha256"],
         "registros": n_sid, "uso": "contexto"},
        {"id": "limite_inei_ana",
         "nombre": "Límite distrital de San Juan de Miraflores (ubigeo 150133), capa de distritos censales INEI",
         "institucion": "INEI (fuente de la geometría); servido por la Autoridad Nacional del Agua (ANA), "
                        "geosnirh.ana.gob.pe",
         "url": e_lim["url"],
         "licencia": "Información pública del Estado peruano (sin licencia explícita en el servicio; se cita INEI y ANA)",
         "fecha_descarga": e_lim["fecha_descarga"], "ruta_raw": e_lim["ruta"], "sha256": e_lim["sha256"],
         "registros": 1, "uso": "cartografia"},
        {"id": "poblacion_inei_2026",
         "nombre": "Perú: Población total proyectada al 30 de junio de cada año, según departamento, provincia y "
                   "distrito, 2018-2026",
         "institucion": "Instituto Nacional de Estadística e Informática (INEI)",
         "url": "https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-"
                "al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026",
         "licencia": "Información pública del Estado peruano (gob.pe; uso con cita de la fuente)",
         "fecha_descarga": e_pob["fecha_descarga"], "ruta_raw": e_pob["ruta"], "sha256": e_pob["sha256"],
         "registros": n_dist, "uso": "exposicion"},
    ]

    with (BASE / "catalogo_fuentes.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fuentes[0].keys()))
        w.writeheader()
        w.writerows(fuentes)

    fechas = sorted(canon["fecha"])
    p = perfil
    pd_dia = p["registros_por_dia"]
    advertencias = [
        f"Criterio 4 NO cumplido: el único extracto publicado cubre {p['max_dias_consecutivos']} días "
        f"({p['fecha_min']} a {p['fecha_max']}); el mínimo es 42. No existen extractos anteriores ni posteriores en el "
        "PNDA (una sola revisión, 2026-06-10), aunque la ficha declara frecuencia mensual. Los resultados del modelo "
        "deben presentarse como exploratorios.",
        "Criterio 6 NO cumplido: arranque 16–21 may con "
        f"{sum(list(pd_dia.values())[:6]) / 6:.1f} registros/día frente a ~110 desde el 22 may (+77 % entre la primera y "
        "la segunda semana completa). Coincide con 'desde el inicio de operaciones del sistema CCO' de los metadatos, "
        "pero la fuente no lo confirma. Recomendación para la Fase 2: evaluar excluir 2026-05-16 a 2026-05-21 del "
        "entrenamiento o modelarlo explícitamente.",
        f"Censura a la derecha: el dataset solo incluye incidencias cerradas a la fecha de corte. El 2026-06-10 tiene "
        f"{pd_dia.get('2026-06-10')} registros y 0 % de cierres > 23 h (frente a ~61–72 % los días previos): faltan las "
        "incidencias abiertas que se cerrarían automáticamente al día siguiente. Recomendación: no usar 2026-06-10 "
        "(y revisar 2026-06-09) como día de prueba sin corrección.",
        "El Excel de 01_alcance no se usa como fuente: Excel convirtió en número 67 celdas de ID_INCIDENCIA y alteró 21 "
        "ID (ceros a la izquierda y notación científica); dos ID distintos '0e…' quedaron como 0, que es el duplicado "
        "aparente (2 591 únicos en 2 592 filas). El CSV original del PNDA tiene 2 592 ID únicos y el mismo contenido. "
        "Las hojas 'Calc_Dashboard' y 'Dashboard' son cálculos del autor, no dato fuente.",
        "Ubigeo: la fuente publica 150141 y lo describe como INEI de SJM, pero en INEI/SIDPOL/límites 150141 es "
        "Surquillo; SJM es 150133. El canónico usa 150133. En el CSV se escribe sin comillas: leer ubigeo_inei como "
        "texto (dtype=str) para conservar el formato de 6 caracteres.",
        f"{len(p['fuera_del_distrito'])} puntos ({100 - p['pct_dentro_distrito']:.2f} %) caen fuera del límite: 20 a "
        "menos de 120 m del borde (Atocongo, Óvalo Los Eucaliptos), 10 entre 290 m y 1,9 km (VES, Chorrillos, Parque "
        "Industrial) y 2 errores groseros (Bellavista-Callao a 15 km y lat -9,37 en Áncash). Se marcan con "
        "dentro_distrito = False; la Fase 2 decide si los excluye o usa una tolerancia de borde.",
        "La columna NIVEL de la fuente (Común/Relevante/Grave, 1 687 vacíos) es la gravedad 'asignada por el operador "
        "durante la coordinación' (diccionario oficial): se fija después del registro y está vacía en el 100 % de las "
        "'No atendida' con cierre automático. Es posterior al evento ([POST]) y no pasa al canónico; no debe usarse "
        "como predictor ni como etiqueta de gravedad.",
        f"{p['no_atendida_con_cierre_mayor_23h']} incidencias 'No atendida' se cierran después de 23 h (mediana de "
        "tiempo de respuesta 1 441 min): patrón de cierre automático. Las columnas [POST] solo sirven para descripción.",
        "Sesgo de registro: 74,5 % de los registros provienen de 'CAMARAS CECOP' y 77,9 % los reporta un agente "
        "municipal; la distribución espacial refleja dónde hay cámaras y patrullaje, no la incidencia real. "
        "20,9 % sin sector y 12,0 % sin zona en la fuente.",
        "Catálogo con erratas de origen que se conservan tal cual en el canónico (p. ej. 'LLAMDA TELEFONICA', "
        "'PREUNTOS ACONTECIMIENTOS ESPECIALES', 'CONTRA CONTRA LA PERSONA'); solo se normalizaron mayúsculas y "
        "espacios dobles. La Fase 2 puede agruparlas.",
        "Alternativa fuera de Lima registrada pero no recomendada: Callao (Municipalidad Provincial del Callao) publica "
        "913 238 incidencias de cámaras 2023-10 a 2025-11 con coordenadas desde jun-2024, pero es otra provincia, es "
        "muy inestable (cambios mensuales de hasta 117 %), 86 % de puntos dentro del distrito Callao, no tiene subtipo "
        "y solo el 3 % es 'seguridad ciudadana'. Ver datos/procesados/matriz_candidatos.csv.",
        "Vía para cumplir el criterio 4 sin cambiar de distrito: los metadatos indican actualización mensual y cortes "
        "a demanda desde el sistema interno; el usuario puede solicitar a la MDSJM (tecnologia@munisjm.gob.pe, o por "
        "transparencia) un extracto actualizado del mismo dataset. Si llega, basta colocarlo como nueva fuente "
        "'cco_mdsjm_*' y reejecutar 02–05: 02_unificar.py ya deduplica por ID_INCIDENCIA.",
        "Nota de contexto: el usuario se refirió al distrito como 'SJL', pero el alcance y el dataset corresponden a "
        "San Juan de Miraflores (SJM, 150133), no a San Juan de Lurigancho (150132).",
    ]

    lima = timezone(timedelta(hours=-5))
    handoff = {
        "version": 1,
        "generado": datetime.now(lima).isoformat(timespec="seconds"),
        "decision": "A",
        "justificacion_resumen": (
            "No existen extractos adicionales del CCO de SJM en el PNDA (una sola versión, corte 2026-06-10), y ningún "
            "distrito de Lima publica incidencias georreferenciadas a nivel de punto; el único candidato con puntos y "
            "series largas (Callao) es de otra provincia, inestable y no claramente superior. Se usa el mismo extracto "
            "en su CSV oficial (sin la corrupción de ID del Excel), con límite INEI, SIDPOL y población como contexto; "
            "los criterios 4 y 6 quedan como limitaciones documentadas."),
        "requiere_confirmacion_usuario": False,
        "distrito": {"nombre": "San Juan de Miraflores", "ubigeo_inei": "150133", "ubigeo_fuente": "150141"},
        "dataset_principal": {
            "ruta": rel(CANON),
            "registros": int(len(canon)),
            "fecha_min": fechas[0],
            "fecha_max": fechas[-1],
            "dias_cubiertos": int(p["dias_con_registros"]),
            "pct_georreferenciado": float(p["pct_georreferenciado"]),
            "pct_dentro_distrito": float(p["pct_dentro_distrito"]),
            "sha256": sha256(CANON),
        },
        "alternativa": {"descripcion": "No aplica: decisión A (se mantiene el distrito del alcance).", "ruta": None},
        "fuentes": fuentes,
        "contexto": {
            "sidpol": {"ruta": rel(PROC / "sidpol_sjm_mensual.csv"), "periodo": periodo_sid},
            "limite_distrital": {"ruta": rel(BASE / "datos" / "cartografia" / "limite_distrito.geojson"),
                                 "fuente": "INEI – límites distritales censales (ubigeo 150133), servido por ANA "
                                           "(geosnirh.ana.gob.pe, capa Hosted/distritos)"},
            "poblacion": {"ruta": rel(PROC / "poblacion_sjm.csv"),
                          "fuente": "INEI – Población total proyectada al 30 de junio, 2018-2026 (SJM 2026: "
                                    + f"{int(pd.read_csv(PROC / 'poblacion_sjm.csv').query('anio == 2026').poblacion_proyectada.iat[0]):,}"
                                    .replace(",", " ") + " hab.)"},
        },
        "criterios_viabilidad": [
            {"criterio": c["criterio"], "umbral": c["umbral"], "valor": c["valor"], "cumple": bool(c["cumple"])}
            for c in p["criterios_viabilidad"]
        ],
        "advertencias": advertencias,
    }
    (BASE / "handoff_fase1.json").write_text(json.dumps(handoff, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"handoff: decision {handoff['decision']}, {handoff['dataset_principal']['registros']} registros, "
          f"sha256 {handoff['dataset_principal']['sha256'][:12]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
