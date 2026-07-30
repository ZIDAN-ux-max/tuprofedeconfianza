# -*- coding: utf-8 -*-
"""Formulario (cheat-sheet): genera un resumen de formulas y conceptos
clave de un curso, usando el material real subido a la biblioteca y
priorizando los temas donde el alumno tiene mas dificultad.

renderizar_generador_formulario() es la parte reutilizable (se usa tanto
en la pagina completa 'Formulario' como en el panel flotante del Chat).
"""
import streamlit as st

from database import listar_cursos, obtener_muestra_estilo_curso
from tutor_ai import generar_formulario
from materias_data import materias_de_carrera


def renderizar_generador_formulario(usuario, modo=None, key_prefix="", curso_fijo=None):
    """Dibuja el selector de curso + boton de generar + resultado.
    Si 'modo' ya viene definido (ej: desde el Chat, que ya sabe la materia
    actual), no se vuelve a pedir la materia - se va directo al curso.
    Si 'curso_fijo' viene definido (ej: el mismo curso ya elegido en el
    popover de Curso del Chat), se usa ese directamente sin volver a
    preguntar - asi el Formulario siempre coincide con el curso activo."""
    if modo is None:
        materias_alumno = materias_de_carrera(usuario.get("carrera"))
        modo = st.selectbox("Materia", materias_alumno, key=f"{key_prefix}form_materia")

    if curso_fijo:
        curso = curso_fijo
        st.markdown(f"<p style='color:rgba(255,255,255,0.6); font-size:0.85em'>Curso: <strong style='color:#00C9FF'>{curso}</strong></p>", unsafe_allow_html=True)
    else:
        cursos_disponibles = listar_cursos(modo)
        if not cursos_disponibles:
            st.info(f"Todavia no hay documentos de {modo} en tu biblioteca. Sube algunos en 'Documentos' primero.")
            return
        curso = st.selectbox("Curso", cursos_disponibles, key=f"{key_prefix}form_curso")

    if st.button("✨ Generar formulario", key=f"{key_prefix}form_generar", use_container_width=True):
        with st.spinner("Revisando tu material y armando el formulario..."):
            material = obtener_muestra_estilo_curso(modo, curso, limite_caracteres=15000)
            if not material:
                st.warning("No se encontro material suficiente de este curso.")
            else:
                formulario_html = generar_formulario(modo, usuario, curso, material)
                st.session_state[f"{key_prefix}ultimo_formulario"] = formulario_html
                st.session_state[f"{key_prefix}ultimo_formulario_curso"] = curso

    if st.session_state.get(f"{key_prefix}ultimo_formulario"):
        st.divider()
        curso_mostrado = st.session_state.get(f'{key_prefix}ultimo_formulario_curso')
        st.markdown(f"<h4 style='color:#92FE9D'>📋 {curso_mostrado}</h4>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:16px;'>{st.session_state[f'{key_prefix}ultimo_formulario']}</div>",
            unsafe_allow_html=True
        )
        st.download_button(
            "⬇️ Descargar como texto",
            data=st.session_state[f"{key_prefix}ultimo_formulario"],
            file_name=f"formulario_{curso_mostrado}.txt",
            key=f"{key_prefix}form_descargar",
            use_container_width=True
        )


def mostrar_formulario(usuario):
    """Pagina completa de Formulario (accesible desde el menu lateral)."""
    st.markdown("<h1 style='text-align:center;'>📋 Formulario</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Un resumen de formulas para repasar rapido, generado de tus documentos y ajustado a tu nivel</p>", unsafe_allow_html=True)
    st.divider()
    renderizar_generador_formulario(usuario)
