import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import json
import logging
import time
import paho.mqtt.client as mqtt
from config import MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_TOPIC_TELEMETRIA, MQTT_CLIENT_ID
from database import guardar_lectura

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("IngestaMQTT")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Conectado exitosamente al broker MQTT ({MQTT_BROKER_HOST}:{MQTT_BROKER_PORT})")
        client.subscribe(MQTT_TOPIC_TELEMETRIA, qos=1)
        logger.info(f"Suscrito al tópico de telemetría: {MQTT_TOPIC_TELEMETRIA}")
    else:
        logger.error(f"Fallo en la conexión MQTT, código de retorno: {rc}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8")
        logger.info(f"Mensaje recibido en [{topic}]: {payload_str}")

        data = json.loads(payload_str)

        # Validación básica de estructura requerida
        if "device_id" not in data or "lat" not in data or "lon" not in data:
            logger.warning(f"Trama rechazada por falta de campos obligatorios: {payload_str}")
            return

        # Validación de rango y estado del sensor (plataforma/AGENTS.md):
        # la telemetría inválida NO se descarta: se persiste con fix_valido=False
        # y database.guardar_lectura() se encarga de conservar la última posición válida.
        lat = float(data.get("lat", 0.0))
        lon = float(data.get("lon", 0.0))
        fuera_de_rango = not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0)
        if fuera_de_rango:
            logger.warning(f"Coordenadas fuera de rango físico: lat={lat}, lon={lon}. Se almacenarán con alerta.")

        fix_valido = data.get("fix_valido", True)
        if isinstance(fix_valido, str):
            fix_valido = fix_valido.strip().lower() in ("1", "true", "sí", "si", "yes")
        if fuera_de_rango or not bool(fix_valido):
            data["fix_valido"] = False
            logger.warning("Trama sin fix válido: se conservará la última coordenada válida y se alertará al operador.")

        # Guardar en SQLite
        guardar_lectura(data)
        logger.info(f"Lectura persistida correctamente para dispositivo {data.get('device_id')}")

    except json.JSONDecodeError:
        logger.error(f"Error al decodificar payload JSON inválido: {msg.payload}")
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)

def main():
    logger.info("Iniciando servicio de ingesta continua MQTT para Bovinos ITESHU...")
    
    # Compatibilidad con Paho MQTT 2.x
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    except AttributeError:
        client = mqtt.Client(client_id=MQTT_CLIENT_ID)

    client.on_connect = on_connect
    client.on_message = on_message

    # Ciclo de reconexión tolerante a fallos
    while True:
        try:
            logger.info(f"Intentando conectar a {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
            client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
            client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Deteniendo servicio de ingesta por orden del usuario.")
            break
        except Exception as e:
            logger.warning(f"Broker no disponible ({e}). Reintentando conexión en 5 segundos...")
            time.sleep(5)

if __name__ == "__main__":
    main()
