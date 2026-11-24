# Plataforma IoT para Monitoreo GPS de Bovinos en el Valle del Mezquital

[![MIM - ITESHU](https://img.shields.io/badge/ITESHU-Maestría%20en%20Mecatrónica-blue.svg)](http://www.iteshu.edu.mx/)
[![Stack](https://img.shields.io/badge/Stack-ESP32%20·%20LoRa%20·%20MQTT%20·%20Python%20·%20Docker-green.svg)](#)
[![Metodología](https://img.shields.io/badge/Methodology-OpenCode%20·%20OpenSpec-orange.svg)](#)
[![Licencia](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#)

Sistema integral de geolocalización y supervisión remota para ganado bovino en pastoreo extensivo en la región del Valle del Mezquital, Estado de Hidalgo. Proyecto desarrollado como MVP funcional para la asignatura de **Internet de las Cosas (IoT)** y trabajo de tesis de maestría.

---

## 1. Arquitectura de dos tramos

```
[ Bovino: Collar LoRa + GPS ]
              │ (Radio LoRa 915 MHz, SF7, 125 kHz, 20 dBm - canal privado)
              ▼
[ Gateway: Heltec ESP32 LoRa v2 ]  ← retiene la última coordenada válida
              │ (Wi-Fi / TCP-IP, LWT en estado)
              ▼
[ Broker MQTT (Mosquitto) ]
              │ (Telemetría: bovinos/{device_id}/telemetria)
              ▼
[ Ingesta Python (paho-mqtt v2) + SQLite ]
              ├──► Dashboard Streamlit .......... http://localhost:8501
              └──► Webapp Flask + API RBAC ...... http://localhost:5000
```

**Regla de oro (fail-safe):** si el GPS pierde el fix, el collar transmite `lat=0, lon=0, fix_valido=0`. El gateway reenvía la última coordenada válida que recibió, la plataforma **no la reemplaza** por `(0,0)` y la muestra en **amarillo / desactualizada**, generando la alerta `sin_fix`. Ver el detalle en `openspec/changes/fix-failsafe-gps-y-resiliencia/design.md`.

---

## 2. Estructura del repositorio

```text
plataforma_iot_bovinos/
├── AGENTS.md                          # Reglas globales: MQTT, fail-safe, millis(), git
├── README.md                          # Esta guía
├── .gitignore                         # Excluye *.db, .env, __pycache__, etc.
├── openspec/
│   ├── specs/contrato-mqtt/spec.md    # Contrato MQTT (fuente de verdad)
│   └── changes/
│       ├── mvp-monitoreo-bovinos/     # Propuesta original del MVP
│       └── fix-failsafe-gps-y-resiliencia/  # Propuesta/diseño/tasks del último arreglo
├── firmware/
│   ├── AGENTS.md                      # Reglas de firmware (915 MHz, 20 dBm, sin delay)
│   ├── nodo_collar_gps/               # Emisor LoRa + GPS (TinyGPS++)
│   │   ├── config.h
│   │   └── nodo_collar_gps.ino
│   └── nodo_gateway_lora_mqtt/        # Puente LoRa → Wi-Fi → MQTT con LWT
│       ├── config.h
│       └── nodo_gateway_lora_mqtt.ino
├── plataforma/                        # Backend + dashboard (Stack oficial ITESHU)
│   ├── AGENTS.md
│   ├── requirements.txt               # paho-mqtt, streamlit, pandas, folium, pytest...
│   ├── Dockerfile
│   ├── docker-compose.yml             # Mosquitto + contenedor de la plataforma
│   ├── .env.example                   # Plantilla de variables de entorno
│   └── src/
│       ├── config.py                  # Broker, rutas DB y umbrales 600/1800 s
│       ├── database.py                # DDL, sembrado, consultas y fail-safe
│       ├── ingesta_mqtt.py            # Suscriptor continuo con reconexión
│       └── dashboard.py               # Streamlit + Folium (OSM / ESRI)
├── tests/
│   ├── test_runner.py                 # Pruebas unittest (no requiere pytest)
│   ├── test_database.py               # Las mismas pruebas en formato pytest
│   └── simulador_esp32.py             # 3 bovinos de Huichapan vía MQTT
├── webapp/                            # Interfaz Flask con RBAC y analítica
│   ├── app.py                         # Vistas, API REST, descargas CSV/JSON
│   ├── requirements.txt               # Flask + Werkzeug
│   ├── iniciar_webapp.bat
│   ├── database/
│   │   ├── db_manager.py              # Acceso SQL parametrizado y RBAC
│   │   ├── schema.sql
│   │   └── seed.sql                   # Usuarios y datos de demostración
│   ├── templates/                     # Jinja2 (dashboard, mapa, alertas, reportes...)
│   └── static/                        # CSS, JS e imágenes
└── docs/
    ├── despliegue_subdominio.md       # Publicación HTTPS con subdominio (Cloudflare / VPS)
    ├── despliegue_sti.md              # Reemplazo de ThingsBoard en sti.itsoeh.edu.mx
    ├── manual_despliegue_para_no_tecnico.md  # Manual explicado sin tecnicismos
    ├── Manual_Despliegue_STI_ITESHU.pdf      # Versión PDF lista para imprimir/entregar
    └── guion_presentacion_final.md    # Guion para evaluación en clase
```

> Las bases de datos `*.db` **no se versionan**. Se crean automáticamente la primera vez que arranca cada aplicación.

---

## 3. Contrato MQTT (fuente de verdad)

| Tópico | Dirección | Payload / propósito |
|---|---|---|
| `bovinos/{device_id}/telemetria` | Gateway → Web | `device_id`, `animal_id`, `lat`, `lon`, `altitud_m`, `velocidad_kmh`, `bateria_pct`, `rssi_dbm`, `snr_db`, `satelites`, `fix_valido`, `timestamp` |
| `bovinos/{device_id}/comandos` | Web → Gateway/Collar | Comandos de configuración (reservado para futuras iteraciones) |
| `bovinos/{device_id}/estado` | Gateway → Web | Last Will and Testament: `{"estado":"online"}` / `{"estado":"offline"}` retenido |

Configuración LoRa: **915.0 MHz**, **SF7**, **125 kHz**, **20 dBm (PA_BOOST)**, *sync word* `0x34`.

---

## 4. Puesta en marcha

### 4.1 Opción A: Docker (recomendada)

```bash
cd plataforma
docker compose up -d --build
```

- Dashboard: http://localhost:8501
- Broker MQTT: `localhost:1883` (WebSocket en `9001`)

### 4.2 Opción B: sin Docker (Windows / local)

```bat
iniciar_plataforma_local.bat
```

Instala `plataforma/requirements.txt` y levanta Streamlit en el puerto 8501. En otra terminal, si necesitas el flujo MQTT:

```bat
python -m pip install -r plataforma\requirements.txt
python plataforma\src\ingesta_mqtt.py
python tests\simulador_esp32.py
```

> Sin broker MQTT el simulador avisa y termina; la ingesta reintenta cada 5 s hasta que Mosquitto esté disponible. Para una prueba aislada puedes usar `DB_PATH` apuntando a un archivo temporal y no tocar la base real.

### 4.3 Webapp Flask (interfaz RBAC)

```bat
cd webapp
iniciar_webapp.bat
```

Abre http://localhost:5000. Para producción define `FLASK_SECRET_KEY` en el entorno (el valor por defecto es solo de demostración).

**Usuarios de demostración** (definidos en `webapp/database/seed.sql`):

| Correo | Contraseña | Rol |
|---|---|---|
| `admin@mezquital.mx` | `admin123` | `administrador` |
| `dueno@mezquital.mx` | `dueno123` | `administrador` de rancho |
| `operador@mezquital.mx` | `operador123` | `operador` |
| `tecnico@mezquital.mx` | `tecnico123` | `tecnico_mantenimiento` |

Cambia estas credenciales antes de cualquier despliegue público.

Para desplegar en el servidor ITESHU (`sti.itsoeh.edu.mx`) y sustituir ThingsBoard:
- Guía técnica: [`docs/despliegue_sti.md`](docs/despliegue_sti.md)
- Manual explicado para personal no técnico: [`docs/manual_despliegue_para_no_tecnico.md`](docs/manual_despliegue_para_no_tecnico.md)
- Manual en PDF (para imprimir o entregar): [`docs/Manual_Despliegue_STI_ITESHU.pdf`](docs/Manual_Despliegue_STI_ITESHU.pdf)

El PDF se regenera desde la raíz del repo con `python generar_pdf_manual_despliegue.py`; el script también deja una copia en el escritorio principal.

---

## 5. Pruebas

```bash
python tests/test_runner.py            # unittest, 4 pruebas, sin pytest
python tests/test_database.py          # requiere pytest (en requirements.txt)
python tests/simulador_esp32.py        # inyecta 3 bovinos cada 10 s por MQTT
```

Cobertura actual:

- Creación del esquema y sembrado del Valle del Mezquital.
- Persistencia y recuperación de lecturas GPS.
- Generación automática de alerta por batería < 20 %.
- Resumen del dashboard (totales y semáforo de vigencia).
- Simulador: 3 tramas válidas contra el contrato MQTT.
- Regresión manual ejecutada el 24/11/2026: ingesta con mensajes simulados, endpoints Flask (RBAC 200/403 y descargas CSV/JSON 200) y health check de Streamlit.

Para no ensuciar tus datos reales fuerza una base temporal:

```powershell
$env:DB_PATH = "$env:TEMP\datos_iot_prueba.db"
python tests\test_runner.py -v
```

---

## 6. Reglas de operación y semáforo

| Estado | Tiempo desde el último reporte | Color |
|---|---|---|
| Actualizada | < 10 min (600 s) | Verde |
| Retrasada | 10–30 min (600–1800 s), **o sin fix GPS** | Amarillo |
| Sin comunicación | > 30 min (1800 s) | Rojo |

Reglas adicionales:

- `loop()` del ESP32 nunca usa `delay()`; todo se basa en `millis()`.
- El gateway reconecta MQTT con compuerta de 3 s sin bloquear la recepción LoRa.
- Todo el SQL está parametrizado en `database.py` / `db_manager.py`.
- No se versionan bases de datos, `.env`, ni `__pycache__`.

---

## 7. Flujo de cambio (OpenSpec)

1. Escribir la propuesta en `openspec/changes/<nombre>/` (`proposal.md`, `design.md`, `tasks.md`, `specs/.../spec.md`).
2. Implementar el código marcando las tareas en `tasks.md`.
3. Ejecutar pruebas con bases temporales.
4. Hacer commits atómicos en español con Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).

El contrato MQTT vivo está en `openspec/specs/contrato-mqtt/spec.md`; los deltas de cada cambio se documentan dentro de su carpeta en `openspec/changes/`.

---

## 8. Limitaciones conocidas

- El broker de demostración no usa autenticación; configura Mosquitto con usuario/contraseña antes de exponerlo a Internet.
- El collar aún no entra en `deep sleep`; el ahorro de energía actual es por transmisión periódica (`INTERVALO_ENVIO_MS = 30000` en laboratorio). La implementación física de deep sleep queda pendiente de pruebas con hardware.
- El mapa Folium usa el color `orange` para el amarillo porque la librería no expone un icono `yellow`; el *badge* HTML sí usa amarillo (`#e9c46a`).

---

## 9. Créditos

- **Estudiante:** Ing. Iván Rodríguez Hernández
- **Docente titular:** DTI. Carlos Arturo Espinoza Galicia
- **Institución:** Instituto Tecnológico Superior de Huichapan (ITESHU)
- **Posgrado:** Maestría en Ingeniería Mecatrónica (MIM)
- **Periodo:** Semestre Agosto – Diciembre 2026
