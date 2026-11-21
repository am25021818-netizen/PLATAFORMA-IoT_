# Plataforma IoT para Monitoreo GPS de Bovinos en el Valle del Mezquital

[![MIM - ITESHU](https://img.shields.io/badge/ITESHU-Maestría%20en%20Mecatrónica-blue.svg)](http://www.iteshu.edu.mx/)
[![Stack](https://img.shields.io/badge/Stack-ESP32%20·%20LoRa%20·%20MQTT%20·%20Python%20·%20Docker-green.svg)](#)
[![Metodología](https://img.shields.io/badge/Methodology-OpenCode%20·%20OpenSpec-orange.svg)](#)
[![Licencia](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#)

Sistema integral de geolocalización y supervisión remota para ganado bovino en pastoreo extensivo en la región del Valle del Mezquital, Estado de Hidalgo. Proyecto desarrollado como MVP funcional para la asignatura de **Internet de las Cosas (IoT)** y trabajo de tesis de maestría.

---

## 📌 1. Arquitectura de Dos Tramos

```
[ Bovino: Collar LoRa + GPS ]
             │ (Radio LoRa 915 MHz - Canal Privado)
             ▼
[ Gateway: Heltec ESP32 Base ]
             │ (Wi-Fi / Red TCP-IP)
             ▼
[ Broker MQTT (Mosquitto) ]
             │ (Tópico: bovinos/+/telemetria)
             ▼
[ Contenedor Docker: Python Ingesta + SQLite + Streamlit ]
             │ (Puerto 8501 / HTTPS)
             ▼
[ Subdominio Web: bovinos.tudominio.com ]
```

---

## 📂 2. Estructura del Repositorio (Monorepo)

```
plataforma_iot_bovinos/
├── AGENTS.md                          # Reglas globales mecatrónicas y fail-safe
├── .gitignore                         # Exclusión de base de datos y credenciales
├── README.md                          # Documentación general del repositorio
├── openspec/                          # Especificaciones y planos formales
│   ├── specs/contrato-mqtt/spec.md    # Contrato formal MQTT (Fuente de verdad)
│   └── changes/mvp-monitoreo-bovinos/ # Propuesta técnica, diseño y tareas
│       ├── proposal.md
│       ├── design.md
│       ├── tasks.md
│       └── specs/telemetria.md
├── firmware/                          # Código para microcontroladores
│   ├── AGENTS.md                      # Reglas de firmware: millis() y LoRa 915MHz
│   ├── nodo_collar_gps/               # Nodo emisor collar (Heltec LoRa + GPS)
│   │   ├── config.h
│   │   └── nodo_collar_gps.ino
│   └── nodo_gateway_lora_mqtt/        # Nodo retransmisor base (LoRa a MQTT)
│       ├── config.h
│       └── nodo_gateway_lora_mqtt.ino
├── plataforma/                        # Aplicación web y backend en Docker
│   ├── AGENTS.md                      # Reglas Python y Streamlit
│   ├── requirements.txt               # Dependencias Python
│   ├── Dockerfile                     # Receta de construcción del contenedor
│   ├── docker-compose.yml             # Orquestación con broker Mosquitto y volumen
│   ├── .env.example                   # Variables de entorno de configuración
│   └── src/
│       ├── config.py                  # Parámetros y umbrales de vigencia
│       ├── database.py                # Base de datos SQLite (DDL, sembrado y queries)
│       ├── ingesta_mqtt.py            # Suscriptor continuo 24/7 a MQTT
│       └── dashboard.py               # Aplicación web reactiva Streamlit (Mapas Folium)
├── tests/                             # Pruebas y simuladores
│   ├── simulador_esp32.py             # Emulador de nodos Heltec sin hardware
│   ├── test_runner.py                 # Ejecutor de pruebas unitarias
│   └── test_database.py               # Pruebas con pytest
└── docs/                              # Manuales de apoyo
    ├── despliegue_subdominio.md       # Guía de publicación con subdominio web
    └── guion_presentacion_final.md    # Guion para evaluación en clase
```

---

## 🚀 3. Instrucciones de Despliegue con Docker

1. Clonar el repositorio y entrar a la carpeta de la plataforma:
   ```bash
   git clone https://github.com/tu-usuario/plataforma_iot_bovinos.git
   cd plataforma_iot_bovinos/plataforma
   ```

2. Levantar el servicio en segundo plano con Docker Compose:
   ```bash
   docker compose up -d --build
   ```

3. Acceder al dashboard en tu navegador:
   ```
   http://localhost:8501
   ```

4. Para publicar bajo subdominio web con HTTPS automático gratuito:
   Consulta la guía completa en [docs/despliegue_subdominio.md](docs/despliegue_subdominio.md).

---

## 🧪 4. Pruebas Unitarias y Simulación de Hardware

Para ejecutar las pruebas unitarias:
```bash
python tests/test_runner.py
```

Para activar el simulador de hardware (inyección periódica de coordenadas de 3 bovinos en Huichapan por MQTT):
```bash
python tests/simulador_esp32.py
```

---

## 👨‍💻 Autor y Asesoría
- **Estudiante:** Ing. Iván Rodríguez Hernández
- **Docente Titular:** DTI. Carlos Arturo Espinoza Galicia
- **Institución:** Instituto Tecnológico Superior de Huichapan (ITESHU)
- **Posgrado:** Maestría en Ingeniería Mecatrónica (MIM)
- **Periodo:** Semestre Agosto - Diciembre 2026
