"""
simulador_esp32.py
Simulador de nodos Heltec LoRa ESP32 v2 para Monitoreo de Bovinos en el Valle del Mezquital.
Publica tramas MQTT periódicas emulando el movimiento real de los animales.
Cumple con la especificación de openspec/specs/contrato-mqtt/spec.md
"""

import time
import json
import random
import datetime
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

BOVINOS_SIMULADOS = [
    {
        "device_id": "HELTEC-COLLAR-01",
        "animal_id": "BOV-001",
        "nombre": "El Barón",
        "lat": 20.37542,
        "lon": -99.65431,
        "bateria": 92
    },
    {
        "device_id": "HELTEC-COLLAR-02",
        "animal_id": "BOV-002",
        "nombre": "La Paloma",
        "lat": 20.37890,
        "lon": -99.65820,
        "bateria": 85
    },
    {
        "device_id": "HELTEC-COLLAR-03",
        "animal_id": "BOV-003",
        "nombre": "El Pinto",
        "lat": 20.36950,
        "lon": -99.64910,
        "bateria": 22
    }
]

def main():
    print("=========================================================")
    print("  SIMULADOR ESP32 HELTEC LORA - MONITOREO DE BOVINOS   ")
    print("  Maestría en Mecatrónica - ITESHU                      ")
    print("=========================================================")
    
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="simulador-esp32-iteshu")
    except AttributeError:
        client = mqtt.Client(client_id="simulador-esp32-iteshu")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        print(f"[CONECTADO] Broker MQTT en {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar al broker ({e}). ¿Está Mosquitto corriendo?")
        return

    ciclo = 1
    try:
        while True:
            print(f"\n--- Ráfaga de Telemetría LoRa/MQTT Ciclo #{ciclo} ---")
            for bov in BOVINOS_SIMULADOS:
                # Simular desplazamiento ligero en el potrero
                desp_lat = random.uniform(-0.0003, 0.0003)
                desp_lon = random.uniform(-0.0003, 0.0003)
                bov["lat"] += desp_lat
                bov["lon"] += desp_lon
                
                # Consumo de batería gradual
                if random.random() < 0.2 and bov["bateria"] > 5:
                    bov["bateria"] -= 1

                payload = {
                    "device_id": bov["device_id"],
                    "animal_id": bov["animal_id"],
                    "lat": round(bov["lat"], 6),
                    "lon": round(bov["lon"], 6),
                    "altitud_m": round(2105.0 + random.uniform(-2, 3), 1),
                    "velocidad_kmh": round(random.uniform(0.2, 2.5), 1),
                    "bateria_pct": bov["bateria"],
                    "rssi_dbm": random.randint(-82, -65),
                    "snr_db": round(random.uniform(7.0, 10.0), 1),
                    "satelites": random.randint(8, 12),
                    "fix_valido": True,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                topico = f"bovinos/{bov['device_id']}/telemetria"
                client.publish(topico, json.dumps(payload), qos=1)
                print(f"[TX MQTT] {bov['nombre']} ({bov['device_id']}) -> Lat: {payload['lat']}, Lon: {payload['lon']}, Bat: {payload['bateria_pct']}%")

            ciclo += 1
            print("Esperando 10 segundos para el siguiente envío...")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nDeteniendo simulador ESP32.")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
