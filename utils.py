# -*- coding: utf-8 -*-
"""Funciones utilitarias generales: seguridad, lectura de PDF y niveles."""
import hashlib
import io
import PyPDF2


def hash_password(password):
    """Genera un hash SHA-256 de la contrasena."""
    return hashlib.sha256(password.encode()).hexdigest()


def extraer_texto_pdf(archivo, max_caracteres=3000):
    """Extrae texto de un PDF. Por defecto solo 3000 caracteres (uso rapido
    en el chat), pero la biblioteca de documentos pide mucho mas
    (ver documentos.py) para no perder la mayor parte del contenido."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(archivo.read()))
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text()
        return texto[:max_caracteres]
    except Exception:
        return None


def obtener_nivel(total):
    """Devuelve el nivel (texto + color) segun el total de preguntas hechas."""
    if total < 10:
        return "Principiante 🌱", "#6B7280"
    elif total < 50:
        return "Intermedio ⭐", "#D97706"
    elif total < 100:
        return "Avanzado 🔥", "#2563EB"
    else:
        return "Experto 👑", "#7C3AED"


def dividir_en_fragmentos(texto, tamano=900, solape=150):
    """Divide un texto largo (ej: un PDF de varias paginas) en fragmentos
    pequenos con algo de solape entre ellos, para poder buscar despues solo
    los fragmentos relevantes a una pregunta en vez de mandar todo el texto
    junto al tutor."""
    fragmentos = []
    inicio = 0
    n = len(texto)
    while inicio < n:
        fin = min(inicio + tamano, n)
        fragmentos.append(texto[inicio:fin])
        if fin == n:
            break
        inicio = fin - solape
    return fragmentos


def normalizar_latex(texto):
    """La IA a veces escribe formulas con \\[ \\] o \\( \\) en vez de $$ $$
    o $ $ (que es lo que el renderizador de Streamlit reconoce). Tambien a
    veces usa corchetes simples [ ] sin barra invertida, en su propia linea,
    como forma de 'destacar' una formula. Esto convierte todo eso al formato
    que Streamlit si reconoce, sin depender 100% de que la IA siga el
    formato pedido al pie de la letra."""
    if not texto:
        return texto
    texto = texto.replace("\\[", "$$").replace("\\]", "$$")
    texto = texto.replace("\\(", "$").replace("\\)", "$")

    import re

    def _convertir_linea(match):
        contenido = match.group(1).strip()
        return f"$${contenido}$$"

    # lineas que son SOLO una formula entre corchetes simples (ej: "[ v(t)=3t+1 ]")
    texto = re.sub(r'(?m)^\s*\[\s*(.+?)\s*\]\s*$', _convertir_linea, texto)

    # si una formula (con simbolo $) quedo atrapada dentro de un <h4> o <li>,
    # Streamlit no la renderiza ahi adentro. Quitamos esa etiqueta especifica
    # (solo cuando tiene una formula) para que el LaTeX si se muestre bien.
    texto = re.sub(r'<h4[^>]*>([^<]*\$[^<]*)</h4>', lambda m: f"\n**{m.group(1)}**\n", texto)
    texto = re.sub(r'<li>([^<]*\$[^<]*)</li>', lambda m: f"- {m.group(1)}\n", texto)

    return texto
