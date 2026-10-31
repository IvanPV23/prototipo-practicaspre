"""Gráficos Plotly reutilizables con los colores de los tokens."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from tema import COMPONENTE_COLOR, COMPONENTE_NOMBRE, NIVEL_COLOR

from seguridad_ciudadana.formato import fmt

ALTO_FILA_PX = 26
ALTO_MIN_PX = 220


def barra_composicion(df: pd.DataFrame, titulo: str) -> go.Figure:
    """Barra apilada horizontal w1·R + w2·G + w3·F por microzona (mismos tres colores en toda la app)."""
    etiquetas = [f"#{p} {m}" for p, m in zip(df.posicion, df.microzona_id)]
    fig = go.Figure()
    for comp, col in (("R", "aporte_r"), ("G", "aporte_g"), ("F", "aporte_f")):
        fig.add_bar(
            y=etiquetas, x=df[col], orientation="h", name=COMPONENTE_NOMBRE[comp],
            marker_color=COMPONENTE_COLOR[comp],
            hovertemplate="%{y}<br>" + COMPONENTE_NOMBRE[comp] + ": %{x:.3f}<extra></extra>",
        )  # fmt: skip
    fig.add_scatter(
        y=etiquetas, x=df.p, mode="text", text=[fmt(v, 2) for v in df.p], textposition="middle right",
        showlegend=False, hoverinfo="skip",
    )  # fmt: skip
    fig.update_layout(
        barmode="stack", title=titulo, xaxis_title="Prioridad sugerida P (0–1)", xaxis_range=[0, 1.08],
        yaxis={"autorange": "reversed"}, height=max(ALTO_MIN_PX, ALTO_FILA_PX * len(df) + 120),
        legend={"orientation": "h", "y": -0.25 if len(df) <= 10 else -0.08},
    )  # fmt: skip
    return fig


def barras_componentes(componentes: list[dict]) -> go.Figure:
    fig = go.Figure()
    for c in componentes:
        fig.add_bar(
            y=["P"], x=[c["aporte"]], orientation="h", name=f"{c['componente']} · {c['nombre']}",
            marker_color=COMPONENTE_COLOR[c["componente"]],
            hovertemplate=f"{c['componente']}: {fmt(c['valor'], 2)} × {fmt(c['peso'], 2)} = {fmt(c['aporte'], 3)}<extra></extra>",
        )  # fmt: skip
    fig.update_layout(barmode="stack", height=190, xaxis_range=[0, 1], margin={"t": 56, "b": 40},
                      xaxis_title="Aporte a la prioridad P", yaxis_visible=False,
                      legend={"orientation": "h", "x": 0, "y": 1.45})  # fmt: skip
    return fig


def barras_probabilidad(probabilidades: dict[str, float]) -> go.Figure:
    niveles = list(probabilidades)
    fig = go.Figure(
        go.Bar(
            x=niveles, y=[probabilidades[n] for n in niveles], marker_color=[NIVEL_COLOR[n] for n in niveles],
            marker_line_color="#5A5A5A", marker_line_width=0.5, text=[fmt(probabilidades[n], 2) for n in niveles],
            textposition="outside",
        )
    )  # fmt: skip
    fig.update_layout(height=240, yaxis_range=[0, 1.15], title="Probabilidades del modelo por nivel",
                      margin={"t": 48, "b": 32})  # fmt: skip
    return fig


def grafico(fig: go.Figure, key: str) -> None:
    """Muestra la figura con la plantilla del design system (explícita: Streamlit no respeta el default de Plotly)."""
    fig.update_layout(template=pio.templates["seguridad"])
    st.plotly_chart(fig, theme=None, key=key)
