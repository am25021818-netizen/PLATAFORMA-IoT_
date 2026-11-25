#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simular_datos_integrales.py
 ============================================================
 SIMULADOR INTEGRAL DE HATO - VALLE DEL MEZQUITAL, HIDALGO
 Maestría en Ingeniería Mecatrónica - ITESHU
 ============================================================

Genera datos de prueba realistas y deterministas en las dos bases
SQLite del proyecto:

  * Webapp Flask : webapp/database/bovinos_iot.db
  * Streamlit    : plataforma/data/datos_iot.db

Incluye ranchos, potreros, animales, collares LoRa, gateways,
telemetría de 48 horas, semáforo de vigencia y alertas variadas.
Respeta el fail-safe de GPS: las lecturas sin fix conservan la última
coordenada válida y se registran con fix_valido=0 para marcarlas como
posición desactualizada, sin degradar el mapa con (0, 0).

Uso típico:
    python simular_datos_integrales.py
    python simular_datos_integrales.py --verificar
    python simular_datos_integrales.py --solo-webapp
    python simular_datos_integrales.py --horas 24 --intervalo-minutos 15
"""

from __future__ import annotations

import argparse
import math
import os
import random
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 20261125
VERDE_MAX = 600
AMARILLO_MAX = 1800
TS_FMT = "%Y-%m-%d %H:%M:%S"

# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO CANÓNICO
# ─────────────────────────────────────────────────────────────────────────────

RANCHOS = [
    {"key": 1, "id": "RAN-01", "nombre": "Rancho El Mezquital (Huichapan)",
     "propietario": "Don Aurelio Trejo", "municipio": "Huichapan",
     "lat": 20.37542, "lon": -99.65431, "ha": 120.5},
    {"key": 2, "id": "RAN-02", "nombre": "Rancho San Clemente (Tecozautla)",
     "propietario": "Don Aurelio Trejo", "municipio": "Tecozautla",
     "lat": 20.52118, "lon": -99.63005, "ha": 185.0},
    {"key": 3, "id": "RAN-03", "nombre": "Rancho Los Nopales (Ixmiquilpan)",
     "propietario": "Don Aurelio Trejo", "municipio": "Ixmiquilpan",
     "lat": 20.48620, "lon": -99.21780, "ha": 95.0},
]

POTREROS = [
    {"key": 1, "id": "POT-01", "rancho": 1, "nombre": "La Cantera",
     "pasto": "Buffel / Matorral", "lat": 20.37800, "lon": -99.65100,
     "radio_m": 420.0, "ha": 55.0, "color": "#2d6a4f"},
    {"key": 2, "id": "POT-02", "rancho": 1, "nombre": "El Mezquite",
     "pasto": "Zacate Estrella", "lat": 20.36950, "lon": -99.66200,
     "radio_m": 380.0, "ha": 45.0, "color": "#40916c"},
    {"key": 3, "id": "POT-03", "rancho": 2, "nombre": "Sabino Grande",
     "pasto": "Pasto Pangola", "lat": 20.52400, "lon": -99.62800,
     "radio_m": 500.0, "ha": 70.0, "color": "#52b788"},
    {"key": 4, "id": "POT-04", "rancho": 3, "nombre": "Los Cardos",
     "pasto": "Matorral Nativo", "lat": 20.48900, "lon": -99.21400,
     "radio_m": 350.0, "ha": 38.0, "color": "#1b4332"},
]

# last_min controla el semáforo: <10 verde, 10-30 amarillo, >30 rojo.
ANIMALES = [
    {"key": 1,  "id": "BOV-001", "arete": "MX-HGO-001", "nombre": "El Barón",
     "categoria": "Toro",     "sexo": "Macho",  "raza": "Simental",     "peso": 645, "rancho": 1, "potrero": 1, "last_min": 2,  "bateria": 94, "pelaje": "Rojo y blanco",  "nacimiento": "2020-03-15", "edad": 68, "icono": "green"},
    {"key": 2,  "id": "BOV-002", "arete": "MX-HGO-002", "nombre": "La Paloma",
     "categoria": "Vaca",     "sexo": "Hembra", "raza": "Charolais",    "peso": 485, "rancho": 1, "potrero": 1, "last_min": 4,  "bateria": 88, "pelaje": "Blanco crema",   "nacimiento": "2021-06-20", "edad": 53, "icono": "green"},
    {"key": 3,  "id": "BOV-003", "arete": "MX-HGO-003", "nombre": "El Pinto",
     "categoria": "Novillo",  "sexo": "Macho",  "raza": "Suizo",        "peso": 540, "rancho": 1, "potrero": 2, "last_min": 6,  "bateria": 76, "pelaje": "Gris manchado",  "nacimiento": "2021-01-10", "edad": 58, "icono": "green"},
    {"key": 4,  "id": "BOV-004", "arete": "MX-HGO-004", "nombre": "La Gitana",
     "categoria": "Vaca",     "sexo": "Hembra", "raza": "Angus",        "peso": 425, "rancho": 1, "potrero": 2, "last_min": 8,  "bateria": 82, "pelaje": "Negro brillante","nacimiento": "2022-04-05", "edad": 43, "icono": "green"},
    {"key": 5,  "id": "BOV-005", "arete": "MX-HGO-005", "nombre": "El Huasteco",
     "categoria": "Semental", "sexo": "Macho",  "raza": "Brahman",      "peso": 715, "rancho": 2, "potrero": 3, "last_min": 3,  "bateria": 91, "pelaje": "Gris perla",     "nacimiento": "2019-11-30", "edad": 84, "icono": "green"},
    {"key": 6,  "id": "BOV-006", "arete": "MX-HGO-006", "nombre": "La Canela",
     "categoria": "Vaquilla", "sexo": "Hembra", "raza": "Simbrah",      "peso": 392, "rancho": 3, "potrero": 4, "last_min": 5,  "bateria": 86, "pelaje": "Canela rojiza",  "nacimiento": "2023-02-14", "edad": 33, "icono": "green"},
    {"key": 7,  "id": "BOV-007", "arete": "MX-HGO-007", "nombre": "El Cometa",
     "categoria": "Novillo",  "sexo": "Macho",  "raza": "Gelbvieh",     "peso": 505, "rancho": 2, "potrero": 3, "last_min": 7,  "bateria": 73, "pelaje": "Rubio dorado",   "nacimiento": "2022-09-08", "edad": 38, "icono": "green"},
    {"key": 8,  "id": "BOV-008", "arete": "MX-HGO-008", "nombre": "La Esperanza",
     "categoria": "Vaca",     "sexo": "Hembra", "raza": "Hereford",     "peso": 460, "rancho": 1, "potrero": 1, "last_min": 12, "bateria": 64, "pelaje": "Blanco y rojo",  "nacimiento": "2021-12-02", "edad": 48, "icono": "orange"},
    {"key": 9,  "id": "BOV-009", "arete": "MX-HGO-009", "nombre": "El Rayo",
     "categoria": "Novillo",  "sexo": "Macho",  "raza": "Simental",     "peso": 520, "rancho": 2, "potrero": 3, "last_min": 18, "bateria": 57, "pelaje": "Rojo y blanco",  "nacimiento": "2022-07-19", "edad": 40, "icono": "orange"},
    {"key": 10, "id": "BOV-010", "arete": "MX-HGO-010", "nombre": "La Dormida",
     "categoria": "Vaca",     "sexo": "Hembra", "raza": "Angus",        "peso": 438, "rancho": 3, "potrero": 4, "last_min": 25, "bateria": 38, "pelaje": "Negro brillante","nacimiento": "2022-02-11", "edad": 45, "icono": "orange"},
    {"key": 11, "id": "BOV-011", "arete": "MX-HGO-011", "nombre": "El Tobiano",
     "categoria": "Toro",     "sexo": "Macho",  "raza": "Charolais",    "peso": 690, "rancho": 1, "potrero": 2, "last_min": 45, "bateria": 26, "pelaje": "Blanco crema",   "nacimiento": "2020-08-23", "edad": 63, "icono": "red"},
    {"key": 12, "id": "BOV-012", "arete": "MX-HGO-012", "nombre": "La Nubes",
     "categoria": "Vaca",     "sexo": "Hembra", "raza": "Suizo",        "peso": 455, "rancho": 3, "potrero": 4, "last_min": 70, "bateria": 17, "pelaje": "Gris manchado",  "nacimiento": "2021-10-05", "edad": 49, "icono": "red"},
]

GATEWAYS = [
    {"key": 13, "id": "HELTEC-GTW-01", "nombre": "Gateway Huichapan",   "rancho": 1, "last_min": 1, "rssi": -52, "snr": 12.5},
    {"key": 14, "id": "HELTEC-GTW-02", "nombre": "Gateway Tecozautla",  "rancho": 2, "last_min": 2, "rssi": -58, "snr": 11.8},
    {"key": 15, "id": "HELTEC-GTW-03", "nombre": "Gateway Ixmiquilpan", "rancho": 3, "last_min": 3, "rssi": -61, "snr": 10.9},
]

USUARIOS_WEBAPP = [
    (1, "Administrador Central", "admin@mezquital.mx", "admin123", "administrador", "7731002233"),
    (2, "Don Aurelio Trejo (Propietario)", "dueno@mezquital.mx", "dueno123", "propietario", "7611029384"),
    (3, "Juan Hernández (Encargado de Campo)", "operador@mezquital.mx", "operador123", "operador_campo", "7735928172"),
    (4, "Ing. Roberto Silva (Técnico Mantenimiento)", "tecnico@mezquital.mx", "tecnico123", "tecnico_mantenimiento", "7719876543"),
]

# ─────────────────────────────────────────────────────────────────────────────
# DDL de respaldo para la base de Streamlit (si no existe)
# ─────────────────────────────────────────────────────────────────────────────

DDL_PLATAFORMA = """
CREATE TABLE IF NOT EXISTS ranchos (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    propietario TEXT NOT NULL,
    municipio TEXT NOT NULL,
    estado_geografico TEXT DEFAULT 'Hidalgo',
    lat_centro REAL, lon_centro REAL, superficie_ha REAL,
    activo INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS potreros (
    id TEXT PRIMARY KEY,
    rancho_id TEXT NOT NULL,
    nombre TEXT NOT NULL,
    tipo_pasto TEXT,
    lat_centro REAL NOT NULL, lon_centro REAL NOT NULL,
    radio_m REAL NOT NULL,
    color_hex TEXT DEFAULT '#2d6a4f',
    activo INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    correo TEXT NOT NULL,
    rol TEXT NOT NULL,
    rancho_id TEXT,
    activo INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS dispositivos (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    modelo TEXT DEFAULT 'Heltec LoRa ESP32 v2 (SX1276)',
    mac_address TEXT,
    frecuencia_mhz REAL DEFAULT 915.0,
    spreading_factor INTEGER DEFAULT 7,
    bandwidth_khz REAL DEFAULT 125.0,
    tx_power_dbm INTEGER DEFAULT 20,
    sync_word TEXT DEFAULT '0x34',
    bateria_pct INTEGER DEFAULT 100,
    voltaje_bateria REAL DEFAULT 4.1,
    rssi_dbm INTEGER, snr_db REAL,
    estado_operacion TEXT DEFAULT 'activo',
    ultima_comunicacion TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS animales (
    id TEXT PRIMARY KEY,
    arete_siniga TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    raza TEXT NOT NULL,
    edad_meses INTEGER, peso_kg REAL,
    rancho_id TEXT NOT NULL,
    potrero_id TEXT,
    device_id TEXT UNIQUE,
    estado TEXT DEFAULT 'activo',
    color_icono TEXT DEFAULT 'green',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS lecturas_gps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    lat REAL NOT NULL, lon REAL NOT NULL,
    altitud_m REAL DEFAULT 0.0,
    velocidad_kmh REAL DEFAULT 0.0,
    bateria_pct INTEGER DEFAULT 100,
    rssi_dbm INTEGER, snr_db REAL,
    satelites INTEGER DEFAULT 0,
    fix_valido INTEGER DEFAULT 1,
    fuente_conexion TEXT DEFAULT 'lora_mqtt',
    fecha_captura TIMESTAMP NOT NULL,
    fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    animal_id TEXT, device_id TEXT,
    descripcion TEXT NOT NULL,
    nivel TEXT DEFAULT 'warning',
    lat REAL, lon REAL,
    atendida INTEGER DEFAULT 0,
    atendida_por TEXT,
    notas_atencion TEXT,
    fecha_atencion TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_lecturas_anim_fecha ON lecturas_gps(animal_id, fecha_captura);
CREATE INDEX IF NOT EXISTS idx_dispositivos_lastcomm ON dispositivos(ultima_comunicacion);
CREATE INDEX IF NOT EXISTS idx_animales_rancho ON animales(rancho_id);
"""


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

def fmt(dt: datetime) -> str:
    return dt.strftime(TS_FMT)


def conecta(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def existe_tabla(conn: sqlite3.Connection, nombre: str) -> bool:
    fila = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nombre,)
    ).fetchone()
    return fila is not None


def respaldar(path: Path, activo: bool) -> None:
    if not activo or not path.exists():
        return
    destino = path.with_name(path.name + ".bak")
    shutil.copy2(path, destino)
    print(f"  Respaldo: {destino}")


def color_por_fecha(ultima: str | None, ahora: datetime) -> str:
    if not ultima:
        return "rojo"
    try:
        ts = datetime.strptime(ultima, TS_FMT)
    except ValueError:
        return "rojo"
    seg = max(0, (ahora - ts).total_seconds())
    if seg < VERDE_MAX:
        return "verde"
    if seg <= AMARILLO_MAX:
        return "amarillo"
    return "rojo"


def collar_id_texto(animal: dict) -> str:
    return f"HELTEC-COLLAR-{animal['key']:02d}"


def dispositivos(ahora: datetime) -> list[dict]:
    resultado = []
    for a in ANIMALES:
        ultima = ahora - timedelta(minutes=a["last_min"])
        resultado.append({
            "key": a["key"],
            "id": collar_id_texto(a),
            "tipo": "collar",
            "nombre": f"Collar {a['nombre']}",
            "rancho": a["rancho"],
            "bateria": a["bateria"],
            "ultima": fmt(ultima),
            "rssi": -96 if a["bateria"] < 30 else random.Random(SEED + a["key"]).randint(-90, -68),
            "snr": 4.8 if a["bateria"] < 30 else round(7.0 + a["key"] * 0.21, 1),
        })
    for g in GATEWAYS:
        resultado.append({
            "key": g["key"], "id": g["id"], "tipo": "gateway",
            "nombre": g["nombre"], "rancho": g["rancho"],
            "bateria": 100,
            "ultima": fmt(ahora - timedelta(minutes=g["last_min"])),
            "rssi": g["rssi"], "snr": g["snr"],
        })
    return resultado


def generar_lecturas(horas: int, intervalo: int, ahora: datetime) -> dict[int, list[dict]]:
    """Devuelve {key_animal: [lecturas]} con movimiento acotado al potrero."""
    pasos = max(1, int(horas * 60 // intervalo))
    por_animal: dict[int, list[dict]] = {}

    for a in ANIMALES:
        rng = random.Random(SEED + a["key"] * 101)
        pot = next(p for p in POTREROS if p["key"] == a["potrero"])
        rancho = next(r for r in RANCHOS if r["key"] == a["rancho"])
        fin = ahora - timedelta(minutes=a["last_min"])
        inicio = fin - timedelta(minutes=intervalo * pasos)

        lat, lon = pot["lat"], pot["lon"]
        bateria_inicial = min(100, a["bateria"] + max(2, int(pasos * 0.09)))
        lecturas = []

        for k in range(pasos + 1):
            ts = inicio + timedelta(minutes=intervalo * k)
            lat += rng.uniform(-0.00042, 0.00042)
            lon += rng.uniform(-0.00050, 0.00050)

            # Limita el recorrido al 85 % del radio de la geocerca.
            dlat = lat - pot["lat"]
            dlon = (lon - pot["lon"]) * math.cos(math.radians(pot["lat"]))
            dist_m = math.hypot(dlat, dlon) * 111320.0
            if dist_m > pot["radio_m"] * 0.85:
                factor = (pot["radio_m"] * 0.85) / dist_m
                lat = pot["lat"] + dlat * factor
                lon = pot["lon"] + (dlon * factor) / math.cos(math.radians(pot["lat"]))

            fraccion = k / pasos
            bateria = round(bateria_inicial - (bateria_inicial - a["bateria"]) * fraccion)
            velocidad = round(rng.uniform(0.2, 2.9), 1)

            lecturas.append({
                "animal_key": a["key"],
                "animal_id": a["id"],
                "device_id": collar_id_texto(a),
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "altitud": round(rancho["lat"] * 0 + (2105.0 if a["rancho"] == 1 else 1885.0 if a["rancho"] == 2 else 1760.0) + rng.uniform(-3, 3), 1),
                "velocidad": velocidad,
                "hdop": round(rng.uniform(0.8, 2.4), 1),
                "satelites": rng.randint(6, 12),
                "bateria": bateria,
                "rssi": rng.randint(-92, -66),
                "snr": round(rng.uniform(5.0, 11.0), 1),
                "fix_valido": 1,
                "fuente": "simulacion",
                "fecha": fmt(ts),
            })

        # Caso 1: animal fuera de geocerca (coordenada válida, pero lejos del centro).
        if a["key"] == 8:
            lecturas[-1]["lat"] = round(pot["lat"] + 0.012, 6)
            lecturas[-1]["lon"] = round(pot["lon"] + 0.004, 6)
            lecturas[-1]["velocidad"] = 3.8

        # Caso 2: velocidad anómala para generar alerta.
        if a["key"] == 9:
            lecturas[-1]["velocidad"] = 18.5

        # Caso 3: GPS sin fix. Se conserva la última coordenada válida y se
        # marca con fix_valido=0 para que el dashboard la muestre como retrasada.
        if a["key"] == 4:
            valida = lecturas[-1]
            lecturas.append({
                "animal_key": a["key"], "animal_id": a["id"],
                "device_id": collar_id_texto(a),
                "lat": valida["lat"], "lon": valida["lon"], "altitud": valida["altitud"],
                "velocidad": 0.0, "hdop": 9.9, "satelites": 0,
                "bateria": a["bateria"], "rssi": -99, "snr": 3.1,
                "fix_valido": 0, "fuente": "simulacion",
                "fecha": fmt(fin + timedelta(minutes=1)),
            })

        # Caso 4: coordenadas fuera de rango reportadas por el collar.
        # Se rechaza el valor imposible y se conserva la última posición válida.
        if a["key"] == 10:
            valida = lecturas[-1]
            lecturas.append({
                "animal_key": a["key"], "animal_id": a["id"],
                "device_id": collar_id_texto(a),
                "lat": valida["lat"], "lon": valida["lon"], "altitud": valida["altitud"],
                "velocidad": 0.0, "hdop": 9.9, "satelites": 1,
                "bateria": a["bateria"], "rssi": -98, "snr": 3.4,
                "fix_valido": 0, "fuente": "simulacion",
                "fecha": fmt(fin + timedelta(minutes=2)),
            })

        por_animal[a["key"]] = lecturas

    return por_animal


def definir_alertas(por_animal: dict[int, list[dict]], ahora: datetime) -> list[dict]:
    """Construye alertas con fechas relativas y tipos válidos para cada esquema."""
    def posicion(key: int) -> tuple[float, float]:
        validas = [r for r in por_animal[key] if r["fix_valido"] == 1]
        ultima = validas[-1]
        return ultima["lat"], ultima["lon"]

    definiciones = [
        # key, tipo_webapp, tipo_plataforma, minutos, nivel, mensaje, atendida
        (5,  "bateria_baja",       "bateria_baja",        18, "critical", "Batería del collar al 91%; se programa revisión preventiva.", False),
        (11, "bateria_baja",       "bateria_baja",        44, "critical", "Batería crítica al 26%. Requiere reemplazo de celda LiPo.", False),
        (12, "bateria_baja",       "bateria_baja",        66, "critical", "Batería crítica al 17%. Collar en modo de bajo consumo.", False),
        (11, "sin_comunicacion",   "desconexion",         46, "warning",  "El Tobiano no reporta posición desde hace más de 45 minutos.", False),
        (12, "sin_comunicacion",   "desconexion",         72, "critical", "La Nubes sin comunicación por más de 70 minutos en Los Cardos.", False),
        (8,  "fuera_geocerca",     "fuera_potrero",       13, "warning",  "La Esperanza salió del radio asignado en La Cantera.", False),
        (9,  "velocidad_anormal",  "velocidad_anormal",    8, "warning",  "Desplazamiento de 18.5 km/h detectado en El Rayo.", False),
        (4,  "dispositivo_caido",  "sin_fix",              3, "warning",  "GPS sin fix satelital; se conserva la última coordenada válida.", False),
        (10, "dispositivo_caido",  "coordenadas_invalidas",2, "warning",  "Coordenadas fuera de rango recibidas (95.512, -99.214); se conserva la última válida.", False),
        (3,  "bateria_baja",       "bateria_baja",       240, "info",     "Revisión de batería completada en El Pinto.", True),
        (2,  "fuera_geocerca",     "fuera_potrero",      310, "info",     "La Paloma fue reintegrada al potrero La Cantera.", True),
        (6,  "velocidad_anormal",  "velocidad_anormal",  420, "info",     "Movimiento intenso descartado tras revisión de campo.", True),
    ]

    alertas = []
    for key, tw, tp, minutos, nivel, mensaje, atendida in definiciones:
        a = next(x for x in ANIMALES if x["key"] == key)
        lat, lon = posicion(key)
        creada = ahora - timedelta(minutes=minutos)
        alertas.append({
            "animal_key": key,
            "animal_id": a["id"],
            "device_id": collar_id_texto(a),
            "tipo_webapp": tw,
            "tipo_plataforma": tp,
            "mensaje": mensaje,
            "nivel": nivel,
            "lat": lat, "lon": lon,
            "atendida": 1 if atendida else 0,
            "creada": fmt(creada),
            "atendida_en": fmt(creada + timedelta(minutes=8)) if atendida else None,
            "notas": "Verificado por personal de campo." if atendida else None,
        })
    return alertas


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTADOR WEBAPP (Flask)
# ─────────────────────────────────────────────────────────────────────────────

def asegurar_esquema_webapp(conn: sqlite3.Connection) -> None:
    if existe_tabla(conn, "usuarios"):
        return
    schema = ROOT / "webapp" / "database" / "schema.sql"
    seed = ROOT / "webapp" / "database" / "seed.sql"
    if schema.exists():
        conn.executescript(schema.read_text(encoding="utf-8"))
    if seed.exists() and conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        conn.executescript(seed.read_text(encoding="utf-8"))
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        raise RuntimeError("No se pudo inicializar el esquema de la webapp.")


def poblar_webapp(path: Path, horas: int, intervalo: int, ahora: datetime,
                  hacer_backup: bool) -> None:
    respaldar(path, hacer_backup)
    conn = conecta(path)
    try:
        asegurar_esquema_webapp(conn)
        for tabla in ("lecturas_gps", "alertas", "usuarios_ranchos",
                      "animales", "dispositivos", "potreros", "ranchos"):
            conn.execute(f"DELETE FROM {tabla}")

        owner = conn.execute(
            "SELECT id FROM usuarios WHERE correo='dueno@mezquital.mx'"
        ).fetchone() or conn.execute("SELECT id FROM usuarios ORDER BY id LIMIT 1").fetchone()
        owner_id = owner[0] if owner else 2

        conn.executemany(
            """INSERT INTO ranchos
               (id, propietario_id, nombre, municipio, estado, lat_centro, lon_centro, superficie_ha)
               VALUES (?,?,?,?,?,?,?,?)""",
            [(r["key"], owner_id, r["nombre"], r["municipio"], "Hidalgo",
              r["lat"], r["lon"], r["ha"]) for r in RANCHOS],
        )
        conn.executemany(
            """INSERT INTO potreros
               (id, rancho_id, nombre, lat_centro, lon_centro, radio_m, superficie_ha)
               VALUES (?,?,?,?,?,?,?)""",
            [(p["key"], p["rancho"], p["nombre"], p["lat"], p["lon"],
              p["radio_m"], p["ha"]) for p in POTREROS],
        )

        devs = dispositivos(ahora)
        conn.executemany(
            """INSERT INTO dispositivos
               (id, mac_id, tipo, nombre, rancho_id, firmware_ver, bateria_pct, ultima_conexion, activo)
               VALUES (?,?,?,?,?,?,?,?,1)""",
            [(d["key"], d["id"], d["tipo"], d["nombre"], d["rancho"],
              "1.2.0" if d["tipo"] == "collar" else "1.1.0",
              d["bateria"], d["ultima"]) for d in devs],
        )

        conn.executemany(
            """INSERT INTO animales
               (id, arete, nombre, raza, sexo, peso_kg, propietario_id, rancho_id,
                potrero_id, collar_id, color_pelaje, fecha_nacimiento, activo)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)""",
            [(a["key"], a["arete"], a["nombre"], a["raza"], a["sexo"], a["peso"],
              owner_id, a["rancho"], a["potrero"], a["key"], a["pelaje"],
              a["nacimiento"]) for a in ANIMALES],
        )

        operador = conn.execute("SELECT id FROM usuarios WHERE rol='operador_campo'").fetchone()
        if operador:
            conn.executemany(
                "INSERT INTO usuarios_ranchos (usuario_id, rancho_id) VALUES (?,?)",
                [(operador[0], 1), (operador[0], 2), (operador[0], 3)],
            )

        por_animal = generar_lecturas(horas, intervalo, ahora)
        filas = []
        for key, lecturas in por_animal.items():
            for r in lecturas:
                filas.append((
                    key, key, r["lat"], r["lon"], r["altitud"], r["velocidad"],
                    r["hdop"], r["satelites"], r["bateria"], r["rssi"], r["fecha"],
                ))
        conn.executemany(
            """INSERT INTO lecturas_gps
               (animal_id, dispositivo_id, lat, lon, altitud_m, velocidad_kmh,
                hdop, satelites, bateria_pct, rssi_lora, timestamp_utc)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""", filas,
        )

        alertas = definir_alertas(por_animal, ahora)
        conn.executemany(
            """INSERT INTO alertas
               (animal_id, dispositivo_id, tipo, mensaje, lat, lon,
                atendida, atendida_por, creada_en, atendida_en)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            [(al["animal_key"], al["animal_key"], al["tipo_webapp"], al["mensaje"],
              al["lat"], al["lon"], al["atendida"], 1 if al["atendida"] else None,
              al["creada"], al["atendida_en"]) for al in alertas],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTADOR PLATAFORMA (Streamlit)
# ─────────────────────────────────────────────────────────────────────────────

def asegurar_esquema_plataforma(conn: sqlite3.Connection) -> None:
    if existe_tabla(conn, "ranchos"):
        return
    conn.executescript(DDL_PLATAFORMA)


def poblar_plataforma(path: Path, horas: int, intervalo: int, ahora: datetime,
                      hacer_backup: bool) -> None:
    respaldar(path, hacer_backup)
    conn = conecta(path)
    try:
        asegurar_esquema_plataforma(conn)
        for tabla in ("lecturas_gps", "alertas", "animales",
                      "dispositivos", "potreros", "usuarios", "ranchos"):
            conn.execute(f"DELETE FROM {tabla}")

        conn.executemany(
            """INSERT INTO ranchos
               (id, nombre, propietario, municipio, estado_geografico,
                lat_centro, lon_centro, superficie_ha, activo)
               VALUES (?,?,?,?,?,?,?,?,1)""",
            [(r["id"], r["nombre"], r["propietario"], r["municipio"], "Hidalgo",
              r["lat"], r["lon"], r["ha"]) for r in RANCHOS],
        )
        conn.executemany(
            """INSERT INTO potreros
               (id, rancho_id, nombre, tipo_pasto, lat_centro, lon_centro,
                radio_m, color_hex, activo)
               VALUES (?,?,?,?,?,?,?,?,1)""",
            [(p["id"], next(r["id"] for r in RANCHOS if r["key"] == p["rancho"]),
              p["nombre"], p["pasto"], p["lat"], p["lon"], p["radio_m"], p["color"])
             for p in POTREROS],
        )
        conn.executemany(
            """INSERT INTO usuarios
               (id, username, password, nombre_completo, correo, rol, rancho_id, activo)
               VALUES (?,?,?,?,?,?,?,1)""",
            [("USR-01", "admin", "admin123", "Ing. Iván Rodríguez Hernández",
              "ivan.rodriguez@iteshu.edu.mx", "admin", "RAN-01"),
             ("USR-02", "ganadero", "vaca123", "Don Aurelio Trejo",
              "aurelio@rancho.mx", "ganadero", "RAN-01"),
             ("USR-03", "vaquero", "campo123", "Juan Pérez Morales",
              "juan.vaquero@iteshu.edu.mx", "vaquero", "RAN-01"),
             ("USR-04", "tecnico", "tec123", "M.C. Carlos Espinoza Galicia",
              "carlos.espinoza@iteshu.edu.mx", "tecnico", "RAN-01")],
        )

        devs = dispositivos(ahora)
        conn.executemany(
            """INSERT INTO dispositivos
               (id, tipo, modelo, mac_address, frecuencia_mhz, spreading_factor,
                bandwidth_khz, tx_power_dbm, sync_word, bateria_pct, voltaje_bateria,
                rssi_dbm, snr_db, estado_operacion, ultima_comunicacion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [(d["id"], d["tipo"],
              "Heltec LoRa ESP32 v2 (SX1276)" if d["tipo"] == "collar" else "Heltec LoRa ESP32 Base Station",
              f"E0:5A:1B:77:{d['key']:02X}", 915.0, 7, 125.0, 20, "0x34",
              d["bateria"], round(3.3 + d["bateria"] / 100, 2), d["rssi"], d["snr"],
              "activo", d["ultima"]) for d in devs],
        )

        conn.executemany(
            """INSERT INTO animales
               (id, arete_siniga, nombre, categoria, raza, edad_meses, peso_kg,
                rancho_id, potrero_id, device_id, estado, color_icono)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            [(a["id"], a["arete"], a["nombre"], a["categoria"], a["raza"],
              a["edad"], a["peso"],
              next(r["id"] for r in RANCHOS if r["key"] == a["rancho"]),
              next(p["id"] for p in POTREROS if p["key"] == a["potrero"]),
              collar_id_texto(a), "activo", a["icono"]) for a in ANIMALES],
        )

        por_animal = generar_lecturas(horas, intervalo, ahora)
        filas = []
        for key, lecturas in por_animal.items():
            for r in lecturas:
                recepcion = (datetime.strptime(r["fecha"], TS_FMT) + timedelta(seconds=3))
                filas.append((
                    r["animal_id"], r["device_id"], r["lat"], r["lon"], r["altitud"],
                    r["velocidad"], r["bateria"], r["rssi"], r["snr"], r["satelites"],
                    r["fix_valido"], r["fuente"], r["fecha"], fmt(recepcion),
                ))
        conn.executemany(
            """INSERT INTO lecturas_gps
               (animal_id, device_id, lat, lon, altitud_m, velocidad_kmh,
                bateria_pct, rssi_dbm, snr_db, satelites, fix_valido,
                fuente_conexion, fecha_captura, fecha_recepcion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", filas,
        )

        alertas = definir_alertas(por_animal, ahora)
        conn.executemany(
            """INSERT INTO alertas
               (tipo, animal_id, device_id, descripcion, nivel, lat, lon,
                atendida, atendida_por, notas_atencion, fecha_atencion, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            [(al["tipo_plataforma"], al["animal_id"], al["device_id"], al["mensaje"],
              al["nivel"], al["lat"], al["lon"], al["atendida"],
              "USR-01" if al["atendida"] else None, al["notas"],
              al["atendida_en"], al["creada"]) for al in alertas],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class Verificador:
    def __init__(self) -> None:
        self.fallos: list[str] = []

    def check(self, nombre: str, condicion: bool, detalle: str = "") -> None:
        estado = "OK" if condicion else "FALLO"
        print(f"    [{estado}] {nombre}" + (f" -> {detalle}" if detalle else ""))
        if not condicion:
            self.fallos.append(nombre)


def verificar_webapp(path: Path, ahora: datetime, v: Verificador) -> None:
    print(f"  Webapp: {path}")
    if not path.exists():
        v.check("base webapp existe", False, str(path))
        return
    conn = conecta(path)
    try:
        animales = conn.execute("SELECT COUNT(*) FROM animales WHERE activo=1").fetchone()[0]
        collares = conn.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo='collar' AND activo=1").fetchone()[0]
        gateways = conn.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo='gateway' AND activo=1").fetchone()[0]
        ranchos = conn.execute("SELECT COUNT(*) FROM ranchos").fetchone()[0]
        lecturas = conn.execute("SELECT COUNT(*) FROM lecturas_gps").fetchone()[0]
        alertas_activas = conn.execute("SELECT COUNT(*) FROM alertas WHERE atendida=0").fetchone()[0]
        tipos = conn.execute("SELECT COUNT(DISTINCT tipo) FROM alertas").fetchone()[0]

        v.check("12 animales activos", animales == 12, str(animales))
        v.check("12 collares activos", collares == 12, str(collares))
        v.check("3 gateways activos", gateways == 3, str(gateways))
        v.check("3 ranchos", ranchos == 3, str(ranchos))
        v.check("lecturas generadas", lecturas >= 200, str(lecturas))
        v.check("alertas activas", alertas_activas >= 5, str(alertas_activas))
        v.check("tipos de alerta variados", tipos >= 3, str(tipos))

        filas = conn.execute("""
            SELECT a.id,
                   (SELECT timestamp_utc FROM lecturas_gps
                    WHERE animal_id=a.id ORDER BY timestamp_utc DESC LIMIT 1) AS ultima
            FROM animales a WHERE a.activo=1
        """).fetchall()
        conteo = {"verde": 0, "amarillo": 0, "rojo": 0}
        for fila in filas:
            conteo[color_por_fecha(fila["ultima"], ahora)] += 1
        v.check("semáforo con verde", conteo["verde"] > 0, str(conteo["verde"]))
        v.check("semáforo con amarillo", conteo["amarillo"] > 0, str(conteo["amarillo"]))
        v.check("semáforo con rojo", conteo["rojo"] > 0, str(conteo["rojo"]))
        print(f"    Semáforo: verde={conteo['verde']} amarillo={conteo['amarillo']} rojo={conteo['rojo']}")
    finally:
        conn.close()


def verificar_plataforma(path: Path, v: Verificador) -> None:
    print(f"  Plataforma: {path}")
    if not path.exists():
        v.check("base plataforma existe", False, str(path))
        return
    conn = conecta(path)
    try:
        animales = conn.execute("SELECT COUNT(*) FROM animales WHERE estado='activo'").fetchone()[0]
        collares = conn.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo='collar'").fetchone()[0]
        gateways = conn.execute("SELECT COUNT(*) FROM dispositivos WHERE tipo='gateway'").fetchone()[0]
        lecturas = conn.execute("SELECT COUNT(*) FROM lecturas_gps").fetchone()[0]
        recientes = conn.execute(
            "SELECT COUNT(*) FROM lecturas_gps WHERE fecha_captura >= datetime(?, '-48 hours')",
            (datetime.now().strftime(TS_FMT),),
        ).fetchone()[0]
        sin_fix = conn.execute("SELECT COUNT(*) FROM lecturas_gps WHERE fix_valido=0").fetchone()[0]
        posiciones_validas = conn.execute("""
            SELECT COUNT(*) FROM lecturas_gps lg
            INNER JOIN (
                SELECT animal_id, MAX(id) AS mid FROM lecturas_gps
                WHERE fix_valido=1 OR (lat<>0 OR lon<>0)
                GROUP BY animal_id
            ) x ON lg.id=x.mid
            WHERE (lg.lat<>0 OR lg.lon<>0)
        """).fetchone()[0]
        alertas_activas = conn.execute("SELECT COUNT(*) FROM alertas WHERE atendida=0").fetchone()[0]
        tipos = conn.execute("SELECT COUNT(DISTINCT tipo) FROM alertas").fetchone()[0]

        v.check("12 animales activos", animales == 12, str(animales))
        v.check("12 collares", collares == 12, str(collares))
        v.check("3 gateways", gateways == 3, str(gateways))
        v.check("lecturas generadas", lecturas >= 200, str(lecturas))
        v.check("lecturas recientes", recientes >= 200, str(recientes))
        v.check("lecturas sin fix registradas", sin_fix >= 2, str(sin_fix))
        v.check("posiciones vigentes válidas", posiciones_validas == 12, str(posiciones_validas))
        v.check("alertas activas", alertas_activas >= 5, str(alertas_activas))
        v.check("tipos de alerta variados", tipos >= 3, str(tipos))
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def rutas_por_defecto() -> tuple[Path, Path]:
    webapp = Path(os.getenv("WEBAPP_DB_PATH", str(ROOT / "webapp" / "database" / "bovinos_iot.db")))
    plataforma = Path(os.getenv("DB_PATH", str(ROOT / "plataforma" / "data" / "datos_iot.db")))
    return webapp, plataforma


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Simulación integral de datos bovinos para Flask y Streamlit."
    )
    parser.add_argument("--solo-webapp", action="store_true", help="Solo actualiza la base de Flask.")
    parser.add_argument("--solo-plataforma", action="store_true", help="Solo actualiza la base de Streamlit.")
    parser.add_argument("--webapp-db", type=Path, help="Ruta explícita a bovinos_iot.db.")
    parser.add_argument("--plataforma-db", type=Path, help="Ruta explícita a datos_iot.db.")
    parser.add_argument("--horas", type=int, default=48, help="Horas de telemetría a generar (default: 48).")
    parser.add_argument("--intervalo-minutos", type=int, default=15,
                        help="Intervalo entre lecturas (default: 15).")
    parser.add_argument("--verificar", action="store_true", help="Solo verifica, no escribe.")
    parser.add_argument("--no-backup", action="store_true", help="No crea copias .bak.")
    args = parser.parse_args(argv)

    if args.horas <= 0 or args.intervalo_minutos <= 0:
        parser.error("--horas y --intervalo-minutos deben ser mayores que cero.")

    webapp_db, plataforma_db = rutas_por_defecto()
    if args.webapp_db:
        webapp_db = args.webapp_db
    if args.plataforma_db:
        plataforma_db = args.plataforma_db

    if args.solo_webapp and args.solo_plataforma:
        parser.error("No uses --solo-webapp y --solo-plataforma al mismo tiempo.")

    objetivos = []
    if not args.solo_plataforma:
        objetivos.append("webapp")
    if not args.solo_webapp:
        objetivos.append("plataforma")

    ahora = datetime.now()
    print("=" * 68)
    print("  SIMULACIÓN INTEGRAL DE HATO - VALLE DEL MEZQUITAL")
    print("=" * 68)
    print(f"  Momento de referencia : {fmt(ahora)}")
    print(f"  Objetivos             : {', '.join(objetivos)}")
    print(f"  Telemetría            : {args.horas} h cada {args.intervalo_minutos} min")
    print()

    if not args.verificar:
        print("Escribiendo datos simulados...")
        if "webapp" in objetivos:
            print("  Webapp Flask")
            poblar_webapp(webapp_db, args.horas, args.intervalo_minutos,
                          ahora, not args.no_backup)
        if "plataforma" in objetivos:
            print("  Plataforma Streamlit")
            poblar_plataforma(plataforma_db, args.horas, args.intervalo_minutos,
                              ahora, not args.no_backup)
        print()

    print("Verificando resultados...")
    verificador = Verificador()
    if "webapp" in objetivos:
        verificar_webapp(webapp_db, ahora, verificador)
    if "plataforma" in objetivos:
        verificar_plataforma(plataforma_db, verificador)

    print()
    if verificador.fallos:
        print("RESULTADO: FALLOS -> " + ", ".join(verificador.fallos))
        return 1
    print("RESULTADO: TODO OK")
    print("Recuerda: los archivos .db y .bak no se versionan en Git.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
