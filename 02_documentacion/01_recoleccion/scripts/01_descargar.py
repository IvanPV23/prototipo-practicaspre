"""Fase 1 · Paso 1: descarga de fuentes a datos/raw/<id_fuente>/<fecha_descarga>/ y registro en manifest.json.

Uso (desde cualquier carpeta):
    python 01_descargar.py [--fecha YYYY-MM-DD] [--sin-candidatos] [--forzar]

- Cada fuente va a su propia carpeta. Nada de lo descargado se ejecuta: solo se lee después con pandas/json.
- Si el archivo ya existe en la carpeta de esa fecha, no se vuelve a descargar (salvo --forzar).
- Calcula SHA-256 y tamaño de cada archivo y actualiza datos/manifest.json (una entrada por archivo).
- Si una descarga falla, se registra el error en el manifest; no se inventa contenido.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parents[1]          # 02_documentacion/01_recoleccion
RAIZ = BASE.parents[1]
RAW = BASE / "datos" / "raw"
MANIFEST = BASE / "datos" / "manifest.json"
PNDA = "https://www.datosabiertos.gob.pe/sites/default/files/"
ANA_DIST = "https://geosnirh.ana.gob.pe/server/rest/services/Hosted/distritos/FeatureServer/0/query"
UA = {"User-Agent": "Mozilla/5.0 (investigacion academica UNMSM; practicaspre)"}

# id_fuente -> lista de (nombre_local, url)
FUENTES: dict[str, list[tuple[str, str]]] = {
    # Dataset principal: CCO de la MDSJM (mismo extracto que 01_alcance, pero en CSV original con ID como texto)
    "cco_mdsjm_2026": [
        ("incidencias_seguridad_sjm_20260610.csv", PNDA + "incidencias_seguridad_sjm_20260610.csv"),
        ("DICCIONARIO-DATOS_20260610_151901.xlsx", PNDA + "DICCIONARIO-DATOS_20260610_151901.xlsx"),
        ("METADATOS_20260610.docx", PNDA + "METADATOS_20260610.docx"),
        ("ficha_package_show.json",
         "https://www.datosabiertos.gob.pe/api/3/action/package_show?id=af9dff57-53a2-4ee0-b7c3-d7787505207d"),
    ],
    # Contexto: denuncias policiales SIDPOL (conteos por mes, distrito y modalidad)
    "sidpol_mininter": [
        ("DATASET_Denuncias_Policiales_Enero_2018_a_Septiembre_2026.csv",
         PNDA + "DATASET_Denuncias%20Policiales%20-%20Enero%202018%20a%20Septiembre%202026.csv"),
        ("DICCIONARIO_DATOS_Denuncias_Policiales_Abr_2026.xlsx",
         PNDA + "DICCIONARIO_DATOS_Denuncias_Policiales_Abr%202026.xlsx"),
        ("METADATO_Denuncias_Policiales_Septiembre_2026.docx",
         PNDA + "METADATO_Denuncias_Policiales_Septiembre%202026.docx"),
    ],
    # Cartografía: límite distrital INEI servido por el geoservidor de la ANA (capa Hosted/distritos)
    "limite_inei_ana": [
        ("limite_150133_sjm.geojson",
         ANA_DIST + "?where=ubigeo%3D%27150133%27&outFields=*&outSR=4326&f=geojson"),
        ("distritos_lima_atributos.json",
         ANA_DIST + "?where=provincia%3D%27LIMA%27&outFields=ubigeo,distrito,provincia,capital,fuente"
                    "&returnGeometry=false&f=json"),
    ],
    # Exposición: población proyectada INEI 2018-2026 por distrito
    "poblacion_inei_2026": [
        ("poblacion_proyectada_distrital_2018_2026.xlsx",
         "https://cdn.www.gob.pe/uploads/document/file/8261096/"
         "6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026.xlsx"),
    ],
}

# Candidatos evaluados para la opción C (solo perfilado; no entran al canónico)
CANDIDATOS: dict[str, list[tuple[str, str]]] = {
    "cand_callao_mpc": [
        ("REGISTRO_TOTAL_INCIDENCIAS_CAMARAS_CALLAO_MPC.csv",
         PNDA + "REGISTRO%20TOTAL%20DE%20INCIDENCIAS%20OBSERVADAS%20MEDIANTE%20LA%20CENTRAL%20DE%20MONITOREO%20DE%20"
                "C%C3%81MARAS%20Y%20VIDEOVIGILANCIA%20CALLAO-MPC.csv"),
        ("limite_070101_callao.geojson",
         ANA_DIST + "?where=ubigeo%3D%27070101%27&outFields=*&outSR=4326&f=geojson"),
    ],
    "cand_san_isidro_2026": [
        ("SC-APOYO_POR_SEGURIDAD_2026.xls", PNDA + "SC-APOYO%20POR%20SEGURIDAD%202026.xls"),
    ],
    "cand_smp_2026": [
        ("DATA_BASE_INCIDENCIAS_1ER_SEMESTRE.xlsx", PNDA + "DATA%20BASE%20INCIDENCIAS%201ER%20SEMESTRE.xlsx"),
    ],
    "cand_jesus_maria": [
        ("dataset_vf_5.csv", PNDA + "dataset_vf_5.csv"),
    ],
    "cand_gore_callao": [
        ("DATASET_SEGURIDAD_CALLAO_FEBRERO2024_0.csv", PNDA + "DATASET_SEGURIDAD_CALLAO_FEBRERO2024_0.csv"),
    ],
    "cand_miraflores": [
        ("4_Atencion_de_emergencia_II_2021.xlsx", PNDA + "4_Atencion_de_emergencia_II_2021.xlsx"),
    ],
}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def descargar(url: str, destino: Path) -> None:
    ultimo_error = None
    for intento in range(3):
        try:
            with requests.get(url, headers=UA, timeout=300, stream=True) as r:
                r.raise_for_status()
                tmp = destino.with_suffix(destino.suffix + ".part")
                with tmp.open("wb") as f:
                    for bloque in r.iter_content(1 << 20):
                        f.write(bloque)
                tmp.replace(destino)
                return
        except requests.RequestException as error:  # noqa: PERF203
            ultimo_error = error
            time.sleep(3 * (intento + 1))
    raise RuntimeError(str(ultimo_error))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fecha", default=date.today().isoformat())
    parser.add_argument("--sin-candidatos", action="store_true")
    parser.add_argument("--forzar", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"archivos": []}
    previas = {(a["id_fuente"], a["ruta"]): a for a in manifest.get("archivos", [])}

    fuentes = dict(FUENTES)
    if not args.sin_candidatos:
        fuentes.update(CANDIDATOS)

    fallos = 0
    for id_fuente, archivos in fuentes.items():
        carpeta = RAW / id_fuente / args.fecha
        carpeta.mkdir(parents=True, exist_ok=True)
        for nombre, url in archivos:
            destino = carpeta / nombre
            rel = destino.relative_to(RAIZ).as_posix()
            entrada = {"id_fuente": id_fuente, "archivo": nombre, "ruta": rel, "url": url,
                       "fecha_descarga": args.fecha}
            try:
                if args.forzar or not destino.exists():
                    descargar(url, destino)
                    print(f"[descargado] {rel}")
                else:
                    print(f"[existente]  {rel}")
                entrada.update({"sha256": sha256(destino), "bytes": destino.stat().st_size, "error": None})
            except Exception as error:  # registrar y seguir
                fallos += 1
                entrada.update({"sha256": None, "bytes": None, "error": str(error)})
                print(f"[FALLA] {url}: {error}", file=sys.stderr)
            previas[(id_fuente, rel)] = entrada

    # Referencia local: el Excel de 01_alcance (solo lectura, no se copia)
    xlsx = RAIZ / "01_alcance" / "incidencias_seguridad_sjm_20260610.xlsx"
    if xlsx.exists():
        rel = xlsx.relative_to(RAIZ).as_posix()
        previas[("alcance_xlsx", rel)] = {
            "id_fuente": "alcance_xlsx", "archivo": xlsx.name, "ruta": rel,
            "url": "local: 01_alcance (copia en Excel del CSV del PNDA, entregada con el alcance)",
            "fecha_descarga": None, "sha256": sha256(xlsx), "bytes": xlsx.stat().st_size, "error": None,
        }

    lima = timezone(timedelta(hours=-5))
    manifest = {
        "generado": datetime.now(lima).isoformat(timespec="seconds"),
        "descripcion": "Archivos crudos de la Fase 1 con URL de origen, fecha de descarga, SHA-256 y tamaño en bytes.",
        "archivos": sorted(previas.values(), key=lambda a: (a["id_fuente"], a["ruta"])),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {len(manifest['archivos'])} archivos, {fallos} fallos")
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
