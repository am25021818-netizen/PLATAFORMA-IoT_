# Diseño: Footer institucional

## 1. Ubicación

- **Login:** `login.html` no extiende `base.html`, por lo que lleva su propio `<footer>` con posición fija al fondo y un `padding-bottom` en `body` para evitar solapamiento en móviles.
- **Autenticación:** `base.html` muestra el footer dentro de `#content`, después de `<main>`, aprovechando el layout flex existente.

## 2. Contenido

Ambos footers muestran:

- ITESHU · Maestría en Ingeniería Mecatrónica · Internet de las Cosas.
- Plataforma IoT de Monitoreo Bovino · Valle del Mezquital, Hidalgo · © 2026.
- Créditos: estudiante y docente titular.

## 3. Estilo

Se reutilizan Bootstrap Icons y los colores slate/blue ya presentes. No se crea CSS externo nuevo; se usan utilidades de Bootstrap y estilos embebidos mínimos para el footer fijo del login.
