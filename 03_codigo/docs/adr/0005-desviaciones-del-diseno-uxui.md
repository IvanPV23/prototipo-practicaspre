# ADR 0005 — Desviaciones del diseño UX/UI

- **Estado:** aceptada (2026-10-31)
- **Contexto:** el diseño (§3–§4) es el acuerdo de interfaz. Algunas piezas no se pueden hacer literalmente con los componentes de Streamlit.
- **Decisiones (solución más cercana):**
  1. **Barra "Composición de P" dentro de la tabla.** `st.dataframe` no admite barras apiladas por celda. La tabla del Ranking muestra R, G, F y P como números, y justo debajo hay un gráfico Plotly de barras apiladas horizontales con las mismas filas y el mismo orden, en los tres colores de §4.3. Al seleccionar una fila de la tabla aparece el botón "Ver detalle".
  2. **Clic en el mapa.** `streamlit-folium` devuelve la celda clicada pero no puede navegar por sí mismo. El clic fija la microzona seleccionada y muestra "Ver detalle", tal como prevé §3.2 en la alternativa "o fija la microzona seleccionada y ofrece Ver detalle".
  3. **Interruptor de capa de puntos.** Se usa un `st.toggle` desactivado por defecto en lugar del control de capas de Leaflet. Muestra las incidencias de los 7 días previos a la fecha.
  4. **Formato numérico.** Las tablas muestran los decimales como texto con coma (las columnas numéricas de `st.dataframe` usan punto). Plotly usa `separators=", "`.
  5. **Nombres de página en la barra de navegación.** Streamlit toma el nombre del archivo, que va sin tildes por portabilidad ("Metodologia", "Detalle de microzona"). Los títulos dentro de cada página sí llevan tildes.
  6. **Fecha y turno por defecto.** La fecha es el 9 jun (operativa; ver ADR 0003) y el turno, "Mañana", que es el primer turno de esa fecha y por tanto el siguiente turno tras el corte.
  7. **Pie de la barra lateral.** Se muestra la fecha del último día completo (8 jun) como "Datos hasta". El corte de la fuente (10 jun) se explica en Inicio y en Metodología.
  8. **Ficha en fechas de demostración.** Se añade un recuadro con el nivel observado, para que el operador vea en qué acertó o falló el modelo. No aparece en la fecha operativa.
- **Consecuencias:** las siete pantallas, los estados de §3.7, los tokens de §4.1 a §4.3, el microcopy de §4.6 y el aviso de uso responsable (visible en Ranking y Mapa) se implementan sin otras desviaciones.
