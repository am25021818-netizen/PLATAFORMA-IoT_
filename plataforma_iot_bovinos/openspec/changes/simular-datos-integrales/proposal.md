# Propuesta de Cambio: Simulación integral de datos bovinos

## 1. Contexto

Las semillas actuales contienen 6 bovinos y fechas fijas (`2026-11-19`), por lo que el semáforo de vigencia se muestra todo en rojo, hay pocas lecturas y casi no hay variedad de alertas. Esto no permite demostrar los resultados integrales del sitio publicado: métricas por rancho, distribución de razas, estado de baterías, reporte de actividad, historial, mapa y alertas.

Existen dos bases SQLite con esquemas distintos:

- `webapp/database/bovinos_iot.db`: la consume Flask en `127.0.0.1:5000`.
- `plataforma/data/datos_iot.db`: la consume Streamlit en `127.0.0.1:8501`.

## 2. Objetivo

Crear un simulador determinista e idempotente que llene ambas bases con un hato de prueba realista del Valle del Mezquital y genere telemetría, estados de comunicación y alertas suficientes para que todas las vistas muestren resultados integrales y verificables.

## 3. Alcance

- Nuevo script `simular_datos_integrales.py` sin dependencias externas.
- Datos para 12 bovinos, 3 ranchos, 4 potreros, 12 collares y 3 gateways.
- Hasta 48 horas de lecturas GPS con intervalos configurables.
- Estados de vigencia: verde (< 10 min), amarillo (10–30 min) y rojo (> 30 min).
- Alertas de batería baja, sin comunicación, fuera de geocerca, velocidad anormal, sin fix y coordenadas inválidas, con algunas atendidas.
- Respeta el fail-safe: las lecturas sin fix o fuera de rango se conservan con `fix_valido=0` y no sobreescriben la última posición válida.
- Documentación de ejecución en servidor y locale.

## 4. Restricciones

- No commitear archivos `*.db`.
- No modificar contratos MQTT, RBAC ni lógica de negocio.
- No instalar paquetes nuevos: solo `sqlite3`, `datetime`, `random`, `argparse`, `math` y `pathlib`.
- La simulación debe poder repetirse sin duplicar registros.

## 5. Criterios de aceptación

- `python simular_datos_integrales.py --verificar` reporta ambas bases con conteos esperados y sin fallos.
- Flask muestra 12 animales activos, 12 collares, 3 gateways, 3 ranchos, alertas activas y semáforo con los tres colores.
- Streamlit muestra 12 animales activos, trayectorias recientes y alertas de distintos tipos.
- Las lecturas con `fix_valido=0` no se convierten en la posición vigente.
- El script se puede ejecutar otra vez sin aumentar el número de animales, collares ni lecturas.
