# -*- coding: utf-8 -*-
"""Mi Dia: lista simple de tareas de texto libre que cada alumno arma para
su propio dia (ej: gym, leer, tender la cama). Personal, no se comparte
entre alumnos."""
from datetime import date, timedelta

import streamlit as st

from database import (
    agregar_tarea, listar_tareas_dia, marcar_tarea, eliminar_tarea,
    listar_tareas_rango
)


def _seccion_lista(usuario):
    """Lista de hoy: solo para borrar tareas. Marcar como hecha se hace
    directo en la tabla de la semana, en el cruce dia/actividad."""
    tareas = listar_tareas_dia(usuario["id"])
    if not tareas:
        return

    total = len(tareas)
    hechas = sum(1 for t in tareas if t.get("completado"))
    st.progress(hechas / total)
    st.markdown(f"<p style='color:rgba(255,255,255,0.6)'>{hechas} de {total} completadas hoy</p>", unsafe_allow_html=True)

    for tarea in tareas:
        col1, col2 = st.columns([5, 1])
        with col1:
            marca = "✓" if tarea.get("completado") else "○"
            st.markdown(f"<p style='margin:6px 0;'>{marca} {tarea['texto']}</p>", unsafe_allow_html=True)
        with col2:
            if st.button("🗑️", key=f"del_tarea_{tarea['id']}"):
                eliminar_tarea(tarea["id"])
                st.rerun()


def _bateria_html(pct):
    """Bateria vertical: llena y verde/cian si pct alto, roja si bajo,
    o un guion neutral si ese dia no habia ninguna tarea planeada
    (no es 'fallo', simplemente no se propuso nada ese dia)."""
    if pct is None:
        return "<div style='text-align:center; color:rgba(255,255,255,0.3); font-size:1.3em;'>–</div>"
    if pct >= 70:
        color = "linear-gradient(180deg, #92FE9D, #00C9FF)"
    elif pct >= 40:
        color = "linear-gradient(180deg, #FDE68A, #F59E0B)"
    else:
        color = "linear-gradient(180deg, #FCA5A5, #EF4444)"
    return (
        "<div style='display:flex; flex-direction:column; align-items:center;'>"
        "<div style='width:20px; height:32px; border:2px solid rgba(255,255,255,0.35); "
        "border-radius:5px; position:relative; display:flex; flex-direction:column-reverse; "
        "overflow:hidden; background:rgba(255,255,255,0.05); margin:0 auto;'>"
        f"<div style='width:100%; height:{pct}%; background:{color};'></div>"
        "</div>"
        f"<span style='font-size:0.65em; color:rgba(255,255,255,0.6);'>{pct}%</span>"
        "</div>"
    )


def _seccion_semana(usuario):
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    nombres_dia = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

    tareas = listar_tareas_rango(usuario["id"], lunes, dias_semana[-1])

    filas_actividades = []
    vistos = set()
    for t in tareas:
        clave = t["texto"].strip().lower()
        if clave not in vistos:
            vistos.add(clave)
            filas_actividades.append(t["texto"].strip())

    tareas_por_dia = {str(d): [t for t in tareas if t["fecha"] == str(d)] for d in dias_semana}
    proporciones = [2] + [1] * 7

    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0;'>📅 Esta semana</h3>", unsafe_allow_html=True)

        col1, col2 = st.columns([4, 1])
        with col1:
            texto = st.text_input(
                "Agregar tarea",
                key="tarea_texto",
                label_visibility="collapsed",
                placeholder="Agregar tarea de hoy (ej: gym, leer, tender la cama)"
            )
        with col2:
            if st.button("➕ Agregar", use_container_width=True, key="btn_agregar_semana"):
                if not texto or not texto.strip():
                    st.warning("Escribe algo primero")
                else:
                    agregar_tarea(usuario["id"], texto)
                    st.rerun()

        if not filas_actividades:
            st.info("Todavia no hay tareas esta semana para mostrar en la tabla.")
            return

        st.write("")

        # --- encabezado: dias arriba ---
        header = st.columns(proporciones)
        header[0].markdown("&nbsp;", unsafe_allow_html=True)
        for i, d in enumerate(dias_semana):
            resaltado = "color:#00C9FF;" if d == hoy else "color:white;"
            header[i + 1].markdown(
                f"<div style='text-align:center; font-weight:600; {resaltado}'>{nombres_dia[i]}"
                f"<br><span style='font-weight:400; font-size:0.75em; color:rgba(255,255,255,0.6);'>{d.strftime('%d/%m')}</span></div>",
                unsafe_allow_html=True
            )

        st.markdown("<hr style='margin:8px 0; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # --- filas: una por actividad, casillero clickeable en cada cruce con el dia ---
        for actividad in filas_actividades:
            clave = actividad.lower()
            fila = st.columns(proporciones)
            fila[0].markdown(f"<div style='padding-top:6px; font-weight:600;'>{actividad}</div>", unsafe_allow_html=True)
            for i, d in enumerate(dias_semana):
                por_texto = {t["texto"].strip().lower(): t for t in tareas_por_dia[str(d)]}
                t = por_texto.get(clave)
                with fila[i + 1]:
                    if t is None:
                        st.markdown("<div style='text-align:center; color:rgba(255,255,255,0.2); padding-top:8px;'>·</div>", unsafe_allow_html=True)
                    else:
                        marcada = st.checkbox(
                            actividad,
                            value=bool(t.get("completado")),
                            key=f"celda_{t['id']}",
                            label_visibility="collapsed"
                        )
                        if marcada != bool(t.get("completado")):
                            marcar_tarea(t["id"], marcada)
                            st.rerun()

        st.markdown("<hr style='margin:8px 0; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # --- fila final: bateria del dia (resumen de todas las actividades de ese dia) ---
        fila_bat = st.columns(proporciones)
        fila_bat[0].markdown("<div style='padding-top:10px; font-weight:600;'>Batería</div>", unsafe_allow_html=True)
        for i, d in enumerate(dias_semana):
            tareas_dia = tareas_por_dia[str(d)]
            total = len(tareas_dia)
            hechas = sum(1 for t in tareas_dia if t.get("completado"))
            pct = round(100 * hechas / total) if total > 0 else None
            fila_bat[i + 1].markdown(_bateria_html(pct), unsafe_allow_html=True)

        st.markdown(
            "<p style='color:rgba(255,255,255,0.4); font-size:0.8em; margin-top:10px;'>"
            "· = no planeada ese dia &nbsp;&nbsp; el casillero se marca tocandolo</p>",
            unsafe_allow_html=True
        )


def mostrar_tareas(usuario):
    st.markdown("<h1 style='text-align:center;'>☀️ Mi Dia</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center; color:rgba(255,255,255,0.6)'>"
        f"{date.today().strftime('%d/%m/%Y')} · Que vas a hacer hoy?</p>",
        unsafe_allow_html=True
    )
    st.divider()
    _seccion_semana(usuario)
    st.write("")
    _seccion_lista(usuario)
