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
# Canvas Estilo Artículo Académico LaTeX (Encabezado y Pie de Página)
# ----------------------------------------------------------------------
class AcademicNumberedCanvas(canvas.Canvas):
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
        self.saveState()
        
        # En la primera página no colocamos encabezado superior completo
        if self._pageNumber > 1:
            self.setFont("Times-Italic", 8.5)
            self.setFillColor(colors.HexColor("#222222"))
            self.drawString(54, 752, "Instituto Tecnológico Superior de Huichapan · Maestría en Mecatrónica · Internet de las Cosas")
            self.drawRightString(558, 752, "MVP Monitoreo GPS LoRa/MQTT de Bovinos")
            
            self.setStrokeColor(colors.HexColor("#444444"))
            self.setLineWidth(0.6)
            self.line(54, 746, 558, 746)

        # Pie de página estilo LaTeX (Línea sutil y numeración centrada o en extremos)
        self.setStrokeColor(colors.HexColor("#888888"))
        self.setLineWidth(0.5)
        self.line(54, 44, 558, 44)

        self.setFont("Times-Roman", 8.5)
        self.setFillColor(colors.HexColor("#333333"))
        self.drawString(54, 32, "Ing. Iván Rodríguez Hernández · DTI. Carlos Arturo Espinoza Galicia")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 32, page_str)

        self.restoreState()

# ----------------------------------------------------------------------
# Construcción del Documento Técnico Integral
# ----------------------------------------------------------------------
def generar_documento_latex(ruta_pdf):
    doc = SimpleDocTemplate(
        ruta_pdf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Colores sobrios estilo LaTeX / IEEE
    COLOR_PRIMARY = colors.HexColor("#0f2b1d")   # Verde oscuro bosque técnico
    COLOR_SECONDARY = colors.HexColor("#1b4332") # Verde sobrio
    COLOR_BODY = colors.HexColor("#1a1a1a")      # Negro tipográfico
    COLOR_MUTED = colors.HexColor("#4a4a4a")     # Gris carbón
    COLOR_RULE = colors.HexColor("#2b2b2b")      # Líneas formales

    # Tipografías Serif estilo LaTeX (Times-Roman)
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=20,
        leading=24,
        textColor=COLOR_PRIMARY,
        alignment=1, # Centrado
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=12,
        leading=16,
        textColor=COLOR_MUTED,
        alignment=1,
        spaceAfter=15
    )

    author_style = ParagraphStyle(
        'AuthorBlock',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        textColor=COLOR_BODY,
        alignment=1,
        spaceAfter=20
    )

    abstract_title = ParagraphStyle(
        'AbstractTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        leading=13,
        textColor=COLOR_PRIMARY,
        alignment=1,
        spaceAfter=4
    )

    abstract_body = ParagraphStyle(
        'AbstractBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        leading=12,
        textColor=COLOR_BODY,
        alignment=4, # Justificado
        leftIndent=24,
        rightIndent=24,
        spaceAfter=15
    )

    sec_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=13,
        leading=17,
        textColor=COLOR_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    subsec_style = ParagraphStyle(
        'SubSectionHeader',
        parent=styles['Normal'],
        fontName='Times-BoldItalic',
        fontSize=10.5,
        leading=14.5,
        textColor=COLOR_SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyAcademic',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        textColor=COLOR_BODY,
        alignment=4, # Justificado
        firstLineIndent=16,
        spaceAfter=5
    )

    body_no_indent = ParagraphStyle(
        'BodyNoIndent',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        textColor=COLOR_BODY,
        alignment=4,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletAcademic',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9,
        leading=13,
        textColor=COLOR_BODY,
        leftIndent=20,
        spaceAfter=3
    )

    formula_style = ParagraphStyle(
        'MathFormula',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=9.5,
        leading=14,
        textColor=COLOR_PRIMARY,
        alignment=1,
        spaceBefore=6,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeListing',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10,
        textColor=colors.HexColor("#1b1b1b")
    )

    th_style = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    tb_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8,
        leading=10.5,
        textColor=COLOR_BODY
    )

    tb_bold = ParagraphStyle(
        'TableBodyBold',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=8,
        leading=10.5,
        textColor=COLOR_BODY
    )

    story = []

    # ==================================================================
    # ENCABEZADO INSTITUCIONAL Y TÍTULO TIPO ARTÍCULO CIENTÍFICO LATEX
    # ==================================================================
    story.append(Paragraph("INSTITUTO TECNOLÓGICO SUPERIOR DE HUICHAPAN", ParagraphStyle(
        'InstTop', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=15, textColor=COLOR_SECONDARY, alignment=1
    )))
    story.append(Paragraph("DIVISIÓN DE ESTUDIOS DE POSGRADO E INVESTIGACIÓN · MAESTRÍA EN INGENIERÍA MECATRÓNICA<br/>ASIGNATURA: INTERNET DE LAS COSAS (IoT)", ParagraphStyle(
        'InstSubTop', parent=styles['Normal'], fontName='Times-Roman', fontSize=9, leading=12, textColor=COLOR_MUTED, alignment=1
    )))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceAfter=14, spaceBefore=4))

    story.append(Paragraph("Desarrollo de un MVP de Plataforma IoT para el Monitoreo GPS de Bovinos en Pastoreo Extensivo en el Valle del Mezquital Asistido por Programación Agéntica y OpenCode", title_style))
    story.append(Paragraph("Arquitectura de Dos Tramos LoRa-MQTT, Contenerización Docker, Geolocalización en Tiempo Real y Reglas Fail-Safe", subtitle_style))

    # Bloque de autores y adscripción
    story.append(Paragraph(
        "<b>Ing. Iván Rodríguez Hernández</b><sup>1</sup> &nbsp;&nbsp;·&nbsp;&nbsp; <b>DTI. Carlos Arturo Espinoza Galicia</b><sup>2</sup><br/>"
        "<sup>1</sup>Estudiante de Maestría en Ingeniería Mecatrónica, ITESHU (ivan.rodriguez@iteshu.edu.mx)<br/>"
        "<sup>2</sup>Docente Titular de la Asignatura de Internet de las Cosas, ITESHU (carlos.espinoza@iteshu.edu.mx)<br/>"
        "Huichapan, Estado de Hidalgo, México · Noviembre de 2026",
        author_style
    ))

    # Bloque de Resumen / Abstract
    story.append(HRFlowable(width="90%", thickness=0.6, color=COLOR_RULE, spaceAfter=8, spaceBefore=4))
    story.append(Paragraph("RESUMEN EJECUTIVO", abstract_title))
    story.append(Paragraph(
        "En este trabajo se presenta el diseño, desarrollo, validación y despliegue del Producto Mínimo Viable (MVP) de una plataforma integral de Internet de las Cosas (IoT) orientada al monitoreo geográfico en tiempo real de ganado bovino en pastoreo semi-extensivo para la región geográfica del Valle del Mezquital, Estado de Hidalgo. La arquitectura aborda la severa limitante de ausencia de conectividad celular en las serranías y potreros mediante una topología desacoplada de dos tramos: el Tramo 1 opera en campo mediante nodos collar de cuero equipados con microcontroladores Heltec LoRa ESP32 v2 y receptores GPS u-blox NMEA transmitiendo por radiofrecuencia en la banda ISM de 915 MHz; el Tramo 2 comprende una estación base o gateway que actúa como puente translacional hacia el protocolo MQTT (broker Eclipse Mosquitto). En el servidor, un microservicio de ingesta desarrollado en Python procesa y persiste los paquetes en una base de datos SQLite relacional, mientras que una interfaz web reactiva desarrollada en Streamlit proporciona visualización cartográfica satelital, geocercas de potreros, cálculo de semáforo de vigencia temporal y módulo de atención de incidentes. Todo el desarrollo se estructuró bajo la metodología agéntica asistida por IA con OpenCode y OpenSpec (Spec-Driven Development), con un lazo de ejecución no bloqueante con millis() y validación estricta de consistencia técnica.",
        abstract_body
    ))
    story.append(Paragraph(
        "<i><b>Palabras clave:</b> Internet de las Cosas, LoRa 915 MHz, Heltec ESP32, MQTT, Monitoreo Pecuario, Valle del Mezquital, OpenCode, OpenSpec, Streamlit, Docker.</i>",
        abstract_body
    ))
    story.append(HRFlowable(width="90%", thickness=0.6, color=COLOR_RULE, spaceAfter=14, spaceBefore=4))

    # ==================================================================
    # SECCIÓN 1: INTRODUCCIÓN Y CONTEXTO REGIONAL
    # ==================================================================
    story.append(Paragraph("1. Introducción y Contexto Regional del Valle del Mezquital", sec_style))
    story.append(Paragraph(
        "La producción ganadera en el Estado de Hidalgo constituye una actividad económica y social de primordial relevancia, particularmente en la demarcación del Valle del Mezquital (que comprende municipios de vocación pecuaria como Huichapan, Nopala de Villagrán, Tecozautla, Alfajayucan, Chapantongo e Ixmiquilpan). Las unidades de producción ganadera en esta región operan preponderantemente bajo modalidades de pastoreo extensivo y semi-intensivo, en terrenos que abarcan desde agostaderos llanos con pasto Buffel y zacate estrella, hasta serranías áridas caracterizadas por matorral espinoso, mezquitales y cardonales densos.",
        body_style
    ))
    story.append(Paragraph(
        "En este entorno operativo, los productores pecuarios enfrentan tres contingencias críticas cotidianas:<br/>"
        "1. <b>Dispersión y extravío de ejemplares:</b> La topografía accidentada y la presencia de barrancas propician que toros sementales, vacas de cría o novillos se desvíen del hato principal hacia predios colindantes o zonas de riesgo físico.<br/>"
        "2. <b>Abigeato (Sustracción no autorizada de ganado):</b> En zonas rurales apartadas, el robo de cabezas de ganado representa pérdidas patrimoniales severas, las cuales suelen detectarse días después debido a la falta de supervisión continua.<br/>"
        "3. <b>Altos costos de inspección presencial:</b> La revisión física tradicional obliga al ganadero o a vaqueros a efectuar recorridos diarios a caballo o vehículo, demandando múltiples horas-hombre y combustible sin ofrecer garantía de localización rápida.",
        body_style
    ))
    story.append(Paragraph(
        "La incorporación de tecnologías de geolocalización satelital convencional (GPS con módem GSM/GPRS celular) resulta técnica y económicamente inviable en la mayor parte del Valle del Mezquital debido a dos factores: la cobertura de telefonía celular 3G/4G es deficiente o nula en los potreros serranos, y el consumo energético de un módem celular drenaría una batería portátil en menos de 48 horas.",
        body_style
    ))

    # ==================================================================
    # SECCIÓN 2: ALCANCE: COMPARATIVA ENTRE MVP Y PLATAFORMA IDEAL
    # ==================================================================
    story.append(Paragraph("2. Delimitación de Alcance: MVP vs. Plataforma Ideal", sec_style))
    story.append(Paragraph(
        "En consonancia con las buenas prácticas de ingeniería de software y el documento de requerimientos aprobado el 13 de noviembre de 2026, se fijó un umbral nítido entre el Producto Mínimo Viable (MVP) y las capacidades evolutivas de la plataforma:",
        body_style
    ))

    # Tabla Académica de Alcance
    alcance_data = [
        [Paragraph("Módulo o Capacidad", th_style), Paragraph("Producto Mínimo Viable (MVP Funcional)", th_style), Paragraph("Plataforma Ideal (Evolución Futura)", th_style)],
        [
            Paragraph("<b>Identidad y Catálogo</b>", tb_bold),
            Paragraph("Registro de ranchos, usuarios por rol, arete pecuario SINIGA y asignación 1 a 1 de collar por animal.", tb_style),
            Paragraph("Gestión federada multi-rancho, control reproductivo, árboles genealógicos y trazabilidad sanitaria comercial.", tb_style)
        ],
        [
            Paragraph("<b>Comunicación RF</b>", tb_bold),
            Paragraph("Enlace punto a punto LoRa 915 MHz (Collar a Gateway) y puente a MQTT Mosquitto vía Wi-Fi local.", tb_style),
            Paragraph("Red mallada LoRaWAN multi-gateway, roaming con respaldo celular 4G y buffer de almacenamiento offline.", tb_style)
        ],
        [
            Paragraph("<b>Georreferenciación</b>", tb_bold),
            Paragraph("Visualización satelital en tiempo real, trazado de polilíneas de recorrido y semáforo estricto de vigencia.", tb_style),
            Paragraph("Geocercas poligonales dinámicas multipunto con alertas acústicas y predicción de rutas basada en IA.", tb_style)
        ],
        [
            Paragraph("<b>Gestión de Alertas</b>", tb_bold),
            Paragraph("Detección de batería crítica (<20%), pérdida de comunicación (>30 min) y módulo de atención con bitácora.", tb_style),
            Paragraph("Notificaciones push por WhatsApp, SMS y llamadas automatizadas de emergencia al personal de vigilancia.", tb_style)
        ],
        [
            Paragraph("<b>Variables Físicas</b>", tb_bold),
            Paragraph("Latitud, longitud, altitud, velocidad, satélites, voltaje y porcentaje de carga de celda LiPo.", tb_style),
            Paragraph("Temperatura ruminal, acelerometría triaxial para detección de celo y sensores de frecuencia cardiaca.", tb_style)
        ]
    ]
    t_alcance = Table(alcance_data, colWidths=[100, 200, 204])
    t_alcance.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEABOVE', (0,0), (-1,0), 1.2, COLOR_PRIMARY),
        ('LINEBELOW', (0,0), (-1,0), 1.0, COLOR_PRIMARY),
        ('LINEBELOW', (0,-1), (-1,-1), 1.2, COLOR_PRIMARY),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#dddddd")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9f9f9")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_alcance)
    story.append(Spacer(1, 8))

    # ==================================================================
    # SECCIÓN 3: ARQUITECTURA DE HARDWARE Y RADIOENLACE LORA
    # ==================================================================
    story.append(Paragraph("3. Arquitectura Mecatrónica de Dos Tramos y Radioenlace LoRa", sec_style))
    story.append(Paragraph(
        "Para garantizar un alcance superior a 5 kilómetros en línea de vista con consumos de corriente en el orden de miliamperios, se estructuró una arquitectura de dos tramos desacoplados:",
        body_style
    ))

    story.append(Paragraph("3.1 Tramo 1: Collar Emisor en Campo (Heltec LoRa ESP32 v2 + GPS)", subsec_style))
    story.append(Paragraph(
        "Cada animal porta un collar de cuero de alta resistencia mecánica dotado de una caja estanca de policarbonato con clasificación de protección <b>IP67</b> para soportar lodo, inmersión accidental en bebederos y frotamiento contra árboles. El nodo emisor integra:<br/>"
        "• <b>Unidad de Procesamiento:</b> Tarjeta Heltec LoRa ESP32 v2 impulsada por el microprocesador Xtensa dual-core LX6 a 240 MHz con 520 KB de SRAM y chip RF Semtech SX1276 integrado.<br/>"
        "• <b>Módulo GPS:</b> u-blox NEO-6M con antena de parche cerámica activa de 25x25 mm interconectado mediante el puerto UART serie de hardware (RX: GPIO 22, TX: GPIO 23) a 9600 baudios.<br/>"
        "• <b>Monitoreo de Energía:</b> Divisor resistivo interno conectado al pin ADC GPIO 37 para cuantificar el voltaje de la batería LiPo de 3.7 V (1200 mAh).",
        body_style
    ))

    # Ecuación de Pérdida en Espacio Libre (FSPL)
    story.append(Paragraph("La atenuación del radioenlace LoRa a 915 MHz en el Valle del Mezquital se modela mediante la ecuación de propagación en espacio libre (Free-Space Path Loss):", body_no_indent))
    story.append(Paragraph(
        "<i>FSPL (dB) = 20 · log<sub>10</sub>(d) + 20 · log<sub>10</sub>(f) - 147.55</i>",
        formula_style
    ))
    story.append(Paragraph(
        "donde <i>d</i> es la distancia en metros y <i>f</i> es la frecuencia central (915 × 10<sup>6</sup> Hz). Con una potencia de salida configurada a <b>+20 dBm (100 mW)</b> y una sensibilidad de recepción del chip SX1276 de <b>-137 dBm</b> a Spreading Factor 7 (SF7) con ancho de banda de 125 kHz, el sistema dispone de un margen de enlace (Link Budget) superior a <b>157 dB</b>, permitiendo salvar obstáculos orográficos y vegetación típica del Valle del Mezquital.",
        body_style
    ))

    story.append(Paragraph("3.2 Tramo 2: Gateway Concentrador y Puente LoRa a MQTT", subsec_style))
    story.append(Paragraph(
        "Instalado en la estación base o casco del rancho, una segunda tarjeta Heltec LoRa ESP32 opera en escucha continua de radiofrecuencia a 915 MHz. Al recibir un paquete binario válido, el Gateway extrae el identificador del collar, coordenadas GPS y telemetría de salud, mide la potencia de señal recibida (<b>RSSI</b> en dBm) y la relación señal a ruido (<b>SNR</b> en dB), y empaqueta la información en formato JSON para su inmediata transmisión por Wi-Fi hacia el broker <b>Mosquitto</b>.",
        body_style
    ))

    # ==================================================================
    # SECCIÓN 4: MODELO DE DATOS Y CONTRATO MQTT FORMAL
    # ==================================================================
    story.append(Paragraph("4. Modelo de Datos y Contrato Formal MQTT", sec_style))
    story.append(Paragraph(
        "El contrato de datos publicado en <code>openspec/specs/contrato-mqtt/spec.md</code> funge como la fuente de verdad técnica para toda la plataforma:",
        body_style
    ))

    mqtt_code = """// Contrato JSON publicado en tópico: bovinos/{device_id}/telemetria (QoS 1)
{
  "device_id": "HELTEC-COLLAR-01",
  "animal_id": "BOV-001",
  "lat": 20.37542,
  "lon": -99.65431,
  "altitud_m": 2105.0,
  "velocidad_kmh": 1.2,
  "bateria_pct": 94,
  "rssi_dbm": -68,
  "snr_db": 9.5,
  "satelites": 9,
  "fix_valido": true,
  "timestamp": "2026-11-19 15:58:00"
}"""
    story.append(Paragraph(mqtt_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Reglas de Vigencia Temporal (RF-07)", subsec_style))
    story.append(Paragraph(
        "Para evitar la interpretación errónea de ubicaciones desactualizadas, el software calcula la diferencia en segundos entre la marca temporal de recepción y la hora del servidor (Δt):<br/>"
        "• <b>🟢 Estado Actualizado:</b> Δt &lt; 600 s (Menor a 10 minutos). Marcador verde en mapa.<br/>"
        "• <b>🟡 Estado Retrasado:</b> 600 s ≤ Δt ≤ 1800 s (Entre 10 y 30 minutos). Posible zona de sombra LoRa.<br/>"
        "• <b>🔴 Estado Sin Comunicación:</b> Δt &gt; 1800 s (Mayor a 30 minutos). Disparo de alerta operativa para inspección física.",
        body_style
    ))

    # ==================================================================
    # SECCIÓN 5: METODOLOGÍA AGÉNTICA: OPENCODE, OPENSPEC Y REGLAS AGENTS.md
    # ==================================================================
    story.append(Paragraph("5. Metodología de Desarrollo: Programación Agéntica con OpenCode y OpenSpec", sec_style))
    story.append(Paragraph(
        "En cumplimiento de la guía metodológica del ITESHU para la materia de IoT, el proyecto se desarrolló bajo el enfoque <b>Spec-Driven Development (Desarrollo Guiado por Especificaciones)</b>, erradicando la improvisación mediante el ciclo Plan -> Propose -> Apply -> Validate -> Archive:",
        body_style
    ))

    story.append(Paragraph(
        "• <b>El Reglamento del Taller (AGENTS.md):</b> Ubicado en la raíz y subcarpetas, impone límites inviolables al asistente de IA: prohibición absoluta de <code>delay()</code> en el lazo principal <code>loop()</code> del ESP32 (uso obligatorio de cronómetros no bloqueantes con <code>millis()</code>), modulación estricta a 915 MHz autorizada por el IFT en México, e interbloqueos fail-safe que impiden sobreescribir coordenadas válidas con ceros ante pérdidas de señal GPS.<br/>"
        "• <b>Los Planos de Fabricación (OpenSpec):</b> Se redactaron las propuestas de cambio en <code>openspec/changes/mvp-monitoreo-bovinos/</code> conteniendo <code>proposal.md</code>, <code>design.md</code>, <code>tasks.md</code> y <code>specs/telemetria/spec.md</code> bajo sintaxis BDD (Given-When-Then).<br/>"
        "• <b>Certificación Técnica:</b> El comando CLI <code>openspec validate --all</code> fue ejecutado satisfactoriamente, arrojando <b>2 passed, 0 failed</b>.",
        body_style
    ))

    # ==================================================================
    # SECCIÓN 6: INTERFAZ GRÁFICA, GEOCERCAS Y HARDWARE REAL
    # ==================================================================
    story.append(Paragraph("6. Plataforma Web Interactiva y Conexión de Hardware Real", sec_style))
    story.append(Paragraph(
        "La interfaz web desarrollada en <b>Python + Streamlit</b> incorpora los siguientes módulos de interacción pecuaria:",
        body_style
    ))

    story.append(Paragraph(
        "• <b>Tablero Geográfico General:</b> Mapa interactivo multi-capa (Satélite Esri World Imagery, Topográfico y OpenStreetMap) centrado en Huichapan y el Valle del Mezquital. Representa los potreros de pastoreo como geocercas circulares translúcidas y utiliza marcadores diferenciados para toros (🐂) y vacas (🐄).<br/>"
        "• <b>Fichas Técnicas del Hato:</b> Catálogo interactivo de 6 ejemplares con arete oficial SINIGA, raza (Simental, Charolais, Suizo, Angus, Brahman, Simbrah), edad, peso y barra porcentual de batería del collar.<br/>"
        "• <b>Módulo de Conexión de Nodos Reales:</b> Diseñado especialmente para la evaluación en laboratorio y operación en rancho:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;a) <i>Enlace MQTT en Vivo:</i> Verificación y sniffer de paquetes provenientes del Gateway Heltec LoRa.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;b) <i>Lector Serial USB Directo:</i> Auto-detección de puertos COM de Windows mediante <code>pyserial</code> para conectar tarjetas Heltec ESP32 vía cable USB y capturar telemetría a 115200 baudios sin depender de Wi-Fi en el aula.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;c) <i>Aprovisionamiento de Hardware:</i> Formulario para dar de alta nuevos collares generando el código <code>config.h</code> para Arduino IDE.<br/>"
        "• <b>Simulador de Campo:</b> Inyector dinámico de trayectorias que actualiza la base de datos para demostraciones funcionales en clase.",
        body_style
    ))

    # ==================================================================
    # SECCIÓN 7: CONTENERIZACIÓN DOCKER Y PUBLICACIÓN CON SUBDOMINIO
    # ==================================================================
    story.append(Paragraph("7. Despliegue en Contenedores Docker y Publicación Web", sec_style))
    story.append(Paragraph(
        "La plataforma se encuentra orquestada mediante <code>docker-compose.yml</code> integrando dos microservicios independientes:<br/>"
        "1. <b>iteshu_mosquitto_broker:</b> Broker MQTT Eclipse Mosquitto en puertos 1883 y 9001 con persistencia de bitácoras.<br/>"
        "2. <b>iteshu_plataforma_iot:</b> Contenedor Python 3.11-slim que ejecuta en paralelo el daemon de ingesta <code>ingesta_mqtt.py</code> y la aplicación web <code>dashboard.py</code> en el puerto 8501 con volumen mapeado en <code>./data:/app/data</code>.",
        body_style
    ))
    story.append(Paragraph(
        "Para dar cumplimiento a la evidencia de publicación bajo subdominio referente al proyecto, se integró la solución <b>Cloudflare Tunnel (cloudflared)</b>, la cual genera un túnel seguro cifrado bajo HTTPS (ejemplo: <code>https://bovinos-mezquital.trycloudflare.com</code> o <code>https://bovinos.tudominio.com</code>) sin necesidad de abrir puertos en el módem del usuario.",
        body_style
    ))

    # ==================================================================
    # SECCIÓN 8: GUION Y ESTRATEGIA DE EVALUACIÓN EN CLASE
    # ==================================================================
    story.append(Paragraph("8. Estrategia de Evaluación y Defensa en Clase", sec_style))
    story.append(Paragraph(
        "Durante la presentación final ante el docente DTI. Carlos Arturo Espinoza Galicia, se seguirá la siguiente secuencia demostrativa:<br/>"
        "1. <b>Presentación del Repositorio Git:</b> Mostrar el historial de commits atómicos en español (<code>feat:</code>, <code>fix:</code>, <code>docs:</code>) y la ejecución limpia de <code>openspec validate --all</code>.<br/>"
        "2. <b>Apertura de la Plataforma Web:</b> Abrir el subdominio publicado mostrando los 6 bovinos georreferenciados en los potreros de Huichapan y Tecozautla.<br/>"
        "3. <b>Demostración de Telemetría en Vivo:</b> Emplear el microcontrolador Heltec ESP32 conectado por USB (o el inyector del simulador) para enviar una coordenada: demostrar en pantalla que el novillo <i>BOV-003</i> pasa automáticamente de estado 'Sin comunicación' (🔴) a 'Actualizado' (🟢).<br/>"
        "4. <b>Atención de Alerta:</b> Ingresar al Centro de Alertas y registrar el reconocimiento y nota de campo sobre la batería baja del collar.<br/>"
        "5. <b>Trazado de Trayectorias:</b> Visualizar las polilíneas de recorrido histórico de <i>El Barón</i> junto con sus perfiles de elevación.",
        body_style
    ))

    # ==================================================================
    # REFERENCIAS BIBLIOGRÁFICAS (ESTILO IEEE)
    # ==================================================================
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_RULE, spaceAfter=8, spaceBefore=4))
    story.append(Paragraph("Referencias Bibliográficas", sec_style))
    story.append(Paragraph("[1] Semtech Corporation, <i>SX1276/77/78/79 Wireless & Sensing Data Sheet: 137 MHz to 1020 MHz Low Power Long Range Transceiver</i>, Rev. 7, 2020.", bullet_style))
    story.append(Paragraph("[2] Espressif Systems, <i>ESP32 Series Datasheet: 2.4 GHz Wi-Fi and Bluetooth combo chip</i>, v4.2, 2023.", bullet_style))
    story.append(Paragraph("[3] Instituto Federal de Telecomunicaciones (IFT), <i>Cuadro Nacional de Atribución de Frecuencias: Disposiciones para Bandas de Uso Libre en México (902-928 MHz)</i>, Diario Oficial de la Federación, 2018.", bullet_style))
    story.append(Paragraph("[4] OASIS Standard, <i>MQTT Version 5.0: Core Specification</i>, OASIS Standard, 2019.", bullet_style))
    story.append(Paragraph("[5] C. A. Espinoza Galicia, <i>Desarrollo de Sistemas IoT Asistido por IA con OpenCode y OpenSpec: Guía Metodológica para Tres Escenarios de Ingeniería</i>, Instituto Tecnológico Superior de Huichapan, 2026.", bullet_style))

    # Construir documento final
    doc.build(story, canvasmaker=AcademicNumberedCanvas)
    print(f"[OK] Documento PDF estilo LaTeX generado exitosamente en: {ruta_pdf}")

if __name__ == "__main__":
    salida = sys.argv[1] if len(sys.argv) > 1 else "Documento_Integral_Desarrollo_Plataforma_IoT_Bovinos.pdf"
    generar_documento_latex(salida)
