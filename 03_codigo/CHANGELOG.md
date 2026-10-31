# Cambios

## [1.1.0] — 2026-10-31

### Cambiado
- Calibración posterior de los modelos de ML con validación (ADR 0007): temperatura + sesgo por clase y desplazamientos de decisión para Medio y Alto. La regresión logística vigente pasa de marcar Alto en el 34,3 % de prueba a 22,5 % (observado 13,8 %); Macro F1 en prueba 0,418 → 0,435.
- El Macro F1 de validación de los modelos calibrados se calcula dejando un día fuera; la selección usa esa cifra.
- `predecir` toma el nivel de `predict` (incluye la regla de decisión calibrada) y guarda probabilidades calibradas, que alimentan R.

### Añadido
- `modelos/calibracion.py` (`Calibrador`, `ModeloCalibrado`), sección `calibracion` en `config.yaml`, `tests/test_calibracion.py`.
- Proporción predicha y observada por clase en las métricas; métricas `sin_calibrar` en `reportes/metricas_modelos.json`.

## [1.0.0] — 2026-10-31

Primera versión del sistema integrado (Fase 3 de /practicaspre).

### Añadido
- Paquete `seguridad_ciudadana` por capas, con la CLI `init-db`, `ingestar`, `construir`, `entrenar`, `predecir`, `priorizar` y `todo`.
- Base SQLite versionada (12 tablas, claves foráneas y triggers de recursos).
- Reconstrucción desde el CSV canónico de las microzonas (500 m), la tabla de modelado y las 18 variables de la Fase 2, verificada fila a fila.
- Línea base de persistencia, regresión logística, Random Forest y Gradient Boosting, con selección por validación, evaluación única en prueba, métricas por día y turno, IC bootstrap e importancia por permutación por grupos.
- Registro de modelos con versión, sha256 del dato, config y métricas; artefactos joblib.
- Priorización P = w1·R + w2·G + w3·F con pesos por defecto 0,5 / 0,3 / 0,2.
- App Streamlit con Inicio y 6 páginas (Ranking, Mapa, Detalle, Tablero, Recursos, Metodología).
- Tests (pytest + AppTest), ruff, documentación y 6 ADRs.
