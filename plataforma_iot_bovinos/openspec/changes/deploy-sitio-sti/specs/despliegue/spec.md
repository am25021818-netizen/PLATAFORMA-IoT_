# Delta de Especificación: Despliegue en STI

## ADDED Requirements

### Requirement: Publicación del Sitio en el Servidor Institucional
El repositorio SHALL incluir una configuración de producción que permita reemplazar ThingsBoard en `sti.itsoeh.edu.mx` por la webapp Flask y el dashboard Streamlit sin modificar el contrato MQTT.

#### Scenario: Arranque de Producción
- **WHEN** el operador ejecuta `docker compose -f docker-compose.prod.yml up -d --build` en el servidor
- **THEN** los servicios `mosquitto`, `streamlit` y `flask` quedan activos y enlazados solo a `127.0.0.1`

#### Scenario: Acceso Público
- **WHEN** un usuario visita `https://sti.itsoeh.edu.mx/` o `https://sti.itsoeh.edu.mx/dashboard/`
- **THEN** Nginx redirige respectivamente a Flask `:5000` y Streamlit `:8501` con TLS válido

#### Scenario: Reversa Segura
- **WHEN** el despliegue debe cancelarse
- **THEN** la guía permite detener los contenedores, restaurar el sitio de ThingsBoard en Nginx y reactivar su servicio sin borrar el respaldo
