# Diccionario de la fuente: incidencias del CCO de la MDSJM

Fuente: *Relación de incidencias atendidas por el Centro de Control de Operaciones (CCO) - Municipalidad Distrital de San Juan de Miraflores*, versión 1.0, corte 2026-06-10, Plataforma Nacional de Datos Abiertos (PNDA).
Archivo crudo: `datos/raw/cco_mdsjm_2026/2026-10-31/incidencias_seguridad_sjm_20260610.csv` (UTF-8 con BOM, separador coma, 2 592 filas × 22 columnas).
Descripciones: diccionario oficial (`DICCIONARIO-DATOS_20260610_151901.xlsx`, en la misma carpeta). Valores observados: perfil propio del extracto (`scripts/03_normalizar.py`, `datos/procesados/perfil_canonico.json`).

Leyenda de la última columna: **→ col** = pasa al canónico con ese nombre; **[POST]** = se conoce después del registro (prohibido como predictor); **no** = no pasa al canónico.

| # | Columna fuente | Significado (diccionario oficial) | Valores observados | Pasa al canónico |
|---|---|---|---|---|
| 1 | `FECHA_CORTE` | Fecha de corte, estampada al generar el dataset (aaaammdd) | Un solo valor: 20260610 | no (constante; queda en el crudo y en el catálogo) |
| 2 | `UBIGEO` | Ubigeo del distrito (la fuente lo describe como "INEI … SJM = 150141") | Un solo valor: 150141 | no. En INEI, SIDPOL y la cartografía, 150141 es **Surquillo**; SJM es **150133**. El canónico usa `ubigeo_inei = 150133` y el handoff guarda `ubigeo_fuente = 150141` |
| 3 | `ID_INCIDENCIA` | Identificador público, 8 caracteres hexadecimales (GUID truncado) | 2 592 únicos, todos `[0-9a-f]{8}` en el CSV | → `id_incidencia`. En el Excel de `01_alcance`, Excel convirtió 67 celdas en número y alteró 21 ID (p. ej. `01127344` → 1127344, `45184e36` → 4,5184E+40); dos ID `0e…` quedaron ambos como 0 (el "duplicado") |
| 4 | `FECHA_REGISTRO` | Fecha en que el operador registró la incidencia (aaaammdd) | 2026-05-16 a 2026-06-10, 26 días, sin huecos | → `fecha` (`YYYY-MM-DD`) |
| 5 | `HORA_REGISTRO` | Hora de registro, 24 h (HH:MM) | 1 128 valores distintos; ningún nulo | → `hora` (`HH:MM:SS`, segundos = 00) y `fecha_hora` (ISO 8601, `-05:00`) |
| 6 | `TURNO` | Turno operativo: Mañana (06–14), Tarde (14–22), Noche (22–06) | Mañana 1 222 · Noche 754 · Tarde 616; coherente con la hora en 2 592/2 592 | → `turno` |
| 7 | `TIPO` | Tipo de incidencia (nivel 1) | 7 tipos (ver informe, tabla de tipos); 2 tipos no aparecen en todas las semanas | → `tipo` (mayúsculas, espacios dobles colapsados) |
| 8 | `SUBTIPO` | Subtipo (nivel 2) | 23 valores; erratas de origen como `PREUNTOS ACONTECIMIENTOS ESPECIALES`, `CONTRA CONTRA LA PERSONA` | → `subtipo` (misma normalización; erratas sin corregir) |
| 9 | `MODALIDAD` | Modalidad (nivel 3) | 79 valores | → `modalidad` |
| 10 | `ZONA` | Zona del distrito (división interna de la MDSJM) | SAN JUAN 1 060 · PAMPLONA I 870 · MATEO PUMACAHUA 116 · PAMPLONA II 112 · LADERAS DE VILLA 102 · SAGITARIO 20 · vacío 312 (12,0 %) | → `zona` (vacío → nulo) |
| 11 | `SECTOR` | Sector dentro de la zona | SECTOR I 839 · II 660 · III 452 · IV 98 · vacío 543 (20,9 %) | → `sector` (vacío → nulo) |
| 12 | `DIRECCION` | Dirección textual captada por el operador | 1 469 valores; mezcla calles, manzana/lote, códigos Plus (p. ej. `R2XC+F4F`) y referencias | → `direccion` (solo para la ficha de detalle). Barrido de DNI, teléfonos, correos, placas y tratamientos personales: 0 coincidencias. La ficha indica "sin identificación de víctima" |
| 13 | `LATITUD` | Latitud WGS84, grados decimales | 100 % numérica; rango -12,212 a -9,368 (un error grosero en Áncash) | → `lat` |
| 14 | `LONGITUD` | Longitud WGS84 | 100 % numérica; rango -77,090 a -76,947; un valor con espacio inicial | → `lon` (se recorta el espacio) |
| — | (derivada) | Punto dentro del límite INEI 150133 | 2 560 dentro (98,77 %), 32 fuera | → `dentro_distrito` |
| 15 | `FUENTE` | Canal por el que se reportó | CAMARAS CECOP 1 932 (74,5 %) · WHATSAPP 322 · LLAMDA TELEFONICA 318 · OTROS 12 · FISCALIZACION 4 · DESPACHADOR TETRA 3 · JEFE DE OPERACIONES 1 | → `canal_reporte` (errata "LLAMDA" sin corregir) |
| 16 | `TIPO_REPORTANTE` | Categoría de quien reporta | AGENTE DE SEGURIDAD MUNICIPAL 2 018 · CONTRIBUYENTE 551 · AGENTE DE SEGURIDAD EXTERNO 17 · otros 7 | → `tipo_reportante` |
| 17 | `NIVEL` | Gravedad "asignada por el operador **durante la coordinación**" (Común / Relevante / Grave; puede estar vacío) | vacío 1 687 (65,1 %) · Común 882 · Relevante 22 · Grave 1. Los 1 687 vacíos son todos "No atendida"; el 2026-06-10 está informado al 100 % porque solo entraron las cerradas rápido | **no — [POST]**. Se asigna después del registro y su ausencia depende del desenlace (cierre automático). No es predictor ni etiqueta de gravedad válida. Se conserva en el crudo |
| 18 | `ESTADO_FINAL` | Estado de cierre | No atendida 2 205 · Atendida 312 · Justificada 75 | → `estado_final` **[POST]** |
| 19 | `FECHA_CIERRE` | Fecha de cierre (aaaammdd) | 2026-05-17 a 2026-06-10 | → `fecha_hora_cierre` **[POST]** (con `HORA_CIERRE`) |
| 20 | `HORA_CIERRE` | Hora de cierre (HH:MM) | 1 042 valores | → `fecha_hora_cierre` **[POST]** |
| 21 | `TIEMPO_RESPUESTA_MIN` | Minutos entre registro y cierre | 0 a 2 092; mediana 1 441; 1 870 "No atendida" > 1 380 min (cierre automático ~24 h) | → `tiempo_respuesta_min` **[POST]** |
| 22 | `AMBIENTAL` | Incidencia catalogada como ambiental (SI/NO) | Un solo valor: NO | no (constante) |

## Columnas canónicas añadidas por el proceso

| Columna canónica | Valor | Origen |
|---|---|---|
| `fuente_dataset` | `cco_mdsjm_2026` | `catalogo_fuentes.csv` |
| `distrito` | `San Juan de Miraflores` | constante |
| `ubigeo_inei` | `150133` | INEI (verificado en SIDPOL y en la capa de límites) |
| `dentro_distrito` | `True`/`False` | punto en polígono contra `datos/cartografia/limite_distrito.geojson` (shapely) |

## Otras hojas del Excel de `01_alcance`

`Calc_Dashboard` (34 × 12) y `Dashboard` (32 × 11) son tablas de cálculo y un panel elaborados por el autor del alcance a partir de la hoja de datos (conteos por fecha, zona y turno, tasa de atención, tiempo promedio). No son dato fuente y no se usan.
