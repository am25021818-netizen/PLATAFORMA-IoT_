# Propuesta de Cambio: Corrección de Fail-Safe GPS, Resiliencia y Reportes

## 1. Contexto y Problema

La auditoría funcional del repositorio (24/11/2026) detectó desviaciones entre el comportamiento implementado y las reglas de `AGENTS.md`, `firmware/AGENTS.md`, `plataforma/AGENTS.md` y `openspec/specs/contrato-mqtt/spec.md`:

1. **GPS sin fix:** el collar sustituye la posición perdida por coordenadas fijas de laboratorio (`20.37542, -99.65431`) y marca `fix_valido=0`. El gateway republica esa coordenada y la ingesta la persiste como “última ubicación”, por lo que el mapa puede mostrar una posición falsa o un salto a `(0,0)`.
2. **Validación de ingesta:** las tramas con coordenadas fuera de rango se descartan; la regla de plataforma exige **almacenar la telemetría y alertar** el estado del sensor.
3. **No bloqueante:** `reconectarMQTT()` del gateway usa `delay(3000)` y se invoca desde `loop()`.
4. **Potencia LoRa:** el gateway no configura explícitamente `setTxPower(20)` (PA_BOOST).
5. **Reportes de la webapp Flask:** los endpoints CSV/JSON fallan con `NameError: datetime` porque falta el import.
6. **Seguridad y reproducibilidad:** la webapp corre con `debug=True` y clave secreta embebida; no tiene `requirements.txt` propio; el pin de `paho-mqtt` no coincide con el entorno validado.
7. **Higiene Git:** el repositorio remoto contiene `*.db` y `__pycache__` versionados, prohibidos por `AGENTS.md`.

## 2. Objetivo

Corregir las desviaciones anteriores sin cambiar la arquitectura de dos tramos ni el contrato MQTT, dejando una cadena de fail-safe coherente de extremo a extremo: **collar → gateway → ingesta → SQLite → dashboard**.

## 3. Decisión de diseño para el conflicto de reglas

Existe una aparente contradicción entre dos reglas:

- `firmware/AGENTS.md`: si no hay fix, enviar `lat=0, lon=0, fix_valido=0`.
- `AGENTS.md` raíz: no sobreescribir con coordenadas inválidas `(0,0)`; conservar la última válida y marcarla como desactualizada.

Se resuelve con responsabilidades por capa:

| Capa | Acción con `fix_valido=false` |
|---|---|
| Collar | Transmite `lat=0, lon=0, fix_valido=0` (regla de firmware). |
| Gateway | Publica la **última coordenada válida retenida en RAM** con `fix_valido=false`; si nunca hubo fix, publica `0,0` con `fix_valido=false`. |
| Ingesta | Persiste la trama, pero **nunca promueve** una posición sin fix como “actual”: conserva la última coordenada válida de SQLite y genera alerta `sin_fix`. |
| Dashboard | Muestra la última coordenada válida con semáforo en **amarillo/retrasada** mientras el fix siga siendo inválido, aunque el reloj sea reciente. |

## 4. Alcance

- Incluye cambios en firmware ESP32, ingesta MQTT, base de datos, dashboard Streamlit, webapp Flask, documentación, requirements y limpieza Git.
- **Fuera de alcance:** implementación física de `deep sleep` (requiere banco de pruebas con hardware real) y autenticación del broker Mosquitto en producción.

## 5. Criterios de aceptación

- `python tests/test_runner.py` → 4/4 en una base de datos temporal.
- Simulador: 3 paquetes con los campos obligatorios del contrato MQTT.
- Streamlit responde `/_stcore/health` → 200.
- Webapp: descargas CSV/JSON → 200; RBAC → 403 para roles no autorizados.
- Trama `fix_valido=false` → no aparece `(0,0)` en “últimas ubicaciones” y se crea alerta `sin_fix`.
- Trama con coordenadas fuera de rango → se persiste con alerta, no se descarta silenciosamente.
- Repositorio sin `*.db`, `*.sqlite`, `.env` ni `__pycache__` versionados.
