# -*- coding: utf-8 -*-
"""Pagina de Chat: aqui es donde el alumno conversa con el tutor. Ahora usa
tutor_ai para construir un prompt personalizado (edad/grado/ciclo + progreso)
y actualiza el perfil del alumno despues de cada respuesta.

Layout: columna principal (chat) + columna lateral fija a la derecha
(Curso/Formulario/Archivo), que se queda visible aunque el chat crezca
mucho, igual que el panel "Studio" de NotebookLM."""
import streamlit as st

from database import guardar_conversacion, cargar_conversaciones, obtener_estadisticas, verificar_logros, listar_cursos
from tutor_ai import construir_system_prompt, obtener_sugerencias, responder_tutor, actualizar_perfil_alumno
from utils import extraer_texto_pdf
from materias_data import EMOJI_MATERIA
from formulario import renderizar_generador_formulario


def _panel_lateral(usuario, modo):
    """Panel de la derecha: Curso, Formulario, Archivo y por que somos
    diferentes. Se queda fijo en pantalla (position: sticky) mientras el
    chat de la izquierda crece."""
    st.markdown("""
    <style>
    div[data-testid="column"]:nth-of-type(2) {
        position: sticky;
        top: 4rem;
        align-self: flex-start;
    }
    </style>
    """, unsafe_allow_html=True)

    emoji_modo = EMOJI_MATERIA.get(modo, "📘")
    st.markdown(f"<div style='padding:6px 0 14px 0; text-align:center'><span style='color:#00C9FF; font-weight:bold'>{emoji_modo} {modo}</span></div>", unsafe_allow_html=True)

    curso_elegido = None
    cursos_disponibles = listar_cursos(modo)
    if cursos_disponibles:
        with st.popover("📚 Curso", use_container_width=True):
            seleccion = st.selectbox(
                "Elige un curso de tu biblioteca",
                ["Sin curso especifico"] + cursos_disponibles,
                key=f"curso_chat_{modo}",
                help="El tutor usara tus documentos de ese curso como contexto"
            )
            curso_elegido = None if seleccion == "Sin curso especifico" else seleccion

    with st.popover("📋 Formulario", use_container_width=True):
        if curso_elegido:
            renderizar_generador_formulario(usuario, modo=modo, key_prefix=f"popover_{modo}_{curso_elegido}_", curso_fijo=curso_elegido)
        else:
            st.info("Primero elige un curso en '📚 Curso' para poder generar su formulario.")

    with st.popover("📎 Archivo", use_container_width=True):
        archivo = st.file_uploader("PDF o imagen", type=["pdf", "png", "jpg", "jpeg"], key=f"archivo_chat_{modo}")
        if archivo:
            st.success(f"Cargado: {archivo.name}")
            st.session_state.archivo = archivo
        else:
            st.session_state.archivo = None

    with st.expander("✨ Por que es diferente"):
        st.markdown(
            "- 🎯 Personalizado a tu edad y carrera\n"
            "- 🧠 Recuerda tu progreso y se adapta a lo que te cuesta\n"
            "- 📚 Usa TUS documentos reales, no info generica\n"
            "- 📝 Examenes basados en tus examenes pasados"
        )

    return curso_elegido


def mostrar_chat(usuario, modo):
    col_chat, col_panel = st.columns([2.3, 1])

    with col_panel:
        curso_elegido = _panel_lateral(usuario, modo)

    with col_chat:
        if "historial" not in st.session_state or st.session_state.get("modo_actual") != modo:
            st.session_state.historial = cargar_conversaciones(usuario["id"], modo)
            st.session_state.modo_actual = modo

        texto_pdf = ""
        if st.session_state.get("archivo"):
            if st.session_state.archivo.type == "application/pdf":
                texto_pdf = extraer_texto_pdf(st.session_state.archivo)
                if texto_pdf:
                    st.info("PDF cargado - puedes preguntarme sobre el contenido")

        sugerencias = obtener_sugerencias(modo)

        def _procesar_turno(pregunta):
            system_prompt = construir_system_prompt(modo, usuario, texto_pdf, curso_biblioteca=curso_elegido, pregunta=pregunta)
            with st.spinner("Tu profe esta pensando..."):
                texto = responder_tutor(system_prompt, st.session_state.historial)
            st.session_state.historial.append({"role": "assistant", "content": texto})
            guardar_conversacion(usuario["id"], pregunta, texto, modo)
            actualizar_perfil_alumno(usuario["id"], modo, pregunta, texto)
            stats = obtener_estadisticas(usuario["id"])
            nuevos_logros = verificar_logros(usuario["id"], stats)
            return texto, nuevos_logros

        if not st.session_state.historial:
            with st.chat_message("assistant"):
                if modo == "Matematicas":
                    st.write("Hola! Soy tu profe de confianza. Que tema de matematicas te esta costando?")
                else:
                    st.write("Hola! Soy tu profe de confianza. En que te puedo ayudar hoy?")

            st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.5); font-size:0.9em; margin-top:10px'>Preguntas frecuentes:</p>", unsafe_allow_html=True)
            colA, colB = st.columns(2)
            for i, sugerencia in enumerate(sugerencias):
                with colA if i % 2 == 0 else colB:
                    if st.button(sugerencia, use_container_width=True, key=f"sug_{i}"):
                        st.session_state.historial.append({"role": "user", "content": sugerencia})
                        _procesar_turno(sugerencia)
                        st.rerun()

        for mensaje in st.session_state.historial:
            rol = mensaje["role"]
            with st.chat_message(rol):
                st.markdown(mensaje["content"], unsafe_allow_html=True)

        if prompt := st.chat_input("Escribe tu pregunta aqui..."):
            with st.chat_message("user"):
                st.markdown(prompt, unsafe_allow_html=True)

            st.session_state.historial.append({"role": "user", "content": prompt})
            texto, nuevos_logros = _procesar_turno(prompt)

            for logro in nuevos_logros:
                st.balloons()
                st.success(f"🏆 Nuevo logro: {logro['emoji']} {logro['nombre']} - {logro['descripcion']}")

            with st.chat_message("assistant"):
                st.markdown(texto, unsafe_allow_html=True)
