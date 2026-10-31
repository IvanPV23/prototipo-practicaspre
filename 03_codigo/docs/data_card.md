# Ficha de datos (data card)

## Origen

| Campo | Valor |
|---|---|
| Conjunto | Relación de incidencias atendidas por el Centro de Control de Operaciones (CCO), Municipalidad Distrital de San Juan de Miraflores (v1.0, corte 2026-06-10) |
| Publicador | MDSJM, Gerencia de Seguridad Ciudadana, en la Plataforma Nacional de Datos Abiertos |
| URL | https://www.datosabiertos.gob.pe/dataset/relaci%C3%B3n-de-incidencias-atendidas-por-el-centro-de-control-de-operaciones-cco-municipalidad |
| Licencia | Open Data Commons Attribution License (ODC-By 1.0): uso libre citando la fuente |
| Descarga | 2026-10-31 (Fase 1) |
| Archivo usado por el sistema | `02_documentacion/01_recoleccion/datos/procesados/incidencias_canonico.csv` (esquema canónico de la Fase 1) |
| Integridad | sha256 `eea9ec568e26eea03e13b4196de1eb6905a87e72659c52100ce63e733e9dbacd`, verificado en cada `ingestar` contra `handoff_fase1.json` |
| Límite distrital | INEI (ubigeo 150133), servido por la ANA, en `datos/cartografia/limite_distrito.geojson` |
| Gravedad por tipo | `02_documentacion/02_analisis/datos/gravedad_por_tipo.csv`: supuesto de diseño de la Fase 2, escala 1–5 |
| Mapa base de la app | Teselas de OpenStreetMap (© colaboradores de OpenStreetMap, ODbL), con la atribución visible en el mapa |

## Contenido

- **2 592 registros**, uno por incidencia, del 16 de mayo al 10 de junio de 2026 (26 días). Todos tienen latitud y longitud WGS84.
- Columnas usadas: identificador, fecha, hora, turno (Mañana/Tarde/Noche), tipo y subtipo, sector y zona (solo referencia), coordenadas, canal y tipo de reportante (descriptivos) y dirección (solo para la ficha, recortada a la calle).
- Columnas **[POST]** (`estado_final`, `fecha_hora_cierre`, `tiempo_respuesta_min`): se conocen después del evento, **no se cargan** en la base y nunca son predictores.
- No hay datos personales (nombres, DNI, teléfonos, placas). La ficha de detalle no muestra numeración de domicilios.

## Tratamiento (reglas de la Fase 2, reimplementadas en `ingesta/` y `servicios/pipeline.py`)

| Regla | Efecto |
|---|---|
| Identificadores y ubigeo leídos como texto | Evita que ids hexadecimales como `0e12…` se conviertan en números |
| Puntos a más de 150 m del límite → excluidos | 12 registros (10 en distritos vecinos y 2 errores groseros) → **2 580 limpios** |
| 16–21 may = arranque | Solo historial para los rezagos (≈ 32 registros/día y sin turno Noche hasta el 20 may) |
| 9–10 jun = censurados | La fuente publica solo incidencias cerradas al corte (10 jun, ≈ 15:09). Esos días quedan fuera de la historia y del objetivo |
| Asignación a una celda de 500 m (EPSG:32718) | 86 microzonas activas (con registro en entrenamiento) de 121 celdas que tocan el distrito |

## Sesgos y limitaciones

- **Registro, no delito.** Son incidencias atendidas por el CCO: predominan las presuntas infracciones (52 %) y faltas (24 %). Solo el 2 % son presuntamente delictivas.
- **Sesgo de observación.** Unas tres cuartas partes de los registros provienen de las cámaras (CECOP), así que las zonas con más cámaras o más patrullaje registran más. El mapa refleja dónde se mira, no solo lo que pasa.
- **Cambio de cobertura.** El volumen diario sube de mayo a junio (+32,7 % entre semanas, sobre todo por cámaras), y la clase Alto pasa de 9,4 % en entrenamiento a 13,8 % en prueba.
- **Periodo corto.** Hay 18 días utilizables como objetivo, así que no hay estacionalidad observable.
- **Sector incompleto.** El 20,6 % de los registros limpios no tiene sector. El sector de cada microzona es el más frecuente entre sus registros y es solo referencial.
- **Ubigeo de la fuente (150141) ≠ INEI (150133).** Es una inconsistencia de codificación; la ubicación se valida contra el límite oficial.
- **Sin exposición.** No hay población ni flujo por microzona, así que los conteos no son tasas.

## Uso previsto

Apoyar la priorización preventiva de patrullaje por microzona y turno. **No** debe usarse para etiquetar barrios ni personas, ni como medida del delito.
