# -*- coding: utf-8 -*-
"""Mi Dia: lista simple de tareas de texto libre que cada alumno arma para
su propio dia (ej: gym, leer, tender la cama). Personal, no se comparte
entre alumnos."""
from datetime import date, timedelta
import re

import streamlit as st

from database import (
    agregar_tarea, listar_tareas_dia, marcar_tarea, eliminar_tarea,
    listar_tareas_rango
)


def _minificar(html):
    """Streamlit corta el HTML largo en las lineas en blanco (las trata como
    un nuevo bloque de markdown y escapa las etiquetas). Juntamos todo en
    una sola linea para que se renderice entero como HTML."""
    return re.sub(r'\s*\n\s*', '', html)


def _seccion_lista(usuario):
    tareas = listar_tareas_dia(usuario["id"])
    if not tareas:
        st.info("Todavia no agregaste nada para hoy. Agrega tu primera tarea arriba, en la tabla de la semana.")
        return

    total = len(tareas)
    hechas = sum(1 for t in tareas if t.get("completado"))
    st.progress(hechas / total)
    st.markdown(f"<p style='color:rgba(255,255,255,0.6)'>{hechas} de {total} completadas hoy</p>", unsafe_allow_html=True)

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
        return "<div style='text-align:center; color:rgba(255,255,255,0.3); font-size:1.3em;'>–</div>"
    if pct >= 70:
        color = "linear-gradient(180deg, #92FE9D, #00C9FF)"
    elif pct >= 40:
        color = "linear-gradient(180deg, #FDE68A, #F59E0B)"
    else:
        color = "linear-gradient(180deg, #FCA5A5, #EF4444)"
    return (
        "<div style='display:flex; flex-direction:column; align-items:center;'>"
        "<div style='width:22px; height:36px; border:2px solid rgba(255,255,255,0.35); "
        "border-radius:5px; position:relative; display:flex; flex-direction:column-reverse; "
        "overflow:hidden; background:rgba(255,255,255,0.05); margin:0 auto;'>"
        f"<div style='width:100%; height:{pct}%; background:{color};'></div>"
        "</div>"
        f"<span style='font-size:0.65em; color:rgba(255,255,255,0.6); margin-top:2px;'>{pct}%</span>"
        "</div>"
    )


def _seccion_semana(usuario):
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    dias_semana = [lunes + timedelta(days=i) for i in range(7)]
    nombres_dia = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

    tareas = listar_tareas_rango(usuario["id"], lunes, dias_semana[-1])

    # filas = actividades distintas de la semana (sin duplicar por mayus/espacios)
    filas_actividades = []
    vistos = set()
    for t in tareas:
        clave = t["texto"].strip().lower()
        if clave not in vistos:
            vistos.add(clave)
            filas_actividades.append(t["texto"].strip())

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

        tareas_por_dia = {str(d): [t for t in tareas if t["fecha"] == str(d)] for d in dias_semana}

        encabezados_dias = ""
        for i, d in enumerate(dias_semana):
            fondo = " background:rgba(0,201,255,0.08);" if d == hoy else ""
            encabezados_dias += (
                f"<th style='padding:6px 10px; color:white; font-weight:600; white-space:nowrap;{fondo}'>"
                f"{nombres_dia[i]}<br>"
                f"<span style=\"font-weight:400; font-size:0.75em; color:rgba(255,255,255,0.6);\">{d.strftime('%d/%m')}</span>"
                f"</th>"
            )

        filas_html = ""
        for actividad in filas_actividades:
            clave = actividad.lower()
            celdas = ""
            for d in dias_semana:
                por_texto = {t["texto"].strip().lower(): t for t in tareas_por_dia[str(d)]}
                t = por_texto.get(clave)
                fondo = " background:rgba(0,201,255,0.05);" if d == hoy else ""
                if t is None:
                    celdas += f"<td style='text-align:center;{fondo} color:rgba(255,255,255,0.2);'>·</td>"
                elif t.get("completado"):
                    celdas += f"<td style='text-align:center;{fondo} color:#92FE9D; font-size:1.2em;'>✓</td>"
                else:
                    celdas += f"<td style='text-align:center;{fondo} color:rgba(255,255,255,0.35); font-size:1.2em;'>✗</td>"
            filas_html += (
                f"<tr style='border:none;'>"
                f"<td style='padding:8px 12px; color:white; font-weight:600; white-space:nowrap;'>{actividad}</td>"
                f"{celdas}</tr>"
            )

        fila_bateria = "<td style='padding:8px 12px; color:white; font-weight:600;'>Batería</td>"
        for d in dias_semana:
            tareas_dia = tareas_por_dia[str(d)]
            total = len(tareas_dia)
            hechas = sum(1 for t in tareas_dia if t.get("completado"))
            pct = round(100 * hechas / total) if total > 0 else None
            fila_bateria += f"<td style='padding:6px;'>{_bateria_html(pct)}</td>"

        tabla_html = f"""
        <div style='overflow-x:auto;'>
            <table style='border-collapse:collapse; width:100%;'>
                <thead>
                    <tr style='border:none;'>
                        <th></th>
                        {encabezados_dias}
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                    <tr style='border:none; border-top:1px solid rgba(255,255,255,0.15);'>{fila_bateria}</tr>
                </tbody>
            </table>
        </div>
        """
        st.markdown(_minificar(tabla_html), unsafe_allow_html=True)
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
    _seccion_semana(usuario)
    st.write("")
    st.divider()
    _seccion_lista(usuario)
