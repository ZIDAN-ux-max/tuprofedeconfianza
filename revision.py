# -*- coding: utf-8 -*-
"""Revisa mi Solucion: el alumno escribe (o sube una foto de) su
procedimiento, y el tutor lo revisa paso por paso, encontrando el primer
error sin dar la respuesta directa - para que el alumno piense y corrija."""
import base64

import streamlit as st

from tutor_ai import transcribir_procedimiento_imagen, revisar_solucion, actualizar_perfil_alumno
from materias_data import materias_de_carrera
from utils import normalizar_latex


def mostrar_revision(usuario):
    st.markdown("<h1 style='text-align:center;'>🔍 Revisa mi Solución</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Escribe o sube una foto de tu procedimiento - el tutor encuentra donde te equivocaste</p>", unsafe_allow_html=True)
    st.divider()

    materias_alumno = materias_de_carrera(usuario.get("carrera"))
    modo = st.selectbox("Materia", materias_alumno, key="rev_materia")
    problema = st.text_input("¿Que problema estas resolviendo?", key="rev_problema", placeholder="Ej: Resolver la integral de 3x^2 dx de -1 a 3")

    tab1, tab2 = st.tabs(["✍️ Escribir", "📷 Subir foto"])

    with tab1:
        procedimiento_texto = st.text_area(
            "Escribe tu procedimiento paso a paso",
            key="rev_procedimiento_texto",
            height=200,
            placeholder="Paso 1: ...\nPaso 2: ..."
        )
        if st.button("🔍 Revisar mi solución", key="rev_boton_texto", use_container_width=True):
            _ejecutar_revision(usuario, modo, problema, procedimiento_texto)

    with tab2:
        foto = st.file_uploader("Sube una foto de tu procedimiento escrito", type=["png", "jpg", "jpeg"], key="rev_foto")
        if foto and st.button("👁️ Leer la foto", key="rev_boton_leer", use_container_width=True):
            with st.spinner("Leyendo tu procedimiento..."):
                imagen_b64 = base64.b64encode(foto.getvalue()).decode()
                mime = foto.type or "image/jpeg"
                texto_leido = transcribir_procedimiento_imagen(imagen_b64, mime)
                st.session_state["rev_texto_de_foto"] = texto_leido

        if st.session_state.get("rev_texto_de_foto"):
            st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:0.9em'>Esto es lo que la IA leyó de tu foto. <strong>Corrígelo</strong> si algo está mal antes de pedir la revisión:</p>", unsafe_allow_html=True)
            procedimiento_corregido = st.text_area(
                "Transcripción (editable)",
                value=st.session_state["rev_texto_de_foto"],
                key="rev_procedimiento_foto_editado",
                height=200
            )
            if st.button("🔍 Revisar mi solución", key="rev_boton_foto", use_container_width=True):
                _ejecutar_revision(usuario, modo, problema, procedimiento_corregido)

    if st.session_state.get("rev_resultado"):
        st.divider()
        st.markdown(normalizar_latex(st.session_state["rev_resultado"]), unsafe_allow_html=True)


def _ejecutar_revision(usuario, modo, problema, procedimiento):
    if not problema or not problema.strip():
        st.warning("Escribe primero que problema estas resolviendo")
    elif not procedimiento or not procedimiento.strip():
        st.warning("Escribe o sube tu procedimiento primero")
    else:
        with st.spinner("Revisando tu procedimiento paso a paso..."):
            resultado = revisar_solucion(modo, usuario, problema, procedimiento)
        actualizar_perfil_alumno(usuario["id"], modo, problema, resultado)
        st.session_state.pop("temas_debiles_usuario", None)  # se recalcula, por si cambio
        st.session_state["rev_resultado"] = resultado
        st.rerun()
