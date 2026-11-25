# Diseño: Simulación integral de datos bovinos

## 1. Script único, dos adaptadores

`simular_datos_integrales.py` expone un adaptador por esquema:

- `adaptador_webapp`: usa IDs enteros y columnas `timestamp_utc`, `rssi_lora`, `mac_id`, `collar_id`.
- `adaptador_plataforma`: usa IDs textuales (`BOV-001`, `HELTEC-COLLAR-01`) y columnas `fecha_captura`, `rssi_dbm`, `device_id`, `fix_valido`.

La lógica de generación es común: un catálogo canónico de ranchos, potreros, animales y dispositivos se traduce a cada esquema.

## 2. Rutas y configuración

Por defecto:

- Webapp: `WEBAPP_DB_PATH` o `webapp/database/bovinos_iot.db` relativo al script.
- Plataforma: `DB_PATH` o `plataforma/data/datos_iot.db` relativo al script.

Opciones:

- `--solo-webapp`, `--solo-plataforma`.
- `--horas 48`, `--intervalo-minutos 15`.
- `--verificar` solo imprime el estado sin escribir.
- `--no-backup` desactiva la copia `.bak` previa.

Antes de escribir, si la base existe, se crea `bovinos_iot.db.bak` / `datos_iot.db.bak`.

## 3. Conjunto de datos

- Ranchos: El Mezquital (Huichapan), San Clemente (Tecozautla), Los Nopales (Ixmiquilpan).
- Potreros: La Cantera, El Mezquite, Sabino Grande, Los Cardos.
- 12 bovinos con razas Simental, Charolais, Suizo, Angus, Brahman, Simbrah, Hereford, Gelbvieh.
- 12 collares Heltec LoRa ESP32 v2 y 3 gateways, todos a 915 MHz, SF7, 125 kHz y 20 dBm.
- Distribución de vigencia al momento de ejecutar:
  - 7 green: última lectura entre 1 y 8 minutos.
  - 3 orange: última lectura entre 12 y 25 minutos.
  - 2 red: última lectura entre 45 y 95 minutos.
- Baterías: alta (≥ 70%), media (30–69%) y baja (< 30%) para poblar el gráfico correspondiente.

## 4. Telemetría

Se generan `horas * 60 / intervalo` muestras por animal, con movimiento suave dentro del radio del potrero usando `random.Random(20261125)` para repetibilidad. Cada lectura incluye altitud, velocidad, HDOP/SNR, satélites, batería, RSSI y timestamp relativo a `datetime.now()`.

Casos especiales:

- Un collar reporta `fix_valido=0` y coordenadas `(0, 0)`; el script guarda la última coordenada válida como posición vigente.
- Otro collar reporta latitud fuera de rango; se conserva la telemetría con `fix_valido=0` y se genera alerta.

## 5. Alertas

Se insertan alertas con fechas relativas y una mezcla de `atendida=0/1`:

- `bateria_baja`, `sin_comunicacion` / `desconexion`, `fuera_geocerca`, `velocidad_anormal`, `dispositivo_caido`, `sin_fix` y `coordenadas_invalidas`.

Los tipos se adaptan al CHECK constraint de cada esquema. En la plataforma se usan `desconexion`, `sin_fix` y `coordenadas_invalidas`; en la webapp se usan `sin_comunicacion` y `dispositivo_caido`.

Las pruebas unitarias de `tests/test_runner.py` usan marcas de tiempo relativas al momento de ejecución para que sigan siendo válidas cuando la base contenga telemetría simulada reciente.

## 6. Idempotencia

Antes de insertar, se borran únicamente las tablas de simulación (`lecturas_gps`, `alertas`, `animales`, `dispositivos`, `potreros`, `ranchos` y `usuarios_ranchos` en webapp). Los usuarios y sus hashes se conservan. Luego se reinserta el catálogo canónico con IDs fijos, de modo que ejecutar el script dos veces produce los mismos conteos.

## 7. Verificación

`--verificar` consulta ambas bases y valida:

- 12 animales activos, 12 collares y 3 gateways en cada base.
- Al menos 200 lecturas en las últimas 48 h.
- Al menos 1 lectura con `fix_valido=0` en la plataforma.
- Al menos 5 alertas activas y 3 tipos distintos por base.
- Semáforo webapp con verde, amarillo y rojo presentes.
