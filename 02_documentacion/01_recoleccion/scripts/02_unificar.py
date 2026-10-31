"""Fase 1 · Paso 2: unificación de extractos del CCO y preparación de las fuentes de contexto.

Uso:
    python 02_unificar.py

Lee datos/manifest.json (generado por 01_descargar.py) y, para cada fuente, toma la carpeta de descarga
más reciente. Produce en datos/procesados/:
- cco_unificado.csv           todos los extractos CSV del CCO de la MDSJM (fuentes cuyo id empieza por
                              "cco_mdsjm"), mismo esquema, deduplicados por ID_INCIDENCIA (gana el de
                              FECHA_CORTE más reciente). Todo como texto, sin transformar.
- unificacion_cco.json        extractos leídos, solapamientos, duplicados y comparación con el Excel de 01_alcance.
- sidpol_sjm_mensual.csv      denuncias SIDPOL del distrito (UBIGEO_HECHO = 150133) por año, mes y modalidad.
- poblacion_sjm.csv           población proyectada INEI del distrito, 2018-2026.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAIZ = BASE.parents[1]
PROC = BASE / "datos" / "procesados"
MANIFEST = BASE / "datos" / "manifest.json"
UBIGEO_INEI = "150133"
COLUMNAS_FUENTE = [
    "FECHA_CORTE", "UBIGEO", "ID_INCIDENCIA", "FECHA_REGISTRO", "HORA_REGISTRO", "TURNO", "TIPO", "SUBTIPO",
    "MODALIDAD", "ZONA", "SECTOR", "DIRECCION", "LATITUD", "LONGITUD", "FUENTE", "TIPO_REPORTANTE", "NIVEL",
    "ESTADO_FINAL", "FECHA_CIERRE", "HORA_CIERRE", "TIEMPO_RESPUESTA_MIN", "AMBIENTAL",
]


def archivos_recientes(manifest: dict, prefijo: str, patron: str) -> list[Path]:
    """Archivos del manifest cuyo id_fuente empieza por `prefijo` y cuyo nombre cumple `patron`,
    tomando para cada (id_fuente, archivo) la fecha de descarga más reciente."""
    elegidos: dict[tuple[str, str], dict] = {}
    for a in manifest["archivos"]:
        if a["id_fuente"].startswith(prefijo) and a.get("sha256") and re.search(patron, a["archivo"]):
            clave = (a["id_fuente"], a["archivo"])
            if clave not in elegidos or (a["fecha_descarga"] or "") > (elegidos[clave]["fecha_descarga"] or ""):
                elegidos[clave] = a
    return [RAIZ / a["ruta"] for a in sorted(elegidos.values(), key=lambda a: a["ruta"])]


def celdas_numericas(xlsx: Path) -> int:
    """Celdas de ID_INCIDENCIA que Excel almacenó como número (en lugar de texto)."""
    import openpyxl
    ws = openpyxl.load_workbook(xlsx, read_only=True).worksheets[0]
    filas = ws.iter_rows(values_only=True)
    j = list(next(filas)).index("ID_INCIDENCIA")
    return sum(isinstance(r[j], (int, float)) for r in filas)


def unificar_cco(manifest: dict) -> dict:
    rutas = archivos_recientes(manifest, "cco_mdsjm", r"\.csv$")
    if not rutas:
        raise SystemExit("No hay extractos CSV del CCO en el manifest. Ejecuta 01_descargar.py.")
    partes, extractos = [], []
    for ruta in rutas:
        df = pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        df.columns = [c.strip() for c in df.columns]
        if list(df.columns) != COLUMNAS_FUENTE:
            raise SystemExit(f"Esquema distinto en {ruta}: {list(df.columns)}")
        df = df.apply(lambda s: s.str.strip())
        df["_archivo"] = ruta.relative_to(RAIZ).as_posix()
        partes.append(df)
        extractos.append({
            "archivo": df["_archivo"].iat[0], "filas": len(df),
            "fecha_corte": sorted(df["FECHA_CORTE"].unique().tolist()),
            "fecha_registro_min": df["FECHA_REGISTRO"].min(), "fecha_registro_max": df["FECHA_REGISTRO"].max(),
            "ids_unicos": int(df["ID_INCIDENCIA"].nunique()),
        })
    todo = pd.concat(partes, ignore_index=True)
    filas_antes = len(todo)
    ids_en_varios = int(todo.groupby("ID_INCIDENCIA")["_archivo"].nunique().gt(1).sum())
    todo = todo.sort_values(["ID_INCIDENCIA", "FECHA_CORTE"]).drop_duplicates("ID_INCIDENCIA", keep="last")
    todo = todo.sort_values(["FECHA_REGISTRO", "HORA_REGISTRO", "ID_INCIDENCIA"]).reset_index(drop=True)
    PROC.mkdir(parents=True, exist_ok=True)
    todo.drop(columns="_archivo").to_csv(PROC / "cco_unificado.csv", index=False, encoding="utf-8")

    informe = {
        "extractos": extractos,
        "filas_concatenadas": filas_antes,
        "ids_presentes_en_mas_de_un_extracto": ids_en_varios,
        "filas_tras_deduplicar": len(todo),
        "ids_patron_hex8": int(todo["ID_INCIDENCIA"].str.fullmatch(r"[0-9a-f]{8}").sum()),
    }

    # Comparación con el Excel entregado en 01_alcance (solo lectura)
    xlsx = RAIZ / "01_alcance" / "incidencias_seguridad_sjm_20260610.xlsx"
    if xlsx.exists():
        x = pd.read_excel(xlsx, sheet_name=0, dtype=str, keep_default_na=False)
        ids_x = x["ID_INCIDENCIA"].astype(str).str.strip()
        n_hex = int(ids_x.str.fullmatch(r"[0-9a-f]{8}").sum())
        mismo_orden = len(x) == len(todo)
        informe["comparacion_alcance_xlsx"] = {
            "archivo": xlsx.relative_to(RAIZ).as_posix(),
            "hojas": list(pd.ExcelFile(xlsx).sheet_names),
            "filas_hoja_datos": len(x),
            "ids_unicos_xlsx": int(ids_x.nunique()),
            "celdas_id_guardadas_como_numero_en_xlsx": celdas_numericas(xlsx),
            "ids_xlsx_que_no_son_hex8_al_leer_como_texto": len(x) - n_hex,
            "ids_del_csv_no_encontrados_en_xlsx": int((~todo["ID_INCIDENCIA"].isin(set(ids_x))).sum()),
            "explicacion": ("Excel convirtió en número los ID hexadecimales formados solo por dígitos o con "
                            "forma de notación científica (p. ej. '01127344' -> 1127344, '45184e36' -> 4.5184e40, "
                            "'0e…' -> 0). Dos ID distintos del tipo '0e<dígitos>' quedaron ambos como 0: es el "
                            "duplicado aparente. El CSV original del PNDA conserva los ID como texto y no tiene "
                            "duplicados."),
        }
        if mismo_orden:
            for col in ["FECHA_REGISTRO", "TURNO", "TIPO", "ZONA", "SECTOR", "ESTADO_FINAL"]:
                a = pd.Series(sorted(todo[col].tolist()))
                b = pd.Series(sorted(x[col].astype(str).str.strip().tolist()))
                informe["comparacion_alcance_xlsx"][f"distribucion_igual_{col}"] = bool((a == b).all())
    (PROC / "unificacion_cco.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    return informe


def preparar_sidpol(manifest: dict) -> None:
    rutas = archivos_recientes(manifest, "sidpol_mininter", r"^DATASET.*\.csv$")
    if not rutas:
        print("[aviso] sin SIDPOL en el manifest")
        return
    d = pd.read_csv(rutas[-1], dtype=str, encoding="utf-8-sig", low_memory=False)
    d["UBIGEO_HECHO"] = d["UBIGEO_HECHO"].str.zfill(6)
    s = d[d["UBIGEO_HECHO"] == UBIGEO_INEI].copy()
    nombres = s["DIST_HECHO"].unique().tolist()
    if nombres != ["SAN JUAN DE MIRAFLORES"]:
        raise SystemExit(f"UBIGEO {UBIGEO_INEI} no corresponde a SJM en SIDPOL: {nombres}")
    s["cantidad"] = s["cantidad"].astype(int)
    s = s.rename(columns={"ANIO": "anio", "MES": "mes", "P_MODALIDADES": "modalidad", "DIST_HECHO": "distrito",
                          "UBIGEO_HECHO": "ubigeo_inei"})
    s["anio"], s["mes"] = s["anio"].astype(int), s["mes"].astype(int)
    s = s[["anio", "mes", "ubigeo_inei", "distrito", "modalidad", "cantidad"]].sort_values(["anio", "mes", "modalidad"])
    s.to_csv(PROC / "sidpol_sjm_mensual.csv", index=False, encoding="utf-8")
    print(f"SIDPOL SJM: {len(s)} filas, {s['cantidad'].sum()} denuncias, "
          f"{s['anio'].min()}-{s['mes'].iloc[0]:02d} a {s['anio'].max()}-{s[s.anio == s.anio.max()]['mes'].max():02d}")


def preparar_poblacion(manifest: dict) -> None:
    rutas = archivos_recientes(manifest, "poblacion_inei", r"\.xlsx$")
    if not rutas:
        print("[aviso] sin población en el manifest")
        return
    p = pd.read_excel(rutas[-1], header=None, dtype=str)
    cab = p.iloc[4].tolist()
    fila = p[p[0].astype(str).str.strip() == UBIGEO_INEI]
    if len(fila) != 1:
        raise SystemExit("No se encontró el ubigeo en el cuadro de población")
    fila = fila.iloc[0]
    registros = [{"ubigeo_inei": UBIGEO_INEI, "distrito": str(fila[1]).strip(), "anio": int(float(cab[j])),
                  "poblacion_proyectada": int(float(fila[j]))}
                 for j in range(2, len(cab)) if str(cab[j]).strip() not in ("", "nan")]
    pd.DataFrame(registros).to_csv(PROC / "poblacion_sjm.csv", index=False, encoding="utf-8")
    print(f"Población SJM: {registros[0]['anio']}={registros[0]['poblacion_proyectada']} … "
          f"{registros[-1]['anio']}={registros[-1]['poblacion_proyectada']}")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    informe = unificar_cco(manifest)
    print(f"CCO unificado: {informe['filas_tras_deduplicar']} filas de {len(informe['extractos'])} extracto(s); "
          f"ID en más de un extracto: {informe['ids_presentes_en_mas_de_un_extracto']}")
    preparar_sidpol(manifest)
    preparar_poblacion(manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
