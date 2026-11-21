# Especificación de Telemetría GPS para Bovinos

## ADDED Requirements

### Requirement: Ingesta y Validación de Tramas MQTT
El servicio de ingesta SHALL validar que los payloads recibidos en `bovinos/+/telemetria` contengan identificador y coordenadas en rango antes de persistir.

#### Scenario: Inserción Exitosa de Coordenadas
- **WHEN** arriba una trama con latitud y longitud válidas dentro del rango del territorio
- **THEN** la plataforma inserta el registro en la tabla `lecturas_gps` y actualiza la última comunicación del dispositivo.

#### Scenario: Detección de Batería Crítica
- **WHEN** una lectura reporta un nivel de batería inferior al 20%
- **THEN** el sistema genera automáticamente un registro en la tabla `alertas` con nivel warning.

### Requirement: Semáforo de Vigencia Cartográfica
El dashboard SHALL categorizar cada bovino según el intervalo transcurrido desde su última actualización.

#### Scenario: Animal en Tiempo
- **WHEN** la última coordenada fue recibida hace menos de 600 segundos
- **THEN** el animal se muestra con marcador y estado verde ("Actualizada").

#### Scenario: Animal sin Comunicación
- **WHEN** transcurren más de 1800 segundos sin reporte del collar
- **THEN** el animal cambia a estado y marcador rojo ("Sin comunicación").
