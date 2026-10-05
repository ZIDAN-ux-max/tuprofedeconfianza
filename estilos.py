# -*- coding: utf-8 -*-
"""Estilos visuales (CSS) de la app, separados para no ensuciar app.py."""
import base64

import streamlit as st

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap');
    * { font-family: 'Poppins', sans-serif; }
    html, body {
        background: transparent !important;
    }
    .stApp {
        background: transparent !important;
        min-height: 100vh;
    }
    .fondo-video {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        object-fit: cover;
        z-index: -2;
    }
    .fondo-video-overlay {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(15, 12, 41, 0.7);
        z-index: -1;
        pointer-events: none;
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
        background: rgba(15,12,41,0.82);
        backdrop-filter: blur(12px);
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
        background: rgba(15,12,41,0.82) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(12px) !important;
    }
    /* Tarjetas/contenedores con borde que arma Streamlit (st.container,
       st.expander) en Calendario, Ranking, etc. - mismo criterio: se
       destacan del video de fondo sin verse como un cuadro aparte. */
    [data-testid="stContainer"] {
        background: rgba(15,12,41,0.82);
        backdrop-filter: blur(14px);
        border-radius: 16px;
    }
    /* Checkboxes (ej: la grilla de "Mi Dia") como insignias cuadradas de
       color, en vez del tilde plano por defecto - verde/cian si esta
       marcado, gris oscuro si no. */
    [data-testid="stCheckbox"] {
        background: rgba(255,255,255,0.08);
        border: 2px solid rgba(255,255,255,0.18);
        border-radius: 8px;
        padding: 6px;
        display: flex;
        justify-content: center;
        transition: background 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stCheckbox"]:has(input:checked) {
        background: linear-gradient(135deg, #00C9FF, #92FE9D);
        border-color: #00C9FF;
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
    /* Panel de "Que quieres estudiar" del Chat: fijo respecto a la
       pantalla (no a un contenedor padre), asi no se mueve al scrollear
       la conversacion. Streamlit no tiene un contenedor "sticky" nativo,
       por eso se usa "fixed" con un ancho/posicion fijos en vez de
       depender del layout de columnas. */
    .st-key-chat_contexto_sticky {
        position: fixed !important;
        top: 5rem;
        right: 2rem;
        width: 320px;
        max-height: calc(100vh - 7rem);
        overflow-y: auto;
        z-index: 100;
    }
    /* Deja libre, a la derecha de los mensajes del chat, el mismo ancho
       que ocupa el panel fijo de arriba, para que no se tapen. */
    .st-key-chat_main_area {
        padding-right: 360px;
    }
    /* Caja de escribir del chat: un poco de color (en vez de la gris
       plana por defecto) y forzada a quedar pegada abajo de la pantalla
       de verdad, en vez de depender de que Streamlit decida "pinearla"
       solo (esa logica interna no se estaba activando). */
    [data-testid="stChatInput"] {
        border-radius: 24px;
        border: 2px solid transparent;
        background:
            linear-gradient(#1a1a3e, #1a1a3e) padding-box,
            linear-gradient(90deg, #00C9FF, #926EFE) border-box;
        position: fixed !important;
        bottom: 0.75rem;
        left: 23rem;
        right: 380px;
        width: auto;
        z-index: 999;
    }
    /* Streamlit reserva espacio para el chat_input en su lugar "natural"
       aunque se lo haya movido a "fixed" arriba - esto colapsa ese hueco
       vacio que quedaba entre los mensajes y la caja de escribir. */
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    /* Streamlit le agrega un padding extra abajo al contenido principal
       para que no quede tapado por el chat_input - lo achico, ahora que
       el chat_input ya no ocupa ese espacio (esta en "fixed"). */
    [data-testid="stMainBlockContainer"] {
        padding-bottom: 1rem !important;
    }
</style>
"""


def aplicar_estilos():
    st.markdown(CSS, unsafe_allow_html=True)


def aplicar_zoom(porcentaje):
    """Achica o agranda toda la app segun lo que eligio el usuario (100 =
    tamaño normal). Usa la propiedad CSS 'zoom' porque, a diferencia de
    'transform: scale', no deja espacios en blanco raros - funciona en
    Chrome/Edge/Safari, que es lo que corre la gran mayoria de la gente;
    en algun navegador viejo simplemente no hace nada (no rompe nada).

    En 100% no se inyecta nada: no hace falta (no cambia nada visualmente)
    y 'zoom' tiene comportamiento inconsistente entre navegadores con
    elementos 'position: fixed' adentro (como el chat_input de Streamlit),
    asi que mejor no tenerlo puesto de mas para el caso comun (default)."""
    if porcentaje == 100:
        return
    st.markdown(f"<style>.stApp {{ zoom: {porcentaje}%; }}</style>", unsafe_allow_html=True)



def fondo_video_html(nombre_archivo):
    """Arma el <video> de fondo a pantalla completa (con una capa oscura
    encima para que el texto se siga leyendo bien), leyendo el archivo del
    repo y embebiendolo directo en el HTML en vez de depender de que
    Streamlit sirva archivos estaticos (que no siempre esta habilitado).
    Si el archivo no existe todavia (por ejemplo, recien se esta por subir
    a GitHub), no rompe nada - simplemente no muestra ningun video."""
    try:
        with open(nombre_archivo, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        return ""
    return (
        f'<video class="fondo-video" autoplay loop muted playsinline>'
        f'<source src="data:video/mp4;base64,{video_b64}" type="video/mp4">'
        f'</video>'
        f'<div class="fondo-video-overlay"></div>'
    )
