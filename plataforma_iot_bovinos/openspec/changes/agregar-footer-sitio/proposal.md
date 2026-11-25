# Propuesta de Cambio: Footer institucional en el sitio publicado

## 1. Contexto

El sitio Flask ya tiene un pie de página mínimo en `base.html`, pero la pantalla de login no lo muestra y el texto actual no identifica claramente a la institución, el posgrado ni a los responsables del proyecto.

## 2. Objetivo

Agregar un footer visible y coherente en:

1. La pantalla de inicio de sesión (`login.html`).
2. Todas las páginas autenticadas que heredan de `base.html`.

## 3. Alcance

- `webapp/templates/login.html`: footer fijo abajo con datos ITESHU, maestría, proyecto y créditos.
- `webapp/templates/base.html`: footer enriquecido con la misma información institucional.
- Documentación OpenSpec del cambio.

## 4. Restricciones

- No se modifica la lógica de negocio, RBAC ni las APIs.
- No se agregan dependencias nuevas.
- El footer no debe tapar el formulario de login en pantallas pequeñas.

## 5. Criterios de aceptación

- `GET /login` muestra el footer sin necesitar sesión.
- Las páginas autenticadas muestran el footer al final del contenido.
- El texto incluye ITESHU, Maestría en Mecatrónica, Valle del Mezquital y el año 2026.
