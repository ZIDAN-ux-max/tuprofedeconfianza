# -*- coding: utf-8 -*-
"""Pagina de Chat: aqui es donde el alumno conversa con el tutor. Ahora usa
tutor_ai para construir un prompt personalizado (edad/grado/ciclo + progreso)
y actualiza el perfil del alumno despues de cada respuesta."""
import streamlit as st
import textwrap

from database import guardar_conversacion, cargar_conversaciones, obtener_estadisticas, verificar_logros, listar_cursos
from tutor_ai import construir_system_prompt, obtener_sugerencias, responder_tutor, actualizar_perfil_alumno
from utils import extraer_texto_pdf


def mostrar_chat(usuario, modo):
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.image("imagen2.png", use_container_width=True)

    st.markdown(textwrap.dedent(f"""
    <div style='text-align:center; padding:10px 0'>
        <span style='font-size:1.1em; color:rgba(255,255,255,0.7)'>
        Estudiando: <strong style='color:#00C9FF'>{"📐 Matematicas" if modo == "Matematicas" else "🇺🇸 Ingles"}</strong>
        </span>
    </div>
    """), unsafe_allow_html=True)

    cursos_disponibles = listar_cursos(modo)
    curso_elegido = None
    if cursos_disponibles:
        curso_elegido = st.selectbox(
            "📚 Curso especifico (opcional, usa tus documentos subidos como contexto)",
            ["Sin curso especifico"] + cursos_disponibles,
            key=f"curso_chat_{modo}"
        )
        if curso_elegido == "Sin curso especifico":
            curso_elegido = None

    st.divider()

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
                st.write("Hola! Soy tu profe de confianza. En que nivel de ingles estas?")

        st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.5); font-size:0.9em; margin-top:10px'>Preguntas frecuentes:</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        for i, sugerencia in enumerate(sugerencias):
            with col1 if i % 2 == 0 else col2:
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
