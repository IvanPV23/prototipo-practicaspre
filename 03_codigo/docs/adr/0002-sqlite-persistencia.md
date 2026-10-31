# ADR 0002 — SQLite como persistencia y ampliaciones del modelo de datos

- **Estado:** aceptada (2026-10-31)
- **Contexto:** el sistema corre en una PC sin servidor de base de datos. Necesita guardar incidencias, microzonas, observaciones, variables, modelos, predicciones, prioridades y los recursos que ingresa el usuario, con trazabilidad.
- **Decisión:** usar SQLite (`data/seguridad.db`) con el módulo estándar `sqlite3`. El esquema está versionado en `db/schema.sql` (`PRAGMA user_version = 1`) y se aplica con `CREATE ... IF NOT EXISTS`. Cada conexión activa `PRAGMA foreign_keys = ON`, las escrituras van en transacciones explícitas y todo el SQL es parametrizado y vive en `db/`.
- **Ampliaciones del diagrama §5.4 del diseño:**
  1. `microzona` guarda también las celdas sin registros en entrenamiento (`activa = 0`, prefijo `SR-`), para el estado "Sin registros en el periodo" del mapa, y `col`, `fila` y `frac_dentro`.
  2. `incidencia` conserva los 2 592 registros con las marcas de limpieza (`excluida`, `periodo`, `dist_limite_m`), sus coordenadas UTM y la celda. **No guarda** `estado_final`, `fecha_hora_cierre` ni `tiempo_respuesta_min` (son [POST]).
  3. `observacion.particion` admite `operativa` (fecha futura sin objetivo).
  4. `modelo` incorpora `sha256_datos`, `config_hash`, `config`, `metricas` (JSON), `macro_f1_test` y `ejecucion_id`, y tiene un índice único parcial que permite **un solo modelo vigente**.
  5. `prediccion.tipo_fecha` toma los valores `demostracion` u `operativa`.
  6. Triggers `tg_asignacion_no_excede` y `tg_recurso_no_menor_que_asignado`: defensa en profundidad para la regla "no asignar más de lo disponible", que el servicio valida primero.
- **Consecuencias:** es un solo archivo portable y basta con borrarlo para reconstruir todo con `todo`. La concurrencia es limitada (un operador), suficiente para un prototipo local. `data/*.db` está en `.gitignore`.
