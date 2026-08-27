# -*- coding: utf-8 -*-
"""Calendario personal: cada alumno guarda sus propias fechas de examenes
y entregas por materia. No se comparte entre alumnos (a diferencia de la
biblioteca de Documentos). Incluye una vista de mes tipo calendario real
(cuadricula con un boton por dia, estilizado con CSS para verse como
tarjeta), que tambien muestra las tareas de "Mi Dia" ademas de
examenes/entregas."""
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

TEMAS_COLORES = {
    "🎓 Año académico 2026": [(0, 201, 255), (146, 254, 157)],
    "🌙 Oscuro clásico": [(255, 255, 255)],
    "🍂 Cálido": [(245, 158, 11), (239, 68, 68)],
    "🌸 Suave": [(192, 132, 252), (0, 201, 255)],
}


def _construir_fondo(colores, opacidad):
    """Arma un color o degradado CSS a partir de 1 o 2 colores base (r,g,b)
    y una opacidad (0.0 a 1.0). El segundo color, si existe, va a la mitad
    de opacidad para que el degradado se vea suave."""
    if len(colores) == 1:
        r, g, b = colores[0]
        return f"rgba({r},{g},{b},{opacidad:.3f})"
    (r1, g1, b1), (r2, g2, b2) = colores
    return (
        f"linear-gradient(135deg, rgba({r1},{g1},{b1},{opacidad:.3f}) 0%, "
        f"rgba({r2},{g2},{b2},{opacidad * 0.5:.3f}) 100%)"
    )


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

    repetir = st.checkbox("🔁 Repetir cada semana hasta que terminen las clases", key="cal_repetir")

    fecha_inicio_clases = None
    num_semanas = None
    if repetir:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            fecha_inicio_clases = st.date_input(
                "¿Cuándo empiezan las clases?",
                value=fecha,
                key="cal_fecha_inicio_clases",
                help="Se repite el mismo día de la semana que elegiste arriba, empezando desde esta fecha."
            )
        with col_r2:
            num_semanas = st.number_input("Número de semanas del ciclo", min_value=1, max_value=20, value=16, key="cal_num_semanas")

    if st.button("Guardar en mi calendario", use_container_width=True):
        if not titulo or not titulo.strip():
            st.warning("Escribe un titulo primero")
        else:
            materia_final = None if materia == "Sin materia especifica" else materia

            if repetir:
                dia_semana_objetivo = fecha.weekday()
                primera_fecha = fecha_inicio_clases
                # ajusta al primer dia que coincida con el dia de la semana elegido, sin quedar antes del inicio de clases
                diferencia = (dia_semana_objetivo - primera_fecha.weekday()) % 7
                primera_fecha = primera_fecha + timedelta(days=diferencia)

                guardadas = 0
                for i in range(int(num_semanas)):
                    fecha_ocurrencia = primera_fecha + timedelta(weeks=i)
                    if guardar_evento(usuario["id"], titulo, fecha_ocurrencia, tipo=tipo, materia=materia_final, notas=notas):
                        guardadas += 1

                if guardadas:
                    st.success(f"Guardado: {guardadas} fechas repetidas cada semana")
                    st.session_state.pop("cal_fecha_prellenada", None)
                    st.rerun()
                else:
                    st.error("No se pudo guardar, intenta de nuevo")
            else:
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
    hoy = hoy_peru()
    if "cal_anio_actual" not in st.session_state:
        st.session_state["cal_anio_actual"] = hoy.year
    if "cal_mes_actual" not in st.session_state:
        st.session_state["cal_mes_actual"] = hoy.month

    anio = st.session_state["cal_anio_actual"]
    mes = st.session_state["cal_mes_actual"]

    fondo_elegido = st.session_state.get("cal_fondo_tema", list(TEMAS_COLORES.keys())[0])
    intensidad = st.session_state.get("cal_intensidad", 50)

    opacidad_fuerte = 0.06 + (intensidad / 100) * 0.44
    opacidad_tenue = max(0.04, opacidad_fuerte * 0.3)

    st.markdown(
        f"""
        <style>
        .st-key-cal_outer_box {{
            background:{_construir_fondo(TEMAS_COLORES[fondo_elegido], opacidad_tenue)} !important;
            border-radius: 16px !important;
            border-color: transparent !important;
            padding: 4px 6px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True, key="cal_outer_box"):
        col_fondo, col_intensidad = st.columns([2, 2])
        with col_fondo:
            fondo_elegido = st.selectbox("🎨 Fondo del calendario", list(TEMAS_COLORES.keys()), key="cal_fondo_tema")
        with col_intensidad:
            intensidad = st.slider("🎚️ Intensidad del color", 0, 100, 50, key="cal_intensidad")

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

        semanas = calendar_mod.Calendar(firstweekday=6).monthdayscalendar(anio, mes)  # empieza en Domingo
        dia_seleccionado = st.session_state.get("cal_dia_seleccionado")

        st.markdown(
            f"""<style>
            .st-key-cal_calendario_box {{
                background:{_construir_fondo(TEMAS_COLORES[fondo_elegido], opacidad_fuerte)} !important;
                border-radius:14px !important;
                border-color:transparent !important;
                box-shadow:none !important;
            }}
            .st-key-cal_dias_box div[data-testid="stButton"] button {{
                padding: 0px !important;
                min-height: 30px !important;
                height: 30px !important;
                width: 30px !important;
                border-radius: 50% !important;
                font-size: 16px !important;
                line-height: 1 !important;
                margin: 2px auto 0 auto !important;
                display: block !important;
                background: rgba(255,255,255,0.10) !important;
                background-image: none !important;
                border: 1px solid rgba(255,255,255,0.18) !important;
                box-shadow: none !important;
            }}
            </style>""",
            unsafe_allow_html=True
        )

        with st.container(border=True, key="cal_calendario_box"):
            cols_header = st.columns(7)
            for i, nombre_dia in enumerate(DIAS_SEMANA_ES):
                with cols_header[i]:
                    st.markdown(f"<p style='text-align:center; font-size:12px; color:rgba(255,255,255,0.55); font-weight:600; margin:0'>{nombre_dia}</p>", unsafe_allow_html=True)

            with st.container(key="cal_dias_box"):
                for semana in semanas:
                    cols_semana = st.columns(7)
                    for i, dia in enumerate(semana):
                        with cols_semana[i]:
                            if dia == 0:
                                st.markdown("<div style='min-height:72px'></div>", unsafe_allow_html=True)
                                continue

                            fecha_celda = date(anio, mes, dia)

                            color_punto = None
                            if fecha_celda in eventos_por_dia:
                                tipos_del_dia = {e.get("tipo") for e in eventos_por_dia[fecha_celda]}
                                if "Examen" in tipos_del_dia:
                                    color_punto = "🔴"
                                elif "Entrega" in tipos_del_dia:
                                    color_punto = "🟠"
                                elif "Otro" in tipos_del_dia:
                                    color_punto = "🟣"
                            if not color_punto and fecha_celda in tareas_por_dia:
                                color_punto = "🟢"

                            es_hoy = fecha_celda == hoy
                            es_sel = fecha_celda == dia_seleccionado
                            borde = "1.5px solid #00C9FF" if es_sel else ("1.5px solid #F59E0B" if es_hoy else "1px solid rgba(255,255,255,0.5)")
                            fondo_celda = "rgba(0,201,255,0.28)" if es_sel else ("rgba(245,158,11,0.20)" if es_hoy else "rgba(255,255,255,0.28)")

                            st.markdown(
                                f"<div style='border:{borde}; background:{fondo_celda}; border-radius:9px; "
                                f"text-align:center; padding:12px 0 4px 0; min-height:44px; font-size:16px; color:white; margin-bottom:2px'>{dia}</div>",
                                unsafe_allow_html=True
                            )

                            if st.button(color_punto or "·", key=f"cal_dia_{fecha_celda}"):
                                st.session_state["cal_dia_seleccionado"] = fecha_celda
                                st.rerun()

        st.markdown(
            "<p style='font-size:0.78em; color:rgba(255,255,255,0.45); margin-top:8px'>"
            "🔴 Examen &nbsp; 🟠 Entrega &nbsp; 🟣 Otro &nbsp; 🟢 Tarea de Mi Día</p>",
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
