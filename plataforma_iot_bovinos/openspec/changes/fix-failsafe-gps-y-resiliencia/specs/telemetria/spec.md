# Delta de Especificación: Telemetría y Fail-Safe

## MODIFIED Requirements

### Requirement: Ingesta y Validación de Tramas MQTT
El servicio de ingesta SHALL conservar toda la telemetría recibida en `bovinos/+/telemetria`, incluso cuando el sensor reporte un estado inválido, y SHALL registrar una alerta que haga visible la condición anómala en lugar de descartar silenciosamente la trama.

#### Scenario: Inserción Exitosa de Coordenadas
- **WHEN** arriba una trama con latitud y longitud válidas y `fix_valido=true`
- **THEN** la plataforma inserta el registro en `lecturas_gps` y actualiza la última comunicación del dispositivo

#### Scenario: Coordenadas Fuera de Rango
- **WHEN** una trama reporta latitud o longitud fuera del rango físico de la Tierra
- **THEN** la plataforma persiste la telemetría con `fix_valido=0`, reutiliza la última coordenada válida conocida y crea una alerta `coordenadas_invalidas`

## ADDED Requirements

### Requirement: Fail-Safe de Posición sin Fix GPS
La cadena collar → gateway → plataforma SHALL evitar que una lectura sin fix satelital se convierta en la posición vigente del animal.

#### Scenario: Collar sin Cobertura Satelital
- **WHEN** `gps.location.isValid()` es falso en el collar
- **THEN** la trama LoRa se transmite con `lat=0`, `lon=0` y `fix_valido=0`

#### Scenario: Gateway sin Fix Nuevo
- **WHEN** el gateway recibe una trama con `fix_valido=0`
- **THEN** publica en MQTT la última coordenada válida retenida (o `0,0` si nunca recibió una) con `fix_valido=false`

#### Scenario: Plataforma sin Fix
- **WHEN** la ingesta recibe `fix_valido=false`
- **THEN** `obtener_ultimas_ubicaciones()` conserva la última coordenada válida de SQLite, la clasifica como `retrasada` (amarillo) y la alerta `sin_fix` queda pendiente de atención

### Requirement: Reconexión No Bloqueante del Gateway
El gateway SHALL realizar reintentos de conexión MQTT sin invocar `delay()` desde `loop()`.

#### Scenario: Broker MQTT No Disponible
- **WHEN** `mqttClient.connected()` es falso y el broker no responde
- **THEN** `reconectarMQTT()` realiza un único intento por ciclo como máximo, con una compuerta de 3 segundos basada en `millis()`, permitiendo que la recepción LoRa siga activa

### Requirement: Reportes de la Webapp
Los endpoints de descarga de la webapp SHALL generar archivos CSV y JSON válidos.

#### Scenario: Descarga de Reporte de Actividad
- **WHEN** un usuario con rol `administrador` solicita `/api/reportes/descargar/csv` o `/api/reportes/descargar/json`
- **THEN** el servidor responde 200 con el nombre de archivo fechado y el contenido del reporte
