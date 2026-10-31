# Especificación de modelado (para la Fase 3)

Es la versión legible de `handoff_fase2.json`. Permite reconstruir microzonas, tabla, objetivo y variables desde el CSV canónico **sin abrir los notebooks**. La implementación de referencia está en `notebooks/_comun.py` y `notebooks/_features.py`. Si la reconstrucción es correcta, el resultado coincide fila a fila con `datos/tabla_modelado.csv`.

## 0. Constantes

| Constante | Valor |
|---|---|
| CSV canónico | `02_documentacion/01_recoleccion/datos/procesados/incidencias_canonico.csv` (sha256 `eea9ec568e26eea03e13b4196de1eb6905a87e72659c52100ce63e733e9dbacd`) |
| Límite distrital | `02_documentacion/01_recoleccion/datos/cartografia/limite_distrito.geojson` (INEI 150133) |
| CRS métrico | EPSG:32718 (UTM 18S) |
| Tamaño de celda | 500 m |
| Origen de la grilla (x0, y0) | (283 500, 8 651 000): esquina inferior izquierda del límite, redondeada hacia abajo al múltiplo de 500 |
| Tolerancia de borde | 150 m |
| Inicio de la historia | 2026-05-16 |
| Arranque (solo historial) | 2026-05-16 → 2026-05-21 |
| Ventana de filas objetivo | 2026-05-22 → 2026-06-08 (18 días) |
| Excluidos por censura | 2026-06-09, 2026-06-10 |
| Partición | train 2026-05-22 → 2026-05-31 · valid 2026-06-01 → 2026-06-04 · test 2026-06-05 → 2026-06-08 |
| Umbral b | 1 (mediana de los conteos > 0 de train) |
| Turnos | Mañana, Tarde, Noche (según la columna `turno` y la `fecha` de registro) |
| Feriados | {2026-06-07} |

## 1. Limpieza (ver `reglas_limpieza.md`)

```
inc = leer_csv(canónico, dtype texto para id_incidencia, ubigeo_inei, zona, sector)
verificar sha256
x, y = transformar(lon, lat, EPSG:4326 -> EPSG:32718)
dist = 0 si el punto está dentro del límite; si no, la distancia al polígono (m)
inc = inc[dist <= 150]                        # excluye 12 registros -> 2 580
inc.gravedad = unir(gravedad_por_tipo.csv, por [tipo, subtipo]).gravedad
```

## 2. Microzonas

```
col  = floor((x - 283500) / 500)
fila = floor((y - 8651000) / 500)
celdas_distrito = {(c, f) : cuadrado(c, f) interseca el límite}                     # 121
activas = {(c, f) de incidencias con fecha en train} ∩ celdas_distrito               # 86
orden: fila descendente, luego col ascendente  ->  id = "MZ-%04d" (1..86)
```

No se recalculan con valid ni con test. Las incidencias de celdas no activas se usan para las variables de vecinos y de distrito, pero no generan filas.

## 3. Tabla de modelado

```
fechas_hist = 2026-05-16 .. 2026-06-08              # 24 días; NO incluye 9-10 jun
C[c, f, k, t]  = nº de incidencias limpias de la celda (c, f), día k, turno t   (todas las celdas, no solo activas)
G[c, f, k, t]  = suma de gravedad de esas incidencias
Cdia = Σ_t C ;  Gdia = Σ_t G
V[c, f, k, t]  = Σ de C en las 8 celdas vecinas (queen), sin la propia
Vdia = Σ_t V
Dturno[k, t] = Σ_{c,f} C ;  Ddia[k] = Σ_t Dturno

para cada microzona activa m=(c,f), cada fecha d en 2026-05-22..2026-06-08 (k = índice de d), cada turno t:
    w7 = días [max(k-7,0), k-1] ; n7 = nº de días en w7 ; w3 = [max(k-3,0), k-1]
    lag1_turno        = C[m, k-1, t]
    lag7_turno        = C[m, k-7, t]   si k >= 7, si no NaN           (solo 22 may)
    suma3_turno       = Σ_{w3} C[m, ·, t]
    media7_turno      = Σ_{w7} C[m, ·, t] / n7
    lag1_celda        = Cdia[m, k-1]
    suma7_celda       = Σ_{w7} Cdia[m, ·]
    dias_desde_ultima = min(k - último día j<k con Cdia[m, j] > 0, 14); 14 si no hay ninguno
    gravedad_media7_celda = Σ_{w7} Gdia[m, ·] / Σ_{w7} Cdia[m, ·]   (0 si el denominador es 0)
    vecinos_lag1_turno = V[m, k-1, t]
    vecinos_suma7      = Σ_{w7} Vdia[m, ·]
    dia_semana = d.weekday() (0 = lunes) ; fin_de_semana = dia_semana >= 5 ; feriado = d ∈ {2026-06-07}
    distrito_lag1_turno = Dturno[k-1, t] ; distrito_lag1 = Ddia[k-1] ; distrito_media7 = Σ_{w7} Ddia / n7
    conteo = C[m, k, t]                                    # solo para construir el objetivo
    particion = train | valid | test según d
```

Comprobación: filas = 86 × 18 × 3 = **4 644**; un 71,1 % tiene `conteo = 0`.

## 4. Objetivo

```
b = mediana( conteo[particion == train & conteo > 0] )     # = 1
nivel = "Bajo"  si conteo == 0
        "Medio" si 1 <= conteo <= b
        "Alto"  si conteo > b
nivel_lag1_turno = misma regla aplicada a lag1_turno (con el mismo b)
```

| Partición | Bajo | Medio | Alto | Filas |
|---|---|---|---|---|
| train | 1 858 (72,0 %) | 480 (18,6 %) | 242 (9,4 %) | 2 580 |
| valid | 756 (73,3 %) | 172 (16,7 %) | 104 (10,1 %) | 1 032 |
| test | 686 (66,5 %) | 204 (19,8 %) | 142 (13,8 %) | 1 032 |

En la Fase 2, de test solo se cuentan las clases.

## 5. Variables (features)

Hay 18 candidatas en cuatro grupos. Todas usan datos con fecha < d.

| Grupo | Variables |
|---|---|
| Historial de la microzona | `lag1_turno`, `lag7_turno`, `suma3_turno`, `media7_turno`, `lag1_celda`, `suma7_celda`, `dias_desde_ultima`, `gravedad_media7_celda`, `nivel_lag1_turno` |
| Espacial | `vecinos_lag1_turno`, `vecinos_suma7` |
| Calendario | `dia_semana`, `fin_de_semana`, `feriado`, `turno` |
| Contexto del distrito | `distrito_lag1_turno`, `distrito_lag1`, `distrito_media7` |

**Excluidas por fuga:** `estado_final`, `fecha_hora_cierre`, `tiempo_respuesta_min` y `NIVEL` de la fuente (todas [POST]), además de `conteo` y `nivel` (el objetivo de la misma fecha-turno). También queda excluido cualquier agregado (por canal, tipo, gravedad o reportante) de la fecha-turno objetivo o de una posterior, y `mz_col`/`mz_fila` si se usan para codificar el objetivo (target encoding) con datos que incluyan la propia fila.

**Momento de la predicción:** al cierre del día d−1 se predicen los tres turnos del día d. En una operación real, las variables deben calcularse con el registro interno del CCO (incidencias registradas, aunque sigan abiertas), no con el dataset abierto, que solo publica las cerradas.

**Prueba de no fuga (notebook 04):** para cada fecha d se recalculan las variables con la historia truncada en d y con 50 incidencias falsas inyectadas en d. En las 18 fechas, las 17 variables numéricas o categóricas comparables resultan idénticas. La Fase 3 debería repetir esta prueba en sus tests.

## 6. Línea base y protocolo de evaluación

- **Persistencia:** `pred = nivel_lag1_turno`. En validación obtiene **Macro F1 = 0,439** (exactitud 0,636; F1 Bajo 0,784, Medio 0,231 y Alto 0,301). "Siempre Bajo" obtiene 0,282.
- Ajustar solo con train y seleccionar con valid. Test se evalúa **una sola vez** al final. Si se reentrena con train+valid antes de esa evaluación, hay que declararlo. Los umbrales (b) y las microzonas activas no se recalculan.
- Usar `class_weight="balanced"` o una ponderación equivalente. Reportar Macro F1, precisión y recall por clase, la matriz de confusión con soportes y el Macro F1 por día y por turno.
- Imputar `lag7_turno` (solo el 22 de mayo) con `media7_turno`, o excluir esa fecha del ajuste. La regresión logística necesita escalado e *one-hot* de `turno`, `dia_semana` y `nivel_lag1_turno`, ajustados en train.
- `feriado` es constante en train y valid: no aporta.

## 7. Priorización P = w1·R + w2·G + w3·F (sugerencia)

- R: probabilidad de Alto (o nivel esperado normalizado) que dé el modelo.
- G: `gravedad_media7_celda`, normalizada como (G − 1)/4 y recortada a [0, 1]; si no hubo incidencias, G = 0.
- F: `suma7_celda` / máx(`suma7_celda` en train).

Los pesos son ajustables. La gravedad es un **supuesto de diseño** (`datos/gravedad_por_tipo.csv`).
