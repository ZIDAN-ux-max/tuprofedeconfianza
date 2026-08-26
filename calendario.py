# -*- coding: utf-8 -*-
"""Calendario personal: cada alumno guarda sus propias fechas de examenes
y entregas por materia. No se comparte entre alumnos (a diferencia de la
biblioteca de Documentos). Incluye una vista de mes tipo calendario real,
que tambien muestra las tareas de "Mi Dia" ademas de examenes/entregas."""
import calendar as calendar_mod
from datetime import date, timedelta

import streamlit as st

from database import guardar_evento, listar_eventos, eliminar_evento, listar_tareas_rango, marcar_tarea, eliminar_tarea
from materias_data import materias_de_carrera
from utils import hoy_peru

TIPOS_EVENTO = ["Examen", "Entrega", "Otro"]
EMOJI_TIPO = {"Examen": "📝", "Entrega": "📦", "Otro": "📌"}

MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
DIAS_SEMANA_ES = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

TEMAS_FONDO = {
    "🎓 Año académico 2026": "linear-gradient(135deg, rgba(0,201,255,0.14) 0%, rgba(146,254,157,0.06) 100%)",
    "🌙 Oscuro clásico": "rgba(255,255,255,0.025)",
    "🍂 Cálido": "linear-gradient(135deg, rgba(245,158,11,0.16) 0%, rgba(239,68,68,0.07) 100%)",
    "🌸 Suave": "linear-gradient(135deg, rgba(192,132,252,0.15) 0%, rgba(0,201,255,0.06) 100%)",
}

CSS_CALENDARIO = """
<style>
.cal-header-dia {
    text-align:center;
    font-size:0.78em;
    color:rgba(255,255,255,0.55);
    font-weight:600;
    padding-bottom:4px;
}
.cal-celda-vacia { height:44px; }
.cal-marcas { text-align:center; font-size:0.65em; margin-top:-4px; line-height:1; min-height:12px; }
</style>
"""


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
        fecha_default = st.session_state.get("cal_fecha_prellenada", hoy_peru())
        fecha = st.date_input("Fecha", value=fecha_default, key="cal_fecha")
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
                st.session_state.pop("cal_fecha_prellenada", None)
                st.rerun()
            else:
                st.error("No se pudo guardar, intenta de nuevo")


def _seccion_lista(usuario):
    st.markdown("### 📋 Mis proximas fechas")
    eventos = listar_eventos(usuario["id"])
    if not eventos:
        st.info("No tienes fechas guardadas todavia. Agrega la primera en la pestaña 'Agregar'.")
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


def _seccion_calendario_mensual(usuario):
    st.markdown(CSS_CALENDARIO, unsafe_allow_html=True)

    hoy = hoy_peru()
    if "cal_anio_actual" not in st.session_state:
        st.session_state["cal_anio_actual"] = hoy.year
    if "cal_mes_actual" not in st.session_state:
        st.session_state["cal_mes_actual"] = hoy.month

    anio = st.session_state["cal_anio_actual"]
    mes = st.session_state["cal_mes_actual"]

    col_fondo, col_espacio = st.columns([2, 3])
    with col_fondo:
        fondo_elegido = st.selectbox("🎨 Fondo del calendario", list(TEMAS_FONDO.keys()), key="cal_fondo_tema")

    col_prev, col_titulo, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("◀", key="cal_mes_prev", use_container_width=True):
            if mes == 1:
                st.session_state["cal_mes_actual"] = 12
                st.session_state["cal_anio_actual"] = anio - 1
            else:
                st.session_state["cal_mes_actual"] = mes - 1
            st.rerun()
    with col_titulo:
        st.markdown(f"<h3 style='text-align:center; margin:0'>{MESES_ES[mes]} {anio}</h3>", unsafe_allow_html=True)
    with col_next:
        if st.button("▶", key="cal_mes_next", use_container_width=True):
            if mes == 12:
                st.session_state["cal_mes_actual"] = 1
                st.session_state["cal_anio_actual"] = anio + 1
            else:
                st.session_state["cal_mes_actual"] = mes + 1
            st.rerun()

    primer_dia_mes = date(anio, mes, 1)
    ultimo_dia_mes = date(anio, mes, calendar_mod.monthrange(anio, mes)[1])

    eventos = listar_eventos(usuario["id"])
    eventos_por_dia = {}
    for evento in eventos:
        f = date.fromisoformat(str(evento["fecha"]))
        eventos_por_dia.setdefault(f, []).append(evento)

    tareas = listar_tareas_rango(usuario["id"], primer_dia_mes, ultimo_dia_mes)
    tareas_por_dia = {}
    for tarea in tareas:
        f = date.fromisoformat(str(tarea["fecha"]))
        tareas_por_dia.setdefault(f, []).append(tarea)

    cal = calendar_mod.Calendar(firstweekday=6)  # empieza en Domingo, como el ejemplo
    semanas = cal.monthdayscalendar(anio, mes)

    st.markdown(
        f"<div style='background:{TEMAS_FONDO[fondo_elegido]}; border-radius:14px; padding:14px 10px; margin-top:6px'>",
        unsafe_allow_html=True
    )

    cols_header = st.columns(7)
    for i, nombre_dia in enumerate(DIAS_SEMANA_ES):
        with cols_header[i]:
            st.markdown(f"<div class='cal-header-dia'>{nombre_dia}</div>", unsafe_allow_html=True)

    dia_seleccionado = st.session_state.get("cal_dia_seleccionado")

    for semana in semanas:
        cols_semana = st.columns(7)
        for i, dia in enumerate(semana):
            with cols_semana[i]:
                if dia == 0:
                    st.markdown("<div class='cal-celda-vacia'></div>", unsafe_allow_html=True)
                    continue

                fecha_celda = date(anio, mes, dia)
                marcas = ""
                if fecha_celda in eventos_por_dia:
                    tipos_del_dia = {e.get("tipo") for e in eventos_por_dia[fecha_celda]}
                    if "Examen" in tipos_del_dia:
                        marcas += "🔴"
                    if "Entrega" in tipos_del_dia:
                        marcas += "🟠"
                    if "Otro" in tipos_del_dia:
                        marcas += "📌"
                if fecha_celda in tareas_por_dia:
                    marcas += "🟢"

                es_hoy = fecha_celda == hoy
                etiqueta_dia = f"**{dia}**" if es_hoy else str(dia)

                tipo_boton = "primary" if fecha_celda == dia_seleccionado else "secondary"
                if st.button(etiqueta_dia, key=f"cal_dia_{fecha_celda}", use_container_width=True, type=tipo_boton):
                    st.session_state["cal_dia_seleccionado"] = fecha_celda
                    st.rerun()

                st.markdown(f"<div class='cal-marcas'>{marcas}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.78em; color:rgba(255,255,255,0.45); margin-top:8px'>"
        "🔴 Examen &nbsp; 🟠 Entrega &nbsp; 📌 Otro &nbsp; 🟢 Tarea de Mi Día</p>",
        unsafe_allow_html=True
    )

    if dia_seleccionado:
        st.divider()
        st.markdown(f"#### {dia_seleccionado.strftime('%A %d de %B, %Y')}")

        eventos_dia = eventos_por_dia.get(dia_seleccionado, [])
        tareas_dia = tareas_por_dia.get(dia_seleccionado, [])

        if not eventos_dia and not tareas_dia:
            st.caption("No tienes nada guardado para este día.")
        else:
            for evento in eventos_dia:
                emoji_tipo = EMOJI_TIPO.get(evento.get("tipo"), "📌")
                materia_txt = f" · {evento['materia']}" if evento.get("materia") else ""
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"{emoji_tipo} **{evento['titulo']}**{materia_txt}")
                    if evento.get("notas"):
                        st.caption(evento["notas"])
                with col2:
                    if st.button("🗑️", key=f"cal_del_ev_{evento['id']}"):
                        eliminar_evento(evento["id"])
                        st.rerun()

            for tarea in tareas_dia:
                col1, col2 = st.columns([5, 1])
                with col1:
                    completado = st.checkbox(tarea["texto"], value=bool(tarea.get("completado")), key=f"cal_tarea_{tarea['id']}")
                    if completado != bool(tarea.get("completado")):
                        marcar_tarea(tarea["id"], completado)
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"cal_del_tarea_{tarea['id']}"):
                        eliminar_tarea(tarea["id"])
                        st.rerun()

        if st.button("➕ Agregar fecha para este día", key="cal_agregar_desde_dia"):
            st.session_state["cal_fecha_prellenada"] = dia_seleccionado
            st.session_state["cal_tab_forzar"] = "Agregar"
            st.rerun()


def mostrar_calendario(usuario):
    st.markdown("<h1 style='text-align:center;'>📅 Mi Calendario</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Tus examenes, entregas y tareas, solo para ti</p>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🗓️ Calendario", "📋 Mis fechas", "➕ Agregar"])
    with tab1:
        _seccion_calendario_mensual(usuario)
    with tab2:
        _seccion_lista(usuario)
    with tab3:
        _seccion_agregar(usuario)
