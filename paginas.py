# -*- coding: utf-8 -*-
"""Paginas simples de la app: Ranking, Mis Logros, Mis Estadisticas y Acerca de."""
import streamlit as st
import textwrap

from database import obtener_ranking, obtener_logros_usuario, obtener_mi_rango, progreso_siguiente_rango
from logros_data import LOGROS_DISPONIBLES
from materias_data import EMOJI_MATERIA


def mostrar_ranking(usuario):
    st.markdown("<h1 style='text-align:center;'>🏆 Ranking de Estudiantes</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Compite con tus companeros y llega al top!</p>", unsafe_allow_html=True)
    st.divider()
    ranking = obtener_ranking()
    medallas = ["🥇", "🥈", "🥉"]
    for i, est in enumerate(ranking):
        medalla = medallas[i] if i < 3 else f"#{i+1}"
        es_yo = est["nombre"] == usuario["nombre"]
        color = "rgba(0,201,255,0.1)" if es_yo else "rgba(255,255,255,0.05)"
        borde = "1px solid rgba(0,201,255,0.5)" if es_yo else "1px solid rgba(255,255,255,0.1)"
        etiqueta_tu = '<span style="color:#00C9FF; font-size:0.8em"> (Tu)</span>' if es_yo else ''
        html_fila = (
            f"<div style='background:{color}; border:{borde}; border-radius:16px; padding:15px; margin-bottom:8px;'>"
            f"<span style='font-size:1.5em'>{medalla}</span>"
            f"<strong style='color:white; margin-left:10px'>{est['nombre']}</strong>"
            f"{etiqueta_tu}"
            f"<span style='float:right; color:#00C9FF; font-weight:bold;'>⭐ {est['puntos']} pts</span>"
            f"<br>"
            f"<span style='color:rgba(255,255,255,0.6); font-size:0.85em;'>"
            f"💬 {est['total']} mensajes &nbsp; ✅ {est['puntos_tareas']}pts tareas &nbsp; 🏅 {est['puntos_logros']}pts logros &nbsp; 🔥 {est['racha']} dias"
            f"</span>"
            f"</div>"
        )
        st.markdown(html_fila, unsafe_allow_html=True)


def mostrar_acerca_de():
    st.markdown("<h1 style='text-align:center;'>Acerca de Tu Profe de Confianza</h1>", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style='background:rgba(255,255,255,0.05); border:1px solid rgba(0,201,255,0.2); border-radius:16px; padding:25px;'>
        <h3 style='color:#00C9FF'>Nuestra Mision</h3>
        <p style='color:rgba(255,255,255,0.8)'>Hacer la educacion accesible para todos los estudiantes peruanos,
        con un tutor de IA disponible 24/7 que explica de forma simple y cercana.</p>
        <h3 style='color:#00C9FF'>Que ofrecemos</h3>
        <p style='color:rgba(255,255,255,0.8)'>✅ Tutor de Matematicas con explicaciones paso a paso</p>
        <p style='color:rgba(255,255,255,0.8)'>✅ Tutor de Ingles con pronunciacion y traduccion</p>
        <p style='color:rgba(255,255,255,0.8)'>✅ Analisis de tus documentos y libros</p>
        <p style='color:rgba(255,255,255,0.8)'>✅ Sistema de logros para motivarte</p>
        <p style='color:rgba(255,255,255,0.8)'>✅ Ranking de competencia entre estudiantes</p>
        <p style='color:rgba(255,255,255,0.8)'>✅ Registro de asistencia y racha diaria</p>
        <p style='color:rgba(255,255,255,0.8)'>✅ Historial de conversaciones guardado</p>
        <p style='color:rgba(255,255,255,0.8)'>✅ Tutor personalizado segun edad, grado/ciclo y progreso</p>
        <h3 style='color:#00C9FF'>Contacto</h3>
        <p style='color:rgba(255,255,255,0.8)'>Tienes sugerencias? Escribenos y mejoramos juntos.</p>
    </div>
    """, unsafe_allow_html=True)


def mostrar_logros(usuario, racha):
    st.markdown("<h1 style='text-align:center;'>Mis Logros</h1>", unsafe_allow_html=True)
    st.divider()
    logros_ganados = obtener_logros_usuario(usuario["id"])
    st.markdown(f"<h3 style='color:white'>Tienes {len(logros_ganados)} de {len(LOGROS_DISPONIBLES)} logros 🏆</h3>", unsafe_allow_html=True)
    if racha > 0:
        st.markdown(textwrap.dedent(f"""
        <div class='racha-card'>
            <div style='font-size:2em'>🔥</div>
            <div style='font-size:1.5em; font-weight:bold'>{racha} dias de racha</div>
            <div style='font-size:0.9em; opacity:0.9'>Sigue estudiando cada dia para no perderla!</div>
        </div>
        """), unsafe_allow_html=True)
    st.divider()
    cols = st.columns(3)
    for i, logro in enumerate(LOGROS_DISPONIBLES):
        with cols[i % 3]:
            if logro["nombre"] in logros_ganados:
                st.markdown(textwrap.dedent(f"""
                <div class='logro-card'>
                    <div class='logro-emoji'>{logro['emoji']}</div>
                    <div class='logro-nombre'>{logro['nombre']}</div>
                    <div class='logro-desc'>{logro['descripcion']}</div>
                </div>
                """), unsafe_allow_html=True)
            else:
                st.markdown(textwrap.dedent(f"""
                <div class='logro-card' style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.3)'>
                    <div class='logro-emoji'>🔒</div>
                    <div style='font-weight:bold; font-size:0.9em; margin-top:5px'>{logro['nombre']}</div>
                    <div style='font-size:0.75em; opacity:0.6'>{logro['descripcion']}</div>
                </div>
                """), unsafe_allow_html=True)


def mostrar_estadisticas(stats):
    st.markdown("<h1 style='text-align:center;'>Mis Estadisticas</h1>", unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='stat-card'><div class='stat-number'>{stats['total']}</div><div class='stat-label'>Total preguntas</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='stat-card'><div class='stat-number'>{stats['hoy']}</div><div class='stat-label'>Preguntas hoy</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='stat-card'><div class='stat-number'>{stats['semana']}</div><div class='stat-label'>Esta semana</div></div>", unsafe_allow_html=True)
    st.divider()

    por_materia = stats.get("por_materia", {})
    materias_con_datos = [(m, c) for m, c in por_materia.items() if c > 0]
    if materias_con_datos:
        cols = st.columns(min(3, len(materias_con_datos) + 1))
        for i, (materia, cantidad) in enumerate(materias_con_datos):
            with cols[i % len(cols)]:
                emoji = EMOJI_MATERIA.get(materia, "📘")
                st.markdown(f"<div class='stat-card'><div class='stat-number'>{emoji} {cantidad}</div><div class='stat-label'>{materia}</div></div>", unsafe_allow_html=True)
        with cols[len(materias_con_datos) % len(cols)]:
            st.markdown(f"<div class='stat-card'><div class='stat-number'>🔥 {stats['racha']}</div><div class='stat-label'>Dias de racha</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='stat-card'><div class='stat-number'>🔥 {stats['racha']}</div><div class='stat-label'>Dias de racha</div></div>", unsafe_allow_html=True)

    st.divider()
    if stats['total'] > 0:
        if materias_con_datos:
            materia_favorita = max(materias_con_datos, key=lambda x: x[1])[0]
            st.success(f"Tu materia favorita es: **{materia_favorita}** 🎯")
        if stats['hoy'] == 0:
            st.warning("No has estudiado hoy. Abre el chat!")
        elif stats['hoy'] < 5:
            st.info(f"Llevas {stats['hoy']} preguntas hoy. Sigue asi!")
        else:
            st.success(f"Excelente! Llevas {stats['hoy']} preguntas hoy. Eres un crack!")
    else:
        st.info("Aun no tienes estadisticas. Ve al chat y empieza!")


def mostrar_mi_rango(usuario):
    st.markdown("<h1 style='text-align:center;'>🏅 Mi Rango</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:rgba(255,255,255,0.6)'>Tu progreso trimestral de disciplina y estudio</p>",
        unsafe_allow_html=True
    )
    st.divider()

    datos = obtener_mi_rango(usuario["id"])
    nombres_trimestre = {1: "Ene-Mar", 2: "Abr-Jun", 3: "Jul-Sep", 4: "Oct-Dic"}

    st.markdown(
        f"<div style='background:rgba(255,255,255,0.05); border:1px solid rgba(0,201,255,0.3); "
        f"border-radius:16px; padding:25px; text-align:center;'>"
        f"<div style='font-size:2.5em;'>{datos['rango']}</div>"
        f"<div style='color:rgba(255,255,255,0.6); margin-top:5px;'>Trimestre {nombres_trimestre[datos['trimestre']]} {datos['anio']}</div>"
        f"<div style='font-size:1.8em; color:#00C9FF; font-weight:bold; margin-top:10px;'>{datos['puntos']} pts</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.write("")
    siguiente = progreso_siguiente_rango(datos["puntos"])
    if siguiente:
        faltan, proximo = siguiente
        st.markdown(
            f"<p style='text-align:center; color:rgba(255,255,255,0.7)'>"
            f"Te faltan <strong style='color:#00C9FF;'>{faltan} pts</strong> para llegar a {proximo}</p>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<p style='text-align:center; color:rgba(255,255,255,0.7)'>"
            "Llegaste al rango maximo de este trimestre 🎉</p>",
            unsafe_allow_html=True
        )

    if datos["historial"]:
        st.write("")
        st.markdown("<h3>Historial de trimestres</h3>", unsafe_allow_html=True)
        for h in reversed(datos["historial"]):
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); "
                f"border-radius:12px; padding:12px 18px; margin-bottom:6px; "
                f"display:flex; justify-content:space-between; align-items:center;'>"
                f"<span style='color:white;'>{nombres_trimestre.get(h['trimestre'], '')} {h['anio']}</span>"
                f"<span style='color:rgba(255,255,255,0.8);'>{h['rango']} · {h['puntos_totales']} pts</span>"
                f"</div>",
                unsafe_allow_html=True
            )
