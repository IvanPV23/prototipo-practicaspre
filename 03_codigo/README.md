# Priorización preventiva de microzonas — San Juan de Miraflores

Prototipo local de **apoyo a la decisión de patrullaje**. A partir de las incidencias registradas por el Centro de Control de Operaciones (CCO) de la Municipalidad de San Juan de Miraflores (datos abiertos, 16 may–10 jun 2026), el sistema:

1. divide el distrito en **microzonas** de 500 m (86 activas);
2. estima con aprendizaje automático el **nivel de incidencias registradas** (Bajo / Medio / Alto) por microzona y turno;
3. ordena las microzonas por una **prioridad sugerida explicable** P = w1·R + w2·G + w3·F (nivel estimado, gravedad histórica y frecuencia reciente) con pesos ajustables;
4. lo muestra en una **aplicación web local** con ranking, mapa, ficha de detalle, tablero, recursos (segundo nivel) y metodología.

> Los niveles reflejan incidencias registradas por el CCO en el periodo analizado, no delitos ni una condición permanente de la zona. Úselos como apoyo; la decisión final es del operador.

## Requisitos

- Windows 10 u 11 (también funciona en Linux o macOS), **Python 3.10 o superior**, unos 600 MB libres.
- Conexión a internet solo para instalar paquetes y para las teselas del mapa base (OpenStreetMap).
- Los datos de entrada están en `../02_documentacion/` (fases 1 y 2) y no se descargan.

## De cero a la app abierta (Windows, PowerShell)

Copie y pegue, desde la carpeta raíz del proyecto (la que contiene `01_alcance/`, `02_documentacion/` y `03_codigo/`):

```powershell
# 1) Entorno virtual (si ya existe .venv puede omitir esta línea)
python -m venv .venv

# 2) Dependencias y paquete
cd 03_codigo
..\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
..\.venv\Scripts\python -m pip install -e . --no-deps

# 3) Pipeline completo: base SQLite, microzonas, modelos, predicciones y ranking (~1 min)
..\.venv\Scripts\python -m seguridad_ciudadana todo

# 4) Aplicación web (se abre en http://localhost:8501)
..\.venv\Scripts\streamlit run app/Inicio.py
```

Para detener la app, use `Ctrl + C` en la terminal.

### Comandos del pipeline

| Comando | Qué hace |
|---|---|
| `python -m seguridad_ciudadana init-db` | Crea o actualiza el esquema SQLite (`data/seguridad.db`) |
| `python -m seguridad_ciudadana ingestar` | Carga el CSV canónico de la Fase 1 y **verifica su sha256** contra el handoff |
| `python -m seguridad_ciudadana construir` | Microzonas, observaciones microzona × fecha × turno (con ceros), objetivo y variables sin fuga |
| `python -m seguridad_ciudadana entrenar` | Persistencia, regresión logística, Random Forest y Gradient Boosting; selección por validación, evaluación única en prueba y registro |
| `python -m seguridad_ciudadana predecir` | Predicciones del modelo vigente para las fechas de prueba (demostración) y la fecha operativa (9 jun) |
| `python -m seguridad_ciudadana priorizar` | R, G, F y P con los pesos por defecto |
| `python -m seguridad_ciudadana todo` | Todo lo anterior en orden (idempotente) + `reportes/resultado_fase3.json` |

Opciones: `--config RUTA` (otra configuración) y `-v` (log detallado).

### Tests y calidad

```powershell
..\.venv\Scripts\python -m pytest        # 66 tests: esquema, ingesta, no fuga, partición, tabla, priorización,
                                          # recursos, reproducibilidad, servicios, modelos y humo de las 7 páginas
..\.venv\Scripts\python -m ruff check .
```

## Resultados

Partición temporal: entrenamiento 22–31 may, validación 1–4 jun, prueba 5–8 jun. El 9 y el 10 de junio están incompletos en la fuente y no se usan. Los modelos de ML se calibran con validación (v1.1.0, ADR 0007) y el modelo se elige por Macro F1 en validación.

| Modelo | Macro F1 validación* | Macro F1 prueba | IC 95 % prueba** | % Alto predicho en prueba |
|---|---|---|---|---|
| Línea base (persistencia) | 0,439 | 0,432 | [0,416; 0,452] | 12,5 % |
| **Regresión logística (vigente)** | **0,480** | 0,435 | [0,406; 0,456] | 22,5 % |
| Random Forest | 0,477 | **0,448** | [0,422; 0,466] | 11,1 % |
| Gradient Boosting | 0,475 | 0,441 | [0,416; 0,465] | 11,2 % |

\* Modelos de ML: dejando un día fuera tras calibrar. \*\* Bootstrap remuestreando días completos (2 000 réplicas). Proporción de Alto observada en prueba: 13,8 %. Hay más detalle por clase, día y turno en `reportes/` y en la página Metodología.

- **Calibración (v1.1.0):** sin calibrar, la regresión logística marcaba Alto en el 34,3 % de prueba, con un Macro F1 de 0,418. Calibrada marca un 22,5 % y obtiene 0,435, y sus probabilidades coinciden con las frecuencias observadas. La prueba ya se había leído una vez con v1.0.0, así que estas cifras son una segunda lectura (ver `docs/adr/0007-calibracion-posterior.md`).
- **H1 (ensamble > regresión logística y > persistencia en prueba): se sostiene, débilmente.** Random Forest obtiene 0,448, frente a 0,435 y 0,432, pero los intervalos se solapan y la prueba son 4 días.
- **HE1 (historial más importante que calendario): se sostiene.** Al permutar el bloque de historial, el Macro F1 en validación cae 0,142, frente a 0,044 del calendario. Ocurre lo mismo en los tres modelos.
- La reconstrucción coincide exactamente con la Fase 2: 2 580 incidencias limpias, 86 microzonas, 4 644 filas, la misma distribución de clases y persistencia con Macro F1 0,439 en validación.

## Estructura

```
03_codigo/
├── README.md, CHANGELOG.md, requirements*.txt, pyproject.toml
├── config/config.yaml        # rutas, microzona, partición, pesos, semillas, grillas
├── src/seguridad_ciudadana/  # paquete por capas (db, ingesta, espacial, features, modelos,
│                             #   priorizacion, recursos, servicios) + CLI (__main__.py)
├── app/                      # Streamlit: Inicio.py, pages/1..6, componentes/, tema.py
├── .streamlit/config.toml    # tema con los tokens del design system
├── data/                     # seguridad.db (se genera)
├── modelos/                  # artefactos .joblib versionados (se generan)
├── reportes/                 # métricas JSON, figuras PNG, resultado_fase3.json
├── tests/                    # pytest
└── docs/                     # arquitectura, modelo de datos, pipeline ML, model card, data card,
                              #   guía de desarrollo y ADRs
```

Documentación: [arquitectura](docs/arquitectura.md) · [modelo de datos](docs/modelo_datos.md) · [pipeline ML](docs/pipeline_ml.md) · [model card](docs/model_card.md) · [data card](docs/data_card.md) · [guía de desarrollo](docs/guia_desarrollo.md) · [ADRs](docs/adr/).

Informes de las fases anteriores:
- Fase 1, recolección: [`../02_documentacion/01_recoleccion/informe_recoleccion.md`](../02_documentacion/01_recoleccion/informe_recoleccion.md)
- Fase 2, análisis y preparación: [`../02_documentacion/02_analisis/informe_analisis.md`](../02_documentacion/02_analisis/informe_analisis.md) y [`especificacion_modelado.md`](../02_documentacion/02_analisis/especificacion_modelado.md)

## Solución de problemas

| Síntoma | Solución |
|---|---|
| `python` no se reconoce | Instale Python 3.10+ desde python.org marcando "Add python.exe to PATH", o use `py -3.10` |
| `No module named seguridad_ciudadana` | Falta `python -m pip install -e . --no-deps` dentro de `03_codigo` (con el mismo intérprete) |
| La app dice "Ejecute: python -m seguridad_ciudadana todo" | No existe la base o el pipeline no terminó; ejecútelo y recargue |
| `sha256 … no coincide con el handoff` | El CSV canónico de la Fase 1 cambió; regenérelo con sus scripts |
| El mapa sale sin fondo | Sin internet no cargan las teselas de OpenStreetMap; las microzonas se ven igual |
| El puerto 8501 está ocupado | `streamlit run app/Inicio.py --server.port 8502` |
| PowerShell bloquea `Activate.ps1` | No hace falta activar: use las rutas `..\.venv\Scripts\python` como arriba |
| Quiero empezar de cero | Borre `data/seguridad.db` y ejecute `todo` (los recursos ingresados a mano se pierden) |

## Licencias y atribución

Datos: MDSJM (ODC-By 1.0). Límite distrital: INEI (servido por la ANA). Mapa base: © colaboradores de OpenStreetMap (ODbL). Código: MIT.
