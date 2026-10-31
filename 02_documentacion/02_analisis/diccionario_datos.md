# Diccionario de datos (Fase 2)

Todos los archivos están en UTF-8, con separador `,`, punto decimal en el CSV y fechas en ISO. Las rutas son relativas a `RAIZ`.

## 1. `02_documentacion/02_analisis/datos/incidencias_limpias.csv`

Una fila por incidencia limpia (2 580). Se genera en `01_calidad.ipynb`, y `03_espacial.ipynb` le añade las columnas de microzona. Leer con `dtype={"id_incidencia": str, "ubigeo_inei": str, "zona": str, "sector": str, "id_microzona": str}`.

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `id_incidencia` | texto (8 hex) | Identificador de la fuente; único | canónico |
| `fuente_dataset` | texto | `cco_mdsjm_2026` | canónico |
| `distrito` | texto | San Juan de Miraflores | canónico |
| `ubigeo_inei` | texto (6) | `150133` (la fuente publica 150141, que es Surquillo) | canónico |
| `fecha` | `YYYY-MM-DD` | Fecha de registro | canónico |
| `hora` | `HH:MM:SS` | Hora de registro | canónico |
| `fecha_hora` | ISO 8601 (−05:00) | Fecha y hora de registro | canónico |
| `hora_num` | entero 0–23 | Hora de registro | derivada |
| `dia_semana` | entero 0–6 | Día de la semana (0 = lunes) | derivada |
| `turno` | texto | Mañana (06:00–13:59), Tarde (14:00–21:59), Noche (00:00–05:59 y 22:00–23:59 del mismo día calendario) | canónico (coherente con la hora en el 100 %) |
| `periodo` | texto | `arranque` (16–21 may), `estable` (22 may–8 jun), `censurado` (9–10 jun) | R4, R5 |
| `tipo` | texto | Tipo de incidencia tal como viene en la fuente (normalizado por la Fase 1) | canónico |
| `tipo_corto` | texto | Etiqueta corta del tipo (7 valores: Presuntamente delictivas, Presuntas faltas, Presuntas infracciones, Infraestructura y riesgo, Operativos, Ayuda y apoyo, Acontecimientos especiales) | R6 |
| `subtipo` | texto | Subtipo de la fuente (con sus erratas) | canónico |
| `subtipo_norm` | texto | Subtipo con las erratas corregidas | R6 |
| `modalidad` | texto | Modalidad (79 valores) | canónico |
| `zona` | texto, nulo | Zona según la fuente (12,0 % nulo) | canónico |
| `sector` | texto, nulo | Sector según la fuente (20,9 % nulo); solo descriptivo | canónico |
| `lat`, `lon` | real | Coordenadas WGS84 | canónico |
| `x_utm`, `y_utm` | real (m) | Coordenadas en UTM 18S (EPSG:32718) | derivada (pyproj) |
| `dentro_distrito` | booleano | Punto dentro del límite INEI 150133 | canónico |
| `dist_limite_m` | real (m) | Distancia al límite (0 si está dentro) | derivada |
| `en_tolerancia_borde` | booleano | Fuera del límite pero a ≤ 150 m; se conserva | R3 |
| `canal_reporte` | texto | Canal según la fuente (con la errata "LLAMDA") | canónico |
| `canal_norm` | texto | Canal corregido | R6 |
| `tipo_reportante` | texto | Quién reporta | canónico |
| `direccion` | texto | Dirección publicada; solo para la ficha de detalle | canónico |
| `mz_col`, `mz_fila` | entero | Columna y fila de la celda de 500 m: `floor((x_utm − 283 500)/500)`, `floor((y_utm − 8 651 000)/500)` | R10 |
| `id_microzona` | texto, nulo | `MZ-0001`…`MZ-0086` si la celda es activa; nulo en otro caso (28 registros) | R10 |

Columnas del canónico que **no** están en el dataset limpio: `estado_final`, `fecha_hora_cierre` y `tiempo_respuesta_min`, que son [POST] (R7).

## 2. `02_documentacion/02_analisis/datos/tabla_modelado.csv`

Una fila por **microzona activa × fecha × turno**, incluidas las que tienen conteo cero: 86 × 18 × 3 = **4 644 filas**. Las fechas van del 22 de mayo al 8 de junio de 2026. Se genera en `04_preparacion_modelado.ipynb` con `notebooks/_features.py`. Clave: (`id_microzona`, `fecha`, `turno`).

Todas las variables de una fila con fecha objetivo *d* usan solo incidencias de fechas **< d**. La historia empieza el 16 de mayo e incluye el arranque.

| Columna | Tipo | Rol | Descripción |
|---|---|---|---|
| `id_microzona` | texto | clave | `MZ-0001`… (ver `microzonas.geojson`) |
| `mz_col`, `mz_fila` | entero | clave auxiliar | Posición en la grilla de 500 m |
| `fecha` | `YYYY-MM-DD` | clave | Fecha objetivo *d* |
| `turno` | texto | clave y **feature** (calendario) | Mañana, Tarde, Noche |
| `particion` | texto | partición | `train` (22–31 may), `valid` (1–4 jun), `test` (5–8 jun) |
| `lag1_turno` | entero | feature (historial) | Incidencias de la microzona, mismo turno, d−1 |
| `lag7_turno` | entero, nulo | feature (historial) | Ídem, d−7. Nulo solo el 22 de mayo (258 filas), porque d−7 cae antes del inicio de los datos |
| `suma3_turno` | entero | feature (historial) | Suma del mismo turno entre d−3 y d−1 |
| `media7_turno` | real | feature (historial) | Media diaria del mismo turno entre d−7 y d−1, sobre los días disponibles desde el 16 de mayo |
| `lag1_celda` | entero | feature (historial) | Incidencias de la microzona en todos los turnos, d−1 |
| `suma7_celda` | entero | feature (historial) | Suma de todos los turnos entre d−7 y d−1 |
| `dias_desde_ultima` | entero 1–14 | feature (historial) | Días desde el último día con registro en la microzona (14 = ninguno o 14 o más) |
| `gravedad_media7_celda` | real 0–5 | feature (historial) | G media de las incidencias de la microzona entre d−7 y d−1 (0 si no hubo) |
| `nivel_lag1_turno` | texto | feature (historial) y **línea base** | Nivel de `lag1_turno` con el umbral b de entrenamiento |
| `vecinos_lag1_turno` | entero | feature (espacial) | Incidencias en las 8 celdas vecinas, mismo turno, d−1 |
| `vecinos_suma7` | entero | feature (espacial) | Incidencias en las 8 vecinas, todos los turnos, entre d−7 y d−1 |
| `dia_semana` | entero 0–6 | feature (calendario) | 0 = lunes |
| `fin_de_semana` | 0/1 | feature (calendario) | Sábado o domingo |
| `feriado` | 0/1 | feature (calendario) | Feriado nacional (solo el 7 de junio, que está en prueba) |
| `distrito_lag1_turno` | entero | feature (contexto) | Incidencias de todo el distrito, mismo turno, d−1 |
| `distrito_lag1` | entero | feature (contexto) | Incidencias de todo el distrito, d−1 |
| `distrito_media7` | real | feature (contexto) | Media diaria del distrito entre d−7 y d−1 (nivel de cobertura reciente) |
| `conteo` | entero | **origen del objetivo**, excluido por fuga | Incidencias de la microzona en la fecha y turno objetivo |
| `nivel` | texto | **objetivo**, excluido por fuga | Bajo si conteo = 0; Medio si conteo = 1; Alto si conteo ≥ 2 (b = 1, calculado con entrenamiento) |

## 3. `02_documentacion/02_analisis/datos/microzonas.geojson`

Es un FeatureCollection en WGS84 (CRS84) con 86 polígonos, uno por microzona activa: cuadrados de 500 m en UTM 18S reproyectados. El bloque `metadatos` guarda el CRS métrico, el origen, el tamaño, el criterio de activa y la fórmula de asignación.

| Propiedad | Tipo | Descripción |
|---|---|---|
| `id_microzona` | texto | `MZ-0001`…`MZ-0086`, ordenadas de norte a sur (fila descendente) y de oeste a este (columna ascendente) |
| `col`, `fila` | entero | Índices de la grilla |
| `tamano_m` | entero | 500 |
| `x_min_utm`, `y_min_utm` | real (m) | Esquina inferior izquierda en EPSG:32718 |
| `lon_centro`, `lat_centro` | real | Centroide en WGS84 |
| `pct_area_dentro_distrito` | real | Porcentaje del área de la celda que cae dentro del límite distrital |

## 4. `02_documentacion/02_analisis/datos/gravedad_por_tipo.csv`

Hay una fila por combinación tipo × subtipo (23). Es un **supuesto de diseño**.

| Columna | Descripción |
|---|---|
| `tipo`, `subtipo` | Valores tal como vienen en el canónico; sirven de clave de unión |
| `tipo_corto`, `subtipo_norm` | Etiquetas legibles |
| `registros` | Registros limpios con esa combinación (descriptivo) |
| `gravedad` | G ordinal de 1 a 5 |
| `gravedad_norm` | (G − 1) / 4, entre 0 y 1 |
| `justificacion` | Razón del valor asignado |
| `supuesto_de_diseno` | Siempre `True` |

## 5. Archivos auxiliares de métricas

`datos/metricas_calidad.json`, `metricas_temporal.json`, `metricas_espacial.json` y `metricas_modelado.json` contienen las cifras que imprimen los notebooks y se citan en el informe. Los genera cada notebook.
