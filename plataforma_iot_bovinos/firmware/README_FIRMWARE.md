# Instrucciones de Compilación y Flasheo de Nodos Físicos
## Plataforma IoT Bovinos - Valle del Mezquital, Hidalgo

Este directorio contiene el código fuente para los microcontroladores **Heltec WiFi LoRa 32 v2 (ESP32)** que integran el hardware del proyecto.

---

### Estructura del Hardware
1. **`nodo_collar_gps/`**
   - **Dispositivo:** Heltec LoRa ESP32 v2 + Módulo GPS NEO-6M + Batería LiPo 3.7V.
   - **Función:** Se coloca en el collar de cuero del bovino dentro de un gabinete estanco (IP66/IP67). Lee coordenadas NMEA mediante hardware serial y transmite paquetes LoRa en 915.0 MHz usando temporización no bloqueante (`millis()`). Incorpora protección fail-safe para no sobrescribir coordenadas válidas con (0,0) en caso de pérdida momentánea de cobertura satelital.

2. **`nodo_gateway_lora_mqtt/`**
   - **Dispositivo:** Heltec LoRa ESP32 v2 conectado a red WiFi o USB-Serial hacia Raspberry Pi / PC.
   - **Función:** Receptor LoRa en 915.0 MHz. Recibe los paquetes de telemetría de los collares, desempaqueta la trama binaria/JSON y la publica a través de MQTT hacia el Broker (Mosquitto) en el tópico: `rancho/mezquital/telemetria`.

---

### Pasos de Carga en Arduino IDE

1. **Instalar el soporte para placas ESP32:**
   - En Arduino IDE: `Archivo -> Preferencias -> Gestor de URLs adicionales de tarjetas`:
     `https://dl.espressif.com/dl/package_esp32_index.json`
   - En `Herramientas -> Placa -> Gestor de tarjetas`, buscar e instalar **esp32 by Espressif Systems**.
   - Seleccionar placa: **Heltec WiFi LoRa 32(V2)**.

2. **Instalar Librerías Requeridas:**
   - `TinyGPSPlus` (por Mikal Hart)
   - `PubSubClient` (por Nick O'Leary)
   - `ArduinoJson` (v6.x)
   - `Heltec ESP32 Dev-Boards` o librerías nativas LoRa (`LoRa.h`)

3. **Parámetros de Radiofrecuencia LoRa (México - IFT):**
   - **Frecuencia:** `915E6` (915.0 MHz)
   - **Spreading Factor:** `SF7`
   - **Bandwidth:** `125 kHz`
   - **Coding Rate:** `4/5`
   - **Sync Word:** `0x34` (red privada para evitar colisiones)
   - **Potencia TX:** `20 dBm`
