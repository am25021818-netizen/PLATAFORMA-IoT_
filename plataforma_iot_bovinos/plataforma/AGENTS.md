# AGENTS.md — Reglas de Plataforma Web (Python, Streamlit y Docker)

## 1. Stack Tecnológico Estándar (ITESHU)
- **Lenguaje:** Python 3.11+.
- **Framework Web:** Streamlit (ejecutado en puerto 8501).
- **Base de Datos:** SQLite persistida en volumen montado (`/app/data/datos_iot.db`).
- **Librería MQTT:** `paho-mqtt` versión 2.x con callbacks API v2.
- **Visualización Cartográfica:** `folium` y `streamlit-folium` (mapa interactivo con capas OpenStreetMap y Satélite ESRI).

## 2. Reglas de Ingesta y Resiliencia
- El servicio `ingesta_mqtt.py` debe operar de forma continua, reconectando automáticamente ante caídas del broker.
- Validación de datos entrantes: si `lat` y `lon` están fuera del rango válido de la Tierra o si `fix_valido` es falso, almacenar la telemetría pero alertar el estado del sensor.
- Separación de responsabilidades: `database.py` contiene todo el acceso SQL parametrizado (prohibida la inyección de SQL con strings concatenados).
- Los colores de estado en interfaz deben cumplir estrictamente: Verde = Actualizada (< 10 min), Amarillo = Retrasada (10-30 min), Rojo = Sin comunicación (> 30 min).
