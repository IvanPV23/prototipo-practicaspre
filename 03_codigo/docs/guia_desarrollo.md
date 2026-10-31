# Guía de desarrollo

## Entorno

```powershell
cd 03_codigo
python -m venv ..\.venv            # o reutilice RAIZ\.venv
..\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
..\.venv\Scripts\python -m pip install -e . --no-deps
```

Calidad antes de entregar:

```powershell
..\.venv\Scripts\python -m ruff check .
..\.venv\Scripts\python -m ruff format .
..\.venv\Scripts\python -m pytest
```

Convenciones: nombres en español sin tildes (`snake_case`), type hints en funciones públicas, docstrings breves que expliquen el porqué y `logging` en lugar de `print`. SQL **solo** en `src/seguridad_ciudadana/db/`. La interfaz solo llama a `servicios`.

## Añadir un modelo

1. En `modelos/entrenamiento.py`, añada una rama en `construir_estimador` (y en `ajustar` si necesita `sample_weight`) y agregue el nombre a `MODELOS_ML`.
2. En `config/config.yaml` → `modelado.grillas`, añada su grilla (pequeña: se elige con valid).
3. En `dominio.py`, añada el nombre a `MODELOS` y a `NOMBRE_LEGIBLE_MODELO`.
4. Ejecute `python -m seguridad_ciudadana entrenar` (y luego `predecir` y `priorizar`, o `todo`). Si supera a los demás en validación, pasa a ser el vigente.
5. Los tests de `test_modelos.py` comprueban que quede registrado con trazabilidad.

## Añadir una variable (feature)

1. Calcúlela en `features/tabla.py::construir_tabla` usando **solo índices `< k`** (días anteriores a la fecha objetivo).
2. Agréguela a `features.lista` y al grupo que corresponda en `features.grupos` (config).
3. Si es categórica, añádala a `features.categoricas`. Si no es numérica, codifíquela en `codificar()` y, si su nombre choca con una columna de `observacion`, regístrela en `COLUMNA_DE_FEATURE`.
4. Añádala a la lista del test de no fuga si requiere un trato especial, y ejecute `pytest tests/test_no_fuga.py`.
5. Nota: `test_tabla_modelado.py` compara con la tabla de la Fase 2 solo las variables de esa tabla.

## Añadir una página

1. Cree `app/pages/N_Nombre.py` y copie el bloque inicial que agrega `app/` y `src/` a `sys.path`.
2. Llame a `configurar_pagina("Título")` y luego a `sel = barra_lateral()`. Eso le da fecha, turno y pesos, y controla los estados "sin base de datos" y "sin pipeline".
3. Pida los datos a un servicio (añada el método en `servicios/consultas.py` si hace falta) y cachee con `st.cache_data`.
4. Use los tokens de `app/tema.py`, el nivel siempre con texto y color, y el microcopy del diseño (§4.6).
5. `tests/test_app.py` la incluye automáticamente en la prueba de humo.

## Adaptar a otro distrito

1. Fase 1: genere el CSV canónico del distrito (mismo esquema) y su `handoff_fase1.json` con el sha256.
2. Consiga el límite distrital (GeoJSON) y, si cambia el tipo de incidencias, una tabla de gravedad con las columnas `tipo, tipo_corto, subtipo, subtipo_norm, gravedad, justificacion`.
3. En `config/config.yaml`, ajuste `proyecto` (nombre, ubigeo, cita), `rutas`, `datos` (fechas de inicio, arranque, censura y feriados), `microzona` (CRS métrico de la zona UTM y origen = esquina inferior izquierda del límite redondeada al tamaño de celda) y `particion`.
4. `objetivo.umbral_b_esperado` y los conteos de verificación salen del `handoff_fase2.json` del nuevo distrito.
5. Ejecute `python -m seguridad_ciudadana todo`. **No hace falta tocar código.**

## Estructura

```
src/seguridad_ciudadana/
  config.py         carga y valida config.yaml (dataclasses)
  dominio.py        constantes y reglas puras (turnos, niveles)
  db/               schema.sql, conexion.py, repositorios/ (único SQL)
  ingesta/          CSV canónico -> incidencias limpias (reglas de la Fase 2)
  espacial/         proyección, distancia al límite, grilla de microzonas
  features/         tabla microzona×fecha×turno, objetivo, variables sin fuga
  modelos/          linea_base, entrenamiento, evaluacion, registro, figuras
  priorizacion/     R, G, F, P
  recursos/         reglas de asignación
  servicios/        pipeline, priorizacion, consultas, recursos, resultado, dto
app/                Inicio.py, pages/, componentes/, tema.py
tests/              pytest (esquema, ingesta, no fuga, partición, tabla, priorización, recursos,
                    reproducibilidad, servicios, modelos, app)
```

## Solución de problemas en desarrollo

- `ErrorIngesta: sha256 … no coincide`: el CSV canónico cambió. Regenérelo con los scripts de la Fase 1 o actualice el handoff de forma consciente.
- La app muestra "Ejecute: python -m seguridad_ciudadana todo": falta la base o el pipeline no terminó. Revise la tabla `ejecucion_pipeline` (columna `detalle`).
- Para empezar desde cero, borre `data/seguridad.db`, `modelos/*.joblib` y `reportes/*` y ejecute `todo`. Los recursos ingresados a mano se pierden.
