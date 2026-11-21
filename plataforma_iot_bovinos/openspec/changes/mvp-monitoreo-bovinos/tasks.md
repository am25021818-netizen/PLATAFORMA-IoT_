# Lista de Tareas de Implementación (tasks.md)

- [x] **Tarea 1: Estructuración del repositorio y reglas mecatrónicas**
  - [x] Crear `AGENTS.md` raíz con lineamientos de fail-safe, millis() y tópicos MQTT.
  - [x] Crear `.gitignore` para proteger base de datos y credenciales.
  - [x] Redactar contrato formal de telemetría en `openspec/specs/contrato-mqtt/spec.md`.

- [x] **Tarea 2: Firmware Embebido para Heltec ESP32 LoRa v2**
  - [x] Desarrollar `firmware/nodo_collar_gps/nodo_collar_gps.ino` con lectura no bloqueante de NMEA por UART y modulación LoRa a 915 MHz.
  - [x] Desarrollar `firmware/nodo_gateway_lora_mqtt/nodo_gateway_lora_mqtt.ino` con recepción LoRa y puente hacia broker MQTT Mosquitto vía Wi-Fi.

- [x] **Tarea 3: Backend de Persistencia y Base de Datos (SQLite)**
  - [x] Implementar `plataforma/src/database.py` con DDL completo de tablas y función de seeding con datos del Valle del Mezquital (Huichapan).
  - [x] Crear `tests/test_database.py` para validar inserción y consultas.

- [x] **Tarea 4: Servicio de Ingesta MQTT Continuo**
  - [x] Implementar `plataforma/src/ingesta_mqtt.py` con reconexión automática, parser JSON robusto y cálculo de alertas automáticas.
  - [x] Crear `tests/simulador_esp32.py` para generar trayectorias realistas de bovinos en el Mezquital.

- [x] **Tarea 5: Dashboard Web Interactivo con Streamlit**
  - [x] Implementar `plataforma/src/dashboard.py` con mapas interactivos de Folium (centrados en Huichapan/Valle del Mezquital).
  - [x] Implementar tarjetas de estado con semáforo de vigencia (verde, amarillo, rojo).
  - [x] Implementar historial de recorridos con trazado de líneas y selector de intervalos de fechas.
  - [x] Implementar módulo de visualización y atención de alertas.

- [x] **Tarea 6: Contenerización con Docker y Publicación Web**
  - [x] Crear `plataforma/Dockerfile` y `plataforma/docker-compose.yml`.
  - [x] Crear documentación para publicación con subdominio público (Cloudflare Tunnel / Nginx).
  - [x] Preparar guion de presentación y evidencias para la evaluación en clase.
