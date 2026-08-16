# -*- coding: utf-8 -*-
"""Mi Dia: lista simple de tareas de texto libre que cada alumno arma para
su propio dia (ej: gym, leer, tender la cama). Personal, no se comparte
entre alumnos."""
from datetime import date

import streamlit as st

from database import agregar_tarea, listar_tareas_dia, marcar_tarea, eliminar_tarea


def _seccion_agregar(usuario):
    col1, col2 = st.columns([4, 1])
    with col1:
        texto = st.text_input(
            "Agregar tarea (ej: gym, leer, tender la cama)",
            key="tarea_texto",
            label_visibility="collapsed",
            placeholder="Agregar tarea (ej: gym, leer, tender la cama)"
        )
    with col2:
        if st.button("➕ Agregar", use_container_width=True):
            if not texto or not texto.strip():
                st.warning("Escribe algo primero")
            else:
                agregar_tarea(usuario["id"], texto)
                st.rerun()


def _seccion_lista(usuario):
    tareas = listar_tareas_dia(usuario["id"])
    if not tareas:
        st.info("Todavia no agregaste nada para hoy. Escribe tu primera tarea arriba.")
        return

    total = len(tareas)
    hechas = sum(1 for t in tareas if t.get("completado"))
    st.progress(hechas / total)
    st.markdown(f"<p style='color:rgba(255,255,255,0.6)'>{hechas} de {total} completadas</p>", unsafe_allow_html=True)

    for tarea in tareas:
        col1, col2 = st.columns([5, 1])
        with col1:
            marcada = st.checkbox(
                tarea["texto"],
                value=bool(tarea.get("completado")),
                key=f"tarea_check_{tarea['id']}"
            )
            if marcada != bool(tarea.get("completado")):
                marcar_tarea(tarea["id"], marcada)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_tarea_{tarea['id']}"):
                eliminar_tarea(tarea["id"])
                st.rerun()


def mostrar_tareas(usuario):
    st.markdown("<h1 style='text-align:center;'>☀️ Mi Dia</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center; color:rgba(255,255,255,0.6)'>"
        f"{date.today().strftime('%d/%m/%Y')} · Que vas a hacer hoy?</p>",
        unsafe_allow_html=True
    )
    st.divider()
    _seccion_agregar(usuario)
    st.write("")
    _seccion_lista(usuario)
