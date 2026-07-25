# -*- coding: utf-8 -*-
"""Catalogo central de materias y carreras.
Todo lo que antes estaba quemado como 'Matematicas'/'Ingles' en varios
archivos ahora sale de aqui, para que agregar/quitar materias o carreras
sea cambiar esta lista, no buscar en todo el codigo."""

MATERIAS_DISPONIBLES = ["Matematicas", "Ingles", "Fisica", "Quimica General", "Quimica Organica"]

EMOJI_MATERIA = {
    "Matematicas": "📐",
    "Ingles": "🇺🇸",
    "Fisica": "⚛️",
    "Quimica General": "🧪",
    "Quimica Organica": "🧬",
}

# Que materias ve cada carrera en el selector del Chat. "Otro" ve todas.
CARRERAS_MATERIAS = {
    "Medicina": ["Quimica General", "Quimica Organica", "Fisica", "Ingles"],
    "Ingenieria": ["Matematicas", "Fisica", "Quimica General", "Ingles"],
    "Ciencias": ["Matematicas", "Fisica", "Quimica General", "Quimica Organica", "Ingles"],
    "Otro / Todas las materias": MATERIAS_DISPONIBLES,
}

CARRERAS_DISPONIBLES = list(CARRERAS_MATERIAS.keys())


def materias_de_carrera(carrera):
    """Devuelve la lista de materias que le corresponden a una carrera.
    Si la carrera no esta en el catalogo (o no se especifico), devuelve
    todas las materias por defecto."""
    return CARRERAS_MATERIAS.get(carrera, MATERIAS_DISPONIBLES)
