# -*- coding: utf-8 -*-
"""Tu Profe de Confianza - punto de entrada de la app.
Este archivo solo orquesta: arma la pantalla de login/registro, la barra
lateral, y llama a la pagina correspondiente segun lo que el alumno elija.
Toda la logica pesada vive en los otros modulos (database, tutor_ai, chat,
examen, paginas)."""
import streamlit as st

from estilos import aplicar_estilos
from database import login, registrar, registrar_asistencia, obtener_estadisticas, supabase
from utils import obtener_nivel
from chat import mostrar_chat
from examen import mostrar_modo_examen
from paginas import mostrar_ranking, mostrar_acerca_de, mostrar_logros, mostrar_estadisticas

st.set_page_config(
    page_title="Tu Profe de Confianza",
    page_icon=":mortar_board:",
    layout="centered"
)
aplicar_estilos()


# ===================== LOGIN / REGISTRO =====================

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.image("imagen5.png", use_container_width=True)
    st.markdown("<p class='titulo-principal'>Tu Profe de Confianza</p>", unsafe_allow_html=True)
    st.markdown("<p class='subtitulo'>Aprende Matematicas e Ingles a tu ritmo, 24/7 y gratis</p>", unsafe_allow_html=True)
    st.divider()
    try:
        total_usuarios = supabase.table("usuarios").select("id", count="exact").execute()
        st.markdown(f"<p style='text-align:center; color:rgba(255,255,255,0.6)'>🎓 {total_usuarios.count} estudiantes ya aprenden con nosotros</p>", unsafe_allow_html=True)
    except Exception:
        pass
    st.divider()

    tab1, tab2 = st.tabs(["Iniciar Sesion", "Registrarse"])

    with tab1:
        st.subheader("Bienvenido de vuelta")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contrasena", type="password", key="login_pass")
        if st.button("Entrar", use_container_width=True):
            usuario = login(email, password)
            if usuario:
                st.session_state.usuario = usuario
                st.rerun()
            else:
                st.error("Email o contrasena incorrectos")

    with tab2:
        st.subheader("Crea tu cuenta gratis")
        nombre = st.text_input("Tu nombre", key="reg_nombre")
        email_reg = st.text_input("Email", key="reg_email")
        password_reg = st.text_input("Contrasena", type="password", key="reg_pass")

        st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:0.85em; margin-top:10px'>Cuentanos un poco mas de ti asi tu profe se adapta mejor:</p>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            edad_reg = st.number_input("Edad", min_value=10, max_value=90, value=18, step=1, key="reg_edad")
        with col_b:
            nivel_reg = st.selectbox("Nivel educativo", ["Colegio", "Instituto", "Universidad"], key="reg_nivel")

        if nivel_reg == "Colegio":
            grado_reg = st.selectbox(
                "Grado",
                [f"{n}° de secundaria" for n in range(1, 6)] + [f"{n}° de primaria" for n in range(1, 7)],
                key="reg_grado_colegio"
            )
            ciclo_reg = None
        else:
            grado_reg = nivel_reg
            ciclo_reg = st.selectbox("Ciclo", [str(n) for n in range(1, 11)], key="reg_ciclo")

        if st.button("Registrarse", use_container_width=True):
            if nombre and email_reg and password_reg:
                usuario = registrar(nombre, email_reg, password_reg, edad=edad_reg, grado=grado_reg, ciclo=ciclo_reg)
                if usuario:
                    st.session_state.usuario = usuario
                    st.rerun()
                else:
                    st.error("El email ya existe")
            else:
                st.warning("Completa todos los campos")


# ===================== APP PRINCIPAL (usuario ya logueado) =====================

else:
    usuario = st.session_state.usuario
    racha = registrar_asistencia(usuario["id"])
    stats = obtener_estadisticas(usuario["id"])
    nivel, nivel_color = obtener_nivel(stats["total"])

    with st.sidebar:
        st.image("imagen2.png", use_container_width=True)
        st.markdown(f"### Hola, {usuario['nombre']} 👋")
        st.markdown(f"<span style='background:{nivel_color}; color:white; padding:3px 10px; border-radius:20px; font-size:0.85em'>{nivel}</span>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#F59E0B; font-weight:bold; margin-top:8px'>🔥 Racha: {racha} dias</p>", unsafe_allow_html=True)
        st.divider()
        seccion = st.radio("Menu", ["Chat", "Modo Examen", "Mis Estadisticas", "Mis Logros", "Ranking", "Acerca de"])
        st.divider()
        if seccion == "Chat":
            modo = st.radio("Que quieres estudiar?", ["Matematicas", "Ingles"])
            st.divider()
            st.markdown("### Sube un archivo")
            archivo = st.file_uploader("PDF o imagen", type=["pdf", "png", "jpg", "jpeg"])
            if archivo:
                st.success(f"Archivo cargado: {archivo.name}")
                st.session_state.archivo = archivo
            else:
                st.session_state.archivo = None
        st.divider()
        if st.button("Cerrar sesion", use_container_width=True):
            st.session_state.usuario = None
            st.session_state.historial = []
            st.rerun()

    if seccion == "Modo Examen":
        mostrar_modo_examen(usuario)
    elif seccion == "Ranking":
        mostrar_ranking(usuario)
    elif seccion == "Acerca de":
        mostrar_acerca_de()
    elif seccion == "Mis Logros":
        mostrar_logros(usuario, racha)
    elif seccion == "Mis Estadisticas":
        mostrar_estadisticas(stats)
    else:
        mostrar_chat(usuario, modo)
