# -*- coding: utf-8 -*-
"""Todo lo relacionado a la IA del tutor: prompts base, personalizacion segun
el alumno (edad/grado/ciclo + perfil de progreso), y la actualizacion del
perfil despues de cada intercambio."""
import json
import streamlit as st
from groq import Groq

from database import obtener_perfil_alumno, guardar_perfil_alumno, buscar_fragmentos_relevantes

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

MODELO_TUTOR = "openai/gpt-oss-120b"  # antes: llama-3.3-70b-versatile (descontinuado por Groq en agosto 2026)
MODELO_RESUMEN = "openai/gpt-oss-20b"  # antes: llama-3.1-8b-instant (descontinuado por Groq en agosto 2026)


ESTRUCTURA_CLARA = """
IMPORTANTE - estructura visual clara (como una clase bien ordenada, no un parrafo corrido de texto):
- Si la pregunta tiene varias partes, metodos o conceptos distintos, separa cada uno con su propio encabezado: <h4 style='color:#00C9FF; margin-top:18px; margin-bottom:6px'>Nombre de la parte</h4>
- Cada paso va en SU PROPIA linea (usa saltos de linea reales entre pasos, nunca los pegues todos en un solo parrafo)
- Cuando enumeres varias cosas, usa una lista real: <ul style='margin:6px 0'><li>...</li></ul>
- Deja espacio entre secciones (no lo apretes todo junto)
- El resultado final de cada ejercicio va en su propio bloque, bien visible, al final de ese ejercicio (no mezclado con la explicacion)
"""

PROMPTS_BASE = {
    "Matematicas": """Eres Tu Profe de Confianza, un tutor de matematicas
para universitarios peruanos. Eres cercano, paciente y explicas paso a paso.
SIEMPRE usa este formato HTML en tus respuestas:
- Pasos numerados en verde: <span style='color:#92FE9D; font-weight:bold'>Paso 1:</span>
- Resultados finales en naranja: <span style='color:#F59E0B; font-weight:bold'>Resultado:</span>
- Conceptos importantes en azul: <span style='color:#00C9FF; font-weight:bold'>concepto</span>
Cuando escribas formulas usa LaTeX: $$formula$$
Explicas de forma simple con ejemplos de la vida peruana.
Cuando el usuario se equivoca lo animas y corriges con amabilidad.
""" + ESTRUCTURA_CLARA,

    "Ingles": """Eres Tu Profe de Confianza, un tutor de ingles
para universitarios peruanos. Eres cercano y motivador.
SIEMPRE usa este formato HTML en tus respuestas:
- Palabras en ingles en azul: <span style='color:#00C9FF; font-weight:bold'>word</span>
- Traduccion en espanol en verde: <span style='color:#92FE9D; font-weight:bold'>palabra</span>
- Pronunciacion en morado: <span style='color:#C084FC; font-weight:bold'>/pronun/</span>
- Ejemplos en naranja: <span style='color:#F59E0B'>example sentence</span>
Estructura SIEMPRE tus respuestas asi:
1. Palabra en ingles (azul)
2. Traduccion (verde)
3. Pronunciacion (morado)
4. Ejemplo (naranja)
Cada punto en su propia linea, con espacio entre ellos, nunca todo pegado en un parrafo.
Corriges errores con amabilidad.""",

    "Fisica": """Eres Tu Profe de Confianza, un tutor de fisica
para universitarios peruanos. Eres cercano, paciente y explicas paso a paso.
SIEMPRE usa este formato HTML en tus respuestas:
- Pasos numerados en verde: <span style='color:#92FE9D; font-weight:bold'>Paso 1:</span>
- Resultados finales (con unidades) en naranja: <span style='color:#F59E0B; font-weight:bold'>Resultado:</span>
- Conceptos y leyes fisicas en azul: <span style='color:#00C9FF; font-weight:bold'>concepto</span>
Cuando escribas formulas usa LaTeX: $$formula$$
SIEMPRE indica las unidades de cada resultado (N, m/s, J, etc.) y menciona que ley o principio fisico aplica.
Usa ejemplos cotidianos para explicar conceptos abstractos.
Cuando el usuario se equivoca lo animas y corriges con amabilidad.
""" + ESTRUCTURA_CLARA,

    "Quimica General": """Eres Tu Profe de Confianza, un tutor de quimica general
para universitarios peruanos (enfocado en estudiantes de carreras de salud e ingenieria).
Eres cercano, paciente y explicas paso a paso.
SIEMPRE usa este formato HTML en tus respuestas:
- Pasos numerados en verde: <span style='color:#92FE9D; font-weight:bold'>Paso 1:</span>
- Resultados finales en naranja: <span style='color:#F59E0B; font-weight:bold'>Resultado:</span>
- Conceptos y nombres de compuestos en azul: <span style='color:#00C9FF; font-weight:bold'>concepto</span>
Cuando escribas formulas quimicas o ecuaciones usa LaTeX o notacion clara: $$formula$$
Balancea ecuaciones quimicas mostrando cada paso, y explica estequiometria con cuidado.
Cuando el usuario se equivoca lo animas y corriges con amabilidad.
""" + ESTRUCTURA_CLARA,

    "Quimica Organica": """Eres Tu Profe de Confianza, un tutor de quimica organica
para universitarios peruanos (enfocado en estudiantes de medicina y ciencias de la salud).
Eres cercano, paciente y explicas paso a paso.
SIEMPRE usa este formato HTML en tus respuestas:
- Pasos numerados en verde: <span style='color:#92FE9D; font-weight:bold'>Paso 1:</span>
- Resultados/productos de reaccion en naranja: <span style='color:#F59E0B; font-weight:bold'>Resultado:</span>
- Grupos funcionales y nombres IUPAC en azul: <span style='color:#00C9FF; font-weight:bold'>concepto</span>
Explica mecanismos de reaccion paso a paso, y cuando sea relevante menciona nombres IUPAC y grupos funcionales involucrados.
Cuando el usuario se equivoca lo animas y corriges con amabilidad.
""" + ESTRUCTURA_CLARA,
}

SUGERENCIAS = {
    "Matematicas": [
        "Que es una integral?",
        "Explicame las derivadas",
        "Como resuelvo una ecuacion cuadratica?",
        "Que es el limite de una funcion?"
    ],
    "Ingles": [
        "Como me presento en ingles?",
        "Ensename los verbos mas usados",
        "Como pido la hora en ingles?",
        "Corrige mi pronunciacion"
    ],
    "Fisica": [
        "Explicame las leyes de Newton",
        "Como calculo la velocidad y aceleracion?",
        "Que es la energia cinetica y potencial?",
        "Ayudame con un problema de cinematica"
    ],
    "Quimica General": [
        "Como balanceo una ecuacion quimica?",
        "Explicame la tabla periodica",
        "Que es la estequiometria?",
        "Como calculo la molaridad de una solucion?"
    ],
    "Quimica Organica": [
        "Que son los grupos funcionales?",
        "Explicame la nomenclatura IUPAC",
        "Como identifico un mecanismo de reaccion?",
        "Diferencia entre alcanos, alquenos y alquinos"
    ],
}


def _contexto_alumno(usuario, perfil):
    """Arma el bloque de texto que se inyecta al system prompt con todo lo
    que sabemos del alumno: datos basicos + progreso."""
    partes = []

    edad = usuario.get("edad")
    grado = usuario.get("grado")
    ciclo = usuario.get("ciclo")
    datos_basicos = []
    if edad:
        datos_basicos.append(f"tiene {edad} anios")
    if grado:
        datos_basicos.append(f"esta en {grado}")
    if ciclo:
        datos_basicos.append(f"ciclo {ciclo}")
    if datos_basicos:
        partes.append("El estudiante " + ", ".join(datos_basicos) + ". Adapta el nivel de vocabulario y la complejidad de los ejemplos a esto.")

    dominados = perfil.get("temas_dominados") or []
    dificiles = perfil.get("temas_dificiles") or []
    if dominados:
        partes.append("Temas que el alumno ya domina (no los expliques desde cero, puedes referenciarlos): " + ", ".join(dominados) + ".")
    if dificiles:
        partes.append("Temas donde el alumno ha mostrado dificultad (ve con mas calma y refuerza con ejemplos extra): " + ", ".join(dificiles) + ".")
    if perfil.get("ultimo_resumen"):
        partes.append("Nota de la ultima sesion: " + perfil["ultimo_resumen"])

    if not partes:
        return ""
    return "\n\nCONTEXTO DEL ALUMNO (usalo para personalizar, no lo repitas literalmente):\n" + "\n".join(partes)


def construir_system_prompt(modo, usuario, texto_pdf="", curso_biblioteca=None, pregunta=""):
    """Arma el system prompt final: base de la materia + contexto del alumno
    (edad/grado/ciclo + perfil de progreso) + fragmentos relevantes de la
    biblioteca del curso elegido segun la pregunta actual (si hay) + PDF
    subido en el momento (si hay)."""
    base = PROMPTS_BASE.get(modo, PROMPTS_BASE["Matematicas"])

    perfil = obtener_perfil_alumno(usuario["id"], modo)
    prompt = base + _contexto_alumno(usuario, perfil)

    if curso_biblioteca and pregunta:
        fragmentos = buscar_fragmentos_relevantes(modo, curso_biblioteca, pregunta)
        if fragmentos:
            prompt += f"\n\nFragmentos relevantes del material del curso '{curso_biblioteca}' (usalos como fuente principal si aplican a la pregunta del alumno):\n{fragmentos}"

    if texto_pdf:
        prompt += f"\n\nEl estudiante ha subido este documento en esta conversacion:\n{texto_pdf}"

    return prompt


def obtener_sugerencias(modo):
    return SUGERENCIAS.get(modo, SUGERENCIAS["Matematicas"])


def responder_tutor(system_prompt, historial):
    """Llama al modelo principal del tutor con el historial reciente."""
    respuesta = client.chat.completions.create(
        model=MODELO_TUTOR,
        messages=[{"role": "system", "content": system_prompt}] + historial[-10:]
    )
    return respuesta.choices[0].message.content


def actualizar_perfil_alumno(usuario_id, modo, pregunta, respuesta):
    """Despues de cada intercambio, usa un modelo pequeno para extraer que
    tema se toco y si el alumno mostro dificultad, y actualiza su perfil.
    Esto es lo que le da 'memoria' al tutor entre sesiones. Si algo falla
    (limite de uso, respuesta invalida, etc.) simplemente no actualiza nada
    y el chat sigue funcionando normal."""
    try:
        perfil_actual = obtener_perfil_alumno(usuario_id, modo)

        prompt_resumen = f"""Analiza este intercambio entre un tutor y un alumno de {modo}.
Pregunta del alumno: {pregunta}
Respuesta del tutor: {respuesta}

Perfil actual del alumno (JSON):
{json.dumps(perfil_actual, ensure_ascii=False)}

Devuelve SOLO un JSON (sin texto extra, sin markdown) con el perfil actualizado,
con este formato exacto:
{{
  "temas_dominados": ["lista de temas cortos que el alumno parece manejar bien"],
  "temas_dificiles": ["lista de temas cortos donde el alumno mostro confusion o error"],
  "nivel_estimado": "principiante" o "intermedio" o "avanzado",
  "ultimo_resumen": "una frase corta (max 15 palabras) sobre como le fue en este intercambio"
}}
Combina la informacion nueva con la que ya tenia el alumno, sin perder temas anteriores.
Manten cada lista con maximo 8 elementos (si se pasa, elimina los mas antiguos/menos relevantes)."""

        resultado = client.chat.completions.create(
            model=MODELO_RESUMEN,
            messages=[{"role": "user", "content": prompt_resumen}],
            response_format={"type": "json_object"}
        )
        nuevo_perfil = json.loads(resultado.choices[0].message.content)
        guardar_perfil_alumno(usuario_id, modo, nuevo_perfil)
    except Exception:
        # La app nunca debe romperse por esto: si falla, el chat sigue normal
        # y el perfil simplemente no se actualiza en este turno.
        pass


def generar_formulario(modo, usuario, curso, material_curso):
    """Genera un 'formulario' (cheat-sheet) de formulas clave de un curso,
    como tarjetas cortas y numeradas (no un texto largo en parrafos),
    priorizando los temas donde el alumno tiene mas dificultad segun su
    perfil. Devuelve una lista de tarjetas ya estructurada, el diseño
    (cuadricula de tarjetas) lo controla el codigo, no la IA - asi el
    resultado siempre se ve ordenado y consistente."""
    perfil = obtener_perfil_alumno(usuario["id"], modo)
    dificiles = perfil.get("temas_dificiles") or []
    dominados = perfil.get("temas_dominados") or []

    instruccion_nivel = ""
    if dificiles:
        instruccion_nivel += f"\nEl alumno tiene dificultad en: {', '.join(dificiles)}. Para esos temas, agrega una 'nota' corta (max 15 palabras) explicando cuando usar la formula."
    if dominados:
        instruccion_nivel += f"\nEl alumno ya domina: {', '.join(dominados)}. Para esos temas, deja 'nota' vacio (solo la formula, sin explicacion extra)."

    prompt = f"""A partir de este material real del curso '{curso}' ({modo}), extrae las formulas y
conceptos clave que un alumno necesitaria tener a la mano para un examen de este curso.

Devuelve SOLO un JSON (sin texto extra, sin markdown) con este formato exacto:
{{
  "tarjetas": [
    {{"numero": 1, "titulo": "Nombre corto del concepto (max 6 palabras)", "formula": "codigo LaTeX SIN simbolos de dolar, ej: a^n \\\\cdot a^m = a^{{n+m}}", "nota": "explicacion de una linea o vacio si el alumno ya domina esto"}}
  ]
}}
Maximo 16 tarjetas. Cada tarjeta debe ser corta y directa (como una tarjeta de estudio, NO una clase completa).
{instruccion_nivel}

Material real del curso (usalo como fuente principal, no inventes formulas que no esten relacionadas):
{material_curso}
"""
    respuesta = client.chat.completions.create(
        model=MODELO_TUTOR,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2500,
        response_format={"type": "json_object"}
    )
    try:
        return json.loads(respuesta.choices[0].message.content).get("tarjetas", [])
    except Exception:
        return []
