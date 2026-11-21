import sys
from pathlib import Path
import json
import random
import datetime

# Asegurar que la carpeta src esté en sys.path
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

import importlib
import database
importlib.reload(database)

from config import DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON, DEFAULT_ZOOM
from database import (
    obtener_ranchos,
    obtener_potreros,
    obtener_resumen_dashboard,
    obtener_ultimas_ubicaciones,
    obtener_historial_animal,
    obtener_alertas,
    atender_alerta,
    guardar_lectura,
    registrar_dispositivo_real
)

# Configuración de página Streamlit
st.set_page_config(
    page_title="IoT Bovinos | Valle del Mezquital",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Personalizados con Paleta Ganadera Moderna y Tarjetas Visuales
st.markdown("""
<style>
    /* Tipografía y contenedor principal */
    .app-header {
        background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(27, 67, 50, 0.15);
    }
    .app-title {
        font-size: 24px;
        font-weight: 800;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .app-subtitle {
        font-size: 13px;
        color: #d8f3dc;
        margin-top: 4px;
    }
    .chip-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .chip-green { background-color: #2d6a4f; color: #ffffff; }
    .chip-yellow { background-color: #e9c46a; color: #264653; }
    .chip-red { background-color: #e76f51; color: #ffffff; }
    .chip-blue { background-color: #2a9d8f; color: #ffffff; }

    /* Tarjetas de métricas */
    .metric-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 14px 18px;
        border-left: 5px solid #2d6a4f;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 12px;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #1b4332;
        margin: 4px 0;
    }
    .metric-desc {
        font-size: 11px;
        color: #888888;
    }

    /* Ficha animal */
    .animal-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .battery-bar-container {
        width: 100%;
        background-color: #e9ecef;
        border-radius: 6px;
        height: 8px;
        overflow: hidden;
        margin-top: 4px;
    }
    .battery-bar-fill {
        height: 100%;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Barra Lateral de Navegación y Filtros
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2395/2395796.png", width=70)
st.sidebar.markdown("### **Plataforma IoT Ganadera**")
st.sidebar.markdown("*Monitoreo LoRa / MQTT · Valle del Mezquital*")

# Filtro de Rancho / Unidad de Producción
ranchos_disponibles = obtener_ranchos()
nombres_ranchos = {"TODOS": "Todos los Ranchos (Valle del Mezquital)"}
for r in ranchos_disponibles:
    nombres_ranchos[r["id"]] = f"{r['nombre']} ({r['municipio']}, Hgo)"

rancho_seleccionado = st.sidebar.selectbox(
    "📍 Unidad Pecuaria Activa:",
    options=list(nombres_ranchos.keys()),
    format_func=lambda x: nombres_ranchos[x]
)

st.sidebar.markdown("---")

opcion_menu = st.sidebar.radio(
    "Navegación del Sistema:",
    [
        "🗺️ Dashboard y Mapa General",
        "🐄 Fichas del Hato Bovino",
        "📈 Historial de Recorridos",
        "🚨 Centro de Alertas",
        "🔌 Conexión de Hardware Real",
        "⚡ Simulador Rápido de Campo"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Zona:** Valle del Mezquital, Hidalgo  
**Frecuencia:** 915.0 MHz (LoRa México)  
**Usuario:** Ing. Iván Rodríguez (ITESHU)  
**Versión:** 1.2.0 MVP Funcional
""")

# ==============================================================================
# HEADER GENERAL
# ==============================================================================
st.markdown(f"""
<div class="app-header">
    <div class="app-title">
        <span>🐄</span>
        <span>Sistema de Monitoreo GPS de Bovinos en Tiempo Real</span>
    </div>
    <div class="app-subtitle">
        Zona Geográfica: <b>Valle del Mezquital, Estado de Hidalgo</b> · Filtro: <b>{nombres_ranchos[rancho_seleccionado]}</b> · Red LoRa 915 MHz & MQTT Mosquitto
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 1: DASHBOARD Y MAPA GENERAL
# ==============================================================================
if opcion_menu == "🗺️ Dashboard y Mapa General":
    resumen = obtener_resumen_dashboard(rancho_seleccionado)
    
    # Fila de tarjetas métricas interactivas
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #1b4332;">
            <div class="metric-title">Hato Registrado</div>
            <div class="metric-value">{resumen['total_animales']}</div>
            <div class="metric-desc">Ejemplares con arete SINIGA</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2a9d8f;">
            <div class="metric-title">Collares LoRa</div>
            <div class="metric-value">{resumen['total_collares']}</div>
            <div class="metric-desc">Heltec ESP32 v2 vinculados</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2d6a4f;">
            <div class="metric-title">🟢 En Tiempo</div>
            <div class="metric-value">{resumen['actualizados']}</div>
            <div class="metric-desc">Reportes de los últimos 10 min</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #e9c46a;">
            <div class="metric-title">🟡 Retrasados</div>
            <div class="metric-value">{resumen['retrasados']}</div>
            <div class="metric-desc">10 a 30 min sin paquete</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #e76f51;">
            <div class="metric-title">🔴 Sin Conexión</div>
            <div class="metric-value">{resumen['sin_comunicacion']}</div>
            <div class="metric-desc">Mayor a 30 min sin señal</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Disposición: Mapa a la izquierda, lista rápida a la derecha
    col_mapa, col_lista = st.columns([7, 5])

    ubicaciones = obtener_ultimas_ubicaciones(rancho_seleccionado)
    potreros = obtener_potreros(None if rancho_seleccionado == "TODOS" else rancho_seleccionado)

    with col_mapa:
        st.subheader("🗺️ Mapa Satelital y Potreros del Valle del Mezquital")
        
        # Centrar el mapa según el rancho o promedio
        if ubicaciones:
            centro_lat = ubicaciones[0]["lat"] if ubicaciones[0]["lat"] else DEFAULT_CENTER_LAT
            centro_lon = ubicaciones[0]["lon"] if ubicaciones[0]["lon"] else DEFAULT_CENTER_LON
        else:
            centro_lat, centro_lon = DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON

        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=14, control_scale=True)

        # Capas de mapa
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Imagery',
            name='🛰️ Satélite Esri (Alta Resolución)',
            overlay=False
        ).add_to(m)
        folium.TileLayer('OpenStreetMap', name='🗺️ Calles y Caminos (OSM)').add_to(m)
        folium.TileLayer(
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='OpenTopoMap',
            name='⛰️ Topográfico y Relieve'
        ).add_to(m)

        # 1. Dibujar Potreros / Geocercas autorizadas
        for p in potreros:
            folium.Circle(
                radius=p["radio_m"],
                location=[p["lat_centro"], p["lon_centro"]],
                color=p["color_hex"],
                weight=2,
                dash_array='5, 5',
                fill=True,
                fill_color=p["color_hex"],
                fill_opacity=0.15,
                tooltip=f"<b>Potrero:</b> {p['nombre']}<br>Pasto: {p['tipo_pasto']}<br>Radio: {p['radio_m']}m"
            ).add_to(m)

        # 2. Marcadores interactivos de los bovinos
        for u in ubicaciones:
            if u["lat"] and u["lon"]:
                color_icono = "green" if u["estado_vigencia"] == "actualizada" else ("orange" if u["estado_vigencia"] == "retrasada" else "red")
                es_toro = u["categoria"] in ["Toro", "Semental"]
                icono_fa = "bullhorn" if es_toro else "tag"

                popup_html = f"""
                <div style="font-family: sans-serif; width: 220px;">
                    <div style="background-color: #1b4332; color: white; padding: 6px 10px; border-radius: 6px 6px 0 0; font-weight: bold;">
                        {'🐂' if es_toro else '🐄'} {u['nombre_animal']} ({u['raza']})
                    </div>
                    <div style="padding: 8px; border: 1px solid #ddd; border-top: none; background: white; font-size: 12px;">
                        <b>Arete SINIGA:</b> {u['arete_siniga']}<br>
                        <b>Categoría:</b> {u['categoria']} · {u['peso_kg']} kg<br>
                        <b>Rancho:</b> {u['nombre_rancho']} ({u['municipio']})<br>
                        <b>Potrero:</b> {u.get('nombre_potrero', 'Sin asignar')}<br>
                        <hr style="margin: 6px 0; border: 0.5px solid #eee;">
                        <b>Batería Collar:</b> {u['bateria_pct']}%<br>
                        <b>Señal LoRa (RSSI):</b> {u['rssi_dbm']} dBm (SNR: {u['snr_db']} dB)<br>
                        <b>Reporte:</b> Hace {u['tiempo_relativo']}<br>
                        <b>Estado:</b> <span style="color: {'green' if color_icono=='green' else ('orange' if color_icono=='orange' else 'red')}; font-weight: bold;">{u['estado_vigencia'].upper()}</span>
                    </div>
                </div>
                """

                folium.Marker(
                    location=[u["lat"], u["lon"]],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{'🐂' if es_toro else '🐄'} {u['nombre_animal']} ({u['arete_siniga']}) - Bat: {u['bateria_pct']}%",
                    icon=folium.Icon(color=color_icono, icon=icono_fa, prefix="fa")
                ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width="100%", height=480)

    with col_lista:
        st.subheader("📋 Lista Rápida del Ganado")
        for u in ubicaciones:
            es_toro = u["categoria"] in ["Toro", "Semental"]
            color_badge = "chip-green" if u["estado_vigencia"] == "actualizada" else ("chip-yellow" if u["estado_vigencia"] == "retrasada" else "chip-red")
            color_bat = "#2d6a4f" if u["bateria_pct"] > 50 else ("#e9c46a" if u["bateria_pct"] > 20 else "#e76f51")
            
            st.markdown(f"""
            <div class="animal-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 800; font-size: 15px; color: #1b4332;">
                        {'🐂' if es_toro else '🐄'} {u['nombre_animal']} <span style="font-size: 12px; color: #666; font-weight: normal;">({u['arete_siniga']})</span>
                    </div>
                    <span class="chip-badge {color_badge}">{u['estado_vigencia']}</span>
                </div>
                <div style="font-size: 12px; color: #555; margin-top: 4px;">
                    <b>Raza:</b> {u['raza']} | <b>Peso:</b> {u['peso_kg']} kg | <b>Municipio:</b> {u['municipio']}
                </div>
                <div style="font-size: 11px; color: #777; margin-top: 4px;">
                    <b>Collar LoRa:</b> <code>{u['device_id']}</code> | <b>Señal:</b> {u['rssi_dbm']} dBm | <b>Último reporte:</b> {u['tiempo_relativo']}
                </div>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 6px;">
                    <span style="font-size: 11px; font-weight: bold; color: {color_bat};">🔋 {u['bateria_pct']}%</span>
                    <div class="battery-bar-container">
                        <div class="battery-bar-fill" style="width: {u['bateria_pct']}%; background-color: {color_bat};"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 2: FICHAS DEL HATO BOVINO
# ==============================================================================
elif opcion_menu == "🐄 Fichas del Hato Bovino":
    st.markdown("### 📋 Fichas Técnicas del Hato Bovino (Valle del Mezquital)")
    st.markdown("Expediente pecuario, datos genealógicos, potrero asignado y estado del hardware.")

    ubicaciones = obtener_ultimas_ubicaciones(rancho_seleccionado)
    
    for i in range(0, len(ubicaciones), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(ubicaciones):
                u = ubicaciones[i + j]
                es_toro = u["categoria"] in ["Toro", "Semental"]
                color_badge = "chip-green" if u["estado_vigencia"] == "actualizada" else ("chip-yellow" if u["estado_vigencia"] == "retrasada" else "chip-red")
                
                with cols[j]:
                    with st.container(border=True):
                        c_img, c_data = st.columns([1, 2])
                        with c_img:
                            icono_bov = "🐂" if es_toro else "🐄"
                            st.markdown(f"<div style='font-size: 60px; text-align: center; padding: 10px;'>{icono_bov}</div>", unsafe_allow_html=True)
                            st.markdown(f"<center><span class='chip-badge {color_badge}'>{u['estado_vigencia']}</span></center>", unsafe_allow_html=True)
                        with c_data:
                            st.markdown(f"#### {u['nombre_animal']}")
                            st.markdown(f"**Arete SINIGA:** `{u['arete_siniga']}`")
                            st.markdown(f"**Raza:** {u['raza']} · **Categoría:** {u['categoria']}")
                            st.markdown(f"**Edad:** {u['edad_meses']} meses · **Peso:** {u['peso_kg']} kg")
                            st.markdown(f"**Rancho:** {u['nombre_rancho']} ({u['municipio']})")
                            st.markdown(f"**Potrero Asignado:** {u.get('nombre_potrero', 'Sin Asignar')}")
                        
                        st.markdown("---")
                        c_hw1, c_hw2, c_hw3 = st.columns(3)
                        c_hw1.metric("Hardware", u['device_id'])
                        c_hw2.metric("Batería", f"{u['bateria_pct']}%")
                        c_hw3.metric("Señal LoRa", f"{u['rssi_dbm']} dBm")

# ==============================================================================
# MÓDULO 3: HISTORIAL DE RECORRIDOS (RF-08)
# ==============================================================================
elif opcion_menu == "📈 Historial de Recorridos":
    st.markdown("### 📈 Historial y Trazado de Trayectorias de Pastoreo")
    st.markdown("Analiza los desplazamientos para prevención de extravío, detección de áreas de sobrepastoreo o alerta de abigeato.")

    ubicaciones = obtener_ultimas_ubicaciones(rancho_seleccionado)
    opciones_animal = {f"{u['nombre_animal']} ({u['arete_siniga']}) - {u['raza']}": u['animal_id'] for u in ubicaciones}
    
    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1:
        seleccionado_str = st.selectbox("Seleccione el ejemplar:", list(opciones_animal.keys()))
        animal_id_sel = opciones_animal[seleccionado_str]
    with col_sel2:
        num_puntos = st.slider("Puntos a reconstruir:", 5, 100, 25)

    historial = obtener_historial_animal(animal_id_sel, limite=num_puntos)

    if historial:
        coords = [[p["lat"], p["lon"]] for p in historial]
        ultimo_punto = historial[-1]

        m_hist = folium.Map(location=[ultimo_punto["lat"], ultimo_punto["lon"]], zoom_start=15)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satélite').add_to(m_hist)
        folium.TileLayer('OpenStreetMap', name='Calles').add_to(m_hist)

        # Polilínea del recorrido
        folium.PolyLine(
            coords,
            color="#1b4332",
            weight=4,
            opacity=0.85,
            tooltip=f"Ruta de pastoreo ({len(coords)} lecturas)"
        ).add_to(m_hist)

        # Marcar puntos
        for idx, pt in enumerate(historial):
            es_final = (idx == len(historial) - 1)
            folium.CircleMarker(
                location=[pt["lat"], pt["lon"]],
                radius=7 if es_final else 5,
                color="red" if es_final else "#2d6a4f",
                fill=True,
                fill_color="yellow" if es_final else "#52b788",
                fill_opacity=0.9,
                popup=f"Punto #{idx+1}<br>Hora: {pt['fecha_captura']}<br>Velocidad: {pt['velocidad_kmh']} km/h<br>Altitud: {pt['altitud_m']} m"
            ).add_to(m_hist)

        folium.LayerControl().add_to(m_hist)
        st_folium(m_hist, width="100%", height=450)

        # Gráfico de perfil de altitud y velocidad en pastoreo
        st.subheader("📊 Perfil de Desplazamiento y Altitud")
        df_hist = pd.DataFrame(historial)
        
        c_g1, c_g2 = st.columns(2)
        with c_g1:
            st.markdown("**Velocidad Estimada de Caminata (km/h)**")
            st.line_chart(df_hist.set_index("fecha_captura")["velocidad_kmh"])
        with c_g2:
            st.markdown("**Altitud Topográfica (msnm)**")
            st.line_chart(df_hist.set_index("fecha_captura")["altitud_m"])
    else:
        st.warning("No hay suficientes puntos históricos registrados para este ejemplar.")

# ==============================================================================
# MÓDULO 4: CENTRO DE ALERTAS
# ==============================================================================
elif opcion_menu == "🚨 Centro de Alertas":
    st.markdown("### 🚨 Centro de Alertas y Eventos Operativos")
    st.markdown("Incidentes de batería baja, pérdida de comunicación y registro de acciones correctivas.")

    solo_pend = st.checkbox("Mostrar únicamente alertas pendientes de atención", value=True)
    alertas = obtener_alertas(solo_pendientes=solo_pend)

    if alertas:
        for al in alertas:
            nivel_color = "red" if al["nivel"] == "critical" else "orange"
            with st.expander(f"⚠️ [{al['nivel'].upper()}] - {al['tipo']} | Bovino: {al.get('nombre_animal', 'Sin asignar')} ({al['created_at']})", expanded=(al['atendida'] == 0)):
                st.write(f"**Descripción del suceso:** {al['descripcion']}")
                st.write(f"**Dispositivo LoRa:** `{al['device_id']}`")
                
                if al['atendida'] == 1:
                    st.success(f"✅ Atendida por **{al['atendida_por']}** en {al['fecha_atencion']}. Observaciones: {al['notas_atencion']}")
                else:
                    st.warning("Estado: PENDIENTE DE ATENCIÓN EN CAMPO")
                    with st.form(key=f"form_alerta_{al['id']}"):
                        nombre_operador = st.text_input("Operador que atiende:", value="Ing. Iván Rodríguez")
                        notas = st.text_area("Acción correctiva realizada:", placeholder="Ej: Se localizó al animal en el potrero 2. Se procedió a sustituir la batería del collar Heltec.")
                        if st.form_submit_button("✅ Reconocer y Marcar como Atendida"):
                            atender_alerta(al['id'], nombre_operador, notas)
                            st.success("Alerta registrada como atendida.")
                            st.rerun()
    else:
        st.success("🎉 No hay incidentes activos en este momento. El hato opera con normalidad.")

# ==============================================================================
# MÓDULO 5: CONEXIÓN DE HARDWARE REAL (ESPECIAL)
# ==============================================================================
elif opcion_menu == "🔌 Conexión de Hardware Real":
    st.markdown("### 🔌 Enlace y Conexión de Dispositivos Reales (Nodos Físicos)")
    st.markdown("Configura y conecta los microcontroladores **Heltec LoRa ESP32 v2** reales ya sea por **Broker MQTT** o directamente por **Cable USB / Puerto Serie**.")

    tab_mqtt, tab_serial, tab_alta = st.tabs([
        "📡 Enlace MQTT en Vivo (Gateway LoRa)",
        "🔌 Conexión Directa USB (Puerto Serie COM)",
        "🏷️ Pareo y Alta de Nuevo Collar"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: ENLACE MQTT
    # --------------------------------------------------------------------------
    with tab_mqtt:
        st.subheader("Configuración del Broker MQTT")
        st.info("El Gateway Heltec LoRa ESP32 v2 instalado en el rancho publica las lecturas recibidas hacia este broker.")

        c_m1, c_m2, c_m3 = st.columns(3)
        host_mqtt = c_m1.text_input("Host del Broker:", value="localhost")
        port_mqtt = c_m2.number_input("Puerto:", value=1883)
        topico_mqtt = c_m3.text_input("Tópico de Telemetría:", value="bovinos/+/telemetria")

        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            if st.button("🧪 Probar Conexión con Broker MQTT"):
                try:
                    import paho.mqtt.client as test_mqtt
                    cli = test_mqtt.Client(test_mqtt.CallbackAPIVersion.VERSION2 if hasattr(test_mqtt, 'CallbackAPIVersion') else None)
                    cli.connect(host_mqtt, int(port_mqtt), 5)
                    st.success(f"✅ ¡Conexión exitosa con el broker MQTT en {host_mqtt}:{port_mqtt}!")
                    cli.disconnect()
                except Exception as e:
                    st.error(f"❌ No se pudo conectar al broker MQTT: {e}. (Asegúrate de que Mosquitto o Docker estén activos).")

        st.markdown("---")
        st.subheader("Inyector de Paquete de Prueba (Simula Trama Cruda de Gateway Real)")
        with st.form("form_test_packet"):
            col_t1, col_t2 = st.columns(2)
            t_dev = col_t1.selectbox("Collar emisor:", ["HELTEC-COLLAR-01", "HELTEC-COLLAR-02", "HELTEC-COLLAR-03", "HELTEC-COLLAR-04", "HELTEC-COLLAR-05", "HELTEC-COLLAR-06"])
            t_bat = col_t2.slider("Batería LiPo %:", 5, 100, 92)
            
            c_p1, c_p2 = st.columns(2)
            t_lat = c_p1.number_input("Latitud GPS real:", value=20.37560, format="%.6f")
            t_lon = c_p2.number_input("Longitud GPS real:", value=-99.65450, format="%.6f")

            if st.form_submit_button("📡 Publicar Lectura a Base de Datos"):
                payload_real = {
                    "device_id": t_dev,
                    "lat": t_lat,
                    "lon": t_lon,
                    "altitud_m": 2105.0,
                    "velocidad_kmh": 1.2,
                    "bateria_pct": t_bat,
                    "rssi_dbm": -68,
                    "snr_db": 9.5,
                    "satelites": 9,
                    "fix_valido": True,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                guardar_lectura(payload_real, fuente="lora_mqtt")
                st.success(f"✅ Lectura guardada exitosamente para {t_dev}. ¡Revisa el Dashboard y el Mapa!")

    # --------------------------------------------------------------------------
    # TAB 2: CONEXIÓN DIRECTA POR PUERTO SERIE USB
    # --------------------------------------------------------------------------
    with tab_serial:
        st.subheader("Lectura en Vivo de Tarjeta Heltec por Cable USB")
        st.write("Si conectas la tarjeta Heltec LoRa ESP32 directamente a tu computadora por USB (por ejemplo en el laboratorio de ITESHU), puedes capturar las lecturas sin necesidad de conexión Wi-Fi:")

        if SERIAL_AVAILABLE:
            puertos_disponibles = list(serial.tools.list_ports.comports())
            if puertos_disponibles:
                opciones_puertos = [f"{p.device} - {p.description}" for p in puertos_disponibles]
                puerto_elegido = st.selectbox("Puertos COM detectados:", opciones_puertos)
                com_name = puerto_elegido.split(" - ")[0]
            else:
                st.warning("⚠️ No se detectaron puertos COM USB activos en este momento. Conecta tu Heltec ESP32 por USB y recarga.")
                com_name = "COM3"

            c_s1, c_s2 = st.columns(2)
            baud_rate = c_s1.selectbox("Velocidad de transmisión (Baudrate):", [115200, 9600, 57600], index=0)
            
            st.markdown("""
            **Formato de trama serie esperado del ESP32:**  
            `HELTEC-COLLAR-01,BOV-001,20.37542,-99.65431,2105.0,1.2,95,9,1,142`  
            *(ID_DISPOSITIVO, ID_ANIMAL, LAT, LON, ALT, VEL, BATERIA, SATS, FIX_OK, PKT_NUM)*
            """)

            with st.form("form_captura_serial_manual"):
                st.write("Simulación de lectura capturada del puerto serie:")
                trama_serial_ejemplo = st.text_input("Trama recibida en terminal:", value=f"HELTEC-COLLAR-01,BOV-001,20.37590,-99.65480,2106.0,1.5,92,9,1,105")
                if st.form_submit_button("⚡ Procesar e Inyectar Trama Serie"):
                    try:
                        partes = trama_serial_ejemplo.strip().split(",")
                        if len(partes) >= 4:
                            p_datos = {
                                "device_id": partes[0],
                                "animal_id": partes[1],
                                "lat": float(partes[2]),
                                "lon": float(partes[3]),
                                "altitud_m": float(partes[4]) if len(partes) > 4 else 2105.0,
                                "velocidad_kmh": float(partes[5]) if len(partes) > 5 else 0.0,
                                "bateria_pct": int(partes[6]) if len(partes) > 6 else 100,
                                "satelites": int(partes[7]) if len(partes) > 7 else 8,
                                "fix_valido": True if len(partes) > 8 and partes[8] == "1" else False,
                                "rssi_dbm": -65,
                                "snr_db": 10.0,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            guardar_lectura(p_datos, fuente="serial_usb")
                            st.success(f"✅ ¡Trama serie procesada correctamente para {partes[1]}! Fuente: USB Serial ({com_name}).")
                    except Exception as err:
                        st.error(f"Error procesando trama serie: {err}")
        else:
            st.error("Librería `pyserial` no detectada. Ejecuta `pip install pyserial` para habilitar el lector de puertos COM.")

    # --------------------------------------------------------------------------
    # TAB 3: ALTA Y PAREO DE DISPOSITIVO FÍSICO
    # --------------------------------------------------------------------------
    with tab_alta:
        st.subheader("Alta y Aprovisionamiento de Collar Físico")
        st.write("Registra un nuevo dispositivo que vayas a construir o colocar en un collar de cuero:")

        with st.form("form_alta_dispositivo"):
            c_a1, c_a2 = st.columns(2)
            nuevo_id = c_a1.text_input("Identificador Único del Collar:", value="HELTEC-COLLAR-07")
            tipo_dev = c_a2.selectbox("Tipo de Equipo:", ["collar", "gateway"])

            c_a3, c_a4 = st.columns(2)
            mac_dev = c_a3.text_input("Dirección MAC WiFi/BLE:", value="E0:5A:1B:77:4A:07")
            freq_dev = c_a4.selectbox("Frecuencia LoRa (MHz):", [915.0, 915.5, 916.0], index=0)

            c_a5, c_a6 = st.columns(2)
            sf_dev = c_a5.slider("Spreading Factor (SF):", 7, 12, 7)
            pot_dev = c_a6.slider("Potencia de Transmisión (dBm):", 10, 20, 20)

            ubicaciones_all = obtener_ultimas_ubicaciones(None)
            animales_opc = {"": "Ninguno (Dejar en inventario)"}
            for u in ubicaciones_all:
                animales_opc[u["animal_id"]] = f"{u['nombre_animal']} ({u['arete_siniga']})"
            
            animal_vincular = st.selectbox("Asociar de inmediato al bovino:", options=list(animales_opc.keys()), format_func=lambda x: animales_opc[x])

            if st.form_submit_button("💾 Guardar y Generar Configuración Arduino"):
                registrar_dispositivo_real(nuevo_id, tipo_dev, mac_dev, freq_dev, sf_dev, pot_dev, animal_vincular if animal_vincular else None)
                st.success(f"✅ ¡Dispositivo {nuevo_id} registrado con éxito!")
                
                # Generar snippet C++ para Arduino IDE
                st.markdown("**Código C++ generado para tu `config.h` de Arduino IDE:**")
                st.code(f"""
// Configuración generada automáticamente por la Plataforma IoT
#define DEVICE_ID       "{nuevo_id}"
#define BAND            {int(freq_dev)}E6
#define LORA_SPREADING  {sf_dev}
#define LORA_TX_POWER   {pot_dev}
#define LORA_SYNC_WORD  0x34
""", language="cpp")

# ==============================================================================
# MÓDULO 6: SIMULADOR RÁPIDO DE CAMPO
# ==============================================================================
elif opcion_menu == "⚡ Simulador Rápido de Campo":
    st.markdown("### ⚡ Simulador de Telemetría para Demostración en Clase")
    st.markdown("Genera lecturas y desplazamientos sobre la marcha para demostrar en la presentación cómo la plataforma reacciona en tiempo real.")

    ubicaciones = obtener_ultimas_ubicaciones(None)
    nombres_anim = {f"{u['nombre_animal']} ({u['arete_siniga']}) - {u['estado_vigencia'].upper()}": u for u in ubicaciones}
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sel_str = st.selectbox("Bovino a mover:", list(nombres_anim.keys()))
        bov_sel = nombres_anim[sel_str]
        bov_id = bov_sel["animal_id"]
        dev_id = bov_sel["device_id"]
    with col_s2:
        nueva_bat = st.slider("Porcentaje de Batería del Collar (%):", 5, 100, 92)

    col_pos1, col_pos2 = st.columns(2)
    with col_pos1:
        delta_lat = random.uniform(-0.0012, 0.0012)
        nueva_lat = st.number_input("Nueva Latitud GPS:", value=bov_sel["lat"] + delta_lat, format="%.6f")
    with col_pos2:
        delta_lon = random.uniform(-0.0012, 0.0012)
        nueva_lon = st.number_input("Nueva Longitud GPS:", value=bov_sel["lon"] + delta_lon, format="%.6f")

    if st.button("🚀 Enviar Telemetría Ahora (Actualizar Mapa)"):
        p_sim = {
            "device_id": dev_id,
            "animal_id": bov_id,
            "lat": nueva_lat,
            "lon": nueva_lon,
            "altitud_m": round(bov_sel["altitud_m"] + random.uniform(-1, 2), 1),
            "velocidad_kmh": round(random.uniform(0.5, 3.2), 1),
            "bateria_pct": nueva_bat,
            "rssi_dbm": random.randint(-80, -62),
            "snr_db": round(random.uniform(7.5, 10.5), 1),
            "satelites": random.randint(8, 12),
            "fix_valido": True,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        guardar_lectura(p_sim, fuente="simulacion")
        st.success(f"✅ ¡Telemetría inyectada para {bov_sel['nombre_animal']}! Ahora tiene estado ACTUALIZADA (🟢) y su posición en el mapa fue refrescada.")
