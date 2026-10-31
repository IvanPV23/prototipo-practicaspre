"""Tokens del design system (§4) y plantilla única de Plotly."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

COLOR = {
    "primario": "#1F4E79",
    "texto": "#1A1A1A",
    "texto_secundario": "#5A5A5A",
    "fondo": "#FFFFFF",
    "fondo_secundario": "#F3F5F8",
    "aviso_fondo": "#EAF2FB",
    "error": "#B3261E",
    "sin_datos": "#D9D9D9",
}
NIVEL_COLOR = {"Bajo": "#DADAEB", "Medio": "#9E9AC8", "Alto": "#54278F"}
NIVEL_TEXTO = {"Bajo": "#1A1A1A", "Medio": "#1A1A1A", "Alto": "#FFFFFF"}
COMPONENTE_COLOR = {"R": "#1F4E79", "G": "#6A8EAE", "F": "#B7C9D9"}
COMPONENTE_NOMBRE = {"R": "R · nivel estimado", "G": "G · gravedad histórica", "F": "F · frecuencia reciente"}
PARTICION_COLOR = {
    "Arranque (solo historial)": "#D9D9D9",
    "Entrenamiento": "#B7C9D9",
    "Validación": "#6A8EAE",
    "Prueba": "#1F4E79",
    "Censurado (no usado)": "#EFEFEF",
}
RADIO_PX = 6
OPACIDAD_MICROZONA = 0.55

AVISO = (
    "Los niveles reflejan incidencias registradas por el CCO en el periodo analizado, no delitos ni una condición "
    "permanente de la zona. Úselos como apoyo; la decisión final es del operador."
)


def fuente_pie(cita: str) -> str:
    return f"Fuente: elaboración propia a partir del {cita}."


def registrar_plantilla() -> None:
    """Plantilla 'seguridad': colores de los tokens, coma decimal y espacio de miles (separators=', ')."""
    plantilla = go.layout.Template(
        layout=go.Layout(
            font={"family": "sans-serif", "color": COLOR["texto"], "size": 13},
            colorway=[COLOR["primario"], "#6A8EAE", "#B7C9D9", "#54278F", "#9E9AC8"],
            paper_bgcolor=COLOR["fondo"],
            plot_bgcolor=COLOR["fondo"],
            separators=", ",
            margin={"l": 16, "r": 16, "t": 56, "b": 48},
            xaxis={"gridcolor": "#EDEDED", "zeroline": False, "automargin": True, "title": {"standoff": 8}},
            yaxis={"gridcolor": "#EDEDED", "zeroline": False, "automargin": True, "title": {"standoff": 8}},
            title={"font": {"size": 15}},
            legend={"orientation": "h", "y": -0.2},
        )
    )
    pio.templates["seguridad"] = plantilla
    pio.templates.default = "seguridad"


CSS = f"""
<style>
.aviso {{ background: {COLOR["aviso_fondo"]}; border-radius: {RADIO_PX}px; padding: 12px 16px; margin: 8px 0 16px 0;
         color: {COLOR["texto"]}; border-left: 4px solid {COLOR["primario"]}; }}
.tarjeta {{ background: {COLOR["fondo_secundario"]}; border-radius: {RADIO_PX}px; padding: 16px; height: 100%; }}
.tarjeta h4 {{ margin: 0 0 8px 0; color: {COLOR["primario"]}; }}
.nivel {{ border-radius: 4px; padding: 2px 8px; font-weight: 600; display: inline-block; }}
.leyenda span.caja {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin: 0 6px -2px 12px;
                      border: 1px solid #8C8C8C; }}
.nota {{ color: {COLOR["texto_secundario"]}; font-size: 0.85rem; }}
</style>
"""
