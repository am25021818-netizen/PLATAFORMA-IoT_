# AGENTS.md — Monitoreo GPS de Bovinos (Maestría Mecatrónica — ITESHU)

## 1. Arquitectura y Fuente de Verdad
- **Proyecto Unificado (Monorepo):** `firmware/` (Heltec ESP32 LoRa v2) y `plataforma/` (Python + Streamlit + Docker).
- **Contrato MQTT y Fuente de Verdad:** Ubicado en `openspec/specs/contrato-mqtt/spec.md`.
  - **Telemetría (Gateway -> Web):** `bovinos/{device_id}/telemetria`
  - **Comandos (Web -> Gateway/Collar):** `bovinos/{device_id}/comandos`
  - **Estado / Last Will (LWT):** `bovinos/{device_id}/estado`

## 2. Reglas de Hardware y Seguridad Mecatrónica (Fail-Safe)
- **Frecuencia LoRa:** 915.0 MHz (Banda ISM para México / Región US915), Spreading Factor 7, Ancho de Banda 125 kHz.
- **Fail-Safe de Transmisión:** Si el GPS pierde fix (`fix_valido == 0`), no sobreescribir con coordenadas inválidas (0,0); reportar explícitamente flag `fix_valido: false` y mantener última coordenada válida identificada como desactualizada.
- **No Bloqueante:** Prohibido usar `delay()` en la función `loop()` del ESP32; toda temporización se realiza mediante máquinas de estados no bloqueantes con `millis()`.
- **Ahorro de Energía:** Modo de transmisión periódica (ej. 30 segundos en pruebas de laboratorio, 5 a 15 minutos en campo) con deep sleep o ciclo bajo consumo cuando no haya desplazamiento significativo.
- **Validación sin hardware:** Obligatorio validar la plataforma primero mediante `tests/simulador_esp32.py` antes de pruebas en vivo.

## 3. Flujo OpenSpec y Control de Versiones con Git
- **Modo Plan / Modo Build:** Las propuestas y cambios de arquitectura deben redactarse en `openspec/changes/<nombre>/` antes de tocar código fuente.
- **Convención de Commits:** Commits atómicos y en español siguiendo Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
- **Higiene de Repositorio:** Prohibido commitear archivos de base de datos (`*.db`, `*.sqlite`), variables de entorno (`.env`), paquetes binarios o carpetas virtuales (`__pycache__`, `.venv`).
