import pytest
import sqlite3
import sys
from pathlib import Path

# Agregar carpeta plataforma/src al sys.path para importar módulos
SRC_PATH = Path(__file__).resolve().parent.parent / "plataforma" / "src"
sys.path.insert(0, str(SRC_PATH))

import database

def test_database_init():
    """Verifica que la base de datos se inicialice correctamente y cree las tablas necesarias."""
    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [r[0] for r in cursor.fetchall()]
        
        assert "ranchos" in tablas
        assert "usuarios" in tablas
        assert "dispositivos" in tablas
        assert "animales" in tablas
        assert "lecturas_gps" in tablas
        assert "alertas" in tablas

def test_resumen_dashboard():
    """Verifica que la consulta del dashboard devuelva las métricas requeridas."""
    resumen = database.obtener_resumen_dashboard()
    assert "total_animales" in resumen
    assert "total_dispositivos" in resumen
    assert "actualizados" in resumen
    assert resumen["total_animales"] >= 3

def test_guardar_lectura_y_recuperar():
    """Verifica la persistencia de una lectura de telemetría GPS."""
    datos_prueba = {
        "device_id": "HELTEC-COLLAR-01",
        "animal_id": "BOV-001",
        "lat": 20.37600,
        "lon": -99.65400,
        "altitud_m": 2106.0,
        "velocidad_kmh": 1.0,
        "bateria_pct": 90,
        "rssi_dbm": -70,
        "snr_db": 9.0,
        "satelites": 8,
        "fix_valido": True,
        "timestamp": "2026-11-19 15:00:00"
    }
    database.guardar_lectura(datos_prueba)
    historial = database.obtener_historial_animal("BOV-001", limite=1)
    assert len(historial) > 0
    assert historial[-1]["lat"] == pytest.approx(20.37600, rel=1e-4)

def test_alerta_bateria_baja():
    """Verifica que se dispare una alerta automática si la batería es inferior al 20%."""
    datos_bateria_critica = {
        "device_id": "HELTEC-COLLAR-02",
        "animal_id": "BOV-002",
        "lat": 20.37700,
        "lon": -99.65700,
        "bateria_pct": 12,
        "fix_valido": True,
        "timestamp": "2026-11-19 15:05:00"
    }
    database.guardar_lectura(datos_bateria_critica)
    alertas = database.obtener_alertas(solo_pendientes=True)
    alertas_bateria = [a for a in alertas if a["device_id"] == "HELTEC-COLLAR-02" and a["tipo"] == "bateria_baja"]
    assert len(alertas_bateria) > 0
