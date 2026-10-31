"""Figuras nuevas del documento de la Parte I (v2): arquitectura del prototipo y partición temporal.

Uso (desde la raíz del proyecto): .venv/Scripts/python.exe 02_documentacion/04_entregable_parcial/generar_figuras.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = Path(__file__).resolve().parent / "figuras"
PRIMARIO, SECUNDARIO, TERCIARIO = "#1F4E79", "#6A8EAE", "#B7C9D9"
FONDO, TEXTO, GRIS = "#F3F5F8", "#1A1A1A", "#5A5A5A"
CELDAS_DISTRITO = 121  # celdas de 500 m que intersecan el límite (Fase 2)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def caja(ax, x, y, w, h, texto, color=FONDO, borde=PRIMARIO, tam=8.0, color_texto=TEXTO):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
                                fc=color, ec=borde, lw=1.1))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tam, color=color_texto)


def flecha(ax, a, b, color=GRIS):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11, color=color, lw=1.1))


def contenedor(ax, x, w, titulo):
    ax.add_patch(FancyBboxPatch((x, 0.05), w, 0.86, boxstyle="round,pad=0.006,rounding_size=0.015",
                                fc="white", ec=SECUNDARIO, lw=1, ls="--"))
    ax.text(x + w / 2, 0.955, titulo, ha="center", weight="bold", color=PRIMARIO, fontsize=10)


def arquitectura():
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.set_xlim(0, 1.01)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Fuentes
    ax.text(0.095, 0.955, "Fuentes abiertas", ha="center", weight="bold", color=PRIMARIO, fontsize=10)
    fuentes = [("Incidencias CCO\nMDSJM (PNDA)\n2 592 registros", 0.68),
               ("Límite distrital\nINEI (ubigeo 150133)", 0.48),
               ("SIDPOL MININTER\n(solo contexto)", 0.28)]
    for texto, y in fuentes:
        caja(ax, 0.005, y, 0.18, 0.14, texto)
        flecha(ax, (0.19, y + 0.07), (0.228, y + 0.07))

    # Pipeline por lotes
    contenedor(ax, 0.23, 0.36, "Pipeline por lotes (CLI)")
    ax.text(0.41, 0.885, "python -m seguridad_ciudadana todo", ha="center", color=GRIS, fontsize=7.5,
            family="DejaVu Sans Mono")
    pasos = ["1. Ingesta y limpieza\n(verificación sha256, límite, sin [POST])",
             "2. Microzonas: grilla de 500 m (86 activas)",
             "3. Tabla microzona × fecha × turno\ncon 17 variables sin fuga",
             "4. Entrenamiento (train) y selección (valid)",
             "5. Calibración con validación (v1.1.0)",
             "6. Predicción del nivel: Bajo / Medio / Alto",
             "7. Priorización P = w1·R + w2·G + w3·F"]
    y0, alto, sep = 0.77, 0.085, 0.104
    for i, paso in enumerate(pasos):
        y = y0 - i * sep
        caja(ax, 0.25, y, 0.32, alto, paso, color=TERCIARIO if i in (3, 4) else FONDO, tam=7.6)
        if i:
            flecha(ax, (0.41, y + sep - 0.001), (0.41, y + alto + 0.002))

    # Modelo y base de datos
    caja(ax, 0.625, 0.45, 0.13, 0.12, "Modelo vigente\n(.joblib versionado)", tam=7.6)
    caja(ax, 0.625, 0.13, 0.13, 0.23, "SQLite local\n12 tablas\n(incidencias, modelos,\npredicciones,\nprioridades,\nrecursos)",
         color=PRIMARIO, borde=PRIMARIO, color_texto="white", tam=7.4)
    flecha(ax, (0.575, 0.47), (0.622, 0.51), PRIMARIO)
    flecha(ax, (0.575, 0.245), (0.622, 0.245), PRIMARIO)

    # Aplicación web
    contenedor(ax, 0.785, 0.21, "Aplicación web local")
    caja(ax, 0.8, 0.66, 0.18, 0.2, "Páginas (Streamlit)\nInicio · Ranking · Mapa\nDetalle · Tablero\nRecursos · Metodología",
         tam=7.6)
    caja(ax, 0.8, 0.45, 0.18, 0.12, "Servicios\n(ranking, detalle, recursos)", tam=7.6)
    caja(ax, 0.8, 0.19, 0.18, 0.12, "Repositorios\n(único lugar con SQL)", tam=7.6)
    caja(ax, 0.8, 0.07, 0.18, 0.075, "Operador del CCO (decide)", color="white", tam=7.4)
    flecha(ax, (0.89, 0.655), (0.89, 0.573))
    flecha(ax, (0.89, 0.447), (0.89, 0.313))
    flecha(ax, (0.797, 0.51), (0.758, 0.51), PRIMARIO)
    flecha(ax, (0.797, 0.245), (0.758, 0.245), PRIMARIO)

    ax.text(0.5, 0.005, "La aplicación solo lee de la base y del modelo registrado; nunca entrena. "
            "Todo se ejecuta en una PC sin GPU.", ha="center", color=GRIS, fontsize=7.5)
    fig.savefig(SALIDA / "fig_arquitectura.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def particion():
    # Cobertura diaria publicada (incluye los 12 puntos que la limpieza excluye; no cambia la lectura)
    canonico = pd.read_csv(RAIZ / "02_documentacion/01_recoleccion/datos/procesados/incidencias_canonico.csv",
                           usecols=["fecha"])
    dias = pd.date_range("2026-05-16", "2026-06-10")
    conteo = canonico.fecha.value_counts().reindex(dias.strftime("%Y-%m-%d"), fill_value=0)

    def tramo(fecha):
        if fecha <= "2026-05-21":
            return "Arranque (solo historial)", "#D9D9D9"
        if fecha <= "2026-05-31":
            return "Entrenamiento (10 días)", TERCIARIO
        if fecha <= "2026-06-04":
            return "Validación (4 días)", SECUNDARIO
        if fecha <= "2026-06-08":
            return "Prueba (4 días)", PRIMARIO
        return "Excluido: incompleto (9–10 jun)", "#EFEFEF"

    fig, ax = plt.subplots(figsize=(10, 3.6))
    vistos = set()
    for i, (fecha, n) in enumerate(conteo.items()):
        etiqueta, color = tramo(fecha)
        excluido = color == "#EFEFEF"
        ax.bar(i, n, color=color, edgecolor="#9A9A9A" if excluido else color, hatch="//" if excluido else None,
               label=None if etiqueta in vistos else etiqueta, width=0.8)
        vistos.add(etiqueta)
    meses = {5: "may", 6: "jun"}
    ax.set_xticks(range(0, len(dias), 2))
    ax.set_xticklabels([f"{d.day} {meses[d.month]}" for d in dias[::2]], fontsize=8)
    ax.set_ylabel("Incidencias registradas por día")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#E5E5E5", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    ax.set_ylim(0, 230)
    fig.savefig(SALIDA / "fig_particion.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def concentracion():
    """Curva de concentración (HE2) con el criterio de la Fase 2: 22 may–4 jun y las 121 celdas de 500 m que
    intersecan el distrito, incluidas las que no tienen registros (metricas_espacial.json, he2.tv_500)."""
    limpias = pd.read_csv(RAIZ / "02_documentacion/02_analisis/datos/incidencias_limpias.csv",
                          usecols=["fecha", "id_microzona"])
    tramo = limpias[(limpias.fecha >= "2026-05-22") & (limpias.fecha <= "2026-06-04") & limpias.id_microzona.notna()]
    conteos = tramo.id_microzona.value_counts().to_numpy()
    conteos = np.sort(np.concatenate([conteos, np.zeros(CELDAS_DISTRITO - len(conteos))]))[::-1]
    x = [0] + [100 * (i + 1) / len(conteos) for i in range(len(conteos))]
    y = [0] + list(100 * conteos.cumsum() / conteos.sum())
    mitad = next(xi for xi, yi in zip(x, y) if yi >= 50)

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(x, y, color=PRIMARIO, lw=2.2, label="Incidencias registradas (22 may–4 jun)")
    ax.plot([0, 100], [0, 100], color=GRIS, lw=1, ls="--", label="Igualdad perfecta")
    ax.axhline(50, color="#C9C9C9", lw=0.8, ls=":")
    ax.axvline(mitad, color="#C9C9C9", lw=0.8, ls=":")
    ax.annotate(f"{mitad:.1f} % de las microzonas\nacumula el 50 % de los registros".replace(".", ","),
                xy=(mitad, 50), xytext=(48, 22), fontsize=8.5, color=TEXTO,
                arrowprops=dict(arrowstyle="-|>", color=GRIS, lw=0.9))
    ax.set_xlabel("Celdas de 500 m del distrito ordenadas de mayor a menor registro (% acumulado)")
    ax.set_ylabel("Incidencias registradas (% acumulado)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 102)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color="#EEEEEE", lw=0.6)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.savefig(SALIDA / "fig_concentracion.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return mitad


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    arquitectura()
    particion()
    print("50 % en", round(concentracion(), 1), "% de microzonas")
    print("OK", sorted(p.name for p in SALIDA.glob("*.png")))
