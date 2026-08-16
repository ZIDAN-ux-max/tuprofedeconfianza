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


def _bateria_html(pct):
    """Bateria vertical: llena y verde/cian si pct alto, roja si bajo,
    o un guion neutral si ese dia no habia ninguna tarea planeada
    (no es 'fallo', simplemente no se propuso nada ese dia)."""
    if pct is None:
        return "<div style='text-align:center; color:rgba(255,255,255,0.3); font-size:1.5em;'>–</div>"
    if pct >= 70:
        color = "linear-gradient(180deg, #92FE9D, #00C9FF)"
    elif pct >= 40:
        color = "linear-gradient(180deg, #FDE68A, #F59E0B)"
    else:
        color = "linear-gradient(180deg, #FCA5A5, #EF4444)"
    return f"""
    <div style='display:flex; flex-direction:column; align-items:center;'>
        <div style='width:26px; height:44px; border:2px solid rgba(255,255,255,0.35);
                    border-radius:5px; position:relative; display:flex; flex-direction:column-reverse;
                    overflow:hidden; background:rgba(255,255,255,0.05);'>
            <div style='width:100%; height:{pct}%; background:{color};'></div>
        </div>
        <span style='font-size:0.7em; color:rgba(255,255,255,0.6); margin-top:3px;'>{pct}%</span>
    </div>
    """


def _seccion_semana(usuario):
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]

    tareas = listar_tareas_rango(usuario["id"], lunes, dias_semana[-1])

    # columnas = actividades distintas de la semana (sin duplicar por mayus/espacios)
    columnas = []
    vistos = set()
    for t in tareas:
        clave = t["texto"].strip().lower()
        if clave not in vistos:
            vistos.add(clave)
            columnas.append(t["texto"].strip())

    st.markdown("<h3>📅 Esta semana</h3>", unsafe_allow_html=True)

    if not columnas:
        st.info("Todavia no hay tareas esta semana para mostrar en la tabla.")
        return

    nombres_dia = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

    # armamos las filas HTML: dia | celda por cada columna | bateria del dia
    filas_html = ""
    for i, dia in enumerate(dias_semana):
        tareas_dia = [t for t in tareas if t["fecha"] == str(dia)]
        por_texto = {t["texto"].strip().lower(): t for t in tareas_dia}

        celdas = ""
        for col in columnas:
            t = por_texto.get(col.lower())
            if t is None:
                celdas += "<td style='text-align:center; color:rgba(255,255,255,0.2);'>·</td>"
            elif t.get("completado"):
                celdas += "<td style='text-align:center; color:#92FE9D; font-size:1.2em;'>✓</td>"
            else:
                celdas += "<td style='text-align:center; color:rgba(255,255,255,0.35); font-size:1.2em;'>✗</td>"

        total = len(tareas_dia)
        hechas = sum(1 for t in tareas_dia if t.get("completado"))
        pct = round(100 * hechas / total) if total > 0 else None
        es_hoy = " background:rgba(0,201,255,0.08);" if dia == hoy else ""

        filas_html += f"""
        <tr style='border:none;{es_hoy}'>
            <td style='padding:8px 12px; color:white; font-weight:600; white-space:nowrap;'>
                {nombres_dia[i]} {dia.strftime('%d/%m')}
            </td>
            {celdas}
            <td style='padding:6px;'>{_bateria_html(pct)}</td>
        </tr>
        """

    encabezados = "".join(
        f"""<th style='padding:6px; font-weight:600; color:rgba(255,255,255,0.8);
                       writing-mode:vertical-rl; text-orientation:mixed;
                       max-height:110px; font-size:0.85em;'>{c}</th>"""
        for c in columnas
    )

    tabla_html = f"""
    <div style='overflow-x:auto; background:rgba(255,255,255,0.05); backdrop-filter:blur(10px);
                border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:15px;'>
        <table style='border-collapse:collapse; width:100%;'>
            <thead>
                <tr style='border:none;'>
                    <th></th>
                    {encabezados}
                    <th style='color:rgba(255,255,255,0.8); font-size:0.85em;'>Batería</th>
                </tr>
            </thead>
            <tbody>
                {filas_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown(tabla_html, unsafe_allow_html=True)
    st.markdown(
        "<p style='color:rgba(255,255,255,0.4); font-size:0.8em; margin-top:8px;'>"
        "· = no planeada ese dia &nbsp;&nbsp; ✗ = planeada pero no cumplida &nbsp;&nbsp; ✓ = cumplida</p>",
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
    _seccion_agregar(usuario)
    st.write("")
    _seccion_lista(usuario)
    st.write("")
    st.divider()
    _seccion_semana(usuario)
