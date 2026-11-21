# Contrato MQTT — Plataforma de Monitoreo GPS de Bovinos (ITESHU)

## Purpose
Definir la especificación técnica y el contrato formal de comunicación entre los nodos retransmisores (Gateways Heltec LoRa ESP32 v2) y la plataforma de ingesta en la nube/servidor para el monitoreo de bovinos en el Valle del Mezquital.

## Requirements

### Requirement: Telemetría de Ubicación y Estado de Bovinos
El Gateway SHALL publicar tramas JSON periódicas en el tópico `bovinos/{device_id}/telemetria` conteniendo la geolocalización y salud del nodo emisor.

#### Scenario: Transmisión con Fix GPS Válido
- **WHEN** el collar obtiene una posición GPS válida y la retransmite por LoRa al Gateway
- **THEN** el Gateway publica en MQTT un payload JSON con `device_id`, `animal_id`, `lat`, `lon`, `bateria_pct`, `rssi_dbm` y `fix_valido` como true.

#### Scenario: Transmisión sin Cobertura Satelital
- **WHEN** el GPS del collar no tiene cobertura satelital en un potrero techado
- **THEN** el Gateway publica la trama con `fix_valido` como false conservando el último reporte sin sobreescribir coordenadas nulas.

### Requirement: Notificación de Desconexión de Red (LWT)
El broker MQTT SHALL registrar la pérdida de conexión del Gateway mediante Last Will and Testament en el tópico `bovinos/{device_id}/estado`.

#### Scenario: Caída Inesperada de Energía o Internet
- **WHEN** el Gateway pierde alimentación eléctrica o conectividad a Internet
- **THEN** el broker Mosquitto publica automáticamente el mensaje retenido con `estado: "offline"`.
