# Propuesta de Cambio: Despliegue del Sitio Web en servidor STI-ITESHU

## 1. Contexto

El dominio `sti.itsoeh.edu.mx` está ocupado actualmente por una instancia de ThingsBoard. Se solicita sustituirla por el sitio web propio del proyecto (webapp Flask + dashboard Streamlit), conservando el broker MQTT local de la plataforma.

## 2. Objetivo

Aportar al repositorio una configuración de producción reproducible que permita:

1. Detener ThingsBoard de forma segura, con respaldo previo.
2. Publicar la webapp Flask en `/` y el dashboard Streamlit en `/dashboard/`.
3. Terminar TLS con Let's Encrypt o con el certificado institucional.
4. Documentar verificación y reversa.

## 3. Alcance

- Nuevos archivos: `docker-compose.prod.yml`, `webapp/Dockerfile.prod`, `webapp/.dockerignore`, `plataforma/.dockerignore`, `plataforma/mosquitto.conf`, `docs/despliegue_sti.md`, `docs/manual_despliegue_para_no_tecnico.md`, `docs/Manual_Despliegue_STI_ITESHU.pdf` y `generar_pdf_manual_despliegue.py`.
- Actualización de `README.md` con los enlaces a las guías y al PDF.
- **No se modifica** el contrato MQTT ni la lógica funcional de la plataforma.

## 4. Restricciones

- Requiere acceso SSH con `sudo` en el servidor o que el personal de STI ejecute las tareas de sistema.
- El cambio de ThingsBoard debe autorizarse y hacerse en ventana de mantenimiento.
- Los puertos 1883, 5000 y 8501 se publican solo en `127.0.0.1`; Nginx expone únicamente 80/443.

## 5. Criterios de aceptación

- `curl -I https://sti.itsoeh.edu.mx` → 200.
- `curl -I https://sti.itsoeh.edu.mx/dashboard/` → 200.
- `docker compose -f docker-compose.prod.yml ps` → tres servicios activos.
- Guía de reversa documentada y probable sin borrar el respaldo de ThingsBoard.
