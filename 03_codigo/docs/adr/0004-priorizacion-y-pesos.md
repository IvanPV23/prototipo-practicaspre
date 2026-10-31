# ADR 0004 — Fórmula de priorización y pesos por defecto

- **Estado:** aceptada (2026-10-31)
- **Contexto:** el alcance (§11.4) define P = w1·R + w2·G + w3·F con componentes en [0, 1] y pesos ajustables. La Fase 2 sugiere usar `gravedad_media7_celda` y `suma7_celda` para G y F.
- **Decisión:**
  - **R = 0·p(Bajo) + 0,5·p(Medio) + 1·p(Alto)**: el valor esperado del nivel ordinal, normalizado. Se prefiere a usar solo p(Alto) porque conserva el orden de las tres clases y no ignora la masa de Medio.
  - **G = (gravedad media de d−7…d−1 − 1)/4**, recortada a [0, 1], y 0 si la microzona no tuvo registros en esa ventana. La gravedad por tipo (1–5) es un supuesto de diseño de la Fase 2 (`gravedad_por_tipo.csv`) que no usa la columna NIVEL de la fuente ([POST]). Solo usa datos anteriores a la fecha objetivo.
  - **F = suma7_celda / máximo de suma7_celda en entrenamiento (61)**, recortada a 1. Se usa el máximo de entrenamiento para que la escala no dependa del periodo evaluado. Como la cobertura crece hacia junio, algunas celdas se saturan en 1, y eso se documenta.
  - **Pesos por defecto: w1 = 0,5, w2 = 0,3, w3 = 0,2.** R es la única estimación hacia adelante y es lo que el sistema aporta, por eso recibe la mitad. G añade información que el modelo no tiene como objetivo (el modelo estima volumen, no gravedad), así que recibe el segundo peso. F se solapa con R, porque el modelo ya usa `suma7_celda`, `lag1` y otras variables de historial, y un peso alto la contaría dos veces; por eso recibe el menor. Los pesos se normalizan siempre para sumar 1 y se ajustan en la barra lateral ("Restablecer pesos" vuelve a estos valores).
  - Desempate del ranking: P descendente, luego R descendente y luego el id de la microzona.
- **Consecuencias:** la prioridad siempre se puede descomponer en sus aportes w·componente, que la ficha muestra. R, G y F se calculan una vez en `priorizar`; la interfaz solo recombina, lo que permite responder en menos de 2 s.
