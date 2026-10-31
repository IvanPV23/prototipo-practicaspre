"""Convierte el contenido de 01_alcance/ en un único Markdown legible por los agentes.

Uso:
    python extraer_alcance.py --raiz <RAIZ>

Genera:
    02_documentacion/00_contexto/alcance.md          texto de documentos y perfil de datos
    02_documentacion/00_contexto/alcance_hashes.json sha256 por archivo + hash global

Solo usa la biblioteca estándar y pandas/openpyxl (para hojas de cálculo).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
EXT_DOCUMENTO = {".docx"}
EXT_TABLA = {".xlsx", ".xls", ".csv"}
EXT_TEXTO = {".md", ".txt"}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _texto_parrafo(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.iter(f"{W}t")).strip()


def docx_a_markdown(ruta: Path) -> str:
    """Recorre el cuerpo en orden; los párrafos con estilo de título se vuelven encabezados."""
    raiz = ET.fromstring(zipfile.ZipFile(ruta).read("word/document.xml"))
    cuerpo = raiz.find(f"{W}body")
    lineas: list[str] = []
    for nodo in cuerpo:
        if nodo.tag == f"{W}p":
            texto = _texto_parrafo(nodo)
            if not texto:
                continue
            estilo = nodo.find(f"{W}pPr/{W}pStyle")
            nombre = (estilo.get(f"{W}val") or "").lower() if estilo is not None else ""
            if nombre.startswith(("heading", "ttulo", "titulo")) and nombre[-1:].isdigit():
                lineas.append(f"{'#' * min(int(nombre[-1]) + 1, 6)} {texto}")
            elif nombre in {"title", "ttulo", "titulo"}:
                lineas.append(f"# {texto}")
            else:
                lineas.append(texto)
        elif nodo.tag == f"{W}tbl":
            filas = [
                [" ".join(_texto_parrafo(p) for p in celda.iter(f"{W}p")).strip()
                 for celda in fila.iter(f"{W}tc")]
                for fila in nodo.iter(f"{W}tr")
            ]
            if not filas:
                continue
            ancho = max(len(f) for f in filas)
            filas = [f + [""] * (ancho - len(f)) for f in filas]
            lineas.append("| " + " | ".join(filas[0]) + " |")
            lineas.append("|" + "---|" * ancho)
            lineas.extend("| " + " | ".join(f) + " |" for f in filas[1:])
        lineas.append("")
    return "\n".join(lineas)


def perfil_tabla(ruta: Path) -> str:
    import pandas as pd

    if ruta.suffix.lower() == ".csv":
        hojas = {"csv": pd.read_csv(ruta, low_memory=False)}
    else:
        hojas = pd.read_excel(ruta, sheet_name=None)

    partes: list[str] = []
    for nombre, df in hojas.items():
        partes.append(f"**Hoja `{nombre}`** — {len(df):,} filas × {df.shape[1]} columnas".replace(",", " "))
        partes.append("")
        partes.append("| Columna | Tipo | Nulos | Únicos | Ejemplo |")
        partes.append("|---|---|---|---|---|")
        for col in df.columns:
            serie = df[col]
            ejemplo = serie.dropna().iloc[0] if serie.notna().any() else ""
            ejemplo = str(ejemplo).replace("|", "/")[:60]
            partes.append(
                f"| {col} | {serie.dtype} | {int(serie.isna().sum())} | {serie.nunique()} | {ejemplo} |"
            )
        for col in df.columns:
            if "FECHA" in str(col).upper() and df[col].notna().any():
                valores = df[col].dropna().astype(str)  # tipos mixtos en Excel rompen min/max
                partes.append(f"\nRango `{col}`: {valores.min()} → {valores.max()}")
        partes.append("")
    return "\n".join(partes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raiz", required=True, type=Path)
    args = parser.parse_args()

    raiz = args.raiz.resolve()
    alcance = raiz / "01_alcance"
    if not alcance.is_dir():
        print(f"No existe {alcance}", file=sys.stderr)
        return 1

    salida = raiz / "02_documentacion" / "00_contexto"
    salida.mkdir(parents=True, exist_ok=True)

    archivos = sorted(p for p in alcance.rglob("*") if p.is_file() and not p.name.startswith("~$"))
    hashes = {p.relative_to(raiz).as_posix(): sha256(p) for p in archivos}
    hash_global = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(hashes.items())).encode()).hexdigest()

    md: list[str] = [
        "# Contexto del proyecto (extraído de 01_alcance)",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')} · Hash del alcance: `{hash_global[:16]}`",
        "",
        "Archivo generado automáticamente. No editar: se regenera en cada /practicaspre.",
        "",
    ]
    for ruta in archivos:
        rel = ruta.relative_to(raiz).as_posix()
        ext = ruta.suffix.lower()
        md.append(f"---\n\n## Archivo: `{rel}`\n")
        try:
            if ext in EXT_DOCUMENTO:
                md.append(docx_a_markdown(ruta))
            elif ext in EXT_TABLA:
                md.append(perfil_tabla(ruta))
            elif ext in EXT_TEXTO:
                md.append(ruta.read_text(encoding="utf-8", errors="replace"))
            else:
                md.append(f"_Formato `{ext}` no extraído automáticamente; léelo directamente si es relevante._")
        except Exception as error:  # un archivo dañado no debe frenar la extracción del resto
            md.append(f"_No se pudo extraer: {error}_")
        md.append("")

    (salida / "alcance.md").write_text("\n".join(md), encoding="utf-8")
    (salida / "alcance_hashes.json").write_text(
        json.dumps({"hash_alcance": hash_global, "archivos": hashes}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"OK alcance.md ({len(archivos)} archivos) hash={hash_global}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
