# ADR 0007 — Calibración posterior con validación

**Estado:** aceptada (v1.1.0, 2026-10-31)

## Contexto

Los modelos se entrenan con `class_weight="balanced"` (ADR 0006) para que el desbalance (~7,7 Bajo por cada Alto) no los lleve a predecir siempre Bajo. El efecto secundario es que inflan p(Medio) y p(Alto). En v1.0.0 la regresión logística vigente marcaba Alto en el 20,1 % de validación y en el 34,3 % de prueba (hasta 44 % en un día), frente a un 10,1 % y un 13,8 % observados. En la app, el 9 de junio por la mañana aparecían 36 de 86 microzonas en Alto.

Dos problemas:
- **Priorización diluida:** si casi la mitad está en Alto, el nivel deja de ordenar.
- **Estigmatización:** el diseño UX/UI pide no presentar zonas como más críticas de lo que muestran los registros.

## Decisión

Añadir un paso de calibración, ajustado **solo con validación** (`modelos/calibracion.py`, sección `calibracion` de `config.yaml`):

1. **Escalado de temperatura con sesgo por clase** (3 parámetros, máxima verosimilitud). Las probabilidades medias pasan a coincidir con las frecuencias observadas. Son las que se guardan en `prediccion` y alimentan R.
2. **Desplazamientos de decisión** para Medio y Alto sobre las log-probabilidades calibradas, en una rejilla de 0 a 3 con paso 0,1, elegidos por Macro F1. Si hay empate, gana el menor (el más conservador). Es la regla que fija el nivel mostrado.
3. **Selección honesta:** como la misma validación calibra y elige el modelo, el Macro F1 de validación de los modelos calibrados se calcula dejando un día fuera. Cada día se predice con un calibrador ajustado en los otros tres.
4. El artefacto guarda un `ModeloCalibrado` (envoltorio con `predict`/`predict_proba`), así que la predicción y la importancia por permutación lo usan sin cambios. Los parámetros de calibración quedan en `modelo.hiperparametros` y cambian la versión (`1.1.0+hash`).
5. Se conservan las métricas sin calibrar en `reportes/metricas_modelos.json` (`sin_calibrar`) para comparar.

## Alternativas descartadas

- **Quitar `class_weight`:** los modelos casi no predecirían Medio ni Alto, y el Macro F1 caería.
- **Solo corregir el prior** (multiplicar por la frecuencia de entrenamiento): alinea las probabilidades, pero la decisión por argmax casi no predice Medio (4 %) y el Macro F1 de validación baja a 0,417.
- **Topes fijos a la proporción de Alto:** serían arbitrarios; la rejilla por Macro F1 ya los deja en el orden de lo observado en validación.
- **Ajustar con prueba:** prohibido por el protocolo (ADR 0006).

## Consecuencias

| Regresión logística | v1.0.0 | v1.1.0 |
|---|---|---|
| Macro F1 validación | 0,475 (en la muestra) | 0,480 (dejando un día fuera) |
| Macro F1 prueba | 0,418 | 0,435 |
| % Alto predicho en prueba (observado 13,8 %) | 34,3 % | 22,5 % |
| p(Alto) media en prueba | 0,24 (aprox.) | 0,14 |

- Sigue habiendo sobrestimación en prueba (22,5 %), en parte por el desplazamiento de distribución: la prueba incluye fin de semana y feriado, que validación no tiene. Random Forest y Gradient Boosting calibrados predicen un 11 % de Alto en prueba, pero el criterio de selección (validación) mantiene la regresión logística, por un margen mínimo.
- **La prueba ya se había leído con v1.0.0.** La calibración se decidió sin mirarla, pero las cifras de prueba de v1.1.0 son una segunda lectura del mismo periodo y así se informan.
- El pipeline tarda unos 2 s más.
