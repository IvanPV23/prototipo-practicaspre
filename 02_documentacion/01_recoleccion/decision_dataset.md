# Registro de decisión: dataset de la Fase 1

Fecha: 2026-10-31 · Estado: **decidido, decisión A** · Requiere confirmación del usuario: **no**

## 1. Contexto

El proyecto (Parte I, `01_alcance`) necesita incidencias georreferenciadas a nivel de punto, con fecha, hora o turno y tipo, durante el periodo más largo posible, para estimar niveles por microzona y turno con validación temporal (entrenamiento, validación y prueba por fechas).

El dataset del alcance es el extracto del CCO de la Municipalidad Distrital de San Juan de Miraflores (MDSJM): 2 592 incidencias del 16 de mayo al 10 de junio de 2026 (26 días). El propio documento reconoce que el periodo es corto. Hoy (2026-10-31) han pasado casi cinco meses desde el corte, así que lo primero era comprobar si había extractos nuevos.

## 2. Opciones evaluadas

| Opción | Qué implica | Resultado de la búsqueda |
|---|---|---|
| **A**: usar lo existente | Mantener el extracto del alcance y documentar sus limitaciones | Viable. El mismo extracto está publicado en CSV en el PNDA y corrige la corrupción de ID del Excel |
| **B**: complementar SJM | Unir extractos anteriores o posteriores del mismo dataset | **No hay material.** El dataset tiene una sola revisión (publicación inicial v1.0, 2026-06-10, autor `ereyes_munisjm`) y un solo CSV. El grupo de la MDSJM en el PNDA no tiene otros conjuntos del CCO. La ficha declara frecuencia mensual, pero no se publicó ninguna actualización. Los metadatos dicen que la cobertura empieza con el inicio de operaciones del sistema CCO, por lo que no cabe esperar datos anteriores al 16 de mayo |
| **C**: cambiar de distrito | Usar otro distrito de Lima con datos de punto claramente superiores | **Ningún distrito de la provincia de Lima publica incidencias con coordenadas.** San Isidro, San Martín de Porres, Jesús María y Miraflores no tienen coordenadas o publican agregados. El único conjunto con puntos y serie larga es el del **Callao**, que pertenece a otra provincia, no cumple los criterios 6 y 8 y no es claramente superior (ver §3) |

## 3. Criterios (evidencia numérica)

Dataset elegido (SJM, CCO), calculado por `scripts/03_normalizar.py`:

| # | Criterio | Mínimo | Valor | Cumple |
|---|---|---|---|---|
| 1 | Georreferenciación de punto | ≥ 90 % | 100,0 % | Sí |
| 2 | Fecha y hora | 100 % | 100 %; turno coherente con la hora en 2 592/2 592 | Sí |
| 3 | Tipo/subtipo | presente | 7 tipos / 23 subtipos / 79 modalidades | Sí |
| 4 | Días consecutivos | ≥ 42 | **26** | **No** |
| 5 | Volumen | ≥ 2 000 | 2 592 (99,7/día) | Sí |
| 6 | Estabilidad | sin cambios > 50 % sin explicar | mayo 83,7/día → junio 125,3/día (+49,7 %); semanas completas 67,3 → 119,3 → 131,0/día (**+77,3 %**) | **No** |
| 7 | Licencia y fuente oficial | sí | ODC-By 1.0, MDSJM | Sí |
| 8 | Dentro del límite | ≥ 90 % | 98,77 % | Sí |
| 9 | Sin datos personales | sí | 0 coincidencias en el barrido; fuente anonimizada | Sí |

Matriz comparativa (`datos/procesados/matriz_candidatos.csv`, generada por `scripts/04_perfilar_candidatos.py`; mínimos cumplidos de 9):

| Candidato | Prov. Lima | Registros | Periodo | Días consec. | % geo | Máx. cambio mensual | % dentro | Mínimos | Motivo principal |
|---|---|---|---|---|---|---|---|---|---|
| **SJM: CCO MDSJM** | sí | 2 592 | 2026-05-16 → 06-10 | 26 | 100,0 | 49,7 (semanal 77,3) | 98,8 | **7/9** | Falla 4 y 6 |
| Callao: cámaras MPC | **no** | 913 238 | 2023-10-13 → 2025-11-16 | 427 | 95,9 (0 % antes de jun-2024) | **116,8** | **86,0** | 7/9 | Otra provincia; inestable; sin subtipo; 44 % tránsito, 24 % ambientales, 3 % seguridad ciudadana; sin actualizar desde nov-2025 |
| San Isidro: apoyo por seguridad 2026 | sí | 39 224 | 2026-01-01 → 04-30 | 120 | **0** | 21,0 | n/a | 7/9 | LATITUD/LONGITUD vacías (solo dirección y sector) |
| San Martín de Porres: incidencias 1.er sem. | sí | 57 287 | 2026-01-01 → 06-30 | 181 | **0** | 27,6 | n/a | 6/9 | Solo comisaría; licencia no especificada |
| Jesús María: incidencia delictiva | sí | 791 | 2026-01-01 → 06-23 | 103 | **0** | 18,1 | n/a | 5/9 | Sin coordenadas ni hora |
| GORE Callao: hechos delictivos | no | 2 643 | feb-2024 (registro) | 54 | 99,8 | 1 018 | n/a | 6/9 | Un mes; **datos personales** (nacimiento, edad, sexo, ocupación) |
| Miraflores: emergencias | sí | 3 filas | 2020–2021 | 0 | n/a | n/a | n/a | 3/9 | Agregado mensual |

El Callao cumple holgadamente la longitud (criterio 4), pero no cumple la estabilidad (con cambios de 784 a 4 300 registros/día entre meses de 2025) ni el criterio de puntos dentro del límite. Además cambia el objeto de estudio: es mayormente tránsito y ambiente, y no tiene subtipo. Por eso no es "claramente superior", y está fuera de la provincia de Lima que fija el alcance.

## 4. Decisión

**A. Se mantiene San Juan de Miraflores y el mismo extracto del CCO**, tomado del CSV oficial del PNDA en lugar del Excel. Se complementa con contexto: límite INEI, SIDPOL mensual del distrito y población proyectada INEI. Los criterios 4 y 6 quedan como limitaciones documentadas, como ya admitía el alcance.

## 5. Consecuencias

**Para la Fase 2 (análisis y preparación):**
- Partición temporal con 26 días (78 periodos fecha-turno por microzona). Habrá que elegir un tamaño de microzona grande para evitar exceso de ceros.
- Evaluar si se excluye el arranque (16–21 may, 32 registros/día) del entrenamiento o se modela explícitamente. La ventana estable va del 22 de mayo al 9 de junio (19 días).
- El 2026-06-10 está censurado: el dataset solo incluye incidencias cerradas, faltan las que quedaron abiertas al corte y hay 0 % de cierres de más de 23 h. No usarlo como prueba sin corrección.
- Filtrar o tolerar los 32 puntos fuera del límite (`dentro_distrito`). Dos son errores groseros.
- Leer `ubigeo_inei` como texto. No usar `NIVEL`, que no está en el canónico, ni las columnas [POST].
- Con dos meses, la estacionalidad mensual es inobservable. El día de la semana solo tiene 3 o 4 repeticiones.

**Para la Fase 3 (modelo y aplicación):**
- Las métricas tendrán alta varianza (pocos días de prueba), así que conviene reportar intervalos o resultados por día y presentar el modelo como exploratorio.
- El sistema puede reentrenarse si llega un extracto nuevo: el flujo `01`→`05` lo incorpora sin cambios de código (fuentes `cco_mdsjm_*`, deduplicación por `ID_INCIDENCIA`).

**Acción sugerida al usuario (no bloqueante):** los metadatos indican actualización mensual y cortes a demanda desde el sistema interno. Solicitar a la MDSJM (`tecnologia@munisjm.gob.pe` o por la vía de transparencia) un extracto actualizado del mismo dataset es la forma más directa de cumplir el criterio 4 sin cambiar el alcance.
