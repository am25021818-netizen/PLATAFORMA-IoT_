import unittest
import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parent.parent / "plataforma" / "src"
sys.path.insert(0, str(SRC_PATH))

import database

class TestDatabase(unittest.TestCase):
    def test_database_init(self):
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas = [r[0] for r in cursor.fetchall()]
            self.assertIn("ranchos", tablas)
            self.assertIn("usuarios", tablas)
            self.assertIn("dispositivos", tablas)
            self.assertIn("animales", tablas)
            self.assertIn("lecturas_gps", tablas)
            self.assertIn("alertas", tablas)

    def test_resumen_dashboard(self):
        resumen = database.obtener_resumen_dashboard()
        self.assertIn("total_animales", resumen)
        self.assertIn("total_dispositivos", resumen)
        self.assertIn("actualizados", resumen)
        self.assertGreaterEqual(resumen["total_animales"], 3)

    def test_guardar_lectura_y_recuperar(self):
        datos = {
            "device_id": "HELTEC-COLLAR-01",
            "animal_id": "BOV-001",
            "lat": 20.37612,
            "lon": -99.65421,
            "altitud_m": 2106.0,
            "velocidad_kmh": 1.0,
            "bateria_pct": 90,
            "rssi_dbm": -70,
            "snr_db": 9.0,
            "satelites": 8,
            "fix_valido": True,
            "timestamp": "2026-11-19 23:59:59"
        }
        database.guardar_lectura(datos)
        historial = database.obtener_historial_animal("BOV-001", limite=1)
        self.assertGreater(len(historial), 0)
        self.assertAlmostEqual(historial[-1]["lat"], 20.37612, places=4)

    def test_alerta_bateria_baja(self):
        datos = {
            "device_id": "HELTEC-COLLAR-02",
            "animal_id": "BOV-002",
            "lat": 20.37700,
            "lon": -99.65700,
            "bateria_pct": 12,
            "fix_valido": True,
            "timestamp": "2026-11-19 15:05:00"
        }
        database.guardar_lectura(datos)
        alertas = database.obtener_alertas(solo_pendientes=True)
        alertas_bateria = [a for a in alertas if a["device_id"] == "HELTEC-COLLAR-02" and a["tipo"] == "bateria_baja"]
        self.assertGreater(len(alertas_bateria), 0)

if __name__ == "__main__":
    unittest.main()
