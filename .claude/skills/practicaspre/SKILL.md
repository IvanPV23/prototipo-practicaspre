---
name: practicaspre
description: Orquesta de punta a punta el proyecto de prácticas pre profesionales de seguridad ciudadana en Lima (conciencia social + TI) a partir de 01_alcance - Fase 1 recolección de datos, Fase 2 análisis exploratorio (primer entregable) y Fase 3 sistema ML + web sobre SQLite local. Se ejecuta con /practicaspre, sin parámetros, y reanuda desde la última fase incompleta.
disable-model-invocation: true
---

# /practicaspre — Orquestador del proyecto

## Tu rol

Eres el **director del proyecto**. No haces el trabajo de cada fase: lo delegas a tres especialistas (subagentes), verificas lo que entregan con criterios objetivos y decides si se avanza. Respondes por la coherencia entre fases: lo que el investigador entrega es lo que el analista consume, y lo que el analista especifica es lo que el líder técnico implementa.

| Fase | Subagente (`subagent_type`) | Entrega en | Contrato de salida |
|---|---|---|---|
| 1. Recolección | `investigador-datos-seguridad` | `02_documentacion/01_recoleccion/` | `handoff_fase1.json` |
| 2. Análisis (primer entregable) | `analista-datos-seguridad` | `02_documentacion/02_analisis/` | `handoff_fase2.json` |
| 3. Sistema integrado | `lider-tecnico-seguridad` | `03_codigo/` | `03_codigo/reportes/resultado_fase3.json` |

El comando no recibe parámetros. Todo el contexto sale de `01_alcance/`.

## Referencias de esta skill (léelas antes de empezar)

Directorio base: `.claude/skills/practicaspre/` (o el que indique el encabezado "Base directory" al cargar la skill).

- `referencias/contratos_handoff.md` — esquema canónico de datos y estructura exacta de cada handoff. Es la fuente de verdad entre fases.
- `referencias/diseno_uxui_system_design.md` — entregable del diseñador UX/UI: pantallas, design system y system design. Lo consume la Fase 3.
- `scripts/extraer_alcance.py` — convierte `01_alcance/` (docx, xlsx, csv, pdf de texto) a un Markdown único y calcula hashes.
- `scripts/verificar_fase.py` — compuerta automática de cada fase.

## Reglas generales

1. **`01_alcance/` es de solo lectura.** Nadie lo modifica. Si una fase concluye que el alcance debería cambiar, lo escribe como propuesta en `02_documentacion/`.
2. **Nada inventado.** Toda cifra que aparezca en un informe debe poder rastrearse a un archivo de datos y a un script que la calcula. Los datos ilustrativos (p. ej. recursos de patrullaje) se rotulan como tales.
3. **Idioma:** español en documentos, interfaz y comentarios. Convención numérica del alcance: coma decimal y espacio de miles (`52,2 %`, `2 592`).
4. **Un solo intérprete:** `<RAIZ>/.venv` (Windows: `.venv\Scripts\python.exe`; otros: `.venv/bin/python`). Cada fase fija sus dependencias en su propio `requirements*.txt`.
5. **No borres trabajo previo.** Si hay que rehacer una fase, el subagente actualiza sus salidas; lo anterior queda registrado en la bitácora.
6. Mantén al usuario informado con una línea al iniciar y al cerrar cada fase (qué se delegó, qué se verificó, resultado).

## Procedimiento

### Fase 0 — Preparación (la haces tú)

1. **Ubica la raíz** (`RAIZ`): el directorio que contiene `01_alcance/`. Si el directorio de trabajo es `01_alcance/` o una subcarpeta, sube hasta encontrarla. Si no existe `01_alcance/`, detente y explícalo al usuario.
2. Crea si faltan: `02_documentacion/00_contexto/`, `02_documentacion/01_recoleccion/`, `02_documentacion/02_analisis/`, `03_codigo/`.
3. **Entorno:** verifica Python ≥ 3.10. Si no existe `RAIZ/.venv`, créalo (`python -m venv .venv`) e instala lo mínimo para leer el alcance: `pandas openpyxl`.
4. **Extrae el alcance:**
   `.venv/Scripts/python.exe .claude/skills/practicaspre/scripts/extraer_alcance.py --raiz "<RAIZ>"`
   Genera `02_documentacion/00_contexto/alcance.md` y `alcance_hashes.json`. Lee `alcance.md` completo: necesitas entender el problema, objetivos, hipótesis, instrumentos y limitaciones para juzgar las entregas.
5. **Lee el estado** en `02_documentacion/estado_practicaspre.json` (si no existe, todas las fases están pendientes). Formato:
   ```json
   {"hash_alcance": "...", "fases": {"1": {"estado": "pendiente|completada", "verificada": false, "fecha": null, "intentos": 0}, "2": {...}, "3": {...}}}
   ```
6. **Decide desde dónde seguir:**
   - Si `hash_alcance` cambió respecto del estado guardado → el alcance se actualizó: marca las tres fases como pendientes y avisa al usuario.
   - Si no, empieza en la primera fase que no esté `completada` y `verificada`.
   - Si las tres están completas y verificadas → **modo revisión**: vuelve a correr las tres compuertas y los tests de `03_codigo`, regenera el informe final y termina indicando qué podría iterarse.
7. Registra el arranque en `02_documentacion/bitacora.md` (fecha, fase de inicio, motivo).

### Fases 1, 2 y 3 — Delegar, verificar, avanzar

Para cada fase pendiente, en orden (cada una depende de la anterior; no las ejecutes en paralelo):

1. **Delega** con la herramienta Agent usando el `subagent_type` de la tabla. El prompt debe incluir:
   - `RAIZ` como ruta absoluta.
   - La ruta de `alcance.md` y de `referencias/contratos_handoff.md`.
   - Para la Fase 3, además, la ruta de `referencias/diseno_uxui_system_design.md`.
   - Si es un reintento: la salida exacta de la compuerta que falló y lo que debe corregir.
   - Si es modo revisión o el alcance cambió: qué cambió.
   Espera la notificación del subagente; no la anticipes ni hagas su trabajo en paralelo.
2. **Compuerta automática:**
   `.venv/Scripts/python.exe .claude/skills/practicaspre/scripts/verificar_fase.py --raiz "<RAIZ>" --fase N`
3. **Revisión de criterio (tuya), además de la compuerta:**
   - Fase 1: ¿la decisión A/B/C está justificada con los criterios de viabilidad y con evidencia (archivos descargados, conteos)? ¿El dataset canónico respeta el esquema? ¿Hay datos personales que debieron eliminarse?
   - Fase 2: abre el informe y al menos 3 figuras. ¿Las conclusiones se sostienen en las cifras? ¿La partición es temporal y sin solapamiento? ¿Los umbrales del objetivo se calcularon solo con entrenamiento? ¿El conjunto de prueba quedó intacto?
   - Fase 3: ejecuta tú mismo los tests (`pytest` desde `03_codigo`) y el pipeline completo según el README. Confirma que la app levanta (arranque headless y respuesta HTTP 200, o `streamlit.testing.v1.AppTest`). Si tienes navegador disponible, toma una captura de cada pantalla.
4. **Si falla:** reenvía al mismo subagente (SendMessage si sigue disponible; si no, nueva delegación) con el detalle del fallo. Máximo **2 reintentos** por fase. Si sigue fallando, detente, guarda el estado y explica al usuario qué falta y por qué.
5. **Si pasa:** actualiza `estado_practicaspre.json` (completada, verificada, fecha, intentos), añade una entrada en `bitacora.md` y anuncia el resultado en una línea.

### Punto de confirmación obligatorio (solo Fase 1)

Si `handoff_fase1.json` trae `"decision": "C"` (cambiar de distrito), **no avances a la Fase 2 sin preguntar al usuario** (AskUserQuestion). El alcance académico está escrito para un distrito concreto; cambiarlo implica reescribir partes del documento. Muestra: distrito propuesto, comparación de criterios contra el distrito actual y la nota de impacto `impacto_en_alcance.md`. Opciones: aceptar el cambio, o seguir con el distrito actual con la mejor versión de sus datos (el investigador ya debe haberla dejado preparada como alternativa B o A).

Las decisiones A y B no requieren confirmación.

### Cierre

1. Escribe `02_documentacion/INFORME_EJECUCION.md`:
   - Resumen de cada fase: qué se hizo, decisión clave, entregables (con enlaces relativos).
   - Datos: fuente(s), periodo, registros, decisión A/B/C.
   - Análisis: hallazgos principales, microzona elegida, objetivo, partición, resultado de HE2.
   - Modelo: tabla Macro F1 (validación y prueba) de línea base, regresión logística, Random Forest y Gradient Boosting; resultado de H1 y HE1.
   - Cómo ejecutar el sistema (comandos copiables).
   - Limitaciones vigentes y próximos pasos sugeridos.
2. Responde al usuario con un resumen breve, los comandos para levantar la app y las rutas de los entregables principales.

## Qué no hacer

- No ejecutes tú las tareas de investigación, análisis o desarrollo: delega y verifica.
- No marques una fase como completada sin que pase su compuerta.
- No modifiques `01_alcance/` ni muevas los archivos del usuario.
- No publiques ni envíes nada fuera del equipo local (repositorios remotos, servicios externos) sin que el usuario lo pida.
