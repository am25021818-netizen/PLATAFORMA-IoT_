# Propuesta de Cambio: MVP Plataforma IoT de Monitoreo GPS de Bovinos

## 1. Contexto y Problema
En el Valle del Mezquital, Estado de Hidalgo, las actividades ganaderas extensivas sufren riesgos constantes de extravío, dispersión en terreno agreste y robo (abigeato). La supervisión presencial consume tiempo excesivo y carece de trazabilidad geográfica continua.

## 2. Objetivo de la Propuesta
Implementar el Producto Mínimo Viable (MVP) de la plataforma IoT basado en la arquitectura de dos tramos:
1. **Tramo 1 (Campo):** Nodo 1 emisor (Heltec ESP32 LoRa v2 + GPS) instalado en collar de cuero, que transmite ráfagas de telemetría a 915 MHz hacia el Nodo 2 (Gateway).
2. **Tramo 2 (Retransmisión a Nube):** Nodo 2 recibe paquetes LoRa y los reenvía vía MQTT (broker Mosquitto) a una plataforma de ingesta y dashboard web contenida en Docker.
3. **Persistencia y Visualización:** Almacenamiento estructurado en SQLite y dashboard interactivo con mapas en Streamlit accesible mediante subdominio web.

## 3. Alcance del MVP (Conforme al documento entregado el 13 de Noviembre 2026)
- RF-01 a RF-04: Autenticación básica y gestión de catálogo (bovinos, dispositivos, asociación 1 a 1).
- RF-05: Recepción y validación estricta de tramas de telemetría GPS vía MQTT.
- RF-06 y RF-07: Visualización cartográfica en tiempo real del hato y cálculo de semáforo de vigencia:
  - **Actualizada (Verde):** Reporte dentro de los últimos 10 minutos.
  - **Retrasada (Amarillo):** Reporte entre 10 y 30 minutos sin actualización.
  - **Sin comunicación (Rojo):** Más de 30 minutos sin reporte.
- RF-08: Historial de trayectorias con polilíneas sobre el mapa de la región del Mezquital / Huichapan.
- RF-10 y RF-11: Módulo de registro y atención de alertas de comunicación y batería baja.
- Simulación: Generador de telemetría espejo para demostraciones en aula y pruebas sin dependencia física del ganado.
