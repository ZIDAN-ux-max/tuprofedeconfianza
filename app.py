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
</style>
""", unsafe_allow_html=True)

st.image("imagen5.png", use_container_width=True)

st.markdown("<h1 style='text-align:center; color:#1E3A8A;'>Tu Profe de Confianza</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#3B82F6; font-size:18px;'>Aprende Matematicas e Ingles a tu ritmo, 24/7 y gratis</p>", unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.image("icono_mate.png", use_container_width=True)
    if st.button("Estudiar Matematicas", use_container_width=True):
        st.session_state.modo = "Matematicas"
with col2:
    st.image("icono_ingles.png", use_container_width=True)
    if st.button("Estudiar Ingles", use_container_width=True):
        st.session_state.modo = "Ingles"

st.divider()

if "modo" not in st.session_state:
    st.session_state.modo = "Matematicas"

modo = st.session_state.modo

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

st.markdown(f"<h3 style='color:#1E3A8A;'>Modo: {modo}</h3>", unsafe_allow_html=True)

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
