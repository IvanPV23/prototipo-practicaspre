"""Exporta informe_analisis.md a informe_analisis.html con las figuras incrustadas (base64).

Uso (desde RAIZ):
    .venv/Scripts/python.exe 02_documentacion/02_analisis/scripts/exportar_informe_html.py
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

import markdown

BASE = Path(__file__).resolve().parents[1]
ENTRADA = BASE / "informe_analisis.md"
SALIDA = BASE / "informe_analisis.html"

CSS = """
:root { --texto:#1f1f1f; --fondo:#ffffff; --borde:#d9d9e6; --acento:#1F4E79; --suave:#f4f4fa; }
@media (prefers-color-scheme: dark) { :root { --texto:#e8e8ee; --fondo:#16161c; --borde:#3a3a4a; --acento:#8fb5dd; --suave:#20202a; } }
html { background: var(--fondo); }
body { font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: var(--texto); background: var(--fondo);
       max-width: 980px; margin: 0 auto; padding: 24px 16px 64px; line-height: 1.55; font-size: 15px; }
h1 { color: var(--acento); font-size: 1.7em; margin-bottom: .2em; }
h2 { color: var(--acento); border-bottom: 2px solid var(--borde); padding-bottom: .2em; margin-top: 2em; }
h3 { margin-top: 1.5em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: .92em; display: block; overflow-x: auto; }
th, td { border: 1px solid var(--borde); padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: var(--suave); }
img { max-width: 100%; height: auto; display: block; margin: 1.2em auto; border: 1px solid var(--borde); background: #fff; }
blockquote { border-left: 4px solid var(--acento); margin: 1em 0; padding: .4em 1em; background: var(--suave); }
code { background: var(--suave); padding: 1px 4px; border-radius: 3px; font-size: .9em; }
hr { border: none; border-top: 1px solid var(--borde); margin: 2em 0; }
"""


def incrustar(html: str) -> str:
    def reemplazo(m: re.Match) -> str:
        ruta = BASE / m.group(2)
        datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
        return f'{m.group(1)}data:image/png;base64,{datos}{m.group(3)}'
    return re.sub(r'(<img[^>]*src=")(figuras/[^"]+\.png)(")', reemplazo, html)


def main() -> None:
    texto = ENTRADA.read_text(encoding="utf-8")
    cuerpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    cuerpo = incrustar(cuerpo)
    html = (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>Análisis exploratorio SJM</title>\n<style>{CSS}</style>\n</head>\n<body>\n{cuerpo}\n</body>\n</html>\n')
    SALIDA.write_text(html, encoding="utf-8")
    n = len(re.findall(r"data:image/png;base64", html))
    print(f"Escrito {SALIDA} ({SALIDA.stat().st_size / 1e6:.1f} MB, {n} figuras incrustadas)")


if __name__ == "__main__":
    main()
