# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
from supabase import create_client
import hashlib
import PyPDF2
import io

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.set_page_config(
    page_title="Tu Profe de Confianza",
    page_icon=":mortar_board:",
    layout="centered"
)

st.markdown("""
<style>
    .stApp { background-color: #EEF4FF; }
    .stChatMessage { border-radius: 15px; }
    [data-testid="stImage"] img {
        background-color: transparent !important;
        mix-blend-mode: multiply;
    }
</style>
""", unsafe_allow_html=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(email, password):
    result = supabase.table("usuarios").select("*").eq("email", email).eq("password", hash_password(password)).execute()
    if result.data:
        return result.data[0]
    return None

def registrar(nombre, email, password):
    try:
        result = supabase.table("usuarios").insert({
            "nombre": nombre,
            "email": email,
            "password": hash_password(password)
        }).execute()
        return result.data[0]
    except:
        return None

def guardar_conversacion(usuario_id, mensaje, respuesta, materia):
    supabase.table("conversaciones").insert({
        "usuario_id": usuario_id,
        "mensaje": mensaje,
        "respuesta": respuesta,
        "materia": materia
    }).execute()

def cargar_conversaciones(usuario_id, materia):
    result = supabase.table("conversaciones").select("*").eq("usuario_id", usuario_id).eq("materia", materia).execute()
    historial = []
    for conv in result.data:
        historial.append({"role": "user", "content": conv["mensaje"]})
        historial.append({"role": "assistant", "content": conv["respuesta"]})
    return historial

def extraer_texto_pdf(archivo):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(archivo.read()))
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text()
        return texto[:3000]
    except:
        return None

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.image("imagen5.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center; color:#1E3A8A;'>Tu Profe de Confianza</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#3B82F6;'>Aprende Matematicas e Ingles a tu ritmo, 24/7 y gratis</p>", unsafe_allow_html=True)
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
        if st.button("Registrarse", use_container_width=True):
            if nombre and email_reg and password_reg:
                usuario = registrar(nombre, email_reg, password_reg)
                if usuario:
                    st.session_state.usuario = usuario
                    st.rerun()
                else:
                    st.error("El email ya existe")
            else:
                st.warning("Completa todos los campos")

else:
    usuario = st.session_state.usuario

    with st.sidebar:
        st.image("imagen2.png", use_container_width=True)
        st.markdown(f"### Hola, {usuario['nombre']} 👋")
        st.divider()
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

    st.image("imagen5.png", use_container_width=True)
    st.markdown("<h1 style='text-align:center; color:#1E3A8A;'>Tu Profe de Confianza</h1>", unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.image("icono_mate.png", use_container_width=True)
    with col2:
        st.image("icono_ingles.png", use_container_width=True)

    st.divider()

    if "historial" not in st.session_state or st.session_state.get("modo_actual") != modo:
        st.session_state.historial = cargar_conversaciones(usuario["id"], modo)
        st.session_state.modo_actual = modo

    texto_pdf = ""
    if st.session_state.get("archivo"):
        if st.session_state.archivo.type == "application/pdf":
            texto_pdf = extraer_texto_pdf(st.session_state.archivo)
            if texto_pdf:
                st.info("PDF cargado - puedes preguntarme sobre el contenido")

    if modo == "Matematicas":
        system_prompt = """Eres Tu Profe de Confianza, un tutor de matematicas 
        para universitarios peruanos. Eres cercano, paciente y explicas paso a paso.
        SIEMPRE usa este formato HTML en tus respuestas:
        - Pasos numerados en verde: <span style='color:#166534; font-weight:bold'>Paso 1:</span>
        - Resultados finales en naranja: <span style='color:#C2410C; font-weight:bold'>Resultado:</span>
        - Conceptos importantes en azul: <span style='color:#1E3A8A; font-weight:bold'>concepto</span>
        Cuando escribas formulas usa LaTeX: $$formula$$
        Explicas de forma simple con ejemplos de la vida peruana.
        Cuando el usuario se equivoca lo animas y corriges con amabilidad."""
    else:
        system_prompt = """Eres Tu Profe de Confianza, un tutor de ingles
        para universitarios peruanos. Eres cercano y motivador.
        SIEMPRE usa este formato HTML en tus respuestas:
        - Palabras en ingles en azul: <span style='color:#1D4ED8; font-weight:bold'>word</span>
        - Traduccion en español en verde: <span style='color:#15803D; font-weight:bold'>palabra</span>
        - Pronunciacion en morado: <span style='color:#7E22CE; font-weight:bold'>/pronun/</span>
        - Ejemplos en naranja: <span style='color:#C2410C'>example sentence</span>
        Estructura SIEMPRE tus respuestas asi:
        1. Palabra en ingles (azul)
        2. Traduccion (verde)
        3. Pronunciacion (morado)
        4. Ejemplo (naranja)
        Corriges errores con amabilidad."""

    if texto_pdf:
        system_prompt += f"\n\nEl estudiante ha subido este documento, usalo para responder sus preguntas:\n{texto_pdf}"

    if not st.session_state.historial:
        with st.chat_message("assistant"):
            if modo == "Matematicas":
                st.write("Hola! Soy tu profe de confianza. Que tema de matematicas te esta costando?")
            else:
                st.write("Hola! Soy tu profe de confianza. En que nivel de ingles estas?")

    for mensaje in st.session_state.historial:
        if mensaje["role"] == "user":
            with st.chat_message("user"):
                st.markdown(mensaje["content"], unsafe_allow_html=True)
        else:
            with st.chat_message("assistant"):
                st.markdown(mensaje["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("Escribe tu pregunta aqui..."):
        with st.chat_message("user"):
            st.markdown(prompt, unsafe_allow_html=True)

        st.session_state.historial.append({"role": "user", "content": prompt})

        with st.spinner("Tu profe esta pensando..."):
            respuesta = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.historial
            )

        texto = respuesta.choices[0].message.content
        st.session_state.historial.append({"role": "assistant", "content": texto})
        guardar_conversacion(usuario["id"], prompt, texto, modo)

        with st.chat_message("assistant"):
            st.markdown(texto, unsafe_allow_html=True)
