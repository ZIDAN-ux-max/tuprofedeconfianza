# -*- coding: utf-8 -*-
"""Genera el Formulario (cheat-sheet) como PDF descargable, con las formulas
matematicas renderizadas visualmente (no como texto LaTeX crudo). Se separa
de formulario.py porque usa librerias pesadas (matplotlib, reportlab) que
solo hacen falta para este caso puntual."""
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors


def _render_formula_imagen(formula_latex):
    """Convierte una formula en codigo LaTeX a una imagen PNG (matplotlib
    'mathtext' entiende un subconjunto amplio de LaTeX: fracciones,
    exponentes, subindices, letras griegas, raices, etc. - sin necesitar
    una instalacion completa de LaTeX). Si la formula usa algo que
    mathtext no soporta, se devuelve como texto plano en vez de fallar."""
    formula_limpia = (formula_latex or "").strip().strip("$")
    if not formula_limpia:
        return None
    try:
        fig = plt.figure(figsize=(6, 1.1))
        fig.patch.set_alpha(0)
        fig.text(0.5, 0.5, f"${formula_limpia}$", fontsize=22, ha="center", va="center", color="#1a1a2e")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=170, transparent=True, bbox_inches="tight", pad_inches=0.08)
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass
        # Si mathtext no pudo interpretar el LaTeX, se muestra el texto tal cual
        try:
            fig = plt.figure(figsize=(6, 1.1))
            fig.patch.set_alpha(0)
            fig.text(0.5, 0.5, formula_limpia, fontsize=16, ha="center", va="center", color="#1a1a2e")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=170, transparent=True, bbox_inches="tight", pad_inches=0.08)
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception:
            return None


def generar_pdf_formulario(curso, materia, tarjetas):
    """Arma el PDF completo del formulario: titulo, y una tarjeta por cada
    formula (numero, titulo, formula renderizada como imagen, nota).
    Devuelve un BytesIO listo para pasarle a st.download_button."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=18 * mm, bottomMargin=15 * mm, leftMargin=15 * mm, rightMargin=15 * mm
    )
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle("TituloFormulario", parent=estilos["Title"], fontSize=20, textColor=colors.HexColor("#0F0C29"))
    estilo_subtitulo = ParagraphStyle("Subtitulo", parent=estilos["Normal"], fontSize=11, textColor=colors.HexColor("#555577"), alignment=TA_CENTER)
    estilo_card_titulo = ParagraphStyle("CardTitulo", parent=estilos["Normal"], fontSize=12, textColor=colors.HexColor("#0F0C29"), leading=14)
    estilo_nota = ParagraphStyle("Nota", parent=estilos["Normal"], fontSize=9, textColor=colors.HexColor("#666688"), leading=11)

    elementos = [
        Paragraph(f"Formulario - {curso}", estilo_titulo),
        Paragraph(f"{materia} · Generado con Tu Profe de Confianza", estilo_subtitulo),
        Spacer(1, 10 * mm),
    ]

    filas = []
    fila_actual = []
    for i, tarjeta in enumerate(tarjetas):
        numero = tarjeta.get("numero", i + 1)
        titulo = tarjeta.get("titulo", "")
        formula = tarjeta.get("formula", "")
        nota = tarjeta.get("nota", "")

        contenido_celda = [Paragraph(f"<b>{numero}. {titulo}</b>", estilo_card_titulo)]
        img_buf = _render_formula_imagen(formula)
        if img_buf:
            contenido_celda.append(Spacer(1, 2 * mm))
            contenido_celda.append(Image(img_buf, width=70 * mm, height=13 * mm, kind="proportional"))
        if nota:
            contenido_celda.append(Spacer(1, 1 * mm))
            contenido_celda.append(Paragraph(nota, estilo_nota))

        fila_actual.append(contenido_celda)
        if len(fila_actual) == 2:
            filas.append(fila_actual)
            fila_actual = []
    if fila_actual:
        fila_actual.append("")
        filas.append(fila_actual)

    if filas:
        tabla = Table(filas, colWidths=[88 * mm, 88 * mm])
        tabla.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccce0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0f0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)
    return buffer
