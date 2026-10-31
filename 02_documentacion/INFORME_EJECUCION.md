# Informe de ejecución — /practicaspre

**Fecha:** 31 de octubre de 2026 · **Distrito:** San Juan de Miraflores (SJM), Lima · **Estado:** las tres fases están completadas y verificadas.

> Aclaración: en la conversación el distrito se mencionó como "SJL". El alcance y los datos corresponden a **San Juan de Miraflores (SJM)**, ubigeo INEI 150133.

| Fase | Responsable | Resultado | Entregables |
|---|---|---|---|
| 1. Recolección | Investigador | Aprobada (1.er intento) | [01_recoleccion/](01_recoleccion/) |
| 2. Análisis (primer entregable) | Analista | Aprobada (1.er intento) | [02_analisis/](02_analisis/) |
| 3. Sistema integrado | Líder técnico | Aprobada (1.er intento) | [../03_codigo/](../03_codigo/) |

Detalle cronológico: [bitacora.md](bitacora.md).

---

## Fase 1 — Datos

- **Decisión A:** se usa el extracto del CCO de la MDSJM tal cual. La fuente es el CSV oficial de la Plataforma Nacional de Datos Abiertos (licencia ODC-By 1.0), no el Excel de `01_alcance`.
  - **Por qué no el Excel:** al guardarlo, Excel alteró 67 IDs. Por ejemplo, convirtió `45184e36` en 4,5184E+40, y de ahí sale el ID "duplicado".
- **Periodo y volumen:** 2 592 incidencias del 16 de mayo al 10 de junio de 2026 (26 días). El 100 % tiene coordenadas y el 98,77 % cae dentro del límite INEI.
- **Por qué no B ni C:**
  - **B:** el conjunto tiene una sola versión publicada, sin extractos anteriores ni posteriores.
  - **C:** ningún distrito de la provincia de Lima publica incidencias con coordenadas. Se revisaron San Isidro, SMP, Jesús María y Miraflores. Del Callao se revisaron dos conjuntos (el provincial y el del GORE); el provincial, el único con puntos, es de otra provincia, inestable y no mejor.
- **Criterios no cumplidos:**
  - Días cubiertos: 26 frente a un mínimo de 42.
  - Estabilidad: entre meses el volumen cambia +49,7 %, justo en el límite.
- **Contexto reunido:** SIDPOL de SJM (90 272 denuncias, de enero de 2018 a septiembre de 2026), población INEI 2026 (437 390 habitantes) y límite distrital.
- **Columna `NIVEL` de la fuente:** la asigna el operador después de coordinar la atención (es [POST]), así que se excluye.

Documentos: [informe_recoleccion.md](01_recoleccion/informe_recoleccion.md), [decision_dataset.md](01_recoleccion/decision_dataset.md).

## Fase 2 — Análisis exploratorio

- **Limpieza:** quedan 2 580 incidencias. Se excluyeron 12 puntos fuera del límite.
  - **9 y 10 de junio:** son días incompletos, porque la fuente solo publica incidencias ya cerradas. Se excluyen.
  - **16 a 21 de mayo:** es el arranque del registro, con unas 32 incidencias por día. Se usa solo como historial.
- **Microzona:** grilla de 500 m (EPSG:32718), con **86 microzonas activas**.
- **Objetivo:** Bajo = 0, Medio = 1 y Alto ≥ 2 incidencias por microzona y turno. El umbral se fijó con los datos de entrenamiento. La tabla de modelado tiene 4 644 filas, incluidas las combinaciones sin incidencias.
- **Partición:**
  - Entrenamiento: 22–31 de mayo.
  - Validación: 1–4 de junio.
  - Prueba: 5–8 de junio.
- **Línea base de persistencia** (repetir el nivel del día anterior): Macro F1 de 0,439 en validación.
- **HE2 se sostiene (exploratorio):** el 14,0 % de las microzonas acumula el 50 % de los registros y el 33,1 % acumula el 80 % (Gini 0,63).
- **Sesgo de registro:** el 74,5 % de los registros proviene de cámaras CECOP y el 20,9 % no tiene sector.

Documentos: [informe_analisis.html](02_analisis/informe_analisis.html) (14 figuras), [especificacion_modelado.md](02_analisis/especificacion_modelado.md).

## Fase 3 — Modelo y sistema

Versión vigente: **v1.1.0, con calibración posterior** (ver la sección *Calibración* más abajo).

| Modelo | Macro F1 validación* | Macro F1 prueba | IC 95 % prueba | % Alto predicho en prueba |
|---|---|---|---|---|
| Persistencia (línea base) | 0,439 | 0,432 | [0,416; 0,452] | 12,5 % |
| Regresión logística (**seleccionado**) | **0,480** | 0,435 | [0,406; 0,456] | 22,5 % |
| Random Forest | 0,477 | **0,448** | [0,422; 0,466] | 11,1 % |
| Gradient Boosting | 0,475 | 0,441 | [0,416; 0,465] | 11,2 % |

\* Modelos de ML: validación calculada dejando un día fuera tras calibrar. En prueba, la proporción de Alto observada es 13,8 %.

- **Modelo elegido:** la regresión logística, por tener el mejor Macro F1 en validación (el margen sobre los otros dos es mínimo).
- **H1 se sostiene, débilmente:** Random Forest supera a la logística y a la persistencia en prueba, pero los intervalos se solapan y la prueba son solo 4 días.
- **HE1 se sostiene:** al permutar las variables de historial, el Macro F1 cae 0,142; al permutar las de calendario, cae 0,044.

### Calibración (v1.1.0, ADR 0007)

**Problema:** en v1.0.0 la regresión logística marcaba Alto en el 34,3 % de la prueba (hasta 44 % en un día), frente al 13,8 % observado. Es un efecto de `class_weight="balanced"`. Así el ranking pierde valor y se contradice el principio de no estigmatizar zonas.

**Solución:** se añadió una calibración ajustada **solo con validación**, en dos pasos:
1. **Probabilidades:** escalado de temperatura con un sesgo por clase. Ahora coinciden con lo observado: en prueba, p(Alto) promedia 0,14 frente al 13,8 % real.
2. **Decisión:** desplazamientos para Medio y Alto, elegidos por Macro F1.

**Resultado:**

| Regresión logística | v1.0.0 | v1.1.0 |
|---|---|---|
| Macro F1 en prueba | 0,418 | 0,435 (ahora supera a la persistencia, 0,432, por poco) |
| Alto predicho en prueba | 34,3 % | 22,5 % |
| Microzonas en Alto (9 jun, mañana) | 36 de 86 | 26 de 86 |

**Cautela:** la calibración se decidió sin mirar la prueba, pero la prueba ya se había leído una vez con v1.0.0. Las cifras de v1.1.0 son una segunda lectura del mismo periodo.
- **Sistema construido:**
  - Paquete Python por capas sobre SQLite, con 12 tablas y triggers que impiden asignar más recursos de los disponibles.
  - Línea de comandos `python -m seguridad_ciudadana`.
  - App Streamlit con 7 páginas: Inicio, Ranking, Mapa, Detalle, Tablero, Recursos y Metodología.
  - 66 tests y 6 ADR.
- **Verificación del orquestador:** pipeline completo OK, 66 de 66 tests, ruff limpio, y las 7 páginas cargan sin errores en el navegador.

Documentos: [README](../03_codigo/README.md), [model_card.md](../03_codigo/docs/model_card.md), [arquitectura.md](../03_codigo/docs/arquitectura.md).

## Cómo ejecutar

Ejecuta desde `03_codigo`, con el `.venv` de la raíz:

```powershell
..\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
..\.venv\Scripts\python -m pip install -e . --no-deps
..\.venv\Scripts\python -m seguridad_ciudadana todo
..\.venv\Scripts\streamlit run app/Inicio.py
..\.venv\Scripts\python -m pytest
```

## Limitaciones vigentes y próximos pasos

1. **El nivel Alto se sobreestima menos, pero todavía se sobreestima.**
   - **Situación:** tras la calibración, la regresión logística marca Alto en el 22,5 % de la prueba, frente al 13,8 % observado. Antes de calibrar era el 34,3 %.
   - **Posible causa:** la prueba incluye fin de semana y feriado, que validación no tiene.
   - **Siguiente paso:** cuando haya más días de datos, hay que recalibrar con una validación que incluya fines de semana.
2. **Hay pocos datos.** Son 18 días utilizables y la prueba cubre solo 4, así que las métricas tienen mucha varianza. Lo más valioso sería pedir a la MDSJM un extracto más reciente (tecnologia@munisjm.gob.pe o por transparencia). Si llega, basta con volver a ejecutar los scripts de la Fase 1 y `/practicaspre`.
3. **El volumen de registros cambia en el periodo.** Sube +32,7 % de una semana a otra, y la mayor parte viene de las cámaras.
4. **Los recursos de patrullaje son ilustrativos.** No provienen de la municipalidad.
5. **El documento del alcance tiene una errata de ubigeo.** El 150141 que publica la fuente corresponde a Surquillo en INEI; el de SJM es el 150133. Conviene corregirlo en la versión final del documento académico.
