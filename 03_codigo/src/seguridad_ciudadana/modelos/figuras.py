"""Figuras PNG de evaluación para reportes/ (paleta del design system, coma decimal)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from ..dominio import NIVELES, NOMBRE_LEGIBLE_MODELO  # noqa: E402
from ..formato import fmt  # noqa: E402

PRIMARIO = "#1F4E79"
SECUNDARIO = "#6A8EAE"
TERCIARIO = "#B7C9D9"
TEXTO_SECUNDARIO = "#5A5A5A"
COLORES_MODELO = {
    "persistencia": "#B7C9D9",
    "regresion_logistica": "#6A8EAE",
    "random_forest": "#1F4E79",
    "gradient_boosting": "#54278F",
}
DPI = 150


def _pie(fig, fuente: str) -> None:
    fig.text(0.01, 0.01, f"Fuente: elaboración propia a partir del {fuente}.", fontsize=7, color=TEXTO_SECUNDARIO)


def _coma(dec: int) -> FuncFormatter:
    return FuncFormatter(lambda v, _: fmt(v, dec))


def matrices_confusion(metricas_por_modelo: dict[str, dict[str, Any]], titulo: str, ruta: Path, fuente: str) -> Path:
    nombres = list(metricas_por_modelo)
    fig, ejes = plt.subplots(1, len(nombres), figsize=(3.3 * len(nombres), 3.6))
    ejes = np.atleast_1d(ejes)
    for eje, nombre in zip(ejes, nombres):
        m = metricas_por_modelo[nombre]
        cm = np.array(m["matriz_confusion"])
        eje.imshow(cm, cmap="Purples")
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                color = "white" if cm[i, j] > cm.max() * 0.6 else "#1A1A1A"
                eje.text(j, i, fmt(cm[i, j]), ha="center", va="center", color=color, fontsize=9)
        eje.set_xticks(range(len(NIVELES)), NIVELES)
        eje.set_yticks(range(len(NIVELES)), NIVELES)
        eje.set_xlabel("Nivel estimado")
        eje.set_ylabel("Nivel observado")
        eje.set_title(f"{NOMBRE_LEGIBLE_MODELO.get(nombre, nombre)}\nMacro F1 = {fmt(m['macro_f1'], 3)}", fontsize=9)
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    _pie(fig, fuente)
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)
    return ruta


def f1_por_dia(bootstraps: dict[str, dict[str, Any]], titulo: str, ruta: Path, fuente: str) -> Path:
    """Macro F1 por día con su IC bootstrap (filas dentro del día) para cada modelo."""
    fig, eje = plt.subplots(figsize=(8, 3.8))
    nombres = list(bootstraps)
    dias = sorted(next(iter(bootstraps.values()))["por_dia_filas"])
    ancho = 0.8 / len(nombres)
    for k, nombre in enumerate(nombres):
        datos = bootstraps[nombre]["por_dia_filas"]
        x = np.arange(len(dias)) + (k - (len(nombres) - 1) / 2) * ancho
        y = np.array([datos[d]["macro_f1"] for d in dias])
        err = np.array([[y[i] - datos[d]["ic_inf"], datos[d]["ic_sup"] - y[i]] for i, d in enumerate(dias)]).T
        eje.bar(x, y, ancho, color=COLORES_MODELO.get(nombre, PRIMARIO), label=NOMBRE_LEGIBLE_MODELO.get(nombre, nombre))
        eje.errorbar(x, y, yerr=err, fmt="none", ecolor="#1A1A1A", elinewidth=0.8, capsize=2)
    eje.set_xticks(range(len(dias)), dias)
    eje.set_ylabel("Macro F1")
    eje.set_ylim(0, 1)
    eje.yaxis.set_major_formatter(_coma(1))
    eje.legend(fontsize=7, ncol=4, loc="upper left", frameon=False)
    eje.spines[["top", "right"]].set_visible(False)
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    _pie(fig, fuente)
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)
    return ruta


def importancia(importancia_modelo: dict[str, Any], titulo: str, ruta: Path, fuente: str) -> Path:
    grupos = importancia_modelo["por_grupo"]
    variables = importancia_modelo["por_variable"]
    fig, (e1, e2) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1, 1.6]})
    nombres = sorted(grupos, key=lambda g: grupos[g]["media"])
    e1.barh(nombres, [grupos[g]["media"] for g in nombres], xerr=[grupos[g]["desv"] for g in nombres], color=PRIMARIO)
    e1.set_xlabel("Caída del Macro F1 al permutar el grupo")
    e1.xaxis.set_major_formatter(_coma(2))
    orden = sorted(variables, key=lambda v: variables[v]["media"])
    e2.barh(orden, [variables[v]["media"] for v in orden], color=SECUNDARIO)
    e2.set_xlabel("Caída del Macro F1 al permutar la variable")
    e2.xaxis.set_major_formatter(_coma(3))
    e2.tick_params(axis="y", labelsize=7)
    for e in (e1, e2):
        e.spines[["top", "right"]].set_visible(False)
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    _pie(fig, fuente)
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)
    return ruta
