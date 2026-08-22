# -*- coding: utf-8 -*-
"""Calendario personal: cada alumno guarda sus propias fechas de examenes
y entregas por materia. No se comparte entre alumnos (a diferencia de la
biblioteca de Documentos)."""
from datetime import date

import streamlit as st

from database import guardar_evento, listar_eventos, eliminar_evento
from materias_data import materias_de_carrera
from utils import hoy_peru

TIPOS_EVENTO = ["Examen", "Entrega", "Otro"]
EMOJI_TIPO = {"Examen": "📝", "Entrega": "📦", "Otro": "📌"}


def _color_urgencia(dias_faltantes):
    if dias_faltantes < 0:
        return "rgba(255,255,255,0.3)", "rgba(255,255,255,0.15)"  # ya paso
    if dias_faltantes <= 3:
        return "#EF4444", "rgba(239,68,68,0.3)"
    if dias_faltantes <= 7:
        return "#F59E0B", "rgba(245,158,11,0.3)"
    return "#92FE9D", "rgba(146,254,157,0.3)"


def _seccion_agregar(usuario):
    st.markdown("### ➕ Agregar fecha")
    materias_alumno = materias_de_carrera(usuario.get("carrera"))

    col1, col2 = st.columns(2)
    with col1:
        titulo = st.text_input("Titulo (ej: Examen Parcial, Entrega TP3)", key="cal_titulo")
        materia = st.selectbox("Materia (opcional)", ["Sin materia especifica"] + materias_alumno, key="cal_materia")
    with col2:
        fecha = st.date_input("Fecha", value=hoy_peru(), key="cal_fecha")
        tipo = st.selectbox("Tipo", TIPOS_EVENTO, key="cal_tipo")

    notas = st.text_area("Notas (opcional)", key="cal_notas", height=70)

    if st.button("Guardar en mi calendario", use_container_width=True):
        if not titulo or not titulo.strip():
            st.warning("Escribe un titulo primero")
        else:
            materia_final = None if materia == "Sin materia especifica" else materia
            ok = guardar_evento(usuario["id"], titulo, fecha, tipo=tipo, materia=materia_final, notas=notas)
            if ok:
                st.success("Guardado")
                st.rerun()
            else:
                st.error("No se pudo guardar, intenta de nuevo")


def _seccion_lista(usuario):
    st.markdown("### 📋 Mis proximas fechas")
    eventos = listar_eventos(usuario["id"])
    if not eventos:
        st.info("No tienes fechas guardadas todavia. Agrega la primera arriba.")
        return

    hoy = hoy_peru()
    for evento in eventos:
        fecha_evento = date.fromisoformat(str(evento["fecha"]))
        dias_faltantes = (fecha_evento - hoy).days
        color, borde = _color_urgencia(dias_faltantes)

        if dias_faltantes < 0:
            texto_dias = "Ya paso"
        elif dias_faltantes == 0:
            texto_dias = "Es HOY"
        elif dias_faltantes == 1:
            texto_dias = "Mañana"
        else:
            texto_dias = f"En {dias_faltantes} dias"

        emoji_tipo = EMOJI_TIPO.get(evento.get("tipo"), "📌")
        materia_txt = f" · {evento['materia']}" if evento.get("materia") else ""

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.04); border-left:4px solid {borde}; "
                f"border-radius:8px; padding:10px 14px; margin-bottom:8px;'>"
                f"<span style='color:{color}; font-weight:bold'>{texto_dias}</span> — "
                f"{emoji_tipo} <strong style='color:white'>{evento['titulo']}</strong>"
                f"<span style='color:rgba(255,255,255,0.5)'>{materia_txt}</span>"
                f"<br><span style='color:rgba(255,255,255,0.5); font-size:0.85em'>{fecha_evento.strftime('%d/%m/%Y')}</span>"
                + (f"<br><span style='color:rgba(255,255,255,0.6); font-size:0.85em'>{evento['notas']}</span>" if evento.get("notas") else "")
                + "</div>",
                unsafe_allow_html=True
            )
            if evento.get("tipo") == "Examen" and evento.get("materia") and 0 <= dias_faltantes <= 4:
                if st.button(f"🎯 Practicar con un examen de {evento['materia']}", key=f"practicar_{evento['id']}"):
                    st.session_state["menu_seccion"] = "Modo Examen"
                    st.session_state["examen_materia_select"] = evento["materia"]
                    st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_evento_{evento['id']}"):
                eliminar_evento(evento["id"])
                st.rerun()


def mostrar_calendario(usuario):
    st.markdown("<h1 style='text-align:center;'>📅 Mi Calendario</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Tus examenes y entregas, solo para ti</p>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2 = st.tabs(["📋 Mis fechas", "➕ Agregar"])
    with tab1:
        _seccion_lista(usuario)
    with tab2:
        _seccion_agregar(usuario)
