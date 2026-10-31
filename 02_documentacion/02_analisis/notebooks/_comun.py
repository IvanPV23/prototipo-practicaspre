"""Utilidades compartidas por los notebooks de la Fase 2 (análisis y preparación para el modelado).

Todas las rutas se resuelven relativas a RAIZ (el directorio que contiene `01_alcance/`).
Este módulo es también la implementación de referencia de la especificación de modelado:
microzonas, partición, objetivo y variables (ver `especificacion_modelado.md`).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from pyproj import Transformer
from shapely.geometry import Point, box, shape
from shapely.ops import transform


# --------------------------------------------------------------------------- rutas
def encontrar_raiz() -> Path:
    actual = Path.cwd().resolve()
    for candidato in [actual, *actual.parents]:
        if (candidato / "01_alcance").exists() and (candidato / "02_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró RAIZ (carpeta con 01_alcance/ y 02_documentacion/)")


RAIZ = encontrar_raiz()
REC = RAIZ / "02_documentacion" / "01_recoleccion"
ANA = RAIZ / "02_documentacion" / "02_analisis"
CANONICO = REC / "datos" / "procesados" / "incidencias_canonico.csv"
SHA_CANONICO = "eea9ec568e26eea03e13b4196de1eb6905a87e72659c52100ce63e733e9dbacd"
LIMITE = REC / "datos" / "cartografia" / "limite_distrito.geojson"
SIDPOL = REC / "datos" / "procesados" / "sidpol_sjm_mensual.csv"
FIG = ANA / "figuras"
DATOS = ANA / "datos"
FIG.mkdir(parents=True, exist_ok=True)
DATOS.mkdir(parents=True, exist_ok=True)


def rel(ruta: Path) -> str:
    """Ruta relativa a RAIZ con separador '/'."""
    return Path(ruta).resolve().relative_to(RAIZ).as_posix()


# --------------------------------------------------------------------------- constantes del proyecto
SEMILLA = 42
TURNOS = ["Mañana", "Tarde", "Noche"]
NIVELES = ["Bajo", "Medio", "Alto"]
COLOR_NIVEL = {"Bajo": "#DADAEB", "Medio": "#9E9AC8", "Alto": "#54278F"}
AZUL = "#1F4E79"
GRIS = "#8C8C8C"
COLOR_TURNO = {"Mañana": "#1F4E79", "Tarde": "#6BAED6", "Noche": "#3F007D"}
CRS_METRICO = "EPSG:32718"

# Periodos decididos en 01_calidad (evidencia en ese notebook)
FECHA_INICIO_DATOS = "2026-05-16"
FIN_ARRANQUE = "2026-05-21"          # 16–21 may: puesta en marcha -> solo historial para rezagos
INICIO_ESTABLE = "2026-05-22"
FIN_ESTABLE = "2026-06-08"           # último día completo (09 y 10 jun censurados)
FECHAS_CENSURADAS = ["2026-06-09", "2026-06-10"]
TOLERANCIA_BORDE_M = 150.0

# Partición temporal (justificada en 04_preparacion_modelado)
PARTICION = {
    "train": ("2026-05-22", "2026-05-31"),
    "valid": ("2026-06-01", "2026-06-04"),
    "test": ("2026-06-05", "2026-06-08"),
}
# Feriados nacionales del Perú dentro del periodo (Ley N.° 31788: 7 de junio, Día de la Bandera)
FERIADOS = {"2026-06-07"}

FUENTE_CCO = ("Fuente: elaboración propia a partir del extracto de incidencias del CCO "
              "(Municipalidad Distrital de San Juan de Miraflores, 2026).")
FUENTE_CCO_LIMITE = ("Fuente: elaboración propia a partir del extracto de incidencias del CCO "
                     "(Municipalidad Distrital de San Juan de Miraflores, 2026) y del límite distrital (INEI, 2026).")
FUENTE_SIDPOL = ("Fuente: elaboración propia a partir de las denuncias policiales SIDPOL "
                 "(Ministerio del Interior, 2026).")


# --------------------------------------------------------------------------- formato numérico (coma decimal, espacio de miles)
def fmt(x: float, dec: int = 0) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    s = f"{x:,.{dec}f}"
    return s.replace(",", " ").replace(".", ",").replace(" ", " ")


def pct(x: float, dec: int = 1) -> str:
    return f"{fmt(x, dec)} %"


def eje_es(ax, eje: str = "y", dec: int = 0) -> None:
    f = FuncFormatter(lambda v, _: fmt(v, dec))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def configurar_estilo() -> None:
    plt.rcParams.update({
        "figure.dpi": 100, "savefig.dpi": 160, "font.size": 9, "axes.titlesize": 10,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.alpha": 0.25, "axes.axisbelow": True,
    })


def guardar_figura(fig, archivo: str, numero: int, hallazgo: str, nota: str = FUENTE_CCO) -> Path:
    """Título 'Figura N. <hallazgo>', nota de fuente al pie y PNG a 160 dpi en figuras/."""
    fig.suptitle(f"Figura {numero}. {hallazgo}", x=0.01, ha="left", fontsize=10.5, fontweight="bold")
    fig.text(0.01, 0.008, nota, fontsize=7, ha="left", va="bottom", color="#444444", wrap=True)
    alto_in = fig.get_size_inches()[1]
    por_linea = fig.get_size_inches()[0] * 19
    lineas = sum(max(1, int(np.ceil(len(l) / por_linea))) for l in nota.split("\n"))
    abajo = min(0.25, (0.1 + 0.13 * lineas) / alto_in)
    fig.tight_layout(rect=[0, abajo, 1, 0.94])
    ruta = FIG / archivo
    fig.savefig(ruta, dpi=160)
    plt.show()
    plt.close(fig)
    return ruta


# --------------------------------------------------------------------------- datos
def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_canonico() -> pd.DataFrame:
    assert sha256(CANONICO) == SHA_CANONICO, "El CSV canónico no coincide con el sha256 del handoff de la Fase 1"
    return pd.read_csv(CANONICO, dtype={"id_incidencia": str, "ubigeo_inei": str, "zona": str, "sector": str})


def cargar_limpias() -> pd.DataFrame:
    return pd.read_csv(DATOS / "incidencias_limpias.csv",
                       dtype={"id_incidencia": str, "ubigeo_inei": str, "zona": str, "sector": str,
                              "id_microzona": str})


# --------------------------------------------------------------------------- espacial
_A_METRICO = Transformer.from_crs("EPSG:4326", CRS_METRICO, always_xy=True)
_A_WGS84 = Transformer.from_crs(CRS_METRICO, "EPSG:4326", always_xy=True)


def proyectar(lon, lat):
    return _A_METRICO.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))


def limite_wgs84():
    g = json.loads(LIMITE.read_text(encoding="utf-8"))
    return shape(g["features"][0]["geometry"])


def limite_metrico():
    return transform(_A_METRICO.transform, limite_wgs84())


def a_wgs84(geom):
    return transform(_A_WGS84.transform, geom)


def origen_grilla(tamano_m: float, poligono=None) -> tuple[float, float]:
    """Origen (x0, y0) = esquina inferior izquierda del límite, redondeada hacia abajo al múltiplo del tamaño."""
    poligono = poligono if poligono is not None else limite_metrico()
    minx, miny, _, _ = poligono.bounds
    return float(np.floor(minx / tamano_m) * tamano_m), float(np.floor(miny / tamano_m) * tamano_m)


def celda_de(x, y, tamano_m: float, origen: tuple[float, float]):
    col = np.floor((np.asarray(x) - origen[0]) / tamano_m).astype(int)
    fila = np.floor((np.asarray(y) - origen[1]) / tamano_m).astype(int)
    return col, fila


def celdas_que_intersecan(tamano_m: float, origen, poligono) -> pd.DataFrame:
    minx, miny, maxx, maxy = poligono.bounds
    ncol = int(np.ceil((maxx - origen[0]) / tamano_m))
    nfil = int(np.ceil((maxy - origen[1]) / tamano_m))
    filas = []
    for c in range(ncol):
        for f in range(nfil):
            b = box(origen[0] + c * tamano_m, origen[1] + f * tamano_m,
                    origen[0] + (c + 1) * tamano_m, origen[1] + (f + 1) * tamano_m)
            if b.intersects(poligono):
                filas.append({"col": c, "fila": f, "geom": b,
                              "frac_dentro": b.intersection(poligono).area / b.area})
    return pd.DataFrame(filas)


def distancia_al_limite(x, y, poligono) -> np.ndarray:
    return np.array([0.0 if poligono.contains(Point(a, b)) else poligono.distance(Point(a, b)) for a, b in zip(x, y)])


# --------------------------------------------------------------------------- partición
def particion_de(fecha: pd.Series) -> pd.Series:
    fecha = pd.Series(fecha).astype(str)
    salida = pd.Series(pd.NA, index=fecha.index, dtype="object")
    for nombre, (ini, fin) in PARTICION.items():
        salida[(fecha >= ini) & (fecha <= fin)] = nombre
    return salida


def fechas_rango(ini: str, fin: str) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(ini, fin, freq="D")]
