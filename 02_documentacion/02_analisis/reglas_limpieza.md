# Reglas de limpieza

Entrada: `02_documentacion/01_recoleccion/datos/procesados/incidencias_canonico.csv` (2 592 registros, sha256 `eea9ec56…dbacd`, verificado al cargar).
Salida: `02_documentacion/02_analisis/datos/incidencias_limpias.csv` (**2 580 registros**).
Implementación: `notebooks/01_calidad.ipynb` (reglas R1–R9). `notebooks/03_espacial.ipynb` añade después las columnas de microzona (R10). Los conteos están en `datos/metricas_calidad.json`.

Los datos de la Fase 1 no se modifican. Toda corrección se hace en copias o columnas nuevas del dataset limpio.

| ID | Qué | Por qué | Filas afectadas | Acción |
|---|---|---|---|---|
| R1 | Leer `id_incidencia`, `ubigeo_inei`, `zona` y `sector` como texto | El CSV escribe el ubigeo sin comillas. Leído como número perdería el formato de 6 caracteres, y algunos ID hexadecimales (`0e…`, `…e36`) se convertirían en números, como ocurrió en el Excel del alcance | 0 (tipado) | tipado |
| R2 | Excluir puntos a **más de 150 m** del límite INEI 150133 | Hay 10 puntos entre 287 m y 1,9 km del límite, en Chorrillos, Villa El Salvador y el Parque Industrial, que caen en otros distritos. Hay además 2 errores groseros: Bellavista-Callao a 15 km y latitud −9,37 en Áncash, a 304 km | **12** | excluir |
| R3 | Conservar los puntos fuera del límite a ≤ 150 m y marcarlos (`en_tolerancia_borde = True`) | Hay 20 puntos a ≤ 113 m del borde (Atocongo, Óvalo Los Eucaliptos), compatibles con la imprecisión del límite o de la geocodificación. Entre 113 m y 287 m no hay ningún punto: ese hueco natural justifica el umbral de 150 m | 20 | marcar |
| R4 | Marcar del 16 al 21 de mayo como `periodo = arranque` | Es la puesta en marcha del registro: 32,0 registros/día frente a 114,7 entre el 22 y el 31 de mayo. No hay **ningún registro de turno Noche entre el 16 y el 20 de mayo**, el 92 % viene de cámaras y WhatsApp o llamada aportan apenas 2,2 registros/día. Estos días **no generan filas objetivo** y solo sirven de historial para los rezagos | 192 | marcar |
| R5 | Marcar el 9 y el 10 de junio como `periodo = censurado` | El dataset solo publica incidencias cerradas. El corte fue el 10 de junio hacia las 15:09 y el cierre automático tarda unos 1 443 min, así que faltan las incidencias registradas desde aproximadamente las 15:06 del 9 de junio. El 9 de junio no tiene registros entre las 22:00 y las 23:59 (la media es 13,3) y tiene la tarde mermada (23 frente a 30,6). El 10 de junio solo tiene turno mañana y 0 % de cierres de más de 23 h. Ambos quedan **fuera de la tabla de modelado**. El 8 de junio está completo, porque el P99 del cierre (1 522 min) termina antes del corte | 185 | marcar |
| R6 | Añadir `tipo_corto` (7 etiquetas) y copias normalizadas `subtipo_norm` (`PREUNTOS`→`PRESUNTOS`, `CONTRA CONTRA`→`CONTRA`, `ACTIV.CONTRA`→`ACTIV. CONTRA`) y `canal_norm` (`LLAMDA`→`LLAMADA`) | Son erratas de origen. Corregirlas facilita la lectura y la agrupación. Las columnas originales se conservan | 41 subtipo + 318 canal | normalizar |
| R7 | No incluir `estado_final`, `fecha_hora_cierre` ni `tiempo_respuesta_min` en el dataset limpio | Son columnas **[POST]**: se conocen después del evento. Al quitarlas se evita la fuga por diseño. Solo se usaron en `01_calidad` para diagnosticar la censura | 0 (columnas) | eliminar columnas |
| R8 | Revisar duplicados por ID y por contenido (fecha-hora al minuto, coordenadas y modalidad) | Una doble digitación inflaría los conteos | 0 | ninguna (no hay) |
| R9 | Mantener nulos `sector` (543) y `zona` (312) | La ubicación se toma de las coordenadas. El sector falta sobre todo en Laderas de Villa, Mateo Pumacahua, Sagitario y los registros sin zona | 543 | mantener |
| R10 | Añadir `mz_col`, `mz_fila` (grilla de 500 m, EPSG:32718, origen 283 500 / 8 651 000) e `id_microzona`, que queda nulo si la celda no es activa | Asigna cada incidencia a su microzona. Las celdas activas se definen solo con entrenamiento (ver `especificacion_modelado.md`) | 28 sin microzona activa (21 en el periodo estable y 7 en el censurado) | añadir columnas |

## Resultado

| Periodo | Registros limpios | Uso |
|---|---|---|
| `arranque` (16–21 may) | 192 | Solo historial para variables rezagadas |
| `estable` (22 may–8 jun) | 2 203 | Filas objetivo y variables (tabla de modelado) |
| `censurado` (9–10 jun) | 185 | Solo descripción. No entra a la tabla |
| **Total** | **2 580** | |

## Columnas no usadas

- `NIVEL` de la fuente: es [POST] (lo asigna el operador "durante la coordinación") y no está en el canónico. No se usa ni como predictor ni como gravedad.
- Las columnas [POST] del canónico (R7).
