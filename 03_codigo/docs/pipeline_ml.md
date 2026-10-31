# Pipeline de datos → modelo → ranking

Cada paso es un comando de `python -m seguridad_ciudadana` y está implementado en `servicios/pipeline.py`. `todo` los ejecuta en orden.

## 1. `init-db`

Crea o actualiza el esquema (`db/schema.sql`, versión 1). Es idempotente.

## 2. `ingestar`

1. Calcula el sha256 del CSV canónico y lo compara con `handoff_fase1.json`. Si no coincide, **se detiene**.
2. Lee el CSV con los ids, el ubigeo, la zona y el sector como texto, y descarta las columnas [POST].
3. Proyecta a EPSG:32718, calcula la distancia al límite INEI (0 si el punto está dentro) y marca `excluida` cuando es mayor de 150 m (12 registros).
4. Marca el `periodo` (arranque 16–21 may, censurado 9–10 jun, estable el resto) y la celda (`mz_col`, `mz_fila`).
5. Une la gravedad 1–5 por (tipo, subtipo) y se detiene si algún par no la tiene.
6. Guarda la fuente, el catálogo de tipos y las 2 592 incidencias.

## 3. `construir`

1. Arma las celdas de 500 m que intersecan el límite (121). Son activas las que tienen al menos una incidencia limpia en train (86).
2. Historia = incidencias limpias hasta el 8 de junio (sin los días censurados).
3. Para cada microzona activa, cada fecha del 22 may al 8 jun **y la fecha operativa del 9 jun**, y cada turno, calcula las 18 variables con datos de fechas anteriores a d (`features/tabla.py`).
4. b = mediana de los conteos > 0 de train (= 1). El nivel es Bajo con 0, Medio con 1 y Alto con 2 o más. `nivel_lag1_turno` aplica la misma regla a `lag1_turno`.
5. Guarda las observaciones (4 644 con objetivo y 258 operativas) y las variables en formato largo.
6. Compara con el handoff (limpias, activas, filas, distribución, b, persistencia) y escribe `reportes/verificacion_construccion.json`.

## 4. `entrenar`

Protocolo detallado en el ADR 0006.

1. Arma X con las 17 variables (sin `feriado`) e imputa `lag7_turno` con `media7_turno` de la misma fila.
2. Búsqueda en grilla por modelo: ajusta con train y puntúa en valid (Macro F1).
3. **Calibración con valid** (ADR 0007, si `calibracion.activa`): para cada modelo de ML ajusta temperatura y sesgo por clase (las probabilidades medias coinciden con las frecuencias) y desplazamientos de decisión para Medio y Alto (rejilla por Macro F1). Envuelve el estimador en `ModeloCalibrado`.
4. Calcula las métricas de validación de los cuatro modelos, la persistencia incluida. Las de los modelos calibrados salen de la predicción dejando un día fuera.
5. **Selección:** se queda con el de mayor Macro F1 en valid entre los modelos de ML.
6. Calcula la importancia por permutación en valid, por variable y por grupo, para HE1.
7. **Evaluación en test** de los cuatro modelos (tabla de H1), además de las métricas sin calibrar como referencia (`sin_calibrar`).
8. Registra los cuatro modelos en `modelo` y los tres de ML en `modelos/*.joblib`, y marca como vigente el seleccionado.
9. Escribe los reportes: `metricas_modelos.json`, `metricas_por_dia_turno.json`, `busqueda_hiperparametros.json` e `importancia_permutacion.json`, y las figuras `figuras/matrices_confusion_{valid,test}.png`, `figuras/f1_por_dia_{valid,test}.png` y `figuras/importancia_permutacion.png`.

## 5. `predecir`

Carga el artefacto vigente y calcula las probabilidades para:
- las fechas de **prueba** (5–8 jun), como demostración en la app, y
- la **fecha operativa** (9 jun), calculada con historia hasta el 8 de junio.

En total son 1 290 filas (86 × 5 × 3).

## 6. `priorizar`

Por cada predicción calcula:

- **R** = 0·p(Bajo) + 0,5·p(Medio) + 1·p(Alto)
- **G** = (gravedad_media7_celda − 1)/4, recortada a [0, 1]; 0 si no hubo registros en d−7…d−1
- **F** = suma7_celda / máx(suma7_celda en train), recortada a [0, 1]
- **P** = w1·R + w2·G + w3·F, con pesos por defecto **0,5 / 0,3 / 0,2**, normalizados a suma 1

Ordena por P en cada fecha y turno y guarda los resultados en `prioridad`.

### Justificación de los pesos por defecto

Ver el ADR 0004. En resumen: R es la estimación hacia adelante y lo nuevo que aporta el sistema, por eso pesa 0,5. G mide gravedad, algo que el modelo no estima, y pesa 0,3. F se solapa con las variables de historial que ya usa el modelo, así que pesa 0,2 para no contar dos veces la frecuencia. El operador puede cambiarlos en la barra lateral; el ranking y el mapa se recalculan al instante.

## 7. Resultado

`todo` termina escribiendo `reportes/resultado_fase3.json` (contrato §4). La corrida completa de `pytest` actualiza su bloque `tests`.

## Garantías

| Garantía | Dónde se verifica |
|---|---|
| Sin fuga: las variables de d no cambian si se añaden datos de d o posteriores | `tests/test_no_fuga.py` |
| Partición contigua, sin solapamiento e igual al handoff | `tests/test_particion.py` |
| Tabla idéntica a la de la Fase 2, fila a fila | `tests/test_tabla_modelado.py` |
| Reproducibilidad bit a bit | `tests/test_reproducibilidad.py` |
| Un solo vigente, elegido por validación | `tests/test_modelos.py`, índice único parcial en `modelo` |
