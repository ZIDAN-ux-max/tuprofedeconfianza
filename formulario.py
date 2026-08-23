# -*- coding: utf-8 -*-
"""Formulario (cheat-sheet): genera tarjetas cortas y numeradas con las
formulas clave de un curso, usando el material real de la biblioteca y
priorizando los temas donde el alumno tiene mas dificultad.

El diseno (cuadricula de tarjetas) lo controla este archivo, no la IA -
asi el resultado siempre se ve ordenado y consistente, sin depender de
que el modelo "se acuerde" de ser breve.

renderizar_generador_formulario() es la parte reutilizable (se usa tanto
en la pagina completa 'Formulario' como en el panel del Chat).
"""
import streamlit as st

from database import listar_cursos, obtener_muestra_estilo_curso
from tutor_ai import generar_formulario
from materias_data import materias_de_carrera
from pdf_formulario import generar_pdf_formulario


def _mostrar_tarjetas(tarjetas, curso_mostrado, materia_mostrada):
    """Dibuja las tarjetas en una cuadricula de 2 columnas."""
    if not tarjetas:
        st.warning("No se pudo generar el formulario. Intenta de nuevo.")
        return

    st.markdown(f"<h4 style='color:#92FE9D; margin-top:14px'>📋 {curso_mostrado}</h4>", unsafe_allow_html=True)

    cols = st.columns(2)
    for i, tarjeta in enumerate(tarjetas):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(
                    f"<span style='background:#00C9FF; color:#0F0C29; font-weight:bold; "
                    f"border-radius:50%; padding:2px 9px; font-size:0.85em'>{tarjeta.get('numero', i+1)}</span> "
                    f"<strong style='color:white'>{tarjeta.get('titulo', '')}</strong>",
                    unsafe_allow_html=True
                )
                formula = tarjeta.get("formula", "")
                if formula:
                    st.latex(formula)
                nota = tarjeta.get("nota", "")
                if nota:
                    st.caption(nota)

    col_pdf, col_txt = st.columns(2)
    with col_pdf:
        try:
            pdf_buffer = generar_pdf_formulario(curso_mostrado, materia_mostrada, tarjetas)
            st.download_button(
                "📄 Descargar como PDF",
                data=pdf_buffer,
                file_name=f"formulario_{curso_mostrado}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception:
            st.caption("No se pudo generar el PDF, intenta con la descarga en texto.")
    with col_txt:
        texto_plano = "\n".join(
            f"{t.get('numero', i+1)}. {t.get('titulo','')}: {t.get('formula','')}" + (f" ({t['nota']})" if t.get("nota") else "")
            for i, t in enumerate(tarjetas)
        )
        st.download_button(
            "⬇️ Descargar como texto",
            data=texto_plano,
            file_name=f"formulario_{curso_mostrado}.txt",
            use_container_width=True
        )


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

    enfoque = st.text_input(
        "¿Algo en particular? (opcional)",
        key=f"{key_prefix}form_enfoque",
        placeholder="ej: solo cinematica, solo leyes de Newton..."
    )

    if st.button("✨ Generar formulario", key=f"{key_prefix}form_generar", use_container_width=True):
        with st.spinner("Revisando tu material y armando las tarjetas..."):
            material = obtener_muestra_estilo_curso(modo, curso, limite_caracteres=6000)
            if not material:
                st.warning("No se encontro material suficiente de este curso.")
            else:
                tarjetas = generar_formulario(modo, usuario, curso, material, enfoque=enfoque)
                if tarjetas:
                    st.session_state[f"{key_prefix}ultimo_formulario"] = tarjetas
                    st.session_state[f"{key_prefix}ultimo_formulario_curso"] = curso
                    st.session_state[f"{key_prefix}ultimo_formulario_materia"] = modo
                else:
                    st.error("No se pudo generar el formulario (puede ser un corte momentaneo del servicio). Intenta de nuevo en unos segundos.")
                    if st.session_state.get("ultimo_error_formulario"):
                        st.caption(f"Detalle tecnico (para reportar): {st.session_state['ultimo_error_formulario']}")

    if st.session_state.get(f"{key_prefix}ultimo_formulario"):
        st.divider()
        _mostrar_tarjetas(
            st.session_state[f"{key_prefix}ultimo_formulario"],
            st.session_state.get(f"{key_prefix}ultimo_formulario_curso"),
            st.session_state.get(f"{key_prefix}ultimo_formulario_materia") or modo
        )


def mostrar_formulario(usuario):
    """Pagina completa de Formulario (accesible desde el menu lateral)."""
    st.markdown("<h1 style='text-align:center;'>📋 Formulario</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Tarjetas rapidas de formulas, generadas de tus documentos y ajustadas a tu nivel</p>", unsafe_allow_html=True)
    st.divider()
    renderizar_generador_formulario(usuario)
