import sqlite3
import datetime
from pathlib import Path
from config import DB_PATH, UMBRAL_RETRASO_SEG, UMBRAL_DESCONEXION_SEG

def get_connection():
    """Crea la conexión a la base de datos SQLite asegurando que la carpeta exista."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=25.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea el esquema relacional extendido y siembra datos realistas del Valle del Mezquital, Hidalgo."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Tabla de Ranchos / Unidades Pecuarias en el Valle del Mezquital
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ranchos (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            propietario TEXT NOT NULL,
            municipio TEXT NOT NULL,
            estado_geografico TEXT DEFAULT 'Hidalgo',
            lat_centro REAL,
            lon_centro REAL,
            superficie_ha REAL,
            activo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 2. Tabla de Potreros / Geocercas Operativas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS potreros (
            id TEXT PRIMARY KEY,
            rancho_id TEXT NOT NULL,
            nombre TEXT NOT NULL,
            tipo_pasto TEXT,
            lat_centro REAL NOT NULL,
            lon_centro REAL NOT NULL,
            radio_m REAL NOT NULL,
            color_hex TEXT DEFAULT '#2d6a4f',
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (rancho_id) REFERENCES ranchos(id)
        )
        """)

        # 3. Tabla de Usuarios y Roles
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            correo TEXT NOT NULL,
            rol TEXT NOT NULL, -- 'admin', 'ganadero', 'tecnico', 'vaquero'
            rancho_id TEXT,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (rancho_id) REFERENCES ranchos(id)
        )
        """)

        # 4. Tabla de Dispositivos (Hardware Real Heltec LoRa ESP32 v2)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispositivos (
            id TEXT PRIMARY KEY, -- 'HELTEC-COLLAR-01', 'HELTEC-GTW-01'
            tipo TEXT NOT NULL, -- 'collar', 'gateway'
            modelo TEXT DEFAULT 'Heltec LoRa ESP32 v2 (SX1276)',
            mac_address TEXT,
            frecuencia_mhz REAL DEFAULT 915.0,
            spreading_factor INTEGER DEFAULT 7,
            bandwidth_khz REAL DEFAULT 125.0,
            tx_power_dbm INTEGER DEFAULT 20,
            sync_word TEXT DEFAULT '0x34',
            bateria_pct INTEGER DEFAULT 100,
            voltaje_bateria REAL DEFAULT 4.1,
            rssi_dbm INTEGER,
            snr_db REAL,
            estado_operacion TEXT DEFAULT 'activo', -- 'activo', 'mantenimiento', 'baja'
            ultima_comunicacion TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 5. Tabla de Bovinos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS animales (
            id TEXT PRIMARY KEY, -- 'BOV-001'
            arete_siniga TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL, -- 'Toro', 'Vaca', 'Novillo', 'Semental', 'Vaquilla'
            raza TEXT NOT NULL, -- 'Simental', 'Charolais', 'Angus Negro', 'Suizo Europeo', 'Brahman'
            edad_meses INTEGER,
            peso_kg REAL,
            rancho_id TEXT NOT NULL,
            potrero_id TEXT,
            device_id TEXT UNIQUE,
            estado TEXT DEFAULT 'activo', -- 'activo', 'extraviado', 'enfermo', 'en_observacion'
            color_icono TEXT DEFAULT 'green',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rancho_id) REFERENCES ranchos(id),
            FOREIGN KEY (potrero_id) REFERENCES potreros(id),
            FOREIGN KEY (device_id) REFERENCES dispositivos(id)
        )
        """)

        # 6. Tabla de Lecturas GPS (Telemetría temporal)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lecturas_gps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            altitud_m REAL DEFAULT 0.0,
            velocidad_kmh REAL DEFAULT 0.0,
            bateria_pct INTEGER DEFAULT 100,
            rssi_dbm INTEGER,
            snr_db REAL,
            satelites INTEGER DEFAULT 0,
            fix_valido INTEGER DEFAULT 1,
            fuente_conexion TEXT DEFAULT 'lora_mqtt', -- 'lora_mqtt', 'serial_usb', 'simulacion'
            fecha_captura TIMESTAMP NOT NULL,
            fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animales(id),
            FOREIGN KEY (device_id) REFERENCES dispositivos(id)
        )
        """)

        # 7. Tabla de Alertas e Incidentes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL, -- 'desconexion', 'bateria_baja', 'fuera_potrero', 'sin_fix', 'sospecha_abigeato'
            animal_id TEXT,
            device_id TEXT,
            descripcion TEXT NOT NULL,
            nivel TEXT DEFAULT 'warning', -- 'info', 'warning', 'critical'
            lat REAL,
            lon REAL,
            atendida INTEGER DEFAULT 0,
            atendida_por TEXT,
            notas_atencion TEXT,
            fecha_atencion TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animales(id),
            FOREIGN KEY (device_id) REFERENCES dispositivos(id)
        )
        """)

        # Índices de aceleración
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lecturas_anim_fecha ON lecturas_gps(animal_id, fecha_captura)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dispositivos_lastcomm ON dispositivos(ultima_comunicacion)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_animales_rancho ON animales(rancho_id)")

        conn.commit()

        # Si no hay animales sembrados o hay menos de 5, resembrar con los datos completos del Valle del Mezquital
        cursor.execute("SELECT COUNT(*) FROM animales")
        if cursor.fetchone()[0] < 5:
            sembrar_datos_valle_del_mezquital(cursor)
            conn.commit()

def sembrar_datos_valle_del_mezquital(cursor):
    """Siembra catálogo integral de unidades pecuarias, potreros y hato en el Valle del Mezquital, Hgo."""
    # Limpiar tablas para resembrar ordenadamente
    cursor.execute("DELETE FROM lecturas_gps")
    cursor.execute("DELETE FROM alertas")
    cursor.execute("DELETE FROM animales")
    cursor.execute("DELETE FROM potreros")
    cursor.execute("DELETE FROM dispositivos")
    cursor.execute("DELETE FROM usuarios")
    cursor.execute("DELETE FROM ranchos")

    # 1. Ranchos en municipios emblemáticos del Valle del Mezquital
    ranchos = [
        ('RAN-01', 'Rancho San Isidro', 'Don Pedro Martínez Cruz', 'Huichapan', 'Hidalgo', 20.37542, -99.65431, 140.0, 1),
        ('RAN-02', 'Potrero Los Sabinos', 'Ing. Arturo Trejo Reséndiz', 'Tecozautla', 'Hidalgo', 20.53310, -99.63350, 95.0, 1),
        ('RAN-03', 'Agostadero El Mezquital', 'Familia Peña Gómez', 'Ixmiquilpan', 'Hidalgo', 20.48520, -99.21540, 210.0, 1)
    ]
    cursor.executemany("""
    INSERT INTO ranchos (id, nombre, propietario, municipio, estado_geografico, lat_centro, lon_centro, superficie_ha, activo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ranchos)

    # 2. Potreros con geocercas poligonales/radiales
    potreros = [
        ('POT-01', 'RAN-01', 'Potrero La Cantera (Huichapan)', 'Buffel / Matorral', 20.37540, -99.65430, 850.0, '#2d6a4f', 1),
        ('POT-02', 'RAN-01', 'Potrero El Mezquite (Huichapan)', 'Zacate Estrella', 20.37890, -99.65820, 600.0, '#40916c', 1),
        ('POT-03', 'RAN-02', 'Potrero Sabino Grande (Tecozautla)', 'Pasto Pangola', 20.53310, -99.63350, 750.0, '#52b788', 1),
        ('POT-04', 'RAN-03', 'Potrero Los Cardos (Ixmiquilpan)', 'Matorral Nativo', 20.48520, -99.21540, 900.0, '#1b4332', 1)
    ]
    cursor.executemany("""
    INSERT INTO potreros (id, rancho_id, nombre, tipo_pasto, lat_centro, lon_centro, radio_m, color_hex, activo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, potreros)

    # 3. Usuarios
    usuarios = [
        ('USR-01', 'admin', 'admin123', 'Ing. Iván Rodríguez Hernández', 'ivan.rodriguez@iteshu.edu.mx', 'admin', 'RAN-01'),
        ('USR-02', 'ganadero', 'vaca123', 'Don Pedro Martínez Cruz', 'pedro@rancho.mx', 'ganadero', 'RAN-01'),
        ('USR-03', 'vaquero', 'campo123', 'Juan Pérez Morales (Operador)', 'juan.vaquero@iteshu.edu.mx', 'vaquero', 'RAN-01'),
        ('USR-04', 'tecnico', 'tec123', 'M.C. Carlos Espinoza Galicia', 'carlos.espinoza@iteshu.edu.mx', 'tecnico', 'RAN-01')
    ]
    cursor.executemany("""
    INSERT INTO usuarios (id, username, password, nombre_completo, correo, rol, rancho_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, usuarios)

    # 4. Dispositivos Heltec LoRa ESP32 v2
    dispositivos = [
        ('HELTEC-COLLAR-01', 'collar', 'Heltec LoRa ESP32 v2', 'E0:5A:1B:77:4A:01', 915.0, 7, 125.0, 20, '0x34', 94, 4.12, -68, 9.5, 'activo', '2026-11-19 15:58:00'),
        ('HELTEC-COLLAR-02', 'collar', 'Heltec LoRa ESP32 v2', 'E0:5A:1B:77:4A:02', 915.0, 7, 125.0, 20, '0x34', 86, 3.98, -75, 8.2, 'activo', '2026-11-19 15:52:00'),
        ('HELTEC-COLLAR-03', 'collar', 'Heltec LoRa ESP32 v2', 'E0:5A:1B:77:4A:03', 915.0, 7, 125.0, 20, '0x34', 18, 3.42, -96, 4.8, 'activo', '2026-11-19 14:15:00'),
        ('HELTEC-COLLAR-04', 'collar', 'Heltec LoRa ESP32 v2', 'E0:5A:1B:77:4A:04', 915.0, 7, 125.0, 20, '0x34', 91, 4.08, -72, 8.9, 'activo', '2026-11-19 15:55:00'),
        ('HELTEC-COLLAR-05', 'collar', 'Heltec LoRa ESP32 v2', 'E0:5A:1B:77:4A:05', 915.0, 7, 125.0, 20, '0x34', 78, 3.90, -80, 7.5, 'activo', '2026-11-19 15:35:00'),
        ('HELTEC-COLLAR-06', 'collar', 'Heltec LoRa ESP32 v2', 'E0:5A:1B:77:4A:06', 915.0, 7, 125.0, 20, '0x34', 98, 4.18, -65, 10.2, 'activo', '2026-11-19 16:00:00'),
        ('HELTEC-GTW-01', 'gateway', 'Heltec LoRa ESP32 Base Station', 'E0:5A:1B:77:AA:01', 915.0, 7, 125.0, 20, '0x34', 100, 5.00, -52, 12.5, 'activo', '2026-11-19 16:02:00'),
        ('HELTEC-GTW-02', 'gateway', 'Heltec LoRa ESP32 Base Station', 'E0:5A:1B:77:AA:02', 915.0, 7, 125.0, 20, '0x34', 100, 5.00, -58, 11.8, 'activo', '2026-11-19 16:01:00')
    ]
    cursor.executemany("""
    INSERT INTO dispositivos (id, tipo, modelo, mac_address, frecuencia_mhz, spreading_factor, bandwidth_khz, tx_power_dbm, sync_word, bateria_pct, voltaje_bateria, rssi_dbm, snr_db, estado_operacion, ultima_comunicacion)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dispositivos)

    # 5. Animales en el Valle del Mezquital (Raza, arete, edad, peso)
    animales = [
        ('BOV-001', 'MX-13-8901-01', 'El Barón', 'Toro', 'Simental', 48, 840.0, 'RAN-01', 'POT-01', 'HELTEC-COLLAR-01', 'activo', 'green'),
        ('BOV-002', 'MX-13-8901-02', 'La Paloma', 'Vaca', 'Charolais', 36, 590.0, 'RAN-01', 'POT-01', 'HELTEC-COLLAR-02', 'activo', 'green'),
        ('BOV-003', 'MX-13-8901-03', 'El Pinto', 'Novillo', 'Suizo Europeo', 22, 450.0, 'RAN-01', 'POT-02', 'HELTEC-COLLAR-03', 'activo', 'red'),
        ('BOV-004', 'MX-13-8901-04', 'La Gitana', 'Vaca', 'Angus Negro', 42, 620.0, 'RAN-01', 'POT-02', 'HELTEC-COLLAR-04', 'activo', 'green'),
        ('BOV-005', 'MX-13-8901-05', 'El Huasteco', 'Semental', 'Brahman Blanco', 54, 910.0, 'RAN-02', 'POT-03', 'HELTEC-COLLAR-05', 'activo', 'orange'),
        ('BOV-006', 'MX-13-8901-06', 'La Canela', 'Vaquilla', 'Simbrah', 18, 385.0, 'RAN-01', 'POT-01', 'HELTEC-COLLAR-06', 'activo', 'green')
    ]
    cursor.executemany("""
    INSERT INTO animales (id, arete_siniga, nombre, categoria, raza, edad_meses, peso_kg, rancho_id, potrero_id, device_id, estado, color_icono)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, animales)

    # 6. Trayectorias realistas sobre la geografía del Valle del Mezquital
    lecturas = [
        # BOV-001 - El Barón (Recorrido activo en Huichapan - Potrero La Cantera)
        ('BOV-001', 'HELTEC-COLLAR-01', 20.37542, -99.65431, 2105.0, 1.2, 94, -68, 9.5, 9, 1, 'lora_mqtt', '2026-11-19 15:58:00'),
        ('BOV-001', 'HELTEC-COLLAR-01', 20.37590, -99.65480, 2106.5, 1.5, 94, -69, 9.3, 9, 1, 'lora_mqtt', '2026-11-19 15:45:00'),
        ('BOV-001', 'HELTEC-COLLAR-01', 20.37630, -99.65520, 2107.0, 0.8, 95, -70, 9.0, 8, 1, 'lora_mqtt', '2026-11-19 15:30:00'),
        ('BOV-001', 'HELTEC-COLLAR-01', 20.37680, -99.65590, 2108.2, 1.1, 95, -71, 8.8, 9, 1, 'lora_mqtt', '2026-11-19 15:15:00'),
        ('BOV-001', 'HELTEC-COLLAR-01', 20.37720, -99.65650, 2109.0, 0.4, 96, -72, 8.6, 8, 1, 'lora_mqtt', '2026-11-19 15:00:00'),

        # BOV-002 - La Paloma (Huichapan)
        ('BOV-002', 'HELTEC-COLLAR-02', 20.37480, -99.65390, 2104.0, 0.6, 86, -75, 8.2, 8, 1, 'lora_mqtt', '2026-11-19 15:52:00'),
        ('BOV-002', 'HELTEC-COLLAR-02', 20.37510, -99.65410, 2104.5, 0.5, 87, -76, 8.0, 8, 1, 'lora_mqtt', '2026-11-19 15:35:00'),

        # BOV-003 - El Pinto (Huichapan - En el límite del potrero con batería baja y desconexión)
        ('BOV-003', 'HELTEC-COLLAR-03', 20.36950, -99.64910, 2095.0, 0.0, 18, -96, 4.8, 5, 1, 'lora_mqtt', '2026-11-19 14:15:00'),

        # BOV-004 - La Gitana (Huichapan)
        ('BOV-004', 'HELTEC-COLLAR-04', 20.37820, -99.65750, 2110.0, 1.4, 91, -72, 8.9, 9, 1, 'lora_mqtt', '2026-11-19 15:55:00'),
        ('BOV-004', 'HELTEC-COLLAR-04', 20.37860, -99.65790, 2111.0, 0.9, 92, -73, 8.7, 9, 1, 'lora_mqtt', '2026-11-19 15:40:00'),

        # BOV-005 - El Huasteco (Tecozautla - Potrero Sabino Grande)
        ('BOV-005', 'HELTEC-COLLAR-05', 20.53320, -99.63360, 1840.0, 0.7, 78, -80, 7.5, 7, 1, 'lora_mqtt', '2026-11-19 15:35:00'),
        ('BOV-005', 'HELTEC-COLLAR-05', 20.53380, -99.63410, 1842.0, 1.0, 79, -82, 7.2, 7, 1, 'lora_mqtt', '2026-11-19 15:10:00'),

        # BOV-006 - La Canela (Huichapan)
        ('BOV-006', 'HELTEC-COLLAR-06', 20.37520, -99.65460, 2105.0, 1.8, 98, -65, 10.2, 10, 1, 'lora_mqtt', '2026-11-19 16:00:00')
    ]
    cursor.executemany("""
    INSERT INTO lecturas_gps (animal_id, device_id, lat, lon, altitud_m, velocidad_kmh, bateria_pct, rssi_dbm, snr_db, satelites, fix_valido, fuente_conexion, fecha_captura)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, lecturas)

    # 7. Alertas iniciales
    cursor.execute("""
    INSERT INTO alertas (tipo, animal_id, device_id, descripcion, nivel, lat, lon, atendida)
    VALUES ('bateria_baja', 'BOV-003', 'HELTEC-COLLAR-03', 'Batería en nivel crítico (18%). Se recomienda recargar o reemplazar celda LiPo en el collar.', 'critical', 20.36950, -99.64910, 0)
    """)
    cursor.execute("""
    INSERT INTO alertas (tipo, animal_id, device_id, descripcion, nivel, lat, lon, atendida)
    VALUES ('desconexion', 'BOV-003', 'HELTEC-COLLAR-03', 'Sin reporte LoRa por más de 100 minutos en la zona este de Huichapan.', 'warning', 20.36950, -99.64910, 0)
    """)

def obtener_ranchos():
    """Devuelve el catálogo de ranchos activos en el Valle del Mezquital."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ranchos WHERE activo = 1 ORDER BY nombre ASC")
        return [dict(r) for r in cursor.fetchall()]

def obtener_potreros(rancho_id: str = None):
    """Devuelve los potreros / geocercas asociadas a los ranchos."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if rancho_id:
            cursor.execute("SELECT * FROM potreros WHERE rancho_id = ? AND activo = 1", (rancho_id,))
        else:
            cursor.execute("SELECT * FROM potreros WHERE activo = 1")
        return [dict(r) for r in cursor.fetchall()]

def guardar_lectura(datos: dict, fuente: str = "lora_mqtt"):
    """Inserta una lectura GPS aplicando el fail-safe y actualiza dispositivo/alertas.

    Si el GPS no tiene fix o las coordenadas están fuera de rango, la telemetría
    se conserva pero la posición vigente sigue siendo la última válida conocida.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        device_id = datos.get("device_id")
        animal_id = datos.get("animal_id")

        # Si no viene animal_id, buscarlo por el dispositivo
        if not animal_id and device_id:
            cursor.execute("SELECT id FROM animales WHERE device_id = ?", (device_id,))
            row = cursor.fetchone()
            if row:
                animal_id = row["id"]
            else:
                animal_id = "BOV-001" # Default fallback si es collar no asignado

        fecha_captura = datos.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        lat_reportada = float(datos.get("lat", 0.0))
        lon_reportada = float(datos.get("lon", 0.0))
        bateria = int(datos.get("bateria_pct", 100))
        rssi = datos.get("rssi_dbm", -70)
        snr = datos.get("snr_db", 8.0)

        sin_fix = not bool(datos.get("fix_valido", True))
        fuera_de_rango = not (-90.0 <= lat_reportada <= 90.0 and -180.0 <= lon_reportada <= 180.0)
        fix_valido = 0 if (sin_fix or fuera_de_rango) else 1

        lat, lon = lat_reportada, lon_reportada
        tipo_alerta_sensor = None
        if fuera_de_rango:
            tipo_alerta_sensor = "coordenadas_invalidas"
            descripcion_sensor = (
                f"Coordenadas fuera de rango recibidas ({lat_reportada}, {lon_reportada}). "
                "Se conserva la última coordenada válida."
            )
        elif sin_fix:
            tipo_alerta_sensor = "sin_fix"
            descripcion_sensor = "GPS sin fix satelital. Se conserva la última coordenada válida; posición desactualizada."

        if fix_valido == 0:
            # Fail-safe: no sobreescribir con (0,0) ni con valores imposibles.
            cursor.execute("""
            SELECT lat, lon FROM lecturas_gps
            WHERE fix_valido = 1 AND (lat <> 0 OR lon <> 0)
              AND (? IS NULL OR device_id = ?)
              AND (? IS NULL OR animal_id = ?)
            ORDER BY id DESC LIMIT 1
            """, (device_id, device_id, animal_id, animal_id))
            fila_valida = cursor.fetchone()
            if fila_valida:
                lat, lon = float(fila_valida["lat"]), float(fila_valida["lon"])
            else:
                lat, lon = 0.0, 0.0

        # Inserción en histórico
        cursor.execute("""
        INSERT INTO lecturas_gps (
            animal_id, device_id, lat, lon, altitud_m, velocidad_kmh,
            bateria_pct, rssi_dbm, snr_db, satelites, fix_valido, fuente_conexion, fecha_captura
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            animal_id,
            device_id,
            lat,
            lon,
            float(datos.get("altitud_m", 2105.0)),
            float(datos.get("velocidad_kmh", 1.0)),
            bateria,
            rssi,
            snr,
            int(datos.get("satelites", 8)),
            fix_valido,
            fuente,
            fecha_captura
        ))

        # Actualizar dispositivo en tabla
        cursor.execute("""
        UPDATE dispositivos
        SET ultima_comunicacion = ?,
            bateria_pct = ?,
            rssi_dbm = ?,
            snr_db = ?
        WHERE id = ?
        """, (fecha_captura, bateria, rssi, snr, device_id))

        # Alerta automática de batería baja (<20%)
        if bateria < 20:
            cursor.execute("""
            INSERT INTO alertas (tipo, animal_id, device_id, descripcion, nivel, lat, lon, atendida)
            VALUES ('bateria_baja', ?, ?, ?, 'critical', ?, ?, 0)
            """, (animal_id, device_id, f"Batería crítica detectada ({bateria}%). Requiere reemplazo.", lat, lon))

        # Alerta de sensor, evitando duplicados abiertos para el mismo dispositivo.
        if tipo_alerta_sensor:
            cursor.execute("""
            SELECT id FROM alertas
            WHERE tipo = ? AND atendida = 0
              AND (? IS NULL OR device_id = ?)
            LIMIT 1
            """, (tipo_alerta_sensor, device_id, device_id))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO alertas (tipo, animal_id, device_id, descripcion, nivel, lat, lon, atendida)
                VALUES (?, ?, ?, ?, 'warning', ?, ?, 0)
                """, (tipo_alerta_sensor, animal_id, device_id, descripcion_sensor, lat, lon))

        conn.commit()

def obtener_ultimas_ubicaciones(filtro_rancho: str = None):
    """Devuelve la última coordenada conocida de cada bovino con cálculo de vigencia y distancia."""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
        SELECT 
            a.id AS animal_id,
            a.arete_siniga,
            a.nombre AS nombre_animal,
            a.categoria,
            a.raza,
            a.edad_meses,
            a.peso_kg,
            a.rancho_id,
            r.nombre AS nombre_rancho,
            r.municipio,
            p.nombre AS nombre_potrero,
            p.lat_centro AS pot_lat,
            p.lon_centro AS pot_lon,
            p.radio_m AS pot_radio,
            d.id AS device_id,
            d.bateria_pct,
            d.voltaje_bateria,
            d.rssi_dbm,
            d.snr_db,
            d.ultima_comunicacion,
            l.lat,
            l.lon,
            l.altitud_m,
            l.velocidad_kmh,
            l.satelites,
            l.fix_valido,
            l.fuente_conexion,
            l.fecha_captura
        FROM animales a
        JOIN ranchos r ON a.rancho_id = r.id
        LEFT JOIN potreros p ON a.potrero_id = p.id
        LEFT JOIN dispositivos d ON a.device_id = d.id
        LEFT JOIN (
            SELECT lg1.*
            FROM lecturas_gps lg1
            INNER JOIN (
                -- Fail-safe: un reporte (0,0) sin fix no puede convertirse en la posición vigente.
                SELECT animal_id, MAX(id) as max_id
                FROM lecturas_gps
                WHERE fix_valido = 1 OR (lat <> 0 OR lon <> 0)
                GROUP BY animal_id
            ) lg2 ON lg1.id = lg2.max_id
        ) l ON a.id = l.animal_id
        WHERE a.estado = 'activo'
        """
        params = []
        if filtro_rancho and filtro_rancho != "TODOS":
            query += " AND a.rancho_id = ?"
            params.append(filtro_rancho)

        cursor.execute(query, params)
        filas = cursor.fetchall()
        
        resultados = []
        ahora = datetime.datetime.now()
        
        for r in filas:
            f = dict(r)
            
            # Semáforo de vigencia (RF-07)
            estado_vig = "sin_comunicacion"
            color_vig = "red"
            seg_dif = 999999
            
            f_str = f.get("fecha_captura") or f.get("ultima_comunicacion")
            if f_str:
                try:
                    fecha_dt = datetime.datetime.fromisoformat(str(f_str).replace("Z", ""))
                    seg_dif = max(0, (ahora - fecha_dt).total_seconds())
                    
                    if seg_dif < UMBRAL_RETRASO_SEG:
                        estado_vig = "actualizada"
                        color_vig = "green"
                    elif seg_dif <= UMBRAL_DESCONEXION_SEG:
                        estado_vig = "retrasada"
                        color_vig = "orange"
                    else:
                        estado_vig = "sin_comunicacion"
                        color_vig = "red"
                except Exception:
                    pass

            # Una posición retenida por falta de fix se marca como desactualizada
            # aunque el último reporte haya llegado hace segundos.
            f["posicion_desactualizada"] = bool(f.get("fix_valido") == 0)
            if f["posicion_desactualizada"]:
                estado_vig = "retrasada"
                color_vig = "orange"

            f["estado_vigencia"] = estado_vig
            f["color_vigencia"] = color_vig
            f["segundos_desde_ultimo_reporte"] = seg_dif
            f["tiempo_relativo"] = "sin fix GPS" if f["posicion_desactualizada"] else (
                f"{int(seg_dif // 60)} min" if seg_dif < 3600 else f"{int(seg_dif // 3600)} h"
            )

            resultados.append(f)
            
        return resultados

def obtener_historial_animal(animal_id: str, limite: int = 50):
    """Obtiene el historial de las últimas N posiciones ordenadas cronológicamente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM (
            SELECT lat, lon, altitud_m, velocidad_kmh, bateria_pct, rssi_dbm, fecha_captura, fuente_conexion
            FROM lecturas_gps
            WHERE animal_id = ?
            ORDER BY fecha_captura DESC
            LIMIT ?
        ) ORDER BY fecha_captura ASC
        """, (animal_id, limite))
        return [dict(r) for r in cursor.fetchall()]

def obtener_resumen_dashboard(filtro_rancho: str = None):
    """Calcula totales generales filtrables para las tarjetas del Dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        filtro_sql = "WHERE 1=1"
        params = []
        if filtro_rancho and filtro_rancho != "TODOS":
            filtro_sql += " AND rancho_id = ?"
            params.append(filtro_rancho)

        cursor.execute(f"SELECT COUNT(*) FROM animales {filtro_sql}", params)
        total_animales = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo = 'collar'")
        total_collares = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo = 'gateway'")
        total_gateways = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alertas WHERE atendida = 0")
        alertas_activas = cursor.fetchone()[0]

        ubicaciones = obtener_ultimas_ubicaciones(filtro_rancho)
        actualizados = sum(1 for u in ubicaciones if u["estado_vigencia"] == "actualizada")
        retrasados = sum(1 for u in ubicaciones if u["estado_vigencia"] == "retrasada")
        sin_comunicacion = sum(1 for u in ubicaciones if u["estado_vigencia"] == "sin_comunicacion")

        return {
            "total_animales": total_animales,
            "total_dispositivos": total_collares + total_gateways,
            "total_collares": total_collares,
            "total_gateways": total_gateways,
            "alertas_activas": alertas_activas,
            "actualizados": actualizados,
            "retrasados": retrasados,
            "sin_comunicacion": sin_comunicacion
        }

def obtener_alertas(solo_pendientes: bool = True):
    """Devuelve las alertas del sistema enriquecidas con el nombre del bovino."""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
        SELECT al.*, an.nombre AS nombre_animal, an.arete_siniga, an.raza
        FROM alertas al
        LEFT JOIN animales an ON al.animal_id = an.id
        """
        if solo_pendientes:
            query += " WHERE al.atendida = 0 ORDER BY al.created_at DESC"
        else:
            query += " ORDER BY al.created_at DESC LIMIT 50"
            
        cursor.execute(query)
        return [dict(r) for r in cursor.fetchall()]

def atender_alerta(alerta_id: int, usuario: str, notas: str):
    """Reconoce y registra la acción tomada por el operador en campo."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE alertas
        SET atendida = 1,
            atendida_por = ?,
            notas_atencion = ?,
            fecha_atencion = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (usuario, notas, alerta_id))
        conn.commit()

def registrar_dispositivo_real(device_id: str, tipo: str, mac: str, lora_freq: float, lora_sf: int, lora_power: int, animal_id_asociar: str = None):
    """Registra un nuevo nodo físico Heltec LoRa ESP32 v2 y opcionalmente lo asocia a un bovino."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO dispositivos (
            id, tipo, modelo, mac_address, frecuencia_mhz, spreading_factor, tx_power_dbm, estado_operacion, ultima_comunicacion
        ) VALUES (?, ?, 'Heltec LoRa ESP32 v2 (Físico)', ?, ?, ?, ?, 'activo', CURRENT_TIMESTAMP)
        """, (device_id, tipo, mac, lora_freq, lora_sf, lora_power))
        
        if animal_id_asociar:
            cursor.execute("UPDATE animales SET device_id = ? WHERE id = ?", (device_id, animal_id_asociar))
            
        conn.commit()

# Inicialización automática
init_db()
