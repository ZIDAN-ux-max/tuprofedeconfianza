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
