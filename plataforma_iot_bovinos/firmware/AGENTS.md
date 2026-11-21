# AGENTS.md — Reglas de Firmware (Heltec LoRa ESP32 v2)

## 1. Reglas de Programación Embebida
- **Prohibido el uso de `delay()` en `loop()`**: Toda la ejecución periódica debe basarse en cronómetros de tiempo relativo con `millis()`.
- **Frecuencia de Radio LoRa:** Configurar explícitamente a `915E6` (Banda ISM México).
- **Potencia de Transmisión LoRa:** 20 dBm (PA_BOOST).
- **Serial GPS:** Utilizar `HardwareSerial(1)` o `HardwareSerial(2)` en pines dedicados (ej. RX=22, TX=23 o RX=17, TX=16) a 9600 baudios.
- **Fail-Safe de GPS:** Si no hay fix satelital (`gps.location.isValid() == false`), el paquete LoRa debe enviarse con lat=0, lon=0 y `fix_valido=0` para no falsear posiciones anteriores en el mapa.
- **Ahorro de Batería:** Minimizar el tiempo de transmisión LoRa en el collar utilizando empaquetado binario o tramas cortas de texto delimitadas por comas.
