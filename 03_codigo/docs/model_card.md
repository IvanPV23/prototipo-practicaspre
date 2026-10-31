# Ficha del modelo (model card)

## Resumen

| Campo | Valor |
|---|---|
| Tarea | Clasificar el **nivel de incidencias registradas** por microzona (celda de 500 m), fecha y turno: Bajo (0), Medio (1), Alto (≥ 2) |
| Modelo vigente | **Regresión logística** multinomial con `class_weight="balanced"`, C = 10, one-hot de turno, día de la semana y nivel previo, y escalado estándar, **calibrada con validación** (temperatura 1,65, sesgos por clase y desplazamientos de decisión 1,4 / 1,6 para Medio / Alto; ADR 0007) |
| Criterio de selección | Mejor Macro F1 en validación (1–4 jun, calculado dejando un día fuera tras la calibración) entre regresión logística, Random Forest y Gradient Boosting |
| Versión | La registra `modelo.version` (hash de datos, config y parámetros, incluida la calibración); el artefacto está en `modelos/regresion_logistica-1.1.0_<hash>.joblib` |
| Entrenamiento | 2 580 filas (86 microzonas × 10 días × 3 turnos, 22–31 may), semilla 42 |
| Variables | 17: historial de la microzona (9), vecinos (2), calendario (3: día de la semana, fin de semana, turno) y contexto del distrito (3). `feriado` se excluye porque es constante en train y valid. Todas usan solo datos anteriores a la fecha objetivo |
| Salida | Probabilidades por nivel, resumidas en R = 0·p(Bajo) + 0,5·p(Medio) + 1·p(Alto) para la prioridad P |

## Uso previsto y fuera de alcance

- **Previsto:** apoyar al operador del CCO para ordenar en qué microzonas reforzar la presencia preventiva en el próximo turno, junto con la gravedad (G), la frecuencia reciente (F) y su propio criterio.
- **Fuera de alcance:** predecir delitos o dónde ocurrirá un hecho concreto, calificar zonas como "peligrosas" o "seguras", tomar decisiones automáticas, evaluar personas o hacer seguimiento en tiempo real.

## Desempeño (Macro F1, v1.1.0 calibrada)

| Modelo | Macro F1 valid* | Macro F1 test | IC 95 % test (bootstrap por días) | % Alto predicho en test |
|---|---|---|---|---|
| Persistencia (nivel del mismo turno del día anterior) | 0,439 | 0,432 | [0,416; 0,452] | 12,5 % |
| **Regresión logística (vigente)** | **0,480** | 0,435 | [0,406; 0,456] | 22,5 % |
| Random Forest (max_depth 8, min_samples_leaf 5, 300 árboles) | 0,477 | 0,448 | [0,422; 0,466] | 11,1 % |
| Gradient Boosting (100 árboles, lr 0,05, profundidad 3) | 0,475 | 0,441 | [0,416; 0,465] | 11,2 % |

\* Modelos de ML: validación calculada dejando un día fuera (cada día con un calibrador ajustado en los otros tres). Proporción de Alto observada: 10,1 % en validación y 13,8 % en prueba.

**Sin calibrar (v1.0.0), como referencia:** regresión logística 0,475 / 0,418 con un 34,3 % de Alto predicho en prueba; Random Forest 0,457 / 0,451; Gradient Boosting 0,463 / 0,412. Las cifras completas están en `reportes/metricas_modelos.json` (`sin_calibrar`).

Por clase, regresión logística calibrada en **prueba** (soporte 686 / 204 / 142):

| Clase | Precisión | Recall | F1 |
|---|---|---|---|
| Bajo | 0,806 | 0,574 | 0,671 |
| Medio | 0,228 | 0,348 | 0,276 |
| Alto | 0,289 | 0,472 | 0,358 |

Macro F1 por día en prueba (regresión logística): 5 jun 0,459 · 6 jun 0,399 · 7 jun 0,443 · 8 jun 0,412. Por turno: Mañana 0,415 · Tarde 0,377 · Noche 0,454. Las cifras de todos los modelos, con IC por día, están en `reportes/metricas_por_dia_turno.json` y en la página Metodología. Las matrices de confusión están en `reportes/figuras/`.

### Calibración (ADR 0007)

`class_weight="balanced"` hacía que el modelo "sobreavisara": marcaba Alto en el 20 % de validación y en el 34 % de prueba, con días de hasta 44 %, frente al 10–14 % observado. Eso diluía el ranking y contradecía el principio de no estigmatizar. Por eso se añadió un paso posterior, ajustado **solo con validación**:

1. **Probabilidades:** escalado de temperatura con un sesgo por clase. La probabilidad media de cada nivel coincide con su frecuencia, y en prueba p(Alto) promedia 0,14 frente al 13,8 % observado. Estas probabilidades alimentan R.
2. **Decisión:** desplazamientos sobre las log-probabilidades de Medio y Alto, elegidos por Macro F1.

Resultado en prueba: Alto predicho baja del 34,3 % al 22,5 %, y el Macro F1 sube de 0,418 a 0,435. Todavía sobrestima Alto en prueba (22,5 % frente a 13,8 %): en validación la proporción quedó en 13,1 % (observado 10,1 %), y la prueba incluye fin de semana y feriado, que validación no tiene.

**Cautela metodológica:** la calibración se decidió sin mirar prueba, pero la prueba ya se había leído una vez con v1.0.0. Las cifras de prueba de v1.1.0 son, por tanto, una segunda lectura del mismo periodo.

### Lectura

- El modelo vigente supera a la persistencia en validación (+0,041) y, por poco, en prueba (+0,003), con intervalos solapados. En validación la diferencia entre los tres modelos de ML es mínima (0,480 / 0,477 / 0,475).
- **H1 se sostiene de forma débil:** en prueba, Random Forest (0,448) supera a la regresión logística (0,435) y a la persistencia (0,432), con intervalos solapados y solo cuatro días.
- **HE1 se sostiene:** al permutar todo el bloque de historial, el Macro F1 en validación cae 0,142, frente a 0,044 del calendario, 0,036 de los vecinos y 0,023 del contexto. El historial supera al calendario en los tres modelos de ML.
- El **nivel estimado no debe leerse como un pronóstico puntual**: es una señal para ordenar, junto con G y F.

## Desplazamiento de distribución

La proporción de Alto sube de 9,4 % (train) a 10,1 % (valid) y 13,8 % (test), y el registro diario crece en junio, sobre todo por las cámaras. La validación (lunes a jueves) **no tiene fines de semana**; la prueba incluye viernes a lunes y el feriado del 7 de junio. Esto explica en parte la caída de validación a prueba de los modelos más ajustados (regresión logística y Gradient Boosting). Las variables de contexto del distrito (`distrito_lag1`, `distrito_media7`) intentan absorber el cambio de cobertura, pero su importancia es pequeña.

## Datos

Ver `docs/data_card.md`. El objetivo mide el **registro** del CCO, que depende de dónde hay cámaras y patrullaje, no el delito.

## Consideraciones éticas

- **Estigmatización:** un nivel Alto describe registros recientes, no la condición de un barrio. La interfaz usa una paleta ordinal púrpura, evita el rojo y repite el aviso estándar en Ranking y Mapa.
- **Bucle de retroalimentación:** si se patrulla más donde el modelo indica, se registrará más ahí. Hay que revisar periódicamente la distribución espacial y los canales de reporte.
- **Decisión humana:** el sistema sugiere y el operador decide; los pesos son visibles y ajustables.
- **Transparencia:** cada prioridad se descompone en R, G y F con sus pesos, y la ficha de detalle muestra las probabilidades del modelo.

## Limitaciones

Periodo de 18 días utilizables, alta varianza entre días, desplazamiento de distribución, gravedad definida por supuesto, sin datos de exposición, y una fecha operativa (9 jun) que no puede evaluarse porque la fuente está censurada. El modelo no se reentrenó con train+valid. Si se reentrena con más datos, hay que repetir el protocolo (ADR 0006).

## Mantenimiento

Para incorporar un extracto nuevo del CCO: regenerar el canónico (Fase 1), actualizar el sha256 en `handoff_fase1.json`, revisar la partición en `config.yaml` y ejecutar `python -m seguridad_ciudadana todo`. Cada ejecución registra una versión trazable del modelo.
