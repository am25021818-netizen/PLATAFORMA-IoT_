# Delta de Especificación: Webapp

## ADDED Requirements

### Requirement: Footer institucional visible
La webapp SHALL mostrar un pie de página con identificación institucional, del posgrado, del proyecto y de los responsables, tanto en la pantalla de login como en las páginas autenticadas.

#### Scenario: Login sin sesión
- **WHEN** un visitante abre `GET /login`
- **THEN** el HTML contiene un `<footer>` con `ITESHU`, `Maestría en Ingeniería Mecatrónica`, `Valle del Mezquital` y `2026`

#### Scenario: Página autenticada
- **WHEN** un usuario con sesión abre cualquier página que hereda de `base.html`
- **THEN** el footer aparece después de `<main>` con la misma información institucional
