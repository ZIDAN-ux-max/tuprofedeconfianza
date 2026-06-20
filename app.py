# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(
    page_title="Tu Profe de Confianza",
    page_icon=":mortar_board:",
    layout="centered"
)

st.markdown("""
<style>
    .stApp { background-color: #EEF4FF; }
    .stChatMessage { border-radius: 15px; }
    .header-container {
        text-align: center;
        padding: 10px 0 20px 0;
    }
</style>
""", unsafe_allow_html=True)

st.image("imagen5.png", use_container_width=True)

col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("imagen2.png", use_container_width=True)

st.markdown("<h1 style='text-align:center; color:#1E3A8A;'>Tu Profe de Confianza</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#3B82F6; font-size:18px;'>Aprende Matematicas e Ingles a tu ritmo, 24/7 y gratis</p>", unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.image("imagen1.png", use_container_width=True)
with col2:
    st.image("imagen3.png", use_container_width=True)

st.divider()

modo = st.selectbox("Que quieres estudiar hoy?",
                     ["Matematicas", "Ingles"])

if modo == "Matematicas":
    system_prompt = """Eres Tu Profe de Confianza, un tutor de matematicas 
    para universitarios peruanos. Eres cercano, paciente y explicas paso a paso 
    de forma simple. Usas ejemplos de la vida cotidiana peruana. 
    Cuando el usuario se equivoca lo animas y corriges con amabilidad."""
else:
    system_prompt = """Eres Tu Profe de Confianza, un tutor de ingles
    para universitarios peruanos. Eres cercano y motivador.
    Siempre muestras las frases en ingles con su traduccion.
    Corriges errores con amabilidad.
    Mezclas espanol e ingles gradualmente."""

if "historial" not in st.session_state:
    st.session_state.historial = []

if "modo_actual" not in st.session_state:
    st.session_state.modo_actual = modo

if st.session_state.modo_actual != modo:
    st.session_state.historial = []
    st.session_state.modo_actual = modo

if not st.session_state.historial:
    with st.chat_message("assistant"):
        if modo == "Matematicas":
            st.write("Hola! Soy tu profe de confianza. Que tema de matematicas te esta costando?")
        else:
            st.write("Hola! Soy tu profe de confianza. En que nivel de ingles estas?")

for mensaje in st.session_state.historial:
    if mensaje["role"] == "user":
        with st.chat_message("user"):
            st.write(mensaje["content"])
    else:
        with st.chat_message("assistant"):
            st.write(mensaje["content"])

if prompt := st.chat_input("Escribe tu pregunta aqui..."):
    with st.chat_message("user"):
        st.write(prompt)

    st.session_state.historial.append({"role": "user", "content": prompt})

    with st.spinner("Tu profe esta pensando..."):
        respuesta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}] + st.session_state.historial
        )

    texto = respuesta.choices[0].message.content
    st.session_state.historial.append({"role": "assistant", "content": texto})

    with st.chat_message("assistant"):
        st.write(texto)
