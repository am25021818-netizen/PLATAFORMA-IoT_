"""
db_manager.py — Gestor de base de datos SQLite con Autenticación RBAC, Multi-Ranchos, Métricas y Reportes
Valle del Mezquital, Hidalgo
"""
import sqlite3
import os
import math
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "bovinos_iot.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
SEED_PATH   = os.path.join(BASE_DIR, "seed.sql")

VERDE_MAX    = 600    # < 10 min  -> en línea
AMARILLO_MAX = 1800   # < 30 min  -> retrasado
# > 30 min                         -> sin señal


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    cur = conn.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()


def _vigencia_color(ultima_str: str) -> dict:
    if not ultima_str:
        return {"color": "rojo", "segundos": 999999, "etiqueta": "Sin datos"}
    try:
        ts = datetime.strptime(ultima_str, "%Y-%m-%d %H:%M:%S")
        diff = (datetime.now() - ts).total_seconds()
    except ValueError:
        diff = 999999
    if diff < VERDE_MAX:
        color = "verde"
        etiqueta = f"Hace {int(diff)}s"
    elif diff < AMARILLO_MAX:
        color = "amarillo"
        mins = int(diff // 60)
        etiqueta = f"Hace {mins} min"
    else:
        color = "rojo"
        mins = int(diff // 60)
        etiqueta = f"Hace {mins} min"
    return {"color": color, "segundos": int(diff), "etiqueta": etiqueta}


def _haversine_km(lat1, lon1, lat2, lon2):
    """Calcula distancia ortodrómica en kilómetros."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ─────────────────────────── AUTENTICACIÓN ───────────────────────────

def autenticar_usuario(correo: str, password_plano: str):
    conn = get_conn()
    user = conn.execute("SELECT * FROM usuarios WHERE correo=? AND activo=1", (correo.strip().lower(),)).fetchone()
    conn.close()
    if not user:
        return None
    if check_password_hash(user["password_hash"], password_plano):
        return dict(user)
    return None


def obtener_usuario_por_id(user_id: int):
    conn = get_conn()
    user = conn.execute("SELECT id, nombre, correo, rol, telefono FROM usuarios WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


# ─────────────────────────── RANCHOS / LOCACIONES ───────────────────────────

def listar_ranchos_usuario(user: dict) -> list:
    conn = get_conn()
    rol = user.get("rol")
    uid = user.get("id")

    if rol in ('administrador', 'tecnico_mantenimiento'):
        rows = conn.execute("""
            SELECT r.*, u.nombre AS propietario_nombre,
                   (SELECT COUNT(*) FROM animales WHERE rancho_id=r.id AND activo=1) AS total_bovinos,
                   (SELECT COUNT(*) FROM dispositivos WHERE rancho_id=r.id AND activo=1) AS total_nodos
            FROM ranchos r
            LEFT JOIN usuarios u ON u.id = r.propietario_id
            ORDER BY r.id
        """).fetchall()
    elif rol == 'propietario':
        rows = conn.execute("""
            SELECT r.*, u.nombre AS propietario_nombre,
                   (SELECT COUNT(*) FROM animales WHERE rancho_id=r.id AND activo=1) AS total_bovinos,
                   (SELECT COUNT(*) FROM dispositivos WHERE rancho_id=r.id AND activo=1) AS total_nodos
            FROM ranchos r
            LEFT JOIN usuarios u ON u.id = r.propietario_id
            WHERE r.propietario_id = ?
            ORDER BY r.id
        """, (uid,)).fetchall()
    elif rol == 'operador_campo':
        rows = conn.execute("""
            SELECT r.*, u.nombre AS propietario_nombre,
                   (SELECT COUNT(*) FROM animales WHERE rancho_id=r.id AND activo=1) AS total_bovinos,
                   (SELECT COUNT(*) FROM dispositivos WHERE rancho_id=r.id AND activo=1) AS total_nodos
            FROM ranchos r
            INNER JOIN usuarios_ranchos ur ON ur.rancho_id = r.id AND ur.usuario_id = ?
            LEFT JOIN usuarios u ON u.id = r.propietario_id
            ORDER BY r.id
        """, (uid,)).fetchall()
    else:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────── DASHBOARDS POR ROL ───────────────────────────

def resumen_dashboard_rol(user: dict) -> dict:
    conn = get_conn()
    rol = user.get("rol")
    uid = user.get("id")

    filtro_rancho = ""
    filtro_animal = ""
    params = ()

    if rol == 'propietario':
        filtro_rancho = "WHERE propietario_id = ?"
        filtro_animal = "WHERE a.propietario_id = ? AND a.activo=1"
        params = (uid,)
    elif rol == 'operador_campo':
        filtro_rancho = "WHERE id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id = ?)"
        filtro_animal = "WHERE a.rancho_id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id = ?) AND a.activo=1"
        params = (uid,)
    else:
        filtro_animal = "WHERE a.activo=1"

    total_ranchos = conn.execute(f"SELECT COUNT(*) FROM ranchos {filtro_rancho}", params).fetchone()[0]
    total_animales = conn.execute(f"SELECT COUNT(*) FROM animales a {filtro_animal}", params).fetchone()[0]
    
    if rol in ('administrador', 'tecnico_mantenimiento'):
        total_collares = conn.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo='collar' AND activo=1").fetchone()[0]
        total_gateways = conn.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo='gateway' AND activo=1").fetchone()[0]
        alertas_activas = conn.execute("SELECT COUNT(*) FROM alertas WHERE atendida=0").fetchone()[0]
    elif rol == 'propietario':
        total_collares = conn.execute("""
            SELECT COUNT(*) FROM dispositivos WHERE tipo='collar' AND rancho_id IN (SELECT id FROM ranchos WHERE propietario_id=?)
        """, (uid,)).fetchone()[0]
        total_gateways = conn.execute("""
            SELECT COUNT(*) FROM dispositivos WHERE tipo='gateway' AND rancho_id IN (SELECT id FROM ranchos WHERE propietario_id=?)
        """, (uid,)).fetchone()[0]
        alertas_activas = conn.execute("""
            SELECT COUNT(*) FROM alertas WHERE atendida=0 AND animal_id IN (SELECT id FROM animales WHERE propietario_id=?)
        """, (uid,)).fetchone()[0]
    else:
        total_collares = conn.execute("""
            SELECT COUNT(*) FROM dispositivos WHERE tipo='collar' AND rancho_id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id=?)
        """, (uid,)).fetchone()[0]
        total_gateways = conn.execute("""
            SELECT COUNT(*) FROM dispositivos WHERE tipo='gateway' AND rancho_id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id=?)
        """, (uid,)).fetchone()[0]
        alertas_activas = conn.execute("""
            SELECT COUNT(*) FROM alertas WHERE atendida=0 AND animal_id IN (SELECT id FROM animales WHERE rancho_id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id=?))
        """, (uid,)).fetchone()[0]

    filas = conn.execute(f"""
        SELECT a.id,
               (SELECT timestamp_utc FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS ultima
        FROM animales a {filtro_animal}
    """, params).fetchall()

    conteo = {"verde": 0, "amarillo": 0, "rojo": 0}
    for f in filas:
        v = _vigencia_color(f["ultima"])
        conteo[v["color"]] += 1

    conn.close()
    return {
        "rol": user["rol"],
        "usuario_nombre": user["nombre"],
        "total_ranchos": total_ranchos,
        "total_animales": total_animales,
        "total_collares": total_collares,
        "total_gateways": total_gateways,
        "alertas_activas": alertas_activas,
        "vigencia": conteo
    }


# ─────────────────────────── MÉTRICAS AVANZADAS (ADMIN) ───────────────────────────

def metricas_analiticas_admin() -> dict:
    conn = get_conn()

    # 1. Bovinos por Rancho
    ranchos_stats = conn.execute("""
        SELECT r.nombre, r.municipio, COUNT(a.id) as cantidad
        FROM ranchos r
        LEFT JOIN animales a ON a.rancho_id = r.id AND a.activo=1
        GROUP BY r.id
    """).fetchall()

    # 2. Distribución de Razas
    razas_stats = conn.execute("""
        SELECT raza, COUNT(*) as cantidad
        FROM animales
        WHERE activo=1
        GROUP BY raza
    """).fetchall()

    # 3. Estado de Baterías de los Collares
    baterias_stats = conn.execute("""
        SELECT 
          SUM(CASE WHEN bateria_pct >= 70 THEN 1 ELSE 0 END) as alta,
          SUM(CASE WHEN bateria_pct >= 30 AND bateria_pct < 70 THEN 1 ELSE 0 END) as media,
          SUM(CASE WHEN bateria_pct < 30 THEN 1 ELSE 0 END) as baja
        FROM dispositivos
        WHERE tipo='collar' AND activo=1
    """).fetchone()

    # 4. Distribución de Alertas por Tipo
    alertas_tipo = conn.execute("""
        SELECT tipo, COUNT(*) as cantidad
        FROM alertas
        GROUP BY tipo
    """).fetchall()

    # 5. Promedios Globales de Telemetría
    telemetria_avg = conn.execute("""
        SELECT 
          ROUND(AVG(velocidad_kmh), 2) as vel_promedio,
          ROUND(AVG(rssi_lora), 1) as rssi_promedio,
          ROUND(AVG(satelites), 1) as sat_promedio,
          COUNT(*) as total_lecturas
        FROM lecturas_gps
    """).fetchone()

    conn.close()

    return {
        "ranchos": [dict(r) for r in ranchos_stats],
        "razas": [dict(r) for r in razas_stats],
        "baterias": dict(baterias_stats) if baterias_stats else {"alta": 0, "media": 0, "baja": 0},
        "alertas_tipo": [dict(a) for a in alertas_tipo],
        "telemetria": dict(telemetria_avg) if telemetria_avg else {}
    }


# ─────────────────────────── REPORTES DE ACTIVIDAD ───────────────────────────

def reporte_actividad_animales(rancho_id: int = None) -> list:
    """Calcula distancias estimadas recorridas, velocidades y estado de cada bovino."""
    conn = get_conn()
    where = "WHERE a.activo=1"
    params = ()
    if rancho_id:
        where += " AND a.rancho_id=?"
        params = (rancho_id,)

    animales = conn.execute(f"""
        SELECT a.id, a.arete, a.nombre, a.raza, a.sexo, a.peso_kg,
               r.nombre AS rancho, p.nombre AS potrero,
               d.nombre AS collar, d.bateria_pct
        FROM animales a
        LEFT JOIN ranchos r ON r.id = a.rancho_id
        LEFT JOIN potreros p ON p.id = a.potrero_id
        LEFT JOIN dispositivos d ON d.id = a.collar_id
        {where}
        ORDER BY a.id
    """, params).fetchall()

    reporte = []
    for an in animales:
        aid = an["id"]
        # Obtener histórico de lecturas del animal
        lecturas = conn.execute("""
            SELECT lat, lon, velocidad_kmh, altitud_m, timestamp_utc
            FROM lecturas_gps
            WHERE animal_id = ?
            ORDER BY timestamp_utc ASC
        """, (aid,)).fetchall()

        total_pts = len(lecturas)
        distancia_total_km = 0.0
        vel_max = 0.0
        vel_prom = 0.0
        ultima_pos = "N/A"
        ultima_hora = "Sin datos"

        if total_pts > 0:
            vel_acum = 0.0
            for i in range(len(lecturas)):
                v = lecturas[i]["velocidad_kmh"] or 0.0
                vel_acum += v
                if v > vel_max:
                    vel_max = v
                if i > 0:
                    d = _haversine_km(
                        lecturas[i-1]["lat"], lecturas[i-1]["lon"],
                        lecturas[i]["lat"], lecturas[i]["lon"]
                    )
                    distancia_total_km += d
            vel_prom = round(vel_acum / total_pts, 2)
            ult = lecturas[-1]
            ultima_pos = f"{ult['lat']:.5f}, {ult['lon']:.5f}"
            ultima_hora = ult["timestamp_utc"]

        vig = _vigencia_color(ultima_hora if total_pts > 0 else None)

        reporte.append({
            "animal_id": aid,
            "arete": an["arete"],
            "nombre": an["nombre"],
            "raza": an["raza"],
            "sexo": an["sexo"],
            "peso_kg": an["peso_kg"],
            "rancho": an["rancho"],
            "potrero": an["potrero"] or "Sin asignar",
            "collar": an["collar"] or "No asignado",
            "bateria_pct": an["bateria_pct"],
            "total_reportes": total_pts,
            "distancia_km": round(distancia_total_km, 3),
            "vel_max_kmh": round(vel_max, 2),
            "vel_prom_kmh": vel_prom,
            "ultima_posicion": ultima_pos,
            "ultima_conexion": ultima_hora,
            "estado_vigencia": vig["color"]
        })

    conn.close()
    return reporte


# ─────────────────────────── BOVINOS FILTRADOS ───────────────────────────

def listar_bovinos_usuario(user: dict = None) -> list:
    conn = get_conn()
    where_clause = "WHERE a.activo = 1"
    params = ()

    if user:
        rol = user.get("rol")
        uid = user.get("id")
        if rol == 'propietario':
            where_clause += " AND a.propietario_id = ?"
            params = (uid,)
        elif rol == 'operador_campo':
            where_clause += " AND a.rancho_id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id = ?)"
            params = (uid,)

    rows = conn.execute(f"""
        SELECT a.id, a.arete, a.nombre, a.raza, a.sexo, a.peso_kg,
               a.color_pelaje, a.fecha_nacimiento,
               r.nombre AS rancho, r.municipio AS rancho_municipio,
               p.nombre AS potrero,
               u.nombre AS propietario_nombre,
               d.nombre AS collar_nombre, d.bateria_pct,
               (SELECT lat          FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS lat,
               (SELECT lon          FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS lon,
               (SELECT altitud_m    FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS altitud,
               (SELECT velocidad_kmh FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS velocidad,
               (SELECT satelites    FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS satelites,
               (SELECT rssi_lora    FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS rssi,
               (SELECT timestamp_utc FROM lecturas_gps WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS ultima_lectura
        FROM animales a
        LEFT JOIN ranchos r ON r.id = a.rancho_id
        LEFT JOIN potreros p ON p.id = a.potrero_id
        LEFT JOIN dispositivos d ON d.id = a.collar_id
        LEFT JOIN usuarios u ON u.id = a.propietario_id
        {where_clause}
        ORDER BY a.id
    """, params).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        v = _vigencia_color(d.get("ultima_lectura"))
        d["vigencia_color"]   = v["color"]
        d["vigencia_etiqueta"] = v["etiqueta"]
        d["vigencia_segundos"] = v["segundos"]
        result.append(d)
    conn.close()
    return result


def historial_animal(animal_id: int, horas: int = 24) -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT lat, lon, altitud_m, velocidad_kmh, satelites, rssi_lora,
               bateria_pct, timestamp_utc
        FROM lecturas_gps
        WHERE animal_id = ?
          AND timestamp_utc >= datetime('now', ?, 'localtime')
        ORDER BY timestamp_utc ASC
    """, (animal_id, f"-{horas} hours")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────── ALERTAS FILTRADAS ───────────────────────────

def listar_alertas_usuario(user: dict = None, solo_activas: bool = False) -> list:
    conn = get_conn()
    condiciones = []
    params = []

    if solo_activas:
        condiciones.append("al.atendida = 0")

    if user:
        rol = user.get("rol")
        uid = user.get("id")
        if rol == 'propietario':
            condiciones.append("a.propietario_id = ?")
            params.append(uid)
        elif rol == 'operador_campo':
            condiciones.append("a.rancho_id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id = ?)")
            params.append(uid)

    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    rows = conn.execute(f"""
        SELECT al.id, al.tipo, al.mensaje, al.lat, al.lon,
               al.atendida, al.creada_en, al.atendida_en,
               a.nombre AS animal_nombre, a.arete,
               r.nombre AS rancho_nombre,
               d.nombre AS dispositivo_nombre
        FROM alertas al
        LEFT JOIN animales a ON a.id = al.animal_id
        LEFT JOIN ranchos r ON r.id = a.rancho_id
        LEFT JOIN dispositivos d ON d.id = al.dispositivo_id
        {where}
        ORDER BY al.creada_en DESC
        LIMIT 60
    """, tuple(params)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def atender_alerta(alerta_id: int, usuario_id: int = 1) -> bool:
    conn = get_conn()
    conn.execute("""
        UPDATE alertas
        SET atendida=1, atendida_por=?, atendida_en=datetime('now','localtime')
        WHERE id=?
    """, (usuario_id, alerta_id))
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes > 0


# ─────────────────────────── DISPOSITIVOS ───────────────────────────

def listar_dispositivos() -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT d.id, d.mac_id, d.tipo, d.nombre, d.firmware_ver,
               d.bateria_pct, d.ultima_conexion, d.activo,
               r.nombre AS rancho, r.municipio
        FROM dispositivos d
        LEFT JOIN ranchos r ON r.id = d.rancho_id
        ORDER BY d.tipo, d.id
    """).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        v = _vigencia_color(d.get("ultima_conexion"))
        d["estado_color"]   = v["color"]
        d["estado_etiqueta"] = v["etiqueta"]
        result.append(d)
    conn.close()
    return result


def listar_potreros(user: dict = None) -> list:
    conn = get_conn()
    where = "WHERE p.activo = 1"
    params = ()
    if user and user.get("rol") == 'propietario':
        where += " AND r.propietario_id = ?"
        params = (user["id"],)
    elif user and user.get("rol") == 'operador_campo':
        where += " AND p.rancho_id IN (SELECT rancho_id FROM usuarios_ranchos WHERE usuario_id = ?)"
        params = (user["id"],)

    rows = conn.execute(f"""
        SELECT p.id, p.nombre, p.lat_centro, p.lon_centro, p.radio_m,
               p.superficie_ha, r.nombre AS rancho, r.municipio
        FROM potreros p
        LEFT JOIN ranchos r ON r.id = p.rancho_id
        {where}
    """, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────── INSERCIÓN TELEMETRÍA ───────────────────────────

def insertar_lectura(animal_id: int, lat: float, lon: float,
                     altitud: float = 0, velocidad: float = 0,
                     hdop: float = 1.0, satelites: int = 0,
                     bateria: int = 100, rssi: int = -100,
                     dispositivo_id: int = None) -> int:
    if lat == 0.0 and lon == 0.0:
        return -1
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO lecturas_gps
            (animal_id, dispositivo_id, lat, lon, altitud_m, velocidad_kmh,
             hdop, satelites, bateria_pct, rssi_lora, timestamp_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
    """, (animal_id, dispositivo_id, lat, lon, altitud, velocidad,
          hdop, satelites, bateria, rssi))

    if dispositivo_id:
        conn.execute("UPDATE dispositivos SET bateria_pct=?, ultima_conexion=datetime('now','localtime') WHERE id=?",
                     (bateria, dispositivo_id))

    if bateria is not None and bateria < 20:
        existente = conn.execute(
            "SELECT id FROM alertas WHERE animal_id=? AND tipo='bateria_baja' AND atendida=0",
            (animal_id,)
        ).fetchone()
        if not existente:
            conn.execute("""
                INSERT INTO alertas (animal_id, dispositivo_id, tipo, mensaje, lat, lon)
                VALUES (?, ?, 'bateria_baja', ?, ?, ?)
            """, (animal_id, dispositivo_id, f"Batería crítica al {bateria}%. Se requiere reemplazo.", lat, lon))

    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id
