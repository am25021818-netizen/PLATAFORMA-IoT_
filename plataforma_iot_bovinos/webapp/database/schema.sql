-- ============================================================
-- BOVINOS IoT - Valle del Mezquital, Hidalgo
-- Schema con Autenticación RBAC, Password Hash y Multi-Ranchos
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. Tabla de Usuarios con roles y contraseña hasheada
CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    correo          TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    rol             TEXT NOT NULL CHECK(rol IN ('administrador','propietario','operador_campo','tecnico_mantenimiento')),
    telefono        TEXT,
    activo          INTEGER DEFAULT 1,
    creado_en       TEXT DEFAULT (datetime('now','localtime'))
);

-- 2. Tabla de Ranchos / Locaciones en el Valle del Mezquital
-- Un propietario puede ser dueño de múltiples ranchos
CREATE TABLE IF NOT EXISTS ranchos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    propietario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    nombre          TEXT NOT NULL,
    municipio       TEXT NOT NULL,
    estado          TEXT NOT NULL DEFAULT 'Hidalgo',
    lat_centro      REAL,
    lon_centro      REAL,
    superficie_ha   REAL,
    creado_en       TEXT DEFAULT (datetime('now','localtime'))
);

-- 3. Tabla de Potreros / Áreas de pastoreo dentro de un rancho
CREATE TABLE IF NOT EXISTS potreros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    rancho_id       INTEGER NOT NULL REFERENCES ranchos(id),
    nombre          TEXT NOT NULL,
    lat_centro      REAL NOT NULL,
    lon_centro      REAL NOT NULL,
    radio_m         REAL DEFAULT 500.0,
    superficie_ha   REAL,
    activo          INTEGER DEFAULT 1
);

-- 4. Asignación de Operadores / Encargados a Ranchos específicos
CREATE TABLE IF NOT EXISTS usuarios_ranchos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id),
    rancho_id       INTEGER NOT NULL REFERENCES ranchos(id),
    UNIQUE(usuario_id, rancho_id)
);

-- 5. Tabla de Dispositivos Hardware (Heltec ESP32 LoRa v2)
CREATE TABLE IF NOT EXISTS dispositivos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_id          TEXT UNIQUE NOT NULL,
    tipo            TEXT NOT NULL CHECK(tipo IN ('collar','gateway')),
    nombre          TEXT NOT NULL,
    rancho_id       INTEGER REFERENCES ranchos(id),
    firmware_ver    TEXT DEFAULT '1.2.0',
    bateria_pct     INTEGER DEFAULT 100,
    ultima_conexion TEXT,
    activo          INTEGER DEFAULT 1
);

-- 6. Tabla de Animales (Bovinos)
CREATE TABLE IF NOT EXISTS animales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arete           TEXT UNIQUE NOT NULL,
    nombre          TEXT NOT NULL,
    raza            TEXT NOT NULL,
    sexo            TEXT NOT NULL CHECK(sexo IN ('Macho','Hembra')),
    peso_kg         REAL,
    propietario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    rancho_id       INTEGER NOT NULL REFERENCES ranchos(id),
    potrero_id      INTEGER REFERENCES potreros(id),
    collar_id       INTEGER REFERENCES dispositivos(id),
    color_pelaje    TEXT,
    fecha_nacimiento TEXT,
    activo          INTEGER DEFAULT 1
);

-- 7. Tabla de Lecturas GPS de Telemetría
CREATE TABLE IF NOT EXISTS lecturas_gps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id       INTEGER NOT NULL REFERENCES animales(id),
    dispositivo_id  INTEGER REFERENCES dispositivos(id),
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    altitud_m       REAL DEFAULT 0,
    velocidad_kmh   REAL DEFAULT 0,
    hdop            REAL DEFAULT 1.0,
    satelites       INTEGER DEFAULT 0,
    bateria_pct     INTEGER DEFAULT 100,
    rssi_lora       INTEGER DEFAULT -100,
    timestamp_utc   TEXT DEFAULT (datetime('now','localtime'))
);

-- 8. Tabla de Alertas
CREATE TABLE IF NOT EXISTS alertas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id       INTEGER REFERENCES animales(id),
    dispositivo_id  INTEGER REFERENCES dispositivos(id),
    tipo            TEXT NOT NULL CHECK(tipo IN ('sin_comunicacion','bateria_baja','fuera_geocerca','velocidad_anormal','dispositivo_caido')),
    mensaje         TEXT,
    lat             REAL,
    lon             REAL,
    atendida        INTEGER DEFAULT 0,
    atendida_por    INTEGER REFERENCES usuarios(id),
    creada_en       TEXT DEFAULT (datetime('now','localtime')),
    atendida_en     TEXT
);

-- Índices de consulta rápida
CREATE INDEX IF NOT EXISTS idx_animales_propietario ON animales(propietario_id);
CREATE INDEX IF NOT EXISTS idx_animales_rancho      ON animales(rancho_id);
CREATE INDEX IF NOT EXISTS idx_ranchos_propietario  ON ranchos(propietario_id);
CREATE INDEX IF NOT EXISTS idx_lecturas_animal      ON lecturas_gps(animal_id);
CREATE INDEX IF NOT EXISTS idx_lecturas_ts          ON lecturas_gps(timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_alertas_atend        ON alertas(atendida);
