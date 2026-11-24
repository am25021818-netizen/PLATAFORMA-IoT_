"""Genera el PDF del manual de despliegue para personal no técnico.

Uso:
    python generar_pdf_manual_despliegue.py

Salida por defecto:
    Escritorio del usuario -> Manual_Despliegue_STI_ITESHU.pdf
También guarda una copia en docs/ para que quede versionado con el manual .md.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent
MD_PATH = ROOT / "docs" / "manual_despliegue_para_no_tecnico.md"
PDF_NAME = "Manual_Despliegue_STI_ITESHU.pdf"
DESKTOP = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
PDF_ESCRITORIO = DESKTOP / PDF_NAME
PDF_REPO = ROOT / "docs" / PDF_NAME

ANCHO = letter[0] - 108  # márgenes de 54 pt a cada lado

# ---------------------------------------------------------------------------
# Colores institucionales sobrios
# ---------------------------------------------------------------------------
PRIMARY = colors.HexColor("#1b4332")
SECONDARY = colors.HexColor("#2d6a4f")
ACCENT = colors.HexColor("#52b788")
LIGHT = colors.HexColor("#f4f8f5")
BORDER = colors.HexColor("#cfe3d7")
WARNING_BG = colors.HexColor("#fff7e6")
WARNING_LINE = colors.HexColor("#d98c00")
TEXT = colors.HexColor("#202520")
MUTED = colors.HexColor("#5b665e")


# ---------------------------------------------------------------------------
# Canvas con portada limpia, encabezado y numeración de páginas
# ---------------------------------------------------------------------------
class ManualCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._states = []

    def showPage(self):
        self._states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._states)
        for state in self._states:
            self.__dict__.update(state)
            self._decorar(total)
            super().showPage()
        super().save()

    def _decorar(self, total):
        # La portada no lleva encabezado ni pie.
        if self._pageNumber == 1:
            return
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(PRIMARY)
        self.drawString(54, 750, "ITESHU · MAESTRÍA EN MECATRÓNICA · INTERNET DE LAS COSAS")
        self.setFont("Helvetica", 8)
        self.setFillColor(MUTED)
        self.drawRightString(558, 750, "Manual de despliegue · sitio web STI")
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.75)
        self.line(54, 744, 558, 744)

        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Plataforma IoT para monitoreo GPS de bovinos · Valle del Mezquital")
        self.drawRightString(558, 32, f"Página {self._pageNumber} de {total}")
        self.restoreState()


# ---------------------------------------------------------------------------
# Documento con índice automático
# ---------------------------------------------------------------------------
class ManualDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("Seccion", "Subseccion"):
            nivel = 0 if flowable.style.name == "Seccion" else 1
            texto = flowable.getPlainText().replace("&", "&amp;")
            self.notify("TOCEntry", (nivel, texto, self.page))


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
def estilos():
    base = dict(splitLongWords=1)
    return {
        "PortadaTitulo": ParagraphStyle(
            "PortadaTitulo", fontName="Helvetica-Bold", fontSize=25, leading=31,
            textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=12,
        ),
        "PortadaSub": ParagraphStyle(
            "PortadaSub", fontName="Helvetica", fontSize=13.5, leading=18,
            textColor=SECONDARY, alignment=TA_CENTER, spaceAfter=18,
        ),
        "PortadaEtiqueta": ParagraphStyle(
            "PortadaEtiqueta", fontName="Helvetica-Bold", fontSize=9, leading=12,
            textColor=colors.white, alignment=TA_CENTER,
        ),
        "PortadaInfo": ParagraphStyle(
            "PortadaInfo", fontName="Helvetica", fontSize=10, leading=15,
            textColor=TEXT, alignment=TA_LEFT,
        ),
        "IndiceTitulo": ParagraphStyle(
            "IndiceTitulo", fontName="Helvetica-Bold", fontSize=19, leading=23,
            textColor=PRIMARY, spaceAfter=10,
        ),
        "PortadaIndice": ParagraphStyle(
            "PortadaIndice", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
            textColor=SECONDARY, spaceAfter=6,
        ),
        "Seccion": ParagraphStyle(
            "Seccion", fontName="Helvetica-Bold", fontSize=14.5, leading=19,
            textColor=PRIMARY, spaceBefore=16, spaceAfter=7, keepWithNext=1, **base,
        ),
        "Subseccion": ParagraphStyle(
            "Subseccion", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
            textColor=SECONDARY, spaceBefore=12, spaceAfter=5, keepWithNext=1, **base,
        ),
        "Cuerpo": ParagraphStyle(
            "Cuerpo", fontName="Helvetica", fontSize=9.7, leading=14,
            textColor=TEXT, spaceAfter=6, **base,
        ),
        "Viñeta": ParagraphStyle(
            "Viñeta", fontName="Helvetica", fontSize=9.5, leading=13.5,
            textColor=TEXT, leftIndent=18, bulletIndent=4, spaceAfter=3, **base,
        ),
        "Codigo": ParagraphStyle(
            "Codigo", fontName="Courier", fontSize=7.2, leading=9.4,
            textColor=colors.HexColor("#143d2b"), backColor=LIGHT,
            borderColor=BORDER, borderWidth=0.6, borderPadding=6,
            leftIndent=6, spaceBefore=4, spaceAfter=8,
        ),
        "CeldaHead": ParagraphStyle(
            "CeldaHead", fontName="Helvetica-Bold", fontSize=8.4, leading=11,
            textColor=colors.white, **base,
        ),
        "Celda": ParagraphStyle(
            "Celda", fontName="Helvetica", fontSize=8.2, leading=10.8,
            textColor=TEXT, **base,
        ),
        "AvisoCaja": ParagraphStyle(
            "AvisoCaja", fontName="Helvetica", fontSize=9.2, leading=13,
            textColor=colors.HexColor("#6b4b00"), **base,
        ),
        "PieIndice": ParagraphStyle(
            "PieIndice", fontName="Helvetica-Oblique", fontSize=9, leading=13,
            textColor=MUTED, spaceBefore=8, **base,
        ),
    }


# ---------------------------------------------------------------------------
# Conversión de Markdown a HTML simple para ReportLab
# ---------------------------------------------------------------------------
REEMPLAZOS = {
    "→": "->", "←": "<-", "├──": "|--", "└──": "--", "│": "|",
    "⚠️": "[!] AVISO:", "⚠": "[!] AVISO:", "✅": "[SI]", "☑": "[x]", "☐": "[ ]",
    "—": " - ", "–": "-", "“": '"', "”": '"', "’": "'", "…": "...",
}


def limpiar(texto: str) -> str:
    for original, nuevo in REEMPLAZOS.items():
        texto = texto.replace(original, nuevo)
    return texto


def esc(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def en_linea(texto: str) -> str:
    """Convierte negrita, cursiva y código inline a markup de ReportLab."""
    texto = limpiar(texto)
    salto = texto.endswith("  ")
    texto = texto.rstrip()

    partes = re.split(r"(`[^`]*`)", texto)
    salida = []
    for parte in partes:
        if len(parte) >= 2 and parte.startswith("`") and parte.endswith("`"):
            codigo = esc(parte[1:-1])
            salida.append(
                f'<font face="Courier" size="8.6" color="#1b6b4a">{codigo}</font>'
            )
            continue
        trozo = esc(parte)
        trozo = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", trozo)
        trozo = re.sub(r"__(.+?)__", r"<b>\1</b>", trozo)
        trozo = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", trozo)
        salida.append(trozo)
    return "".join(salida) + ("<br/>" if salto else "")


def dividir_fila(linea: str) -> list[str]:
    """Separa celdas de una fila Markdown respetando el código inline."""
    linea = linea.strip()
    if linea.startswith("|"):
        linea = linea[1:]
    if linea.endswith("|"):
        linea = linea[:-1]
    celdas, actual, en_codigo = [], "", False
    for ch in linea:
        if ch == "`":
            en_codigo = not en_codigo
            actual += ch
        elif ch == "|" and not en_codigo:
            celdas.append(actual.strip())
            actual = ""
        else:
            actual += ch
    celdas.append(actual.strip())
    return celdas


def es_separador(linea: str) -> bool:
    return bool(re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", linea)) and "-" in linea


# ---------------------------------------------------------------------------
# Construcción del documento
# ---------------------------------------------------------------------------
def construir_portada(est, toc):
    story = []
    story.append(Spacer(1, 46))
    banda = Table(
        [["ITESHU · MAESTRÍA EN MECATRÓNICA · INTERNET DE LAS COSAS"]],
        colWidths=[ANCHO],
    )
    banda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story += [banda, Spacer(1, 42)]

    story.append(Paragraph(
        "Manual para subir el sitio web<br/>al servidor del ITESHU", est["PortadaTitulo"]
    ))
    story.append(Paragraph(
        "Explicado para una persona que no trabaja en programación",
        est["PortadaSub"],
    ))
    story.append(HRFlowable(width="62%", thickness=1.4, color=ACCENT, spaceBefore=4, spaceAfter=20, hAlign="CENTER"))

    info = Table([
        [Paragraph("<b>Servidor</b>", est["PortadaInfo"]), Paragraph("sti.itsoeh.edu.mx", est["PortadaInfo"])],
        [Paragraph("<b>Proyecto</b>", est["PortadaInfo"]), Paragraph("Plataforma IoT para monitoreo GPS de bovinos", est["PortadaInfo"])],
        [Paragraph("<b>Tiempo estimado</b>", est["PortadaInfo"]), Paragraph("45 a 60 minutos", est["PortadaInfo"])],
        [Paragraph("<b>Requisito previo</b>", est["PortadaInfo"]), Paragraph("Autorización del área de STI del ITESHU", est["PortadaInfo"])],
    ], colWidths=[1.45 * inch, ANCHO - 1.45 * inch])
    info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [info, Spacer(1, 26)]

    story.append(Paragraph("Índice rápido del procedimiento", est["PortadaIndice"]))
    pasos = [
        "Entender los términos y pedir permiso a STI.",
        "Hacer copia de seguridad de ThingsBoard.",
        "Apagar ThingsBoard y preparar el servidor.",
        "Descargar el proyecto desde GitHub y crear la clave secreta.",
        "Encender los tres servicios con Docker.",
        "Configurar Nginx (recepcionista) e HTTPS (candado).",
        "Probar el sitio, verificar y saber cómo volver atrás.",
    ]
    for i, paso in enumerate(pasos, 1):
        story.append(Paragraph(f"{i}. {paso}", est["Viñeta"]))

    story.append(Spacer(1, 18))
    aviso = Table([[Paragraph(
        "<b>Regla de oro:</b> haz el respaldo antes de apagar nada y, si algo falla, detente "
        "y usa la sección «Si algo sale mal». El proceso es reversible.",
        est["AvisoCaja"],
    )]], colWidths=[ANCHO])
    aviso.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARNING_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 3, WARNING_LINE),
        ("BOX", (0, 0), (-1, -1), 0.5, WARNING_LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [aviso, PageBreak()]

    story.append(Paragraph("Contenido", est["IndiceTitulo"]))
    toc.levelStyles = [
        ParagraphStyle("TOC1", fontName="Helvetica-Bold", fontSize=10, leading=15, textColor=PRIMARY),
        ParagraphStyle("TOC2", fontName="Helvetica", fontSize=9, leading=13, leftIndent=16, textColor=MUTED),
    ]
    story += [toc, Spacer(1, 16), Paragraph(
        "Los comandos aparecen en recuadros grises. Puedes copiarlos tal cual; "
        "solo recuerda sustituir <b>usuario</b> y la clave del archivo <b>.env</b>.",
        est["PieIndice"],
    ), PageBreak()]
    return story


def procesar_markdown(ruta: Path, est) -> list:
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    try:
        inicio = next(i for i, l in enumerate(lineas) if i > 0 and l.strip() == "---") + 1
    except StopIteration:
        inicio = 0
    lineas = lineas[inicio:]
    story = []
    i = 0

    while i < len(lineas):
        linea = lineas[i]
        crudo = linea.strip()

        if not crudo:
            i += 1
            continue

        if crudo == "---":
            story += [HRFlowable(width="100%", thickness=0.6, color=BORDER, spaceBefore=8, spaceAfter=8)]
            i += 1
            continue

        if crudo.startswith("```"):
            i += 1
            bloque = []
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                bloque.append(lineas[i].rstrip())
                i += 1
            i += 1  # cierre del bloque
            bloque = [limpiar(l).replace("\t", "    ") for l in bloque]
            max_len = max((len(l) for l in bloque), default=0)
            font_size = 7.4 if max_len <= 108 else 6.6
            estilo_codigo = ParagraphStyle(
                f"Codigo_{i}", parent=est["Codigo"], fontSize=font_size, leading=font_size + 2.2,
            )
            story.append(Preformatted("\n".join(bloque), estilo_codigo))
            continue

        if crudo.startswith("#### "):
            story.append(Paragraph(en_linea(crudo[5:]), est["Subseccion"]))
            i += 1
            continue
        if crudo.startswith("### "):
            story.append(Paragraph(en_linea(crudo[4:]), est["Subseccion"]))
            i += 1
            continue
        if crudo.startswith("## "):
            story.append(Paragraph(en_linea(crudo[3:]), est["Seccion"]))
            i += 1
            continue
        if crudo.startswith("# "):
            i += 1
            continue

        if crudo.startswith(">"):
            aviso = []
            while i < len(lineas) and lineas[i].strip().startswith(">"):
                aviso.append(lineas[i].strip()[1:].strip())
                i += 1
            caja = Table([[Paragraph("<br/>".join(en_linea(x) for x in aviso), est["AvisoCaja"])]], colWidths=[ANCHO])
            caja.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), WARNING_BG),
                ("LINEBEFORE", (0, 0), (0, -1), 3, WARNING_LINE),
                ("BOX", (0, 0), (-1, -1), 0.5, WARNING_LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story += [Spacer(1, 4), caja, Spacer(1, 8)]
            continue

        if crudo.startswith("|") and i + 1 < len(lineas) and es_separador(lineas[i + 1]):
            cabecera = dividir_fila(linea)
            i += 2
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                filas.append(dividir_fila(lineas[i]))
                i += 1
            ncol = len(cabecera)
            if ncol == 3:
                anchos = [ANCHO * 0.24, ANCHO * 0.44, ANCHO * 0.32]
            elif ncol == 2:
                anchos = [ANCHO * 0.32, ANCHO * 0.68]
            else:
                anchos = [ANCHO / ncol] * ncol
            datos = [[Paragraph(en_linea(c), est["CeldaHead"]) for c in cabecera]]
            for fila in filas:
                fila += [""] * (ncol - len(fila))
                datos.append([Paragraph(en_linea(c), est["Celda"]) for c in fila[:ncol]])
            tabla = Table(datos, colWidths=anchos, repeatRows=1, hAlign="LEFT")
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story += [Spacer(1, 2), tabla, Spacer(1, 10)]
            continue

        if crudo.startswith("- [ ] ") or crudo.startswith("- [x] ") or crudo.startswith("- "):
            marcado = crudo[2:]
            if marcado.startswith("[ ] "):
                bala, texto = "[ ]", marcado[4:]
            elif marcado.startswith("[x] "):
                bala, texto = "[x]", marcado[4:]
            else:
                bala, texto = "-", marcado
            story.append(Paragraph(en_linea(texto), est["Viñeta"], bulletText=bala))
            i += 1
            continue

        mnum = re.match(r"^(\d+)\.\s+(.*)$", crudo)
        if mnum:
            story.append(Paragraph(en_linea(mnum.group(2)), est["Viñeta"], bulletText=mnum.group(1) + "."))
            i += 1
            continue

        parrafo = [linea.rstrip()]
        i += 1
        while i < len(lineas):
            siguiente = lineas[i].strip()
            if (not siguiente or siguiente.startswith(("```", "#", "|", ">", "- ")) or
                    es_separador(lineas[i]) or re.match(r"^\d+\.\s", siguiente)):
                break
            parrafo.append(lineas[i].rstrip())
            i += 1
        story.append(Paragraph("<br/>".join(en_linea(x) for x in parrafo), est["Cuerpo"]))

    return story


def generar() -> None:
    est = estilos()
    toc = TableOfContents()
    story = construir_portada(est, toc)
    story += procesar_markdown(MD_PATH, est)

    DESKTOP.mkdir(parents=True, exist_ok=True)
    doc = ManualDoc(
        str(PDF_ESCRITORIO),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
        title="Manual de despliegue STI - ITESHU",
        author="Ing. Iván Rodríguez Hernández",
        subject="Guía explicada para subir el sitio web al servidor del ITESHU",
        canvasmaker=ManualCanvas,
    )
    doc.multiBuild(story)

    shutil.copy2(PDF_ESCRITORIO, PDF_REPO)
    print(f"PDF generado en escritorio: {PDF_ESCRITORIO}")
    print(f"Copia en repositorio:       {PDF_REPO}")
    print(f"Tamaño: {PDF_ESCRITORIO.stat().st_size:,} bytes")


if __name__ == "__main__":
    generar()
