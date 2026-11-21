import os
from pathlib import Path

# Directorios base
BASE_DIR = Path(__file__).resolve().parent.parent

# Conexión al Broker MQTT
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
MQTT_TOPIC_TELEMETRIA = "bovinos/+/telemetria"
MQTT_TOPIC_ESTADO = "bovinos/+/estado"
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "iteshu-ingesta-bovinos-worker")

# Base de datos SQLite
# Si corre dentro de Docker usa /app/data/datos_iot.db; en desarrollo local usa plataforma/data/datos_iot.db
DEFAULT_DB_PATH = BASE_DIR / "data" / "datos_iot.db"
DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH)))

# Umbrales temporales para clasificación de vigencia del dato (en segundos)
# Según especificación entregada:
# - Actualizada: dentro del tiempo esperado (< 10 minutos = 600 s)
# - Retrasada: supera intervalo permitido (10 a 30 minutos = 600 a 1800 s)
# - Sin comunicación: rebasa umbral de desconexión (> 30 minutos = 1800 s)
UMBRAL_RETRASO_SEG = int(os.getenv("UMBRAL_RETRASO_SEG", 600))
UMBRAL_DESCONEXION_SEG = int(os.getenv("UMBRAL_DESCONEXION_SEG", 1800))

# Ubicación por defecto del Rancho Piloto (Huichapan / Valle del Mezquital, Hidalgo)
DEFAULT_CENTER_LAT = 20.37542
DEFAULT_CENTER_LON = -99.65431
DEFAULT_ZOOM = 14
