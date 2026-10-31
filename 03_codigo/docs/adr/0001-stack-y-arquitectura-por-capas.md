# ADR 0001 — Stack Python/Streamlit y arquitectura por capas

- **Estado:** aceptada (2026-10-31)
- **Contexto:** el alcance (§11.2) fija Python, Pandas, NumPy, scikit-learn, Joblib, Streamlit, Folium/PyDeck, Plotly y SQLite. Otro estudiante tiene que poder leer, ejecutar y extender el sistema en Windows 10 instalando solo con `pip`. El diseño UX/UI (§5) pide separar el lote fuera de línea de la consulta en línea, y que la interfaz no toque SQL.
- **Decisión:**
  - Python 3.10+, pandas/NumPy, scikit-learn 1.7 y joblib para el ML.
  - Shapely 2 y pyproj para la parte espacial. **No se usa GeoPandas**: no hace falta (solo se necesita la grilla, la distancia al límite y la reproyección) y así se evitan dependencias binarias en Windows. Es una desviación menor respecto del alcance, que mencionaba GeoPandas.
  - Streamlit multipágina, Folium con `streamlit-folium` para el mapa y Plotly para los gráficos. Matplotlib solo para los PNG de `reportes/`.
  - Paquete `seguridad_ciudadana` (layout `src/`) en capas: `servicios` → dominio (`ingesta`, `espacial`, `features`, `modelos`, `priorizacion`, `recursos`) → `db/repositorios` → SQLite. La app solo importa `servicios` (y utilidades puras de formato y dominio).
  - CLI `python -m seguridad_ciudadana <comando>` con pasos idempotentes y bitácora en `ejecucion_pipeline`.
  - Configuración en `config/config.yaml`; la ruta se puede cambiar con la variable `SEGURIDAD_CONFIG`.
  - No se incluye API REST (FastAPI): la app usa los servicios en el mismo proceso y no hay consumidores externos.
- **Consecuencias:** se puede probar cada capa por separado (pytest y `AppTest` de Streamlit). Para cambiar de distrito basta con cambiar la config y los datos. Streamlit vuelve a ejecutar los scripts en cada interacción; eso se compensa con `st.cache_data` y `st.cache_resource`.
