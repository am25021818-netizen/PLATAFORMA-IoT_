import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# ----------------------------------------------------------------------
# Canvas con Numeración de Páginas y Encabezados Profesionales
# ----------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Omitir encabezado y pie en la portada
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1b4332"))

        # Encabezado
        self.drawString(54, 750, "ITESHU · MAESTRÍA EN MECATRÓNICA · INTERNET DE LAS COSAS")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawRightString(558, 750, "MVP: Monitoreo GPS de Bovinos (Valle del Mezquital)")
        
        self.setStrokeColor(colors.HexColor("#2d6a4f"))
        self.setLineWidth(0.75)
        self.line(54, 744, 558, 744)

        # Pie de página
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))
        self.drawString(54, 32, "Estudiante: Ing. Iván Rodríguez Hernández · Docente: DTI. Carlos Arturo Espinoza Galicia")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 32, page_str)

        self.restoreState()

# ----------------------------------------------------------------------
# Generador Principal del Documento
# ----------------------------------------------------------------------
def crear_documento_integral(ruta_salida):
    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Paleta de colores
    C_PRIMARY = colors.HexColor("#1b4332")
    C_SECONDARY = colors.HexColor("#2d6a4f")
    C_ACCENT = colors.HexColor("#52b788")
    C_DARK = colors.HexColor("#1f2421")
    C_BG_LIGHT = colors.HexColor("#f8f9fa")
    C_BORDER = colors.HexColor("#d8f3dc")

    # Definición de estilos tipográficos
    title_cover = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=C_PRIMARY,
        alignment=1, # Centro
        spaceAfter=15
    )

    sub_cover = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=C_SECONDARY,
        alignment=1,
        spaceAfter=25
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=C_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=C_SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=C_DARK,
        alignment=4, # Justificado
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=C_DARK,
        leftIndent=15,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#2b2d42")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=C_DARK
    )

    story = []

    # ==================================================================
    # PORTADA INSTITUCIONAL
    # ==================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("INSTITUTO TECNOLÓGICO SUPERIOR DE HUICHAPAN", ParagraphStyle(
        'InstHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=C_SECONDARY, alignment=1
    )))
    story.append(Paragraph("DIVISIÓN DE ESTUDIOS DE POSGRADO E INVESTIGACIÓN<br/>MAESTRÍA EN INGENIERÍA MECATRÓNICA", ParagraphStyle(
        'InstSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=colors.HexColor("#495057"), alignment=1
    )))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="80%", thickness=2, color=C_PRIMARY, spaceAfter=30, spaceBefore=10))

    story.append(Paragraph("ACTIVIDAD FINAL: CREA TU PLATAFORMA IoT USANDO PROGRAMACIÓN AGÉNTICA Y OPENCODE", ParagraphStyle(
        'ActTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor("#2d6a4f"), alignment=1
    )))
    story.append(Spacer(1, 15))

    story.append(Paragraph("DOCUMENTO INTEGRAL DE ARQUITECTURA, ESPECIFICACIÓN, DESARROLLO Y DESPLIEGUE DEL MVP", title_cover))
    story.append(Paragraph("Plataforma de Monitoreo GPS de Bovinos en Tiempo Real<br/>para la Zona del Valle del Mezquital del Estado de Hidalgo", sub_cover))

    story.append(Spacer(1, 40))

    # Ficha técnica de autores
    datos_portada = [
        [Paragraph("<b>ASIGNATURA:</b>", table_cell_style), Paragraph("Internet de las Cosas (IoT)", table_cell_style)],
        [Paragraph("<b>DOCENTE TITULAR:</b>", table_cell_style), Paragraph("DTI. Carlos Arturo Espinoza Galicia", table_cell_style)],
        [Paragraph("<b>ESTUDIANTE / AUTOR:</b>", table_cell_style), Paragraph("Ing. Iván Rodríguez Hernández", table_cell_style)],
        [Paragraph("<b>PROYECTO DE TESIS:</b>", table_cell_style), Paragraph("Sistema de Monitoreo Pecuario con Nodos LoRa/GPS y Plataforma Cloud", table_cell_style)],
        [Paragraph("<b>STACK TECNOLÓGICO:</b>", table_cell_style), Paragraph("ESP32 (Heltec LoRa v2) · MQTT · Python (Streamlit) · Docker", table_cell_style)],
        [Paragraph("<b>METODOLOGÍA:</b>", table_cell_style), Paragraph("OpenCode + OpenSpec (Spec-Driven Development) + Git", table_cell_style)],
        [Paragraph("<b>FECHA DE ENTREGA:</b>", table_cell_style), Paragraph("Noviembre de 2026", table_cell_style)]
    ]
    t_portada = Table(datos_portada, colWidths=[150, 300])
    t_portada.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, C_SECONDARY),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ced4da")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_portada)
    story.append(PageBreak())

    # ==================================================================
    # 1. IDENTIFICACIÓN Y DESCRIPCIÓN DE LA PLATAFORMA
    # ==================================================================
    story.append(Paragraph("1. Identificación y Descripción de la Plataforma", h1_style))
    story.append(Paragraph(
        "<b>Nombre formal de la solución:</b> Plataforma Sistema De Monitoreo IoT Para Bovinos en Tiempo Real Para la Zona Del Valle Del Mezquital Del Estado de Hidalgo.<br/>"
        "La plataforma permite consultar la ubicación geográfica más reciente y la trazabilidad histórica de los ejemplares bovinos que porten un dispositivo de rastreo GPS autónomo. Su finalidad principal consiste en apoyar al ganadero, productor o encargado de rancho en la supervisión continua del ganado en pastoreo extensivo, facilitar su pronta localización y mitigar significativamente los riesgos derivados de extravío, dispersión en terreno agreste o abigeato (robo de ganado).",
        body_style
    ))
    story.append(Paragraph(
        "El sistema combina hardware embebido instalado directamente sobre los animales (Collar de cuero con carcasa resistente IP67), comunicación inalámbrica de largo alcance y bajo consumo mediante radiofrecuencia <b>LoRa (Banda ISM 915 MHz para México)</b>, una estación base retransmisora (Gateway), intermediación de mensajería ligera mediante el protocolo <b>MQTT</b> con broker Mosquitto, y una plataforma web centralizada construida con <b>Python y Streamlit</b>, totalmente contenerizada bajo <b>Docker</b> y publicada bajo un subdominio público en Internet.",
        body_style
    ))

    story.append(Paragraph("1.1 Problema u Oportunidad que Atiende", h2_style))
    story.append(Paragraph(
        "En la región geográfica del Valle del Mezquital (municipios como Huichapan, Nopala, Tecozautla, Alfajayucan e Ixmiquilpan), las explotaciones ganaderas operan primordialmente bajo esquemas de pastoreo semi-extensivo en potreros con relieve irregular, vegetación densa (matorral espinoso, mezquites y nopales) y escasa o nula cobertura celular convencional. Tradicionalmente, la supervisión del hato depende de recorridos presenciales diarios a caballo o pie, consumiendo horas/hombre críticas e imposibilitando la detección oportuna de un animal rezagado, lesionado o sustraído.",
        body_style
    ))
    story.append(Paragraph(
        "La plataforma atiende esta problemática centralizando la posición geográfica en tiempo casi real mediante telemetría LoRa, la cual ofrece enlaces de varios kilómetros sin costo por servicio de telefonía celular, permitiendo al productor consultar el estado del hato desde cualquier navegador web o dispositivo móvil.",
        body_style
    ))

    # ==================================================================
    # 2. ALCANCE: COMPARATIVA ENTRE MVP Y PLATAFORMA IDEAL
    # ==================================================================
    story.append(Paragraph("2. Alcance: MVP vs. Plataforma Ideal", h1_style))
    story.append(Paragraph(
        "De conformidad con los lineamientos de diseño de software e ingeniería de requerimientos, se delimitó con exactitud el alcance del Producto Mínimo Viable (MVP) frente a la visión de la plataforma ideal futura:",
        body_style
    ))

    tabla_alcance_data = [
        [Paragraph("Dimensión", table_header_style), Paragraph("Producto Mínimo Viable (MVP Implementado)", table_header_style), Paragraph("Plataforma Ideal (Evolución Futura)", table_header_style)],
        [
            Paragraph("<b>Gestión y Catálogo</b>", table_cell_style),
            Paragraph("Registro de ranchos, usuarios, bovinos y dispositivos con asociación unívoca de collar a ejemplar.", table_cell_style),
            Paragraph("Múltiples ranchos federados, árboles genealógicos, control reproductivo y trazabilidad comercial.", table_cell_style)
        ],
        [
            Paragraph("<b>Comunicaciones y Red</b>", table_cell_style),
            Paragraph("Enlace punto a punto LoRa 915 MHz (Collar a Gateway) y retransmisión por Wi-Fi/Ethernet a broker MQTT.", table_cell_style),
            Paragraph("Red LoRaWAN mallada con gateways redundantes, fallback automático a celular 4G y buffer offline en gateway.", table_cell_style)
        ],
        [
            Paragraph("<b>Geolocalización y Mapas</b>", table_cell_style),
            Paragraph("Visualización en mapa satelital de la última coordenada, semáforo de vigencia y trazado de historial de recorridos.", table_cell_style),
            Paragraph("Geocercas poligonales dinámicas por potrero con alertas automáticas de salida y predicción de rutas por IA.", table_cell_style)
        ],
        [
            Paragraph("<b>Alertas y Eventos</b>", table_cell_style),
            Paragraph("Alertas en dashboard por falta de reporte (desconexión), batería baja (<20%) y módulo de atención con bitácora.", table_cell_style),
            Paragraph("Notificaciones push por WhatsApp, SMS y correo electrónico; sirenas acústicas en rancho.", table_cell_style)
        ],
        [
            Paragraph("<b>Sensores Físicos</b>", table_cell_style),
            Paragraph("Concentración exclusiva en coordenadas GPS, altitud, velocidad, satélites y nivel de batería LiPo.", table_cell_style),
            Paragraph("Medición de temperatura ruminal, frecuencia cardíaca, acelerometría para celo y análisis de rumiación.", table_cell_style)
        ]
    ]
    t_alcance = Table(tabla_alcance_data, colWidths=[100, 200, 204])
    t_alcance.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_alcance)
    story.append(Spacer(1, 10))

    # ==================================================================
    # 3. ROLES DE USUARIO Y MATRIZ DE PERMISOS
    # ==================================================================
    story.append(Paragraph("3. Tipos de Usuario y Matriz de Permisos", h1_style))
    story.append(Paragraph(
        "La plataforma implementa un esquema de control de acceso basado en roles (RBAC) para garantizar la integridad operativa:",
        body_style
    ))

    usuarios_data = [
        [Paragraph("Rol", table_header_style), Paragraph("Descripción y Responsabilidad", table_header_style), Paragraph("Acciones Autorizadas", table_header_style)],
        [
            Paragraph("<b>Administrador</b>", table_cell_style),
            Paragraph("Responsable global del sistema, infraestructura y cuentas de acceso.", table_cell_style),
            Paragraph("Crear/editar usuarios, registrar ranchos, dar de alta dispositivos y asociar collares a animales. Acceso total a configuración.", table_cell_style)
        ],
        [
            Paragraph("<b>Propietario / Ganadero</b>", table_cell_style),
            Paragraph("Dueño de la unidad pecuaria y tomador de decisiones operativas.", table_cell_style),
            Paragraph("Consultar el tablero general, mapa del hato, historial de trayectorias, estado de baterías y revisar incidentes.", table_cell_style)
        ],
        [
            Paragraph("<b>Operador de Campo</b>", table_cell_style),
            Paragraph("Encargado o vaquero asignado a la supervisión diaria en potrero.", table_cell_style),
            Paragraph("Localizar animales en tiempo real, visualizar alertas y registrar notas de atención cuando acude al potrero a verificar un ejemplar.", table_cell_style)
        ],
        [
            Paragraph("<b>Técnico de Soporte</b>", table_cell_style),
            Paragraph("Especialista en mantenimiento de hardware LoRa y electrónica.", table_cell_style),
            Paragraph("Supervisar RSSI, SNR, nivel de voltaje de batería, estado del gateway y bitácora técnica de paquetes recibidos.", table_cell_style)
        ]
    ]
    t_usuarios = Table(usuarios_data, colWidths=[90, 180, 234])
    t_usuarios.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_SECONDARY),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_usuarios)
    story.append(PageBreak())

    # ==================================================================
    # 4. ARQUITECTURA DE HARDWARE Y COMUNICACIÓN DE DOS TRAMOS
    # ==================================================================
    story.append(Paragraph("4. Arquitectura de Hardware y Comunicación de Dos Tramos", h1_style))
    story.append(Paragraph(
        "Para superar la limitante de conectividad rural, el sistema se diseñó bajo una arquitectura desacoplada de dos tramos:",
        body_style
    ))

    story.append(Paragraph("<b>Tramo 1: Dispositivo Collar en Campo a Estación Base (Radiofrecuencia LoRa)</b>", h2_style))
    story.append(Paragraph(
        "• <b>Microcontrolador del Collar:</b> Tarjeta de desarrollo Heltec LoRa ESP32 v2 (Microprocesador Xtensa dual-core a 240 MHz con transceptor SX1276 integrado).<br/>"
        "• <b>Sensor de Posicionamiento:</b> Módulo GPS NMEA (u-blox NEO-6M / M8N) conectado por puerto serie UART (HardwareSerial1, RX: GPIO 22, TX: GPIO 23 a 9600 baudios).<br/>"
        "• <b>Parámetros de Modulación LoRa:</b> Frecuencia central de 915.0 MHz (Banda ISM autorizada en México por el IFT), Factor de Dispersión SF=7, Ancho de Banda BW=125 kHz, Codificación CR=4/5, Potencia de transmisión +20 dBm (PA_BOOST) y SyncWord privada 0x34.<br/>"
        "• <b>Mecánica y Envolvente:</b> Carcasa hermética ABS con empaque de silicón grado IP67 para protección contra polvo, lluvia, rocío e impactos, fijada sólidamente mediante un collar de cuero de alta resistencia al cuello del bovino.<br/>"
        "• <b>Gestión Energética:</b> Batería LiPo de 3.7V con circuito de monitoreo por divisor de voltaje resistivo conectado al canal ADC del ESP32.",
        body_style
    ))

    story.append(Paragraph("<b>Tramo 2: Estación Base (Gateway) a Servidor en la Nube (Wi-Fi + MQTT)</b>", h2_style))
    story.append(Paragraph(
        "• <b>Hardware Concentrador:</b> Segunda tarjeta Heltec LoRa ESP32 v2 configurada en modo receptor continuo (escucha de paquetes en 915 MHz).<br/>"
        "• <b>Ubicación:</b> Instalado en el casco del rancho o torre de comunicación con alimentación permanente y antena omnidireccional con ganancia de +5 dBi.<br/>"
        "• <b>Conectividad IP:</b> Enlace Wi-Fi 802.11 b/g/n conectado al módem de la unidad ganadera con salida a Internet.<br/>"
        "• <b>Puente de Protocolos:</b> Desempaqueta la trama binaria LoRa, extrae los valores de telemetría y calidad de señal (RSSI y SNR), genera un payload JSON estandarizado y lo publica hacia el broker <b>Mosquitto</b> en el tópico <code>bovinos/{device_id}/telemetria</code> con calidad de servicio QoS 1.",
        body_style
    ))

    story.append(Paragraph("<b>Reglas de Vigencia Temporal y Semáforo del Hato (RF-07)</b>", h2_style))
    story.append(Paragraph(
        "La plataforma evalúa la antigüedad de cada coordenada respecto a la marca de tiempo actual del servidor, asignando uno de tres estados visuales rigurosos:<br/>"
        "• <b>🟢 Actualizada (Verde):</b> Reporte recibido en un intervalo menor a 10 minutos (600 segundos). El animal está en tiempo y forma.<br/>"
        "• <b>🟡 Retrasada (Amarillo):</b> Transcurrieron entre 10 y 30 minutos sin recibir paquetes. Indica posible sombra de relieve o retardo de lectura.<br/>"
        "• <b>🔴 Sin Comunicación (Rojo):</b> Transcurrieron más de 30 minutos (1800 segundos) sin enlace. Se genera una alerta operativa automática para revisión presencial.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # ==================================================================
    # 5. METODOLOGÍA AGÉNTICA: OPENCODE, OPENSPEC Y REGLAS AGENTS.md
    # ==================================================================
    story.append(Paragraph("5. Metodología de Desarrollo Asistido por IA: OpenCode y OpenSpec", h1_style))
    story.append(Paragraph(
        "En cumplimiento de los requerimientos metodológicos del docente (DTI. Carlos Arturo Espinoza Galicia), se implementó el paradigma <b>Spec-Driven Development (Desarrollo Guiado por Especificaciones)</b> mediante la combinación de OpenSpec, reglas en AGENTS.md y Git.",
        body_style
    ))

    openspec_items = [
        [Paragraph("Herramienta / Archivo", table_header_style), Paragraph("Función Mecatrónica y Rol en el Proyecto", table_header_style)],
        [
            Paragraph("<b>AGENTS.md (Raíz)</b>", table_cell_style),
            Paragraph("Reglamento del taller: Reglas inviolables para agentes de IA. Establece el uso estricto de millis() (cero delay en loop), interbloqueos fail-safe si el GPS no tiene fix válido y contrato de tópicos MQTT.", table_cell_style)
        ],
        [
            Paragraph("<b>openspec/specs/contrato-mqtt/spec.md</b>", table_cell_style),
            Paragraph("Fuente de verdad del contrato de datos. Define los escenarios BDD (Given-When-Then) para telemetría, estados Last Will and Testament y comandos hacia dispositivos.", table_cell_style)
        ],
        [
            Paragraph("<b>openspec/changes/mvp-monitoreo-bovinos/</b>", table_cell_style),
            Paragraph("Expediente técnico de ingeniería que contiene: proposal.md (propuesta de valor), design.md (diagramas de flujo y arquitectura), tasks.md (lista de verificación de ingeniería) y specs/telemetria/spec.md.", table_cell_style)
        ],
        [
            Paragraph("<b>openspec validate --all</b>", table_cell_style),
            Paragraph("Comando CLI ejecutado para certificar que todas las especificaciones y deltas cumplen la gramática técnica sin errores.", table_cell_style)
        ],
        [
            Paragraph("<b>Git (Commits Atómicos)</b>", table_cell_style),
            Paragraph("Trazabilidad total con mensajes de commit estandarizados en español (feat:, fix:, docs:, test:) y protección de base de datos en .gitignore.", table_cell_style)
        ]
    ]
    t_openspec = Table(openspec_items, colWidths=[160, 344])
    t_openspec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_openspec)
    story.append(PageBreak())

    # ==================================================================
    # 6. ESTRUCTURA DE DATOS Y PERSISTENCIA (SQLITE)
    # ==================================================================
    story.append(Paragraph("6. Estructura del Modelo de Datos Relacional", h1_style))
    story.append(Paragraph(
        "Se implementó un esquema relacional normalizado persistido en SQLite (<code>/app/data/datos_iot.db</code> dentro del contenedor Docker), asegurando integridad referencial e indexación temporal:",
        body_style
    ))

    tablas_sql = [
        [Paragraph("Tabla", table_header_style), Paragraph("Campos Principales", table_header_style), Paragraph("Propósito Operativo", table_header_style)],
        [
            Paragraph("<b>ranchos</b>", table_cell_style),
            Paragraph("id (PK), nombre, ubicacion, municipio, estado_geografico, activo, created_at", table_cell_style),
            Paragraph("Almacena la unidad productiva (Rancho San Isidro, Huichapan, Hgo).", table_cell_style)
        ],
        [
            Paragraph("<b>usuarios</b>", table_cell_style),
            Paragraph("id (PK), username, password, nombre_completo, correo, rol, rancho_id (FK), activo", table_cell_style),
            Paragraph("Control de credenciales y roles (admin, ganadero, tecnico).", table_cell_style)
        ],
        [
            Paragraph("<b>dispositivos</b>", table_cell_style),
            Paragraph("id (PK: HELTEC-COLLAR-01), tipo, modelo, animal_id, bateria_pct, rssi_dbm, snr_db, estado_operacion, ultima_comunicacion", table_cell_style),
            Paragraph("Inventario de collares y gateways con telemetría de salud de hardware.", table_cell_style)
        ],
        [
            Paragraph("<b>animales</b>", table_cell_style),
            Paragraph("id (PK: BOV-001), arete_siniga, nombre, categoria, rancho_id (FK), device_id (FK Unique), estado", table_cell_style),
            Paragraph("Ficha de identidad pecuaria (El Barón, La Paloma, El Pinto) y vínculo 1 a 1 a collar.", table_cell_style)
        ],
        [
            Paragraph("<b>lecturas_gps</b>", table_cell_style),
            Paragraph("id (PK AI), animal_id (FK), device_id (FK), lat, lon, altitud_m, velocidad_kmh, bateria_pct, rssi_dbm, snr_db, satelites, fix_valido, fecha_captura, fecha_recepcion", table_cell_style),
            Paragraph("Serie de tiempo de coordenadas geográficas. Permite la reconstrucción de trayectorias.", table_cell_style)
        ],
        [
            Paragraph("<b>alertas</b>", table_cell_style),
            Paragraph("id (PK AI), tipo, animal_id (FK), device_id (FK), descripcion, nivel, lat, lon, atendida, atendida_por, notas_atencion, fecha_atencion, created_at", table_cell_style),
            Paragraph("Bitácora de incidentes (batería baja, desconexión) con flujo de reconocimiento.", table_cell_style)
        ]
    ]
    t_tablas = Table(tablas_sql, colWidths=[90, 230, 184])
    t_tablas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_SECONDARY),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_tablas)
    story.append(Spacer(1, 10))

    # ==================================================================
    # 7. MATRIZ DE REQUERIMIENTOS FUNCIONALES (RF) Y NO FUNCIONALES (RNF)
    # ==================================================================
    story.append(Paragraph("7. Requerimientos Funcionales y Criterios de Aceptación", h1_style))
    story.append(Paragraph(
        "Mapeo de requerimientos estipulados en el documento de especificación entregado el 13 de noviembre de 2026:",
        body_style
    ))

    rf_data = [
        [Paragraph("ID", table_header_style), Paragraph("Requerimiento Funcional", table_header_style), Paragraph("Criterio de Aceptación / Estado en el MVP", table_header_style)],
        [
            Paragraph("<b>RF-01</b>", table_cell_style),
            Paragraph("Acceso de usuarios por credenciales.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Autenticación y roles en base de datos; panel accesible.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-02</b>", table_cell_style),
            Paragraph("Restricción de vistas por rol.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Administrador, Ganadero y Técnico con permisos delimitados.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-03</b>", table_cell_style),
            Paragraph("Registro de animales y arete SINIGA.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Inventario con clave única, especie, raza y potrero.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-04</b>", table_cell_style),
            Paragraph("Asociación collar-bovino.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Restricción UNIQUE en SQLite impide collares duplicados.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-05</b>", table_cell_style),
            Paragraph("Recepción y parseo de telemetría GPS.", table_cell_style),
            Paragraph("<b>Cumplido:</b> <code>ingesta_mqtt.py</code> valida JSON y descarta datos truncados.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-06</b>", table_cell_style),
            Paragraph("Visualización cartográfica en tiempo real.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Mapa interactivo Folium con capas OSM y Satélite Esri.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-07</b>", table_cell_style),
            Paragraph("Semáforo de vigencia del dato.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Verde (<10 min), Amarillo (10-30 min) y Rojo (>30 min).", table_cell_style)
        ],
        [
            Paragraph("<b>RF-08</b>", table_cell_style),
            Paragraph("Historial de trayectorias.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Módulo de historial con polilíneas sobre el mapa y selector de fechas.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-09</b>", table_cell_style),
            Paragraph("Estado de salud del hardware.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Visualización de batería restante (%), RSSI y SNR de LoRa.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-10</b>", table_cell_style),
            Paragraph("Alertas automáticas de desconexión y batería.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Inserción en tabla <code>alertas</code> cuando bat < 20% o tiempo > 30m.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-11</b>", table_cell_style),
            Paragraph("Atención y reconocimiento de alertas.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Formulario interactivo que registra operador, fecha y acción tomada.", table_cell_style)
        ],
        [
            Paragraph("<b>RF-13</b>", table_cell_style),
            Paragraph("Tarjetas resumen en Dashboard.", table_cell_style),
            Paragraph("<b>Cumplido:</b> Contadores reactivos de animales, collares, alertas y semáforo.", table_cell_style)
        ]
    ]
    t_rf = Table(rf_data, colWidths=[45, 195, 264])
    t_rf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ced4da")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_rf)
    story.append(PageBreak())

    # ==================================================================
    # 8. CONTENERIZACIÓN CON DOCKER Y ORQUESTACIÓN
    # ==================================================================
    story.append(Paragraph("8. Contenerización con Docker y Docker Compose", h1_style))
    story.append(Paragraph(
        "Para garantizar reproducibilidad absoluta en servidores locales, VPS o laboratorios escolares, la plataforma se empaquetó en una arquitectura multicontenedor orquestada:",
        body_style
    ))

    docker_code = """# plataforma/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
RUN mkdir -p /app/data
ENV STREAMLIT_SERVER_PORT=8501 STREAMLIT_SERVER_ADDRESS=0.0.0.0
EXPOSE 8501
CMD sh -c "python src/ingesta_mqtt.py & streamlit run src/dashboard.py"
"""
    story.append(Paragraph(docker_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))
    story.append(Spacer(1, 8))

    compose_code = """# plataforma/docker-compose.yml
services:
  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: iteshu_mosquitto_broker
    restart: unless-stopped
    ports: ["1883:1883", "9001:9001"]
    command: mosquitto -c /mosquitto-no-auth.conf
  plataforma-iot:
    build: .
    container_name: iteshu_plataforma_iot
    restart: unless-stopped
    depends_on: [mosquitto]
    ports: ["8501:8501"]
    environment:
      - MQTT_BROKER_HOST=mosquitto
      - MQTT_BROKER_PORT=1883
      - DB_PATH=/app/data/datos_iot.db
    volumes:
      - ./data:/app/data
"""
    story.append(Paragraph(compose_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))
    story.append(Spacer(1, 10))

    # ==================================================================
    # 9. GUÍA DE PUBLICACIÓN EN SERVIDOR WEB CON SUBDOMINIO
    # ==================================================================
    story.append(Paragraph("9. Procedimiento de Publicación Web con Subdominio", h1_style))
    story.append(Paragraph(
        "Para satisfacer el criterio evaluativo: <i>'debe ser funcional y estar publicada en tu servidor web con un subdominio referente a tu proyecto'</i>, se establecieron dos vías:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Opción Recomendada: Cloudflare Tunnel (100% Gratuito y Seguro)</b><br/>"
        "Permite exponer el contenedor local o de servidor sin necesidad de abrir puertos en el módem del rancho ni exponer la IP pública física:<br/>"
        "1. Instalar el conector de Cloudflare o ejecutarlo en Docker:<br/>"
        "<code>docker run -d --name cloudflared cloudflare/cloudflared tunnel --no-autoupdate run --token TU_TOKEN</code><br/>"
        "2. Asignar el subdominio en el panel de Cloudflare Zero Trust: <code>bovinos.tudominio.com</code> apuntando a <code>http://plataforma-iot:8501</code>.<br/>"
        "3. La plataforma queda disponible bajo HTTPS con certificado SSL firmado automáticamente.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Opción Express para Evaluación: Cloudflare Quick Tunnels</b><br/>"
        "Ejecutando en la terminal: <code>cloudflared tunnel --url http://localhost:8501</code> se obtiene al instante un subdominio público cifrado gratuito (ejemplo: <code>https://bovinos-mezquital-iteshu.trycloudflare.com</code>) válido para la demostración en clase.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # ==================================================================
    # 10. GUION Y PREPARACIÓN DE LA EVALUACIÓN EN CLASE
    # ==================================================================
    story.append(Paragraph("10. Guion Técnico para la Demostración en Clase", h1_style))
    story.append(Paragraph(
        "<b>Fase 1: Presentación de Arquitectura (3 minutos)</b><br/>"
        "Explicar la problemática del Valle del Mezquital, el collar con Heltec LoRa ESP32 v2 a 915 MHz, el Gateway y el broker MQTT.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>Fase 2: Evidencia del Repositorio y Metodología (2 minutos)</b><br/>"
        "Mostrar el repositorio Git con commits atómicos (<code>feat:</code>, <code>fix:</code>, <code>docs:</code>) y ejecutar en terminal <code>openspec validate --all</code> demostrando que la arquitectura pasó las pruebas de consistencia técnica.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>Fase 3: Demostración Funcional en Vivo (5 minutos)</b><br/>"
        "• Abrir la plataforma en el subdominio web publicado frente al docente.<br/>"
        "• Mostrar el mapa con los 3 bovinos de prueba en sus tres estados de semáforo.<br/>"
        "• Activar la pestaña <b>'Simulador Rápido'</b> o encender el collar físico: inyectar una coordenada y demostrar cómo el marcador del bovino <code>BOV-003</code> cambia en tiempo real a verde (Actualizado).<br/>"
        "• Entrar al módulo de <b>'Historial de Recorridos'</b> para mostrar la ruta poligonal sobre Huichapan.<br/>"
        "• Entrar a <b>'Centro de Alertas'</b> y reconocer la alerta de batería baja registrando la observación del operador.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>Fase 4: Defensa Técnica ante Preguntas del Docente</b><br/>"
        "Estar preparado para explicar: por qué LoRa 915 MHz en lugar de GSM (costo nulo por transmisión y alcance en zonas sin red celular), por qué se usó <code>millis()</code> en lugar de <code>delay()</code> (para no trabar la máquina de estados en el lazo principal) y por qué se usó SQLite con Streamlit (ligereza y contención total en un solo contenedor Docker portátil).",
        bullet_style
    ))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=C_SECONDARY, spaceAfter=15, spaceBefore=10))
    story.append(Paragraph(
        "<b>Conclusión del Proyecto:</b> El MVP desarrollado satisface rigurosamente los estándares de ingeniería mecatrónica de ITESHU, fusionando hardware embebido de largo alcance, protocolos de red IoT y una plataforma cloud intuitiva para la ganadería de precisión del Valle del Mezquital.",
        ParagraphStyle('FooterNote', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, leading=13, textColor=C_PRIMARY, alignment=1)
    ))

    # Construir documento
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Documento PDF generado exitosamente en: {ruta_salida}")

if __name__ == "__main__":
    salida = sys.argv[1] if len(sys.argv) > 1 else "Documento_Integral_Desarrollo_Plataforma_IoT_Bovinos.pdf"
    crear_documento_integral(salida)
