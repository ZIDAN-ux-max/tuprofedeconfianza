# -*- coding: utf-8 -*-
"""Formulario (cheat-sheet): genera un resumen de formulas y conceptos
clave de un curso, usando el material real subido a la biblioteca y
priorizando los temas donde el alumno tiene mas dificultad."""
import streamlit as st

from database import listar_cursos, obtener_muestra_estilo_curso
from tutor_ai import generar_formulario
from materias_data import materias_de_carrera


def mostrar_formulario(usuario):
    st.markdown("<h1 style='text-align:center;'>📋 Formulario</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Un resumen de formulas para repasar rapido, generado de tus documentos y ajustado a tu nivel</p>", unsafe_allow_html=True)
    st.divider()

    materias_alumno = materias_de_carrera(usuario.get("carrera"))
    modo = st.selectbox("Materia", materias_alumno, key="form_materia")

    cursos_disponibles = listar_cursos(modo)
    if not cursos_disponibles:
        st.info(f"Todavia no hay documentos de {modo} en tu biblioteca. Sube algunos en 'Documentos' primero para poder generar un formulario.")
        return

    curso = st.selectbox("Curso", cursos_disponibles, key="form_curso")

    if st.button("✨ Generar formulario", use_container_width=True):
        with st.spinner("Revisando tu material y armando el formulario..."):
            material = obtener_muestra_estilo_curso(modo, curso, limite_caracteres=15000)
            if not material:
                st.warning("No se encontro material suficiente de este curso.")
            else:
                formulario_html = generar_formulario(modo, usuario, curso, material)
                st.session_state["ultimo_formulario"] = formulario_html
                st.session_state["ultimo_formulario_curso"] = curso

    if st.session_state.get("ultimo_formulario"):
        st.divider()
        st.markdown(f"<h3 style='color:#92FE9D'>📋 {st.session_state.get('ultimo_formulario_curso')}</h3>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:20px;'>{st.session_state['ultimo_formulario']}</div>",
            unsafe_allow_html=True
        )
        st.download_button(
            "⬇️ Descargar como texto",
            data=st.session_state["ultimo_formulario"],
            file_name=f"formulario_{st.session_state.get('ultimo_formulario_curso', 'curso')}.txt",
            use_container_width=True
        )
