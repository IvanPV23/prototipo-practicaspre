"""Compuerta automática de /practicaspre: valida la entrega de una fase contra su contrato.

Uso:
    python verificar_fase.py --raiz <RAIZ> --fase {1,2,3}

Sale con código 0 si todo pasa y 1 si hay fallos. Imprime una línea por comprobación.
Los contratos están en referencias/contratos_handoff.md.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

COLUMNAS_CANONICAS = [
    "id_incidencia", "fuente_dataset", "distrito", "ubigeo_inei", "fecha", "hora", "fecha_hora",
    "turno", "tipo", "subtipo", "modalidad", "zona", "sector", "lat", "lon", "dentro_distrito",
    "canal_reporte", "tipo_reportante", "direccion", "estado_final", "fecha_hora_cierre",
    "tiempo_respuesta_min",
]
COLUMNAS_POST = {"estado_final", "fecha_hora_cierre", "tiempo_respuesta_min"}
TURNOS = {"Mañana", "Tarde", "Noche"}


class Verificador:
    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz
        self.fallos = 0

    def check(self, condicion: bool, mensaje: str) -> bool:
        print(f"[{'OK' if condicion else 'FALLA'}] {mensaje}")
        self.fallos += not condicion
        return condicion

    def existe(self, rel: str | None) -> bool:
        return self.check(bool(rel) and (self.raiz / rel).exists(), f"existe {rel}")

    def json(self, rel: str) -> dict | None:
        if not self.existe(rel):
            return None
        try:
            return json.loads((self.raiz / rel).read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            self.check(False, f"{rel} es JSON válido ({error})")
            return None

    def claves(self, datos: dict, requeridas: list[str], origen: str) -> None:
        faltan = [c for c in requeridas if c not in datos]
        self.check(not faltan, f"{origen} tiene claves {requeridas}" + (f" — faltan {faltan}" if faltan else ""))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def fase1(v: Verificador) -> None:
    base = "02_documentacion/01_recoleccion"
    for archivo in ["informe_recoleccion.md", "decision_dataset.md", "catalogo_fuentes.csv",
                    "diccionario_fuente.md", "datos/manifest.json"]:
        v.existe(f"{base}/{archivo}")

    h = v.json(f"{base}/handoff_fase1.json")
    if h is None:
        return
    v.claves(h, ["decision", "distrito", "dataset_principal", "fuentes", "criterios_viabilidad"], "handoff_fase1")
    v.check(h.get("decision") in {"A", "B", "C"}, f"decision válida ({h.get('decision')})")
    if h.get("decision") == "C":
        v.existe(f"{base}/impacto_en_alcance.md")
        v.check(h.get("requiere_confirmacion_usuario") is True, "decision C exige requiere_confirmacion_usuario = true")
    v.check(bool(h.get("fuentes")), "hay al menos una fuente registrada")

    dp = h.get("dataset_principal", {})
    if not v.existe(dp.get("ruta")):
        return
    ruta = v.raiz / dp["ruta"]
    v.check(sha256(ruta) == dp.get("sha256"), "sha256 del dataset coincide con el handoff")

    with ruta.open(encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        columnas = lector.fieldnames or []
        filas = list(lector)
    v.check(columnas == COLUMNAS_CANONICAS, "columnas = esquema canónico (mismo orden)"
            + ("" if columnas == COLUMNAS_CANONICAS else f" — recibidas {columnas}"))
    v.check(len(filas) == dp.get("registros"), f"registros = {dp.get('registros')} (archivo: {len(filas)})")
    ids = [r.get("id_incidencia") for r in filas]
    v.check(len(ids) == len(set(ids)), "id_incidencia único")
    turnos = {r.get("turno") for r in filas}
    v.check(turnos <= TURNOS, f"turnos válidos {sorted(t or '' for t in turnos)}")
    try:
        coords_ok = all(-90 <= float(r["lat"]) <= 90 and -180 <= float(r["lon"]) <= 180
                        for r in filas if r["lat"] and r["lon"])
    except (KeyError, ValueError):
        coords_ok = False
    v.check(coords_ok, "lat/lon numéricas y en rango")
    fechas = sorted(r["fecha"] for r in filas if r.get("fecha"))
    if fechas:
        v.check(fechas[0] == dp.get("fecha_min") and fechas[-1] == dp.get("fecha_max"),
                f"rango de fechas coincide ({fechas[0]} → {fechas[-1]})")


def fase2(v: Verificador) -> None:
    base = "02_documentacion/02_analisis"
    for archivo in ["informe_analisis.md", "informe_analisis.html", "diccionario_datos.md",
                    "reglas_limpieza.md", "especificacion_modelado.md", "requirements-analisis.txt"]:
        v.existe(f"{base}/{archivo}")
    for nb in ["01_calidad", "02_temporal", "03_espacial", "04_preparacion_modelado"]:
        if v.existe(f"{base}/notebooks/{nb}.ipynb"):
            celdas = json.loads((v.raiz / base / "notebooks" / f"{nb}.ipynb").read_text(encoding="utf-8"))["cells"]
            con_codigo = [c for c in celdas if c.get("cell_type") == "code" and "".join(c.get("source", [])).strip()]
            ejecutado = all(c.get("execution_count") for c in con_codigo)
            errores = any(o.get("output_type") == "error" for c in con_codigo for o in c.get("outputs", []))
            v.check(ejecutado and not errores, f"{nb} ejecutado sin errores")
    figuras = list((v.raiz / base / "figuras").glob("*.png"))
    v.check(len(figuras) >= 6, f"al menos 6 figuras PNG ({len(figuras)})")

    h = v.json(f"{base}/handoff_fase2.json")
    if h is None:
        return
    v.claves(h, ["dataset_limpio", "microzona", "tabla_modelado", "objetivo", "features",
                 "excluidas_por_fuga", "particion_temporal", "gravedad", "linea_base", "hipotesis"], "handoff_fase2")
    for clave in ["dataset_limpio", "tabla_modelado"]:
        v.existe(h.get(clave, {}).get("ruta"))
    v.existe(h.get("microzona", {}).get("ruta_geojson"))
    v.existe(h.get("gravedad", {}).get("ruta_tabla"))

    excluidas = set(h.get("excluidas_por_fuga", []))
    v.check(COLUMNAS_POST <= excluidas, "excluidas_por_fuga incluye las columnas [POST]")
    nombres = {f.get("nombre") for f in h.get("features", [])}
    v.check(bool(nombres) and not (nombres & excluidas), "ninguna feature está excluida por fuga")
    v.check(h.get("objetivo", {}).get("calculado_sobre") == "entrenamiento", "umbrales calculados sobre entrenamiento")

    pt = h.get("particion_temporal", {})
    try:
        tramos = [tuple(date.fromisoformat(x) for x in pt[k]) for k in ("train", "valid", "test")]
        ordenado = all(a <= b for a, b in tramos)
        contiguo = all((tramos[i + 1][0] - tramos[i][1]).days == 1 for i in range(2))
        v.check(ordenado and contiguo, "partición temporal ascendente, contigua y sin solapamiento")
    except (KeyError, ValueError, TypeError):
        v.check(False, "partición temporal con fechas ISO válidas")
    v.check("macro_f1_test" not in h.get("linea_base", {}), "la línea base no reporta métricas en prueba")


def fase3(v: Verificador) -> None:
    base = "03_codigo"
    for archivo in ["README.md", "requirements.txt", "config/config.yaml", "src/seguridad_ciudadana/__main__.py",
                    "app/Inicio.py", "docs/arquitectura.md", "docs/modelo_datos.md", "docs/model_card.md",
                    "docs/data_card.md", "docs/guia_desarrollo.md"]:
        v.existe(f"{base}/{archivo}")
    v.check(len(list((v.raiz / base / "tests").glob("test_*.py"))) >= 5, "al menos 5 archivos de tests")
    v.check(len(list((v.raiz / base / "app" / "pages").glob("*.py"))) >= 6, "al menos 6 páginas en app/pages")
    v.check(any((v.raiz / base / "docs" / "adr").glob("*.md")), "hay ADRs en docs/adr")

    r = v.json(f"{base}/reportes/resultado_fase3.json")
    if r is None:
        return
    v.claves(r, ["modelos", "modelo_seleccionado", "hipotesis", "base_datos", "tests", "comandos"], "resultado_fase3")
    nombres = {m.get("nombre") for m in r.get("modelos", [])}
    esperados = {"persistencia", "regresion_logistica", "random_forest", "gradient_boosting"}
    v.check(esperados <= nombres, f"se reportan los 4 modelos ({sorted(n or '' for n in nombres)})")
    v.existe(r.get("base_datos", {}).get("ruta"))
    t = r.get("tests", {})
    v.check(t.get("total", 0) > 0 and t.get("fallidos", 1) == 0, f"tests: {t}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raiz", required=True, type=Path)
    parser.add_argument("--fase", required=True, type=int, choices=[1, 2, 3])
    args = parser.parse_args()

    v = Verificador(args.raiz.resolve())
    {1: fase1, 2: fase2, 3: fase3}[args.fase](v)
    print(f"\nFase {args.fase}: {'APROBADA' if v.fallos == 0 else f'{v.fallos} fallo(s)'}")
    return 0 if v.fallos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
