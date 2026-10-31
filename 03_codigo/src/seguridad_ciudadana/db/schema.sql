-- Esquema de la base local (SQLite). Versión 1.
-- Basado en el modelo de datos del diseño (§5.4) con ampliaciones registradas en docs/adr/0002-sqlite-persistencia.md.
-- Idempotente: CREATE ... IF NOT EXISTS. La versión se guarda en PRAGMA user_version.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS fuente_datos (
    id              TEXT PRIMARY KEY,
    nombre          TEXT NOT NULL,
    institucion     TEXT,
    url             TEXT,
    licencia        TEXT,
    sha256          TEXT NOT NULL,          -- sha256 del CSV canónico cargado
    fecha_descarga  TEXT,
    registros       INTEGER NOT NULL CHECK (registros >= 0)
);

CREATE TABLE IF NOT EXISTS tipo_incidencia (
    id            INTEGER PRIMARY KEY,
    tipo          TEXT NOT NULL,
    tipo_corto    TEXT NOT NULL,
    subtipo       TEXT NOT NULL,
    subtipo_norm  TEXT NOT NULL,
    gravedad      REAL NOT NULL CHECK (gravedad BETWEEN 1 AND 5),
    justificacion TEXT,
    UNIQUE (tipo, subtipo)
);

CREATE TABLE IF NOT EXISTS microzona (
    id           TEXT PRIMARY KEY,
    col          INTEGER NOT NULL,
    fila         INTEGER NOT NULL,
    geojson      TEXT NOT NULL,             -- polígono WGS84 (GeoJSON geometry)
    centro_lat   REAL NOT NULL,
    centro_lon   REAL NOT NULL,
    frac_dentro  REAL NOT NULL CHECK (frac_dentro BETWEEN 0 AND 1),
    sector_ref   TEXT,                      -- sector más frecuente (referencial)
    activa       INTEGER NOT NULL CHECK (activa IN (0, 1)),
    UNIQUE (col, fila)
);

CREATE TABLE IF NOT EXISTS incidencia (
    id               TEXT PRIMARY KEY,
    fuente_id        TEXT NOT NULL REFERENCES fuente_datos (id),
    tipo_id          INTEGER REFERENCES tipo_incidencia (id),
    microzona_id     TEXT REFERENCES microzona (id),
    fecha            TEXT NOT NULL,
    hora             TEXT NOT NULL,
    turno            TEXT NOT NULL CHECK (turno IN ('Mañana', 'Tarde', 'Noche')),
    lat              REAL NOT NULL,
    lon              REAL NOT NULL,
    x_utm            REAL NOT NULL,
    y_utm            REAL NOT NULL,
    mz_col           INTEGER NOT NULL,
    mz_fila          INTEGER NOT NULL,
    sector           TEXT,
    zona             TEXT,
    canal_reporte    TEXT,
    tipo_reportante  TEXT,
    direccion        TEXT,
    dist_limite_m    REAL NOT NULL CHECK (dist_limite_m >= 0),
    periodo          TEXT NOT NULL CHECK (periodo IN ('arranque', 'estable', 'censurado')),
    excluida         INTEGER NOT NULL CHECK (excluida IN (0, 1)),   -- 1 = fuera del límite + tolerancia
    gravedad         REAL
);
CREATE INDEX IF NOT EXISTS ix_incidencia_mz_fecha ON incidencia (microzona_id, fecha);
CREATE INDEX IF NOT EXISTS ix_incidencia_fecha ON incidencia (fecha, turno);

CREATE TABLE IF NOT EXISTS observacion (
    id            INTEGER PRIMARY KEY,
    microzona_id  TEXT NOT NULL REFERENCES microzona (id),
    fecha         TEXT NOT NULL,
    turno         TEXT NOT NULL CHECK (turno IN ('Mañana', 'Tarde', 'Noche')),
    conteo        INTEGER CHECK (conteo IS NULL OR conteo >= 0),   -- NULL en la fecha operativa (futuro)
    nivel         TEXT CHECK (nivel IS NULL OR nivel IN ('Bajo', 'Medio', 'Alto')),
    particion     TEXT NOT NULL CHECK (particion IN ('train', 'valid', 'test', 'operativa')),
    UNIQUE (microzona_id, fecha, turno)
);

CREATE TABLE IF NOT EXISTS feature (
    observacion_id  INTEGER NOT NULL REFERENCES observacion (id) ON DELETE CASCADE,
    nombre          TEXT NOT NULL,
    valor           REAL,
    PRIMARY KEY (observacion_id, nombre)
);

CREATE TABLE IF NOT EXISTS ejecucion_pipeline (
    id       INTEGER PRIMARY KEY,
    comando  TEXT NOT NULL,
    inicio   TEXT NOT NULL,
    fin      TEXT,
    estado   TEXT NOT NULL CHECK (estado IN ('en_curso', 'ok', 'error')),
    detalle  TEXT
);

CREATE TABLE IF NOT EXISTS modelo (
    id               INTEGER PRIMARY KEY,
    nombre           TEXT NOT NULL,
    version          TEXT NOT NULL,
    hiperparametros  TEXT NOT NULL,          -- JSON
    sha256_datos     TEXT NOT NULL,
    config_hash      TEXT NOT NULL,
    config           TEXT NOT NULL,          -- JSON de la configuración usada
    metricas         TEXT NOT NULL,          -- JSON (valid y test, por clase, por día y turno)
    macro_f1_valid   REAL NOT NULL,
    macro_f1_test    REAL,
    ruta_artefacto   TEXT,                   -- NULL para la persistencia (no tiene artefacto)
    vigente          INTEGER NOT NULL DEFAULT 0 CHECK (vigente IN (0, 1)),
    creado           TEXT NOT NULL,
    ejecucion_id     INTEGER REFERENCES ejecucion_pipeline (id),
    UNIQUE (nombre, version)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_modelo_un_vigente ON modelo (vigente) WHERE vigente = 1;

CREATE TABLE IF NOT EXISTS prediccion (
    id            INTEGER PRIMARY KEY,
    modelo_id     INTEGER NOT NULL REFERENCES modelo (id),
    microzona_id  TEXT NOT NULL REFERENCES microzona (id),
    fecha         TEXT NOT NULL,
    turno         TEXT NOT NULL CHECK (turno IN ('Mañana', 'Tarde', 'Noche')),
    nivel         TEXT NOT NULL CHECK (nivel IN ('Bajo', 'Medio', 'Alto')),
    p_bajo        REAL NOT NULL CHECK (p_bajo BETWEEN 0 AND 1),
    p_medio       REAL NOT NULL CHECK (p_medio BETWEEN 0 AND 1),
    p_alto        REAL NOT NULL CHECK (p_alto BETWEEN 0 AND 1),
    tipo_fecha    TEXT NOT NULL CHECK (tipo_fecha IN ('demostracion', 'operativa')),
    UNIQUE (modelo_id, microzona_id, fecha, turno)
);
CREATE INDEX IF NOT EXISTS ix_prediccion_fecha ON prediccion (fecha, turno);

CREATE TABLE IF NOT EXISTS prioridad (
    prediccion_id  INTEGER PRIMARY KEY REFERENCES prediccion (id) ON DELETE CASCADE,
    r         REAL NOT NULL CHECK (r BETWEEN 0 AND 1),
    g         REAL NOT NULL CHECK (g BETWEEN 0 AND 1),
    f         REAL NOT NULL CHECK (f BETWEEN 0 AND 1),
    w1        REAL NOT NULL CHECK (w1 BETWEEN 0 AND 1),
    w2        REAL NOT NULL CHECK (w2 BETWEEN 0 AND 1),
    w3        REAL NOT NULL CHECK (w3 BETWEEN 0 AND 1),
    p         REAL NOT NULL CHECK (p BETWEEN 0 AND 1),
    posicion  INTEGER NOT NULL CHECK (posicion >= 1)
);

CREATE TABLE IF NOT EXISTS recurso_disponible (
    id        INTEGER PRIMARY KEY,
    fecha     TEXT NOT NULL,
    turno     TEXT NOT NULL CHECK (turno IN ('Mañana', 'Tarde', 'Noche')),
    tipo      TEXT NOT NULL,
    cantidad  INTEGER NOT NULL CHECK (cantidad >= 0),
    UNIQUE (fecha, turno, tipo)
);

CREATE TABLE IF NOT EXISTS asignacion (
    id            INTEGER PRIMARY KEY,
    recurso_id    INTEGER NOT NULL REFERENCES recurso_disponible (id) ON DELETE CASCADE,
    microzona_id  TEXT NOT NULL REFERENCES microzona (id),
    cantidad      INTEGER NOT NULL CHECK (cantidad > 0),
    creado        TEXT NOT NULL
);

-- Defensa en profundidad: además de la validación del servicio, la base rechaza asignar más de lo disponible.
CREATE TRIGGER IF NOT EXISTS tg_asignacion_no_excede
BEFORE INSERT ON asignacion
FOR EACH ROW
WHEN (SELECT COALESCE(SUM(cantidad), 0) FROM asignacion WHERE recurso_id = NEW.recurso_id) + NEW.cantidad
     > (SELECT cantidad FROM recurso_disponible WHERE id = NEW.recurso_id)
BEGIN
    SELECT RAISE(ABORT, 'asignacion_excede_disponible');
END;

CREATE TRIGGER IF NOT EXISTS tg_recurso_no_menor_que_asignado
BEFORE UPDATE OF cantidad ON recurso_disponible
FOR EACH ROW
WHEN NEW.cantidad < (SELECT COALESCE(SUM(cantidad), 0) FROM asignacion WHERE recurso_id = NEW.id)
BEGIN
    SELECT RAISE(ABORT, 'disponible_menor_que_asignado');
END;

PRAGMA user_version = 1;
