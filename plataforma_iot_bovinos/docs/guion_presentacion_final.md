# Guion para la Evaluación y Presentación Final en Clase

**Proyecto de Tesis:** Monitoreo GPS de Bovinos en Tiempo Real para el Valle del Mezquital, Hidalgo  
**Materia:** Internet de las Cosas (IoT) — MIM ITESHU  
**Docente:** DTI. Carlos Arturo Espinoza Galicia  
**Estudiante:** Ing. Iván Rodríguez Hernández  

---

## 1. Estructura de Diapositivas Recomendada (10 a 12 Minutos)

### Diapositiva 1: Portada y Título
- **Título:** Plataforma IoT y MVP de Monitoreo GPS de Bovinos para el Valle del Mezquital, Hgo.
- **Autor:** Ing. Iván Rodríguez Hernández.
- **Asesor / Docente:** DTI. Carlos Arturo Espinoza Galicia.
- **Programa:** Maestría en Ingeniería Mecatrónica (ITESHU).
- **Subdominio activo de la plataforma:** `https://bovinos.tudominio.com` (o link de presentación).

### Diapositiva 2: Contexto y Problemática Regional
- **El reto en el Valle del Mezquital:** Topografía agreste, parcelas extensas, vegetación que dificulta la supervisión visual.
- **Problemática real:** Pérdida de ganado por dispersión, abigeato (robo de ganado) y horas/hombre invertidas en búsquedas físicas a caballo o pie.
- **Oportunidad IoT:** Monitoreo remoto y oportuno de posición con comunicación de largo alcance y bajo consumo donde la cobertura celular es nula o inestable.

### Diapositiva 3: Arquitectura Mecatrónica en Dos Ramos
- Explicar el diagrama de bloques:
  - **Tramo 1 (En Campo):** Nodo collar en bovino (Heltec LoRa ESP32 v2 + GPS NEO-6M en 915 MHz).
  - **Tramo 2 (Rancho / Casco):** Gateway concentrador (Heltec LoRa ESP32 v2) que puentea paquetes de radio a tramas MQTT vía Wi-Fi.
  - **Nube / Servidor:** Contenedor Docker con ingesta Python continua, base de datos SQLite y dashboard Streamlit en puerto 8501.

### Diapositiva 4: Metodología Agéntica con OpenCode y OpenSpec
- **Spec-Driven Development:** Se definieron planos técnicos formales en `openspec/` antes de escribir código (`proposal.md`, `specs/`, `design.md`, `tasks.md`).
- **Reglas del Taller en `AGENTS.md`:** Interbloqueos de seguridad (fail-safe de GPS sin fix, temporizaciones no bloqueantes estrictas con `millis()`, frecuencia legal en México a 915 MHz).
- **Control de Versiones:** Commits atómicos en Git (`feat:`, `fix:`, `docs:`) garantizando trazabilidad total.

### Diapositiva 5: El MVP y Requerimientos Funcionales Clave
- **RF-01 a RF-04:** Registro de animales, collares y ranchos con unicidad de asociación.
- **RF-06 y RF-07 (Vigencia del dato):** Semáforo visual estricto:
  - 🟢 **Actualizado:** Datos de los últimos 10 min.
  - 🟡 **Retrasado:** 10 a 30 min sin reporte.
  - 🔴 **Sin Comunicación:** Más de 30 min sin paquete recibido.
- **RF-08:** Histórico de trayectorias en mapa satelital.
- **RF-10 y RF-11:** Módulo de atención y reconocimiento de alertas con bitácora de operador.

---

## 2. Demostración Práctica en Vivo (Paso a Paso durante la clase)

1. **Mostrar el despliegue del contenedor:**
   - Abre la terminal en el proyector y muestra:
     ```bash
     docker compose ps
     ```
   - Señala que el contenedor `iteshu_plataforma_iot` y el broker `iteshu_mosquitto_broker` están corriendo en el servidor.

2. **Abrir el Dashboard en el Subdominio Web:**
   - Abre el navegador web en `https://bovinos.tudominio.com`.
   - Explica la interfaz: paleta sobria ganadera, tarjetas de resumen general (3 animales, collares asignados, alertas pendientes).
   - Muestra el mapa centrado en Huichapan con los 3 bovinos en diferentes estados (verde, amarillo y rojo).

3. **Inyectar Telemetría en Vivo (La prueba de fuego):**
   - **Opción A (con hardware físico):** Enciende el collar y el gateway para que envíen el paquete LoRa; observa cómo se actualiza la terminal y el mapa.
   - **Opción B (con simulador rápido integrado):**
     - Ve a la pestaña **"Simulador Rápido"** en la barra lateral.
     - Selecciona al bovino `"BOV-003 (El Pinto)"` (que estaba en rojo por falta de comunicación).
     - Presiona el botón **"🚀 Enviar Telemetría Simulada Ahora"**.
     - Regresa al **"Dashboard Principal"**: ¡BOV-003 ahora tiene marcador verde, su batería subió y la tarjeta de "Actualizados" se incrementó!

4. **Demostrar el Historial de Recorridos (RF-08):**
   - Ve a **"Historial de Recorridos"**.
   - Selecciona a `"El Barón (BOV-001)"`.
   - Muestra cómo la plataforma traza la polilínea del trayecto sobre el mapa satelital mostrando cada punto cronológico.

5. **Demostrar la Atención de Alertas (RF-11):**
   - Ve a **"Centro de Alertas"**.
   - Muestra la alerta crítica de batería baja.
   - Llena el formulario con: *"Revisado en potrero por Ing. Iván. Batería cambiada."*
   - Clic en **"Reconocer y Marcar como Atendida"**. La alerta desaparece de pendientes y queda registrada en auditoría.

---

## 3. Preguntas Frecuentes del Docente y Cómo Responderlas

- **P: ¿Por qué usaste LoRa en lugar de GSM/4G directo en cada collar?**  
  *R:* "En las zonas rurales y cerros del Valle del Mezquital la cobertura celular es deficiente o nula, y los módulos 4G consumen de 10 a 20 veces más energía que un transmisor LoRa. Con LoRa en 915 MHz logramos enlaces de varios kilómetros en línea de vista con un consumo promedio de miliamperios, concentrando el acceso a Internet en un solo punto (el gateway del rancho)."

- **P: ¿Cómo garantizas que el microcontrolador no se trabe si se pierde el GPS o la señal?**  
  *R:* "Implementamos las reglas mecatrónicas de `AGENTS.md`: prohibimos funciones bloqueantes como `delay()` en el `loop()` y utilizamos cronómetros con `millis()`. Además, si la antena GPS pierde fix satelital, el código activa el flag `fix_valido = false` y no sobreescribe las coordenadas anteriores con ceros, evitando corromper la base de datos."

- **P: ¿Por qué elegiste Streamlit en contenedor Docker en lugar de una arquitectura pesada?**  
  *R:* "Cumple fielmente la guía metodológica de la maestría. Streamlit nos permite generar una interfaz web reactiva, ligera y directamente conectada a SQLite y Paho-MQTT sin dependencias externas complejas, asegurando que con un simple `docker compose up` la plataforma se levante en cualquier servidor o Raspberry Pi en segundos."
