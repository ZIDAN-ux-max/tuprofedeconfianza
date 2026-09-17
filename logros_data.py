# -*- coding: utf-8 -*-
"""Catalogo de logros disponibles en la aplicacion. Cada logro se revisa
contra el dict que arma database.obtener_stats_logros() (ver alli que
significa cada 'condicion'): senales de chat, tareas diarias, documentos
subidos, plan de estudio, calendario, horario de estudio y rango."""

LOGROS_DISPONIBLES = [
    # ---- Chat ----
    {"nombre": "Primera Pregunta", "descripcion": "Hiciste tu primera pregunta", "emoji": "🎯", "condicion": "total", "valor": 1, "puntos": 5},
    {"nombre": "Constante", "descripcion": "10 preguntas en total", "emoji": "📚", "condicion": "total", "valor": 10, "puntos": 15},
    {"nombre": "Dedicado", "descripcion": "50 preguntas en total", "emoji": "🏆", "condicion": "total", "valor": 50, "puntos": 30},
    {"nombre": "Centenario", "descripcion": "100 preguntas en total", "emoji": "💯", "condicion": "total", "valor": 100, "puntos": 50},
    {"nombre": "Perseverante", "descripcion": "200 preguntas en total", "emoji": "💪", "condicion": "total", "valor": 200, "puntos": 75},
    {"nombre": "Estudioso del dia", "descripcion": "5 preguntas en un dia", "emoji": "⚡", "condicion": "hoy", "valor": 5, "puntos": 10},
    {"nombre": "Semana Productiva", "descripcion": "20 preguntas en la semana", "emoji": "📈", "condicion": "semana", "valor": 20, "puntos": 20},
    {"nombre": "Madrugador", "descripcion": "Estudio antes de las 7am", "emoji": "⏰", "condicion": "hora", "valor": 7, "puntos": 10},
    {"nombre": "Noctambulo", "descripcion": "Estudio despues de las 11pm", "emoji": "🌙", "condicion": "hora", "valor": 23, "puntos": 10},

    # ---- Racha ----
    {"nombre": "Racha de 3", "descripcion": "3 dias seguidos estudiando", "emoji": "🔥", "condicion": "racha", "valor": 3, "puntos": 10},
    {"nombre": "Racha de 7", "descripcion": "7 dias seguidos estudiando", "emoji": "🔥", "condicion": "racha", "valor": 7, "puntos": 25},
    {"nombre": "Racha de 30", "descripcion": "30 dias seguidos estudiando", "emoji": "🔥", "condicion": "racha", "valor": 30, "puntos": 60},

    # ---- Documentos / Biblioteca ----
    {"nombre": "Primer Aporte", "descripcion": "Subiste tu primer documento a la biblioteca", "emoji": "📤", "condicion": "documentos_subidos", "valor": 1, "puntos": 10},
    {"nombre": "Bibliofilo", "descripcion": "Subiste 5 documentos a la biblioteca", "emoji": "📖", "condicion": "documentos_subidos", "valor": 5, "puntos": 20},
    {"nombre": "Curador", "descripcion": "Subiste 15 documentos a la biblioteca", "emoji": "🗂️", "condicion": "documentos_subidos", "valor": 15, "puntos": 40},
    {"nombre": "Plan Armado", "descripcion": "Generaste tu plan de estudio a partir del Silabo/Ficha", "emoji": "🗺️", "condicion": "plan_estudio", "valor": 1, "puntos": 15},

    # ---- Mi Dia / Tareas ----
    {"nombre": "Primera Tarea", "descripcion": "Completaste tu primera tarea del dia", "emoji": "✅", "condicion": "tareas_completadas", "valor": 1, "puntos": 5},
    {"nombre": "Cumplidor", "descripcion": "Completaste 10 tareas en total", "emoji": "✔️", "condicion": "tareas_completadas", "valor": 10, "puntos": 20},
    {"nombre": "Disciplinado", "descripcion": "Completaste 50 tareas en total", "emoji": "🎖️", "condicion": "tareas_completadas", "valor": 50, "puntos": 45},
    {"nombre": "Dia Perfecto", "descripcion": "Completaste todas las tareas que agregaste en un dia", "emoji": "🌟", "condicion": "dia_perfecto", "valor": 1, "puntos": 15},

    # ---- Calendario / Horario de estudio ----
    {"nombre": "Organizado", "descripcion": "Agregaste tu primer examen o entrega al calendario", "emoji": "🗓️", "condicion": "eventos_calendario", "valor": 1, "puntos": 10},
    {"nombre": "Planificador", "descripcion": "Generaste tu horario de estudio por primera vez", "emoji": "🧭", "condicion": "horario_generado", "valor": 1, "puntos": 15},
    {"nombre": "Al Pie del Cañon", "descripcion": "Seguiste un bloque de estudio programado", "emoji": "📌", "condicion": "bloque_seguido", "valor": 1, "puntos": 15},

    # ---- Rango ----
    {"nombre": "Rumbo al Oro", "descripcion": "Alcanzaste el rango Oro", "emoji": "🥇", "condicion": "tier_alcanzado", "valor": 2, "puntos": 25},
    {"nombre": "Alto Nivel", "descripcion": "Alcanzaste el rango Diamante", "emoji": "💎", "condicion": "tier_alcanzado", "valor": 3, "puntos": 40},
]
