# Informe de recolección de datos (Fase 1)

Proyecto: predicción espaciotemporal de incidencias de seguridad ciudadana en **San Juan de Miraflores (SJM)**, Lima · Fecha: 2026-10-31

> Aclaración: el usuario mencionó el distrito como "SJL", pero el alcance, el dataset y el título del proyecto corresponden a **San Juan de Miraflores** (ubigeo INEI 150133), no a San Juan de Lurigancho (150132). Se trabajó con SJM.

## Resumen ejecutivo

1. Decisión **A**: se mantiene SJM con el único extracto publicado del CCO de la MDSJM (2 592 incidencias, del 16 de mayo al 10 de junio de 2026), tomado del **CSV oficial del PNDA**.
2. El Excel de `01_alcance` tenía 21 ID alterados por Excel; ese es el origen del "duplicado". El CSV conserva 2 592 ID únicos con el mismo contenido.
3. No existen extractos anteriores ni posteriores: el dataset tiene una sola revisión, aunque declara frecuencia mensual. Ningún distrito de la provincia de Lima publica incidencias con coordenadas.
4. Se cumplen 7 de 9 criterios mínimos (punto 100 %, dentro del límite 98,77 %, sin datos personales). **No se cumplen** el criterio 4 (26 de 42 días) ni el 6 (arranque con +77 % entre semanas). El último día está censurado.
5. Se añadieron como contexto el límite distrital INEI, el SIDPOL mensual de SJM (2018-01 a 2026-09) y la población proyectada INEI 2018-2026. No hace falta confirmación del usuario, pero se recomienda pedir a la MDSJM un extracto actualizado.

## 1. Fuentes revisadas

### 1.1 Usadas

| id | Fuente | Uso | Archivo procesado |
|---|---|---|---|
| `cco_mdsjm_2026` | MDSJM: incidencias atendidas por el CCO (PNDA, v1.0, corte 2026-06-10), CSV + diccionario + metadatos + ficha JSON | entrenamiento | `datos/procesados/incidencias_canonico.csv` |
| `sidpol_mininter` | MININTER: denuncias policiales SIDPOL, ene-2018 a sep-2026 (376 715 filas nacionales) | contexto | `datos/procesados/sidpol_sjm_mensual.csv` (700 filas, 90 272 denuncias en SJM) |
| `limite_inei_ana` | Límite distrital INEI (ubigeo 150133) servido por la ANA (capa `Hosted/distritos`, 1 891 distritos, campo `fuente = INEI`) | cartografía | `datos/cartografia/limite_distrito.geojson` |
| `poblacion_inei_2026` | INEI: población total proyectada al 30 de junio, 2018-2026 (1 892 distritos) | exposición | `datos/procesados/poblacion_sjm.csv` (SJM 2026: 437 390 hab.) |

URL, licencia, fecha de descarga, SHA-256 y tamaño: `catalogo_fuentes.csv` y `datos/manifest.json`.

### 1.2 Revisadas y descartadas

| Fuente | Por qué se descarta |
|---|---|
| Excel `01_alcance/incidencias_seguridad_sjm_20260610.xlsx` | Es una copia del CSV del PNDA, pero Excel guardó 67 ID como número y alteró 21 (`01127344` → 1127344, `45184e36` → 4,5184E+40, `0e…` → 0). Dos ID distintos quedaron como 0, que es el duplicado observado (2 591 únicos en 2 592 filas). El resto del contenido es idéntico: misma distribución de fecha, turno, tipo, zona, sector y estado; las coordenadas solo difieren en la precisión decimal. Las hojas `Calc_Dashboard` y `Dashboard` son cálculos del autor |
| Otros extractos del CCO de la MDSJM (búsqueda B) | No existen. La ficha tiene una sola revisión ("Publicación inicial del dataset versión 1.0… Corte al 2026-06-10") y el grupo MDSJM del PNDA solo tiene ese conjunto de seguridad. La ficha declara frecuencia mensual y "cobertura temporal" desde el 2026-01-01, pero los metadatos aclaran que la cobertura va "desde el inicio de operaciones del sistema CCO" y el CSV empieza el 16 de mayo |
| Callao: Municipalidad Provincial del Callao, central de monitoreo de cámaras | Tiene puntos y una serie larga (913 238 casos, 2023-10 a 2025-11), pero es otra provincia. No hay coordenadas antes de junio de 2024, el volumen es muy inestable (hasta +117 % entre meses), el 86 % de los puntos cae dentro del distrito Callao, no tiene subtipo y el 68 % de los casos son tránsito o ambiente. No es claramente superior; ver `decision_dataset.md` |
| San Isidro: Seguridad Ciudadana 2026 (apoyo por seguridad) | 39 224 registros de ene-abr 2026, estables, pero LATITUD y LONGITUD vienen vacías. Geocodificar las direcciones sería un dato derivado y no publicado. Los consolidados 2015-2023 están en msi.gob.pe y tienen filas vacías |
| San Martín de Porres: incidencias 1.er semestre 2026 | Usa el mismo catálogo nacional que SJM, pero solo trae la comisaría como ubicación y la licencia no está especificada |
| Jesús María: incidencia delictiva 2026 | Sin coordenadas ni hora; unos 4 registros/día |
| GORE Callao: hechos delictivos (feb-2024) | Un solo mes; contiene fecha de nacimiento, edad, sexo, estado civil y ocupación (datos personales). No se usa |
| Miraflores: emergencias atendidas | Conteos mensuales agregados de 2020-2021 |
| Lambayeque, Moyobamba, Paita, Piura, Chiclayo, Ventanilla, Tambogrande, La Punta | Fuera de Lima o no son registros de incidencias de punto (inventarios de cámaras, llamadas o patrullaje agregado) |
| Prensa (p. ej. "mapa del delito") | No se usa como dato, por regla del proyecto |

El perfil de los candidatos es reproducible con `scripts/04_perfilar_candidatos.py` sobre `datos/raw/cand_*`.

## 2. Perfil del dato principal

Generado por `scripts/03_normalizar.py` → `datos/procesados/perfil_canonico.json`.

- **Registros:** 2 592 incidencias, 2 592 ID únicos, 26 días consecutivos (2026-05-16 a 2026-06-10), 99,7/día de media.
- **Turno:** Mañana 1 222 (47,1 %) · Noche 754 (29,1 %) · Tarde 616 (23,8 %). La regla del diccionario (06–14, 14–22, 22–06) se cumple en el 100 %.
- **Coordenadas:** 100 % numéricas. 98,77 % dentro del límite INEI. De los 32 puntos fuera, 20 están a menos de 120 m del borde (Atocongo, Óvalo Los Eucaliptos), 10 entre 0,3 y 1,9 km (VES, Chorrillos, Parque Industrial) y 2 son errores groseros (Bellavista-Callao a 15 km; latitud -9,37 en Áncash).
- **Campos administrativos:** sin sector 543 (20,9 %), sin zona 312 (12,0 %).
- **Ubigeo:** la fuente usa 150141. En INEI, SIDPOL y la capa de límites, 150141 es Surquillo y SJM es 150133; se usa 150133.
- **Canal:** cámaras CECOP 74,5 %, WhatsApp 12,4 %, llamada 12,3 %. Reporta un agente municipal en el 77,9 % de los casos.
- **Columnas posteriores al evento:** `ESTADO_FINAL` (No atendida 85,1 %), `FECHA/HORA_CIERRE`, `TIEMPO_RESPUESTA_MIN` (mediana 1 441 min; 1 870 "No atendida" se cierran después de 23 h, lo que indica cierre automático) y `NIVEL`. Según el diccionario oficial, `NIVEL` se asigna "durante la coordinación", y sus 1 687 vacíos son todos "No atendida", así que es [POST] y no pasa al canónico.

Registros por tipo (normalizado):

| Tipo | Registros | % |
|---|---|---|
| Emisión de alertas tempranas en apoyo a la PNP y otras gerencias, en presuntas infracciones | 1 353 | 52,2 |
| Emisión de alertas tempranas en apoyo a la PNP en presuntas faltas | 622 | 24,0 |
| Emisión de alertas tempranas en desastres, infraestructura, servicios y espacios públicos | 265 | 10,2 |
| Operativos | 176 | 6,8 |
| Ayuda y apoyo a personas y entidades | 113 | 4,4 |
| Emisión de alertas tempranas en apoyo a la PNP, en actividades presuntamente delictivas | 53 | 2,0 |
| Acontecimientos especiales | 10 | 0,4 |

Cobertura temporal (registros/día):

| Periodo | Días | Registros | Por día |
|---|---|---|---|
| Semana 11–17 may (parcial: 16–17) | 2 | 33 | 16,5 |
| Semana 18–24 may | 7 | 471 | 67,3 |
| Semana 25–31 may | 7 | 835 | 119,3 |
| Semana 1–7 jun | 7 | 917 | 131,0 |
| Semana 8–14 jun (parcial: 8–10) | 3 | 336 | 112,0 |
| **Mayo** | 16 | 1 339 | 83,7 |
| **Junio** | 10 | 1 253 | 125,3 |

Últimos días y censura: el 7 y 8 de junio, el 71 % de los registros se cerró después de más de 23 h; el 9 de junio, el 61 %; el **10 de junio, 0 %** (80 registros). El dataset excluye las incidencias "en proceso de atención", así que al día del corte le faltan las que se cerrarían automáticamente al día siguiente.

## 3. Criterios de viabilidad

| # | Criterio | Umbral mínimo | Valor | Cumple |
|---|---|---|---|---|
| 1 | Georreferenciación de punto | ≥ 90 % (deseable ≥ 98 %) | 100,0 % | Sí (deseable) |
| 2 | Fecha y hora o turno | 100 % | 100 %; turno coherente 2 592/2 592 | Sí |
| 3 | Tipo/subtipo | presente | 7 / 23 / 79; 5 de 7 tipos presentes en todas las semanas | Sí (catálogo no del todo estable) |
| 4 | Días consecutivos | ≥ 42 (deseable ≥ 90) | 26 | **No** |
| 5 | Volumen | ≥ 2 000 (deseable ≥ 50/día) | 2 592; 99,7/día | Sí (deseable) |
| 6 | Estabilidad de cobertura | sin cambios > 50 % sin explicar | +49,7 % entre meses; +77,3 % entre la 1.ª y la 2.ª semana completa | **No** |
| 7 | Licencia y fuente oficial | sí | ODC-By 1.0; MDSJM, Gerencia de Seguridad Ciudadana | Sí |
| 8 | Dentro del límite distrital | ≥ 90 % (deseable ≥ 98 %) | 98,77 % | Sí (deseable) |
| 9 | Sin datos personales | sí | Fuente anonimizada; barrido de DNI, teléfono, correo, placa y tratamiento: 0 | Sí |

## 4. Decisión

**A: usar el extracto existente** (en su CSV oficial), con las limitaciones documentadas. La búsqueda B no encontró extractos adicionales, y la C no encontró ningún distrito de Lima con datos de punto. El único conjunto con puntos y serie larga (Callao) no es claramente superior según la tabla. Detalle en `decision_dataset.md`.

## 5. Limitaciones de los datos

- **Sesgo de registro:** lo que se registra depende de dónde hay cámaras (74,5 % del CECOP) y patrullaje municipal. Los mapas resultantes muestran dónde mira el CCO, no la incidencia real ni el delito.
- **Selección por cierre:** solo se publican incidencias cerradas, lo que censura el final del periodo.
- **Puesta en marcha:** los primeros 6 días tienen un volumen anómalamente bajo (32/día).
- **Periodo corto:** 26 días impiden ver estacionalidad mensual y dan solo 3 o 4 repeticiones de cada día de la semana.
- **Objeto de estudio:** solo el 2,0 % son actividades presuntamente delictivas. El objeto es la incidencia de seguridad ciudadana, no el delito.
- **SIDPOL:** solo conteos mensuales por distrito y modalidad (90 272 denuncias en SJM entre 2018 y 2026-09, 10 383 en 2025). Sirve de contexto y no es comparable registro a registro con el CCO.
- **Población:** es una proyección distrital (437 390 hab. en 2026). No hay población por microzona, así que los conteos no son tasas.
- **Límite distrital:** es la capa INEI servida por la ANA (no la descarga directa del INEI). El área aproximada calculada es de unos 22,3 km².

## 6. Reproducción

```
.venv/Scripts/python.exe 02_documentacion/01_recoleccion/scripts/01_descargar.py --fecha 2026-10-31
.venv/Scripts/python.exe 02_documentacion/01_recoleccion/scripts/02_unificar.py
.venv/Scripts/python.exe 02_documentacion/01_recoleccion/scripts/03_normalizar.py
.venv/Scripts/python.exe 02_documentacion/01_recoleccion/scripts/04_perfilar_candidatos.py
.venv/Scripts/python.exe 02_documentacion/01_recoleccion/scripts/05_handoff.py
```

Dependencias: pandas, openpyxl, xlrd (para el `.xls` de San Isidro), shapely y requests. `01_descargar.py` no vuelve a descargar archivos que ya existen en la carpeta de la fecha (usar `--forzar` para refrescarlos). El paso 03 es determinista: el SHA-256 del canónico figura en `handoff_fase1.json`.

## Referencias

Autoridad Nacional del Agua. (s. f.). *Distritos* [Servicio de entidades geográficas, fuente INEI]. Recuperado el 31 de octubre de 2026, de https://geosnirh.ana.gob.pe/server/rest/services/Hosted/distritos/FeatureServer

Gobierno Regional del Callao. (2024). *Registros de hechos delictivos en la Provincia Constitucional del Callao* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/registros-de-hechos-delictivos-en-la-provincia-constitucional-del-callao-gobierno-regional

Instituto Nacional de Estadística e Informática. (2025). *Perú: Población total proyectada al 30 de junio de cada año, según departamento, provincia y distrito, 2018-2026* [Cuadro estadístico]. https://www.gob.pe/institucion/inei/informes-publicaciones/6894980-peru-poblacion-total-proyectada-al-30-de-junio-de-cada-ano-segun-departamento-provincia-y-distrito-2018-2026

Ministerio del Interior. (2026). *Denuncias policiales registradas a nivel nacional, enero 2018 a septiembre 2026* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/denuncias-policiales-registradas-nivel-nacional-mininter

Municipalidad Distrital de Jesús María. (2026). *Información estadística de incidencia delictiva* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/informaci%C3%B3n-estad%C3%ADstica-de-incidencia-delictiva-de-la-municipalidad-distrital-de-jes%C3%BAs-mar%C3%ADa

Municipalidad Distrital de Miraflores. (2021). *Emergencias atendidas por la Municipalidad de Miraflores* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/emergencias-atendidas-por-la-municipalidad-de-miraflores

Municipalidad Distrital de San Isidro. (2026). *MDSI - Seguridad Ciudadana, Tránsito y Gestión del Riesgo de Desastres* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/mdsi-seguridad-ciudadana-tr%C3%A1nsito-y-gesti%C3%B3n-del-riesgo-de-desastres

Municipalidad Distrital de San Juan de Miraflores. (2026). *Relación de incidencias atendidas por el Centro de Control de Operaciones (CCO) - Municipalidad Distrital de San Juan de Miraflores* (versión 1.0) [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/relaci%C3%B3n-de-incidencias-atendidas-por-el-centro-de-control-de-operaciones-cco-municipalidad

Municipalidad Distrital de San Martín de Porres. (2026). *Incidencias en el distrito de San Martín de Porres* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/incidencias-en-el-distrito-de-san-martin-de-porres

Municipalidad Provincial del Callao. (2025). *Incidencias observadas mediante cámaras de videovigilancia* [Conjunto de datos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/incidencias-observadas-mediante-c%C3%A1maras-de-videovigilancia-municipalidad-provincial-del

Open Data Commons. (s. f.). *Open Data Commons Attribution License (ODC-By) v1.0*. https://opendatacommons.org/licenses/by/1-0/
