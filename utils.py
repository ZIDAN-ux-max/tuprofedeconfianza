# -*- coding: utf-8 -*-
"""Funciones utilitarias generales: seguridad, lectura de PDF y niveles."""
import hashlib
import io
import PyPDF2


def hash_password(password):
    """Genera un hash SHA-256 de la contrasena."""
    return hashlib.sha256(password.encode()).hexdigest()


def extraer_texto_pdf(archivo):
    """Extrae hasta 3000 caracteres de texto de un PDF subido por el alumno."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(archivo.read()))
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text()
        return texto[:3000]
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
