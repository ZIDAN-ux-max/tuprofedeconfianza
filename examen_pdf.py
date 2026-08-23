# -*- coding: utf-8 -*-
"""Genera el examen (preguntas + clave de respuestas) como PDF descargable,
para que el alumno lo pueda imprimir y resolver en papel. Reutiliza el
mismo renderizador de formulas que el Formulario, para que el texto con
LaTeX tambien se vea bien aca."""
import io
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors

from pdf_formulario import _render_formula_imagen

PATRON_FORMULA = re.compile(r"\$(.+?)\$")


def _texto_o_imagenes(texto, estilo, elementos):
    """Si el texto tiene formulas entre $...$, las separa y renderiza cada
    una como imagen chica en linea con el resto (que sigue como texto
    normal). Si no tiene formulas, es solo un parrafo comun."""
    texto = texto or ""
    partes = PATRON_FORMULA.split(texto)
    if len(partes) == 1:
        elementos.append(Paragraph(texto, estilo))
        return
    for i, parte in enumerate(partes):
        if not parte.strip():
            continue
        if i % 2 == 1:  # es formula (estaba entre $...$)
            img_buf = _render_formula_imagen(parte)
            if img_buf:
                elementos.append(Image(img_buf, width=45 * mm, height=9 * mm, kind="proportional"))
            else:
                elementos.append(Paragraph(parte, estilo))
        else:
            elementos.append(Paragraph(parte, estilo))


def generar_pdf_examen(materia, curso, preguntas):
    """Arma el PDF completo: portada, preguntas con espacio para responder
    en papel, y al final una clave de respuestas separada. Devuelve un
    BytesIO listo para pasarle a st.download_button."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=18 * mm, bottomMargin=15 * mm, leftMargin=18 * mm, rightMargin=18 * mm
    )
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("Titulo", parent=estilos["Title"], fontSize=20, textColor=colors.HexColor("#0F0C29"))
    estilo_subtitulo = ParagraphStyle("Subtitulo", parent=estilos["Normal"], fontSize=11, textColor=colors.HexColor("#555577"), alignment=TA_CENTER)
    estilo_pregunta = ParagraphStyle("Pregunta", parent=estilos["Normal"], fontSize=12, textColor=colors.HexColor("#0F0C29"), leading=15, spaceAfter=4)
    estilo_opcion = ParagraphStyle("Opcion", parent=estilos["Normal"], fontSize=11, textColor=colors.HexColor("#222244"), leftIndent=14, leading=14)
    estilo_clave = ParagraphStyle("Clave", parent=estilos["Normal"], fontSize=10.5, textColor=colors.HexColor("#333355"), leading=14)

    curso_txt = f" - {curso}" if curso else ""
    elementos = [
        Paragraph(f"Examen de {materia}{curso_txt}", estilo_titulo),
        Paragraph("Tu Profe de Confianza - para resolver en papel", estilo_subtitulo),
        Spacer(1, 8 * mm),
    ]

    for i, pregunta in enumerate(preguntas):
        tipo = pregunta.get("tipo")
        bloque = [Paragraph(f"<b>{i+1}.</b>", estilo_pregunta)]
        _texto_o_imagenes(pregunta.get("pregunta", ""), estilo_pregunta, bloque)

        if tipo == "multiple":
            for opcion in pregunta.get("opciones", []):
                bloque.append(Paragraph(f"( &nbsp; ) {opcion}", estilo_opcion))
        elif tipo == "abierta":
            bloque.append(Spacer(1, 4 * mm))
            for _ in range(3):
                bloque.append(Paragraph("_" * 78, estilo_opcion))
        elif tipo == "relacionar":
            columna_a = pregunta.get("columna_a", [])
            columna_b = pregunta.get("columna_b", [])
            for item_a in columna_a:
                bloque.append(Paragraph(f"( &nbsp; ) {item_a}", estilo_opcion))
            bloque.append(Spacer(1, 2 * mm))
            for j, item_b in enumerate(columna_b):
                letra = chr(65 + j)
                bloque.append(Paragraph(f"{letra}) {item_b}", estilo_opcion))

        bloque.append(Spacer(1, 6 * mm))
        elementos.extend(bloque)

    elementos.append(PageBreak())
    elementos.append(Paragraph("Clave de respuestas", estilo_titulo))
    elementos.append(Spacer(1, 6 * mm))
    for i, pregunta in enumerate(preguntas):
        tipo = pregunta.get("tipo")
        correcta = pregunta.get("correcta")
        if tipo == "relacionar" and isinstance(correcta, dict):
            texto_clave = "; ".join(f"{k} → {v}" for k, v in correcta.items())
        else:
            texto_clave = str(correcta)
        elementos.append(Paragraph(f"<b>{i+1}.</b> {texto_clave}", estilo_clave))
        elementos.append(Spacer(1, 2 * mm))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
