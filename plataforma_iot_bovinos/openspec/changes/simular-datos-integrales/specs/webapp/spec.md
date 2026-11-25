# Delta de Especificación: Webapp

## ADDED Requirements

### Requirement: Datos de demostración integrales
La webapp SHALL poder cargar un conjunto determinista de 12 bovinos activos, 12 collares, 3 gateways, 3 ranchos, 4 potreros, telemetría de 48 horas y alertas variadas para demostración.

#### Scenario: Ejecución de la simulación
- **WHEN** se ejecuta `python simular_datos_integrales.py --solo-webapp`
- **THEN** la base `bovinos_iot.db` contiene 12 animales activos y 15 dispositivos activos
- **AND** `resumen_dashboard_rol` devuelve al menos un animal en verde, uno en amarillo y uno en rojo

#### Scenario: Repetición sin duplicados
- **WHEN** se ejecuta el simulador dos veces seguidas
- **THEN** el número de animales, dispositivos y lecturas no aumenta en la segunda ejecución

### Requirement: Alertas de demostración diversas
La webapp SHALL incluir alertas activas y atendidas de al menos tres tipos distintos después de la simulación.

#### Scenario: Consulta de alertas
- **WHEN** un administrador abre la vista de alertas
- **THEN** aparecen alertas de batería baja, sin comunicación o geocerca con fechas relativas recientes
