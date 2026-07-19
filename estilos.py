# -*- coding: utf-8 -*-
"""Estilos visuales (CSS) de la app, separados para no ensuciar app.py."""
import streamlit as st

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap');
    * { font-family: 'Poppins', sans-serif; }
    .stApp {
        background: linear-gradient(135deg, #0F0C29, #302B63, #24243e);
        min-height: 100vh;
    }
    .titulo-principal {
        text-align: center;
        font-size: 3em;
        font-weight: 900;
        background: linear-gradient(90deg, #00C9FF, #92FE9D, #00C9FF);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        margin-bottom: 0;
    }
    @keyframes shine {
        to { background-position: 200% center; }
    }
    .subtitulo {
        text-align: center;
        color: rgba(255,255,255,0.7);
        font-size: 1.1em;
        margin-top: 5px;
    }
    .stat-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 10px;
    }
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,201,255,0.3);
    }
    .stat-number {
        font-size: 2.5em;
        font-weight: 700;
        background: linear-gradient(90deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        color: rgba(255,255,255,0.6);
        font-size: 0.9em;
    }
    .logro-card {
        background: linear-gradient(135deg, rgba(0,201,255,0.2), rgba(146,254,157,0.2));
        border: 1px solid rgba(0,201,255,0.3);
        border-radius: 16px;
        padding: 15px;
        text-align: center;
        color: white;
        margin: 5px;
        min-height: 120px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .logro-card:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(0,201,255,0.4);
    }
    .logro-emoji { font-size: 2em; }
    .logro-nombre { font-weight: bold; font-size: 0.9em; margin-top: 5px; color: #00C9FF; }
    .logro-desc { font-size: 0.75em; opacity: 0.8; color: rgba(255,255,255,0.7); }
    .racha-card {
        background: linear-gradient(135deg, #F59E0B, #EF4444);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 0 30px rgba(239,68,68,0.4);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 30px rgba(239,68,68,0.4); }
        50% { box-shadow: 0 0 50px rgba(239,68,68,0.7); }
    }
    .stButton > button {
        background: linear-gradient(135deg, #00C9FF, #92FE9D) !important;
        color: #0F0C29 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        font-family: 'Poppins', sans-serif !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,201,255,0.5) !important;
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(0,201,255,0.5) !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: 'Poppins', sans-serif !important;
        caret-color: white !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.5) !important;
    }
    .stTextInput label {
        color: rgba(255,255,255,0.8) !important;
    }
    .stChatMessage {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px) !important;
    }
    [data-testid="stSidebar"] {
        background: rgba(15,12,41,0.95) !important;
        border-right: 1px solid rgba(0,201,255,0.2) !important;
    }
    h1, h2, h3 { color: white !important; }
    p { color: rgba(255,255,255,0.8); }
    [data-testid="stImage"] img {
        border-radius: 16px;
        box-shadow: 0 0 30px rgba(0,201,255,0.3);
    }
    @keyframes flotar {
        0%, 100% { transform: translateY(0px) scale(1); opacity: 0.3; }
        50% { transform: translateY(-20px) scale(1.5); opacity: 0.8; }
    }
</style>
"""


def aplicar_estilos():
    st.markdown(CSS, unsafe_allow_html=True)

