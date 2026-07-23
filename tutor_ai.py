# -*- coding: utf-8 -*-
"""Todo lo relacionado a la IA del tutor: prompts base, personalizacion segun
el alumno (edad/grado/ciclo + perfil de progreso), y la actualizacion del
perfil despues de cada intercambio."""
import json
import streamlit as st
from groq import Groq

from database import obtener_perfil_alumno, guardar_perfil_alumno, buscar_fragmentos_relevantes

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

MODELO_TUTOR = "llama-3.3-70b-versatile"
MODELO_RESUMEN = "llama-3.1-8b-instant"  # modelo pequeno y barato solo para resumir progreso


PROMPT_BASE_MATEMATICAS = """Eres Tu Profe de Confianza, un tutor de matematicas
para universitarios peruanos. Eres cercano, paciente y explicas paso a paso.
SIEMPRE usa este formato HTML en tus respuestas:
- Pasos numerados en verde: <span style='color:#92FE9D; font-weight:bold'>Paso 1:</span>
- Resultados finales en naranja: <span style='color:#F59E0B; font-weight:bold'>Resultado:</span>
- Conceptos importantes en azul: <span style='color:#00C9FF; font-weight:bold'>concepto</span>
Cuando escribas formulas usa LaTeX: $$formula$$
Explicas de forma simple con ejemplos de la vida peruana.
Cuando el usuario se equivoca lo animas y corriges con amabilidad."""

PROMPT_BASE_INGLES = """Eres Tu Profe de Confianza, un tutor de ingles
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
Corriges errores con amabilidad."""

SUGERENCIAS_MATEMATICAS = [
    "Que es una integral?",
    "Explicame las derivadas",
    "Como resuelvo una ecuacion cuadratica?",
    "Que es el limite de una funcion?"
]

SUGERENCIAS_INGLES = [
    "Como me presento en ingles?",
    "Ensename los verbos mas usados",
    "Como pido la hora en ingles?",
    "Corrige mi pronunciacion"
]


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
    base = PROMPT_BASE_MATEMATICAS if modo == "Matematicas" else PROMPT_BASE_INGLES

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
    return SUGERENCIAS_MATEMATICAS if modo == "Matematicas" else SUGERENCIAS_INGLES


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
