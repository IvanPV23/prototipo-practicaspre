# Contratos entre fases

Fuente de verdad compartida por el orquestador y los tres subagentes. Si un subagente necesita cambiar un contrato, lo propone en su informe; no lo cambia por su cuenta. Todas las rutas son relativas a `RAIZ` (el directorio que contiene `01_alcance/`) y usan `/`.

---

## 1. Esquema canónico de incidencias

Archivo: `02_documentacion/01_recoleccion/datos/procesados/incidencias_canonico.csv` (UTF-8, separador `,`, una fila por incidencia).

| Columna | Tipo | Descripción | Rol |
|---|---|---|---|
| `id_incidencia` | texto | Identificador de la fuente; único | clave |
| `fuente_dataset` | texto | `id` de la fuente en `catalogo_fuentes.csv` | trazabilidad |
| `distrito` | texto | Nombre del distrito | contexto |
| `ubigeo_inei` | texto (6) | Ubigeo INEI del distrito (no el de la fuente si difiere) | contexto |
| `fecha` | `YYYY-MM-DD` | Fecha de registro | predictor (calendario) |
| `hora` | `HH:MM:SS` | Hora de registro | predictor (calendario) |
| `fecha_hora` | ISO 8601 | `fecha` + `hora`, hora local de Lima | orden temporal |
| `turno` | `Mañana` \| `Tarde` \| `Noche` | Turno según la fuente, validado contra la hora | unidad de modelado |
| `tipo` | texto | Tipo de incidencia (normalizado: mayúsculas, sin espacios dobles) | gravedad |
| `subtipo` | texto | Subtipo | gravedad |
| `modalidad` | texto | Modalidad | descriptivo |
| `zona` | texto, nulo | Zona según la fuente | descriptivo |
| `sector` | texto, nulo | Sector según la fuente; nulo si "sin asignar" | descriptivo |
| `lat` | real | Latitud WGS84 | ubicación |
| `lon` | real | Longitud WGS84 | ubicación |
| `dentro_distrito` | booleano | El punto cae dentro del límite distrital oficial | filtro |
| `canal_reporte` | texto | Canal (WhatsApp, cámaras, etc.) | descriptivo / sesgo |
| `tipo_reportante` | texto | Quién reporta | descriptivo / sesgo |
| `direccion` | texto, nulo | Dirección publicada por la fuente | solo para la ficha de detalle |
| `estado_final` | texto | **[POST]** Estado al cierre | prohibido como predictor |
| `fecha_hora_cierre` | ISO 8601 | **[POST]** Cierre | prohibido como predictor |
| `tiempo_respuesta_min` | entero | **[POST]** Tiempo de respuesta | prohibido como predictor |

Reglas:
- Las columnas **[POST]** se conocen después del evento. Nunca entran como variables del modelo.
- Columnas de la fuente que no estén en esta tabla se conservan en el dato crudo, no en el canónico, salvo que el investigador justifique añadirlas (se listan en `diccionario_fuente.md`).
- Nada de datos personales (nombres, DNI, teléfonos, placas, correos). Si la fuente los trae, no pasan al canónico.

---

## 2. Fase 1 → Fase 2: `02_documentacion/01_recoleccion/handoff_fase1.json`

```json
{
  "version": 1,
  "generado": "2026-10-31T12:00:00-05:00",
  "decision": "A | B | C",
  "justificacion_resumen": "Dos o tres frases.",
  "requiere_confirmacion_usuario": false,
  "distrito": {"nombre": "San Juan de Miraflores", "ubigeo_inei": "150133", "ubigeo_fuente": "150141"},
  "dataset_principal": {
    "ruta": "02_documentacion/01_recoleccion/datos/procesados/incidencias_canonico.csv",
    "registros": 0,
    "fecha_min": "YYYY-MM-DD",
    "fecha_max": "YYYY-MM-DD",
    "dias_cubiertos": 0,
    "pct_georreferenciado": 0.0,
    "pct_dentro_distrito": 0.0,
    "sha256": "hex"
  },
  "alternativa": {
    "descripcion": "Solo si decision = C: dataset del distrito original listo para usar si el usuario rechaza el cambio.",
    "ruta": null
  },
  "fuentes": [
    {
      "id": "cco_mdsjm_2026",
      "nombre": "",
      "institucion": "",
      "url": "",
      "licencia": "",
      "fecha_descarga": "YYYY-MM-DD",
      "ruta_raw": "02_documentacion/01_recoleccion/datos/raw/...",
      "sha256": "hex",
      "registros": 0,
      "uso": "entrenamiento | contexto | cartografia | exposicion"
    }
  ],
  "contexto": {
    "sidpol": {"ruta": null, "periodo": null},
    "limite_distrital": {"ruta": "02_documentacion/01_recoleccion/datos/cartografia/limite_distrito.geojson", "fuente": ""},
    "poblacion": {"ruta": null, "fuente": null}
  },
  "criterios_viabilidad": [
    {"criterio": "", "umbral": "", "valor": "", "cumple": true}
  ],
  "advertencias": []
}
```

Archivos obligatorios de la Fase 1:
- `informe_recoleccion.md`
- `decision_dataset.md` (registro de decisión: contexto, opciones A/B/C, criterios, decisión, consecuencias)
- `catalogo_fuentes.csv` (columnas = claves de cada objeto de `fuentes`)
- `diccionario_fuente.md`
- `datos/manifest.json` (lista de archivos crudos con url, fecha, sha256, tamaño)
- `datos/raw/…`, `datos/procesados/incidencias_canonico.csv`
- `datos/cartografia/limite_distrito.geojson` (si no se consigue, se explica en advertencias y `pct_dentro_distrito` se informa como `null`)
- `impacto_en_alcance.md` (solo si la decisión es C)
- `scripts/` con el código que descarga, unifica y normaliza (reejecutable)

---

## 3. Fase 2 → Fase 3: `02_documentacion/02_analisis/handoff_fase2.json`

```json
{
  "version": 1,
  "generado": "",
  "dataset_limpio": {
    "ruta": "02_documentacion/02_analisis/datos/incidencias_limpias.csv",
    "registros": 0,
    "reglas_limpieza": "02_documentacion/02_analisis/reglas_limpieza.md"
  },
  "microzona": {
    "metodo": "grilla | h3",
    "tamano_m": 500,
    "resolucion_h3": null,
    "crs_metrico": "EPSG:32718",
    "origen_grilla": [0.0, 0.0],
    "criterio_activa": "Celda dentro del límite con ≥1 incidencia en entrenamiento",
    "n_microzonas_activas": 0,
    "ruta_geojson": "02_documentacion/02_analisis/datos/microzonas.geojson",
    "alternativas_evaluadas": [{"tamano_m": 0, "pct_ceros": 0.0, "n_activas": 0, "comentario": ""}]
  },
  "unidad_modelado": "microzona x fecha x turno",
  "tabla_modelado": {"ruta": "02_documentacion/02_analisis/datos/tabla_modelado.csv", "filas": 0, "incluye_ceros": true},
  "objetivo": {
    "nombre": "nivel",
    "clases": ["Bajo", "Medio", "Alto"],
    "regla": "Descripción exacta y reproducible",
    "umbrales": {"Bajo": "conteo <= a", "Medio": "a < conteo <= b", "Alto": "conteo > b"},
    "calculado_sobre": "entrenamiento",
    "distribucion_por_particion": {"train": {}, "valid": {}, "test": {}}
  },
  "features": [
    {"nombre": "", "descripcion": "", "ventana": "", "tipo": "historial | calendario | espacial | contexto", "sin_fuga_porque": ""}
  ],
  "excluidas_por_fuga": ["estado_final", "fecha_hora_cierre", "tiempo_respuesta_min"],
  "particion_temporal": {
    "train": ["YYYY-MM-DD", "YYYY-MM-DD"],
    "valid": ["YYYY-MM-DD", "YYYY-MM-DD"],
    "test":  ["YYYY-MM-DD", "YYYY-MM-DD"]
  },
  "gravedad": {"ruta_tabla": "02_documentacion/02_analisis/datos/gravedad_por_tipo.csv", "metodo": ""},
  "linea_base": {"metodo": "persistencia", "macro_f1_valid": 0.0},
  "hipotesis": {"HE2": {"resultado": "se_sostiene | no_se_sostiene | no_concluyente", "evidencia": ""}},
  "recomendaciones_modelado": [],
  "advertencias": []
}
```

Reglas:
- `test` no se usa en la Fase 2 para nada más que contar filas y clases. Ninguna métrica se calcula sobre prueba en esta fase.
- Las fechas de las tres particiones son contiguas, ascendentes y sin solapamiento.
- Ningún nombre de `features` coincide con `excluidas_por_fuga`.

Archivos obligatorios de la Fase 2:
- `informe_analisis.md` (+ `informe_analisis.html` exportado)
- `notebooks/01_calidad.ipynb`, `02_temporal.ipynb`, `03_espacial.ipynb`, `04_preparacion_modelado.ipynb` ejecutados
- `figuras/*.png`
- `diccionario_datos.md`, `reglas_limpieza.md`, `especificacion_modelado.md`
- `datos/` (limpias, microzonas, tabla de modelado, gravedad)
- `requirements-analisis.txt`

---

## 4. Fase 3 → cierre: `03_codigo/reportes/resultado_fase3.json`

```json
{
  "version": 1,
  "generado": "",
  "modelos": [
    {"nombre": "persistencia", "macro_f1_valid": 0.0, "macro_f1_test": 0.0},
    {"nombre": "regresion_logistica", "macro_f1_valid": 0.0, "macro_f1_test": 0.0},
    {"nombre": "random_forest", "macro_f1_valid": 0.0, "macro_f1_test": 0.0},
    {"nombre": "gradient_boosting", "macro_f1_valid": 0.0, "macro_f1_test": 0.0}
  ],
  "modelo_seleccionado": {"nombre": "", "criterio": "Mejor Macro F1 en validación", "ruta_artefacto": ""},
  "hipotesis": {
    "H1": {"resultado": "se_sostiene | no_se_sostiene", "evidencia": ""},
    "HE1": {"resultado": "se_sostiene | no_se_sostiene | no_concluyente", "evidencia": ""}
  },
  "base_datos": {"ruta": "03_codigo/data/seguridad.db", "tablas": []},
  "tests": {"total": 0, "pasados": 0, "fallidos": 0},
  "comandos": {
    "instalar": "",
    "pipeline": "",
    "app": "",
    "tests": ""
  },
  "advertencias": []
}
```
