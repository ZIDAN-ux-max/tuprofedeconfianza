# -*- coding: utf-8 -*-
"""Tu Profe de Confianza - punto de entrada de la app.
Este archivo solo orquesta: arma la pantalla de login/registro, la barra
lateral, y llama a la pagina correspondiente segun lo que el alumno elija.
Toda la logica pesada vive en los otros modulos (database, tutor_ai, chat,
examen, paginas)."""
import streamlit as st

from estilos import aplicar_estilos
from database import login, registrar, registrar_asistencia, obtener_estadisticas, supabase, listar_cursos, obtener_mi_rango
from utils import obtener_nivel
from chat import mostrar_chat
from examen import mostrar_modo_examen
from documentos import mostrar_documentos
from formulario import mostrar_formulario, renderizar_generador_formulario
from calendario import mostrar_calendario
from tareas import mostrar_tareas
from revision import mostrar_revision
from paginas import mostrar_ranking, mostrar_acerca_de, mostrar_logros, mostrar_estadisticas, mostrar_mi_rango
from materias_data import CARRERAS_DISPONIBLES, materias_de_carrera

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
            carrera_reg = None
            universidad_reg = None
        else:
            grado_reg = nivel_reg
            ciclo_reg = st.selectbox("Ciclo", [str(n) for n in range(1, 11)], key="reg_ciclo")
            carrera_reg = st.selectbox("Carrera (para mostrarte las materias correctas)", CARRERAS_DISPONIBLES, key="reg_carrera")
            universidad_reg = st.text_input(
                "Universidad o instituto",
                key="reg_universidad",
                help="Asi solo veras los documentos de tu propia universidad y ciclo, no mezclados con los de otras"
            )

        if st.button("Registrarse", use_container_width=True):
            if nombre and email_reg and password_reg:
                usuario, error = registrar(nombre, email_reg, password_reg, edad=edad_reg, grado=grado_reg, ciclo=ciclo_reg, carrera=carrera_reg, universidad=universidad_reg)
                if usuario:
                    st.session_state.usuario = usuario
                    st.rerun()
                elif error == "email":
                    st.error("Ese email ya esta registrado")
                elif error == "nombre":
                    st.error("Ese nombre ya esta en uso, elige otro (ej: agrega tu apellido)")
                elif error == "cupo_lleno":
                    st.error("Ya alcanzamos el maximo de cupos disponibles por ahora. Vuelve a intentarlo mas adelante, se liberan cupos regularmente.")
                else:
                    st.error("No se pudo completar el registro, intenta de nuevo")
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

        try:
            datos_rango = obtener_mi_rango(usuario["id"])
            col_img_rango, col_txt_rango = st.columns([1, 2])
            with col_img_rango:
                st.image(f"rangos_img/{datos_rango['imagen']}", use_container_width=True)
            with col_txt_rango:
                st.markdown(
                    f"<div style='margin-top:2px'>"
                    f"<div style='color:white; font-weight:bold; font-size:0.95em; line-height:1.1'>{datos_rango['rango']}</div>"
                    f"<div style='color:#00C9FF; font-size:0.75em'>{datos_rango['puntos']} pts</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        except Exception:
            pass

        st.divider()
        seccion = st.radio("Menu", ["Chat", "Modo Examen", "Revisa mi Solucion", "Documentos", "Formulario", "Calendario", "Mi Dia", "Mi Rango", "Mis Estadisticas", "Mis Logros", "Ranking", "Acerca de"], key="menu_seccion")
        st.divider()
        curso_elegido = None
        if seccion == "Chat":
            materias_alumno = materias_de_carrera(usuario.get("carrera"))
            modo = st.radio("Que quieres estudiar?", materias_alumno)

            cursos_disponibles = listar_cursos(modo, universidad=usuario.get("universidad"))
            if not cursos_disponibles and usuario.get("universidad"):
                # fallback: si todavia no hay documentos etiquetados con tu
                # universidad (por ejemplo los subidos antes de este cambio),
                # mostramos todos los cursos de la materia para no dejarte
                # sin nada util.
                cursos_disponibles = listar_cursos(modo)
            if cursos_disponibles:
                key_selector = f"curso_selector_{modo}"
                # Si el alumno todavia no eligio nada a mano y solo hay un
                # curso subido para esta materia, lo dejamos puesto de una
                # (para que no tenga que re-seleccionarlo cada vez que la
                # pagina se recarga). Con key= aqui, Streamlit ademas
                # recuerda la eleccion durante toda la sesion en vez de
                # resetearla a "Sin curso especifico" en cada rerun.
                if key_selector not in st.session_state and len(cursos_disponibles) == 1:
                    st.session_state[key_selector] = cursos_disponibles[0]

                seleccion_curso = st.selectbox(
                    "📚 Curso (opcional)",
                    ["Sin curso especifico"] + cursos_disponibles,
                    key=key_selector,
                    help="El tutor usara tus documentos de ese curso como contexto"
                )
                curso_elegido = None if seleccion_curso == "Sin curso especifico" else seleccion_curso

            with st.expander("📋 Formulario"):
                if curso_elegido:
                    renderizar_generador_formulario(usuario, modo=modo, key_prefix=f"sidebar_{modo}_{curso_elegido}_", curso_fijo=curso_elegido)
                else:
                    st.info("Elige un curso arriba para generar su formulario.")

            with st.expander("📎 Archivo"):
                archivo = st.file_uploader("PDF o imagen", type=["pdf", "png", "jpg", "jpeg"], key=f"archivo_chat_{modo}")
                if archivo:
                    st.success(f"Cargado: {archivo.name}")
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
    elif seccion == "Documentos":
        mostrar_documentos(usuario)
    elif seccion == "Formulario":
        mostrar_formulario(usuario)
    elif seccion == "Calendario":
        mostrar_calendario(usuario)
    elif seccion == "Mi Dia":
        mostrar_tareas(usuario)
    elif seccion == "Mi Rango":
        mostrar_mi_rango(usuario)
    elif seccion == "Revisa mi Solucion":
        mostrar_revision(usuario)
    elif seccion == "Ranking":
        mostrar_ranking(usuario)
    elif seccion == "Acerca de":
        mostrar_acerca_de()
    elif seccion == "Mis Logros":
        mostrar_logros(usuario, racha)
    elif seccion == "Mis Estadisticas":
        mostrar_estadisticas(stats)
    else:
        mostrar_chat(usuario, modo, curso_elegido)
