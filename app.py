# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
from supabase import create_client
import hashlib
import PyPDF2
import io
import json
import random
from datetime import datetime, timedelta, date

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

st.set_page_config(
    page_title="Tu Profe de Confianza",
    page_icon=":mortar_board:",
    layout="centered"
)

st.markdown("""
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
""", unsafe_allow_html=True)

LOGROS_DISPONIBLES = [
    {"nombre": "Primera Pregunta", "descripcion": "Hiciste tu primera pregunta", "emoji": "🌟", "condicion": "total", "valor": 1},
    {"nombre": "Estudiante Activo", "descripcion": "10 preguntas en total", "emoji": "📚", "condicion": "total", "valor": 10},
    {"nombre": "Crack del Saber", "descripcion": "50 preguntas en total", "emoji": "🏆", "condicion": "total", "valor": 50},
    {"nombre": "Centenario", "descripcion": "100 preguntas en total", "emoji": "💯", "condicion": "total", "valor": 100},
    {"nombre": "Matematico", "descripcion": "10 preguntas de matematicas", "emoji": "📐", "condicion": "matematicas", "valor": 10},
    {"nombre": "Crack de Mates", "descripcion": "50 preguntas de matematicas", "emoji": "🔢", "condicion": "matematicas", "valor": 50},
    {"nombre": "Ingles Basic", "descripcion": "10 preguntas de ingles", "emoji": "🇺🇸", "condicion": "ingles", "valor": 10},
    {"nombre": "English Master", "descripcion": "50 preguntas de ingles", "emoji": "🌍", "condicion": "ingles", "valor": 50},
    {"nombre": "Estudiantazo", "descripcion": "10 preguntas en un dia", "emoji": "⚡", "condicion": "hoy", "valor": 10},
    {"nombre": "Imparable", "descripcion": "20 preguntas en un dia", "emoji": "🔥", "condicion": "hoy", "valor": 20},
    {"nombre": "Primer Parcial", "descripcion": "7 dias seguidos estudiando", "emoji": "🎓", "condicion": "racha", "valor": 7},
    {"nombre": "Aplicado", "descripcion": "30 dias seguidos estudiando", "emoji": "📝", "condicion": "racha", "valor": 30},
    {"nombre": "En Racha", "descripcion": "3 dias seguidos estudiando", "emoji": "🔥", "condicion": "racha", "valor": 3},
    {"nombre": "Madrugador", "descripcion": "Estudio antes de las 7am", "emoji": "⏰", "condicion": "hora", "valor": 7},
    {"nombre": "Noctambulo", "descripcion": "Estudio despues de las 11pm", "emoji": "🌙", "condicion": "hora", "valor": 23},
    {"nombre": "Perseverante", "descripcion": "200 preguntas en total", "emoji": "💪", "condicion": "total", "valor": 200},
    {"nombre": "Bibliofilo", "descripcion": "Subio 5 archivos PDF", "emoji": "📖", "condicion": "pdfs", "valor": 5},
]

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
        "materia": materia,
        "fecha": datetime.now().isoformat()
    }).execute()

def cargar_conversaciones(usuario_id, materia):
    result = supabase.table("conversaciones").select("*").eq("usuario_id", usuario_id).eq("materia", materia).execute()
    historial = []
    for conv in result.data:
        historial.append({"role": "user", "content": conv["mensaje"]})
        historial.append({"role": "assistant", "content": conv["respuesta"]})
    return historial

def registrar_asistencia(usuario_id):
    try:
        hoy = date.today().isoformat()
        hora_actual = datetime.now().hour
        existe = supabase.table("asistencia").select("*").eq("usuario_id", usuario_id).eq("fecha", hoy).execute()
        if not existe.data:
            usuario = supabase.table("usuarios").select("*").eq("id", usuario_id).execute().data[0]
            ultima = usuario.get("ultima_visita")
            racha_actual = usuario.get("racha") or 0
            if ultima:
                ultima_date = date.fromisoformat(str(ultima).split("T")[0])
                diferencia = (date.today() - ultima_date).days
                if diferencia == 1:
                    racha_actual += 1
                elif diferencia > 1:
                    racha_actual = 1
            else:
                racha_actual = 1
            supabase.table("asistencia").insert({
                "usuario_id": usuario_id,
                "fecha": hoy,
                "racha": racha_actual,
                "hora": hora_actual
            }).execute()
            supabase.table("usuarios").update({
                "racha": racha_actual,
                "ultima_visita": hoy
            }).eq("id", usuario_id).execute()
        return supabase.table("usuarios").select("racha").eq("id", usuario_id).execute().data[0].get("racha", 0)
    except:
        return 0

def obtener_estadisticas(usuario_id):
    result = supabase.table("conversaciones").select("*").eq("usuario_id", usuario_id).execute()
    total = len(result.data)
    mate = len([c for c in result.data if c["materia"] == "Matematicas"])
    ingles = len([c for c in result.data if c["materia"] == "Ingles"])
    hoy = datetime.now().date()
    semana = datetime.now() - timedelta(days=7)
    hoy_count = 0
    semana_count = 0
    for c in result.data:
        try:
            if c.get("fecha"):
                fecha = datetime.fromisoformat(str(c["fecha"]).replace("Z", "+00:00").split("+")[0])
                if fecha.date() == hoy:
                    hoy_count += 1
                if fecha >= semana.replace(tzinfo=None):
                    semana_count += 1
        except:
            pass
    try:
        racha_result = supabase.table("usuarios").select("racha").eq("id", usuario_id).execute()
        racha_val = racha_result.data[0].get("racha", 0) if racha_result.data else 0
    except:
        racha_val = 0
    hora_actual = datetime.now().hour
    return {
        "total": total,
        "matematicas": mate,
        "ingles": ingles,
        "hoy": hoy_count,
        "semana": semana_count,
        "racha": racha_val,
        "hora": hora_actual,
        "pdfs": 0
    }

def obtener_ranking():
    try:
        result = supabase.table("conversaciones").select("usuario_id").execute()
        conteo = {}
        for c in result.data:
            uid = c["usuario_id"]
            conteo[uid] = conteo.get(uid, 0) + 1
        ranking = []
        for uid, total in sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]:
            usuario = supabase.table("usuarios").select("nombre, racha").eq("id", uid).execute()
            if usuario.data:
                logros = supabase.table("logros").select("nombre").eq("usuario_id", uid).execute()
                ranking.append({
                    "nombre": usuario.data[0]["nombre"],
                    "total": total,
                    "racha": usuario.data[0].get("racha", 0),
                    "logros": len(logros.data)
                })
        return ranking
    except:
        return []

def obtener_logros_usuario(usuario_id):
    result = supabase.table("logros").select("nombre").eq("usuario_id", usuario_id).execute()
    return [l["nombre"] for l in result.data]

def otorgar_logro(usuario_id, logro):
    supabase.table("logros").insert({
        "usuario_id": usuario_id,
        "nombre": logro["nombre"],
        "descripcion": logro["descripcion"],
        "emoji": logro["emoji"],
        "fecha": datetime.now().isoformat()
    }).execute()

def verificar_logros(usuario_id, stats):
    logros_actuales = obtener_logros_usuario(usuario_id)
    nuevos_logros = []
    for logro in LOGROS_DISPONIBLES:
        if logro["nombre"] not in logros_actuales:
            condicion = logro["condicion"]
            valor = logro["valor"]
            if condicion == "hora":
                if valor == 7 and stats["hora"] < 7:
                    otorgar_logro(usuario_id, logro)
                    nuevos_logros.append(logro)
                elif valor == 23 and stats["hora"] >= 23:
                    otorgar_logro(usuario_id, logro)
                    nuevos_logros.append(logro)
            elif condicion in stats and stats[condicion] >= valor:
                otorgar_logro(usuario_id, logro)
                nuevos_logros.append(logro)
    return nuevos_logros

def extraer_texto_pdf(archivo):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(archivo.read()))
        texto = ""
        for page in pdf_reader.pages:
            texto += page.extract_text()
        return texto[:3000]
    except:
        return None

def obtener_nivel(total):
    if total < 10:
        return "Principiante 🌱", "#6B7280"
    elif total < 50:
        return "Intermedio ⭐", "#D97706"
    elif total < 100:
        return "Avanzado 🔥", "#2563EB"
    else:
        return "Experto 👑", "#7C3AED"

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
    except:
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

    # ===================== MODO EXAMEN =====================
    if seccion == "Modo Examen":
        st.markdown("<h1 style='text-align:center;'>📝 Modo Examen</h1>", unsafe_allow_html=True)
        st.divider()

        materia_examen = st.selectbox("Elige la materia del examen", ["Matematicas", "Ingles"])

        if "examen_activo" not in st.session_state:
            st.session_state.examen_activo = False
        if "preguntas_examen" not in st.session_state:
            st.session_state.preguntas_examen = []
        if "respuestas_examen" not in st.session_state:
            st.session_state.respuestas_examen = {}
        if "examen_terminado" not in st.session_state:
            st.session_state.examen_terminado = False
        if "resultado_examen" not in st.session_state:
            st.session_state.resultado_examen = None

        if not st.session_state.examen_activo and not st.session_state.examen_terminado:
            st.markdown("""
            <div style='background:rgba(255,255,255,0.05); border:1px solid rgba(0,201,255,0.2); border-radius:16px; padding:25px; text-align:center;'>
                <div style='font-size:3em'>📝</div>
                <h3 style='color:#00C9FF'>Pon a prueba tus conocimientos</h3>
                <p style='color:rgba(255,255,255,0.7)'>El examen tiene 9 preguntas mixtas:</p>
                <p style='color:rgba(255,255,255,0.7)'>✅ 3 preguntas de opcion multiple</p>
                <p style='color:rgba(255,255,255,0.7)'>✍️ 3 preguntas de respuesta abierta</p>
                <p style='color:rgba(255,255,255,0.7)'>🔗 3 preguntas de relacionar conceptos</p>
            </div>
            """, unsafe_allow_html=True)
            st.divider()

            if st.button("🚀 Iniciar Examen", use_container_width=True):
                with st.spinner("Generando tu examen personalizado..."):
                    prompt_examen = f"""Crea un examen de {materia_examen} para universitarios peruanos con EXACTAMENTE este formato JSON y nada mas:
{{
  "preguntas": [
    {{
      "tipo": "multiple",
      "pregunta": "texto de la pregunta",
      "opciones": ["A) opcion1", "B) opcion2", "C) opcion3", "D) opcion4"],
      "correcta": "A"
    }},
    {{
      "tipo": "multiple",
      "pregunta": "texto de la pregunta",
      "opciones": ["A) opcion1", "B) opcion2", "C) opcion3", "D) opcion4"],
      "correcta": "B"
    }},
    {{
      "tipo": "multiple",
      "pregunta": "texto de la pregunta",
      "opciones": ["A) opcion1", "B) opcion2", "C) opcion3", "D) opcion4"],
      "correcta": "C"
    }},
    {{
      "tipo": "abierta",
      "pregunta": "texto de la pregunta abierta",
      "correcta": "respuesta esperada"
    }},
    {{
      "tipo": "abierta",
      "pregunta": "texto de la pregunta abierta",
      "correcta": "respuesta esperada"
    }},
    {{
      "tipo": "abierta",
      "pregunta": "texto de la pregunta abierta",
      "correcta": "respuesta esperada"
    }},
    {{
      "tipo": "relacionar",
      "pregunta": "Relaciona cada concepto con su definicion",
      "columna_a": ["concepto1", "concepto2", "concepto3"],
      "columna_b": ["definicion1", "definicion2", "definicion3"],
      "correcta": {{"concepto1": "definicion1", "concepto2": "definicion2", "concepto3": "definicion3"}}
    }},
    {{
      "tipo": "relacionar",
      "pregunta": "Relaciona cada termino con su significado",
      "columna_a": ["termino1", "termino2", "termino3"],
      "columna_b": ["significado1", "significado2", "significado3"],
      "correcta": {{"termino1": "significado1", "termino2": "significado2", "termino3": "significado3"}}
    }},
    {{
      "tipo": "relacionar",
      "pregunta": "Relaciona correctamente",
      "columna_a": ["item1", "item2", "item3"],
      "columna_b": ["match1", "match2", "match3"],
      "correcta": {{"item1": "match1", "item2": "match2", "item3": "match3"}}
    }}
  ]
}}
Responde SOLO con el JSON, sin explicaciones ni texto adicional."""

                    respuesta_examen = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt_examen}],
                        max_tokens=2000
                    )

                    try:
                        texto_json = respuesta_examen.choices[0].message.content
                        texto_json = texto_json.replace("```json", "").replace("```", "").strip()
                        datos_examen = json.loads(texto_json)
                        st.session_state.preguntas_examen = datos_examen["preguntas"]
                        st.session_state.examen_activo = True
                        st.session_state.respuestas_examen = {}
                        st.session_state.examen_terminado = False
                        st.rerun()
                    except:
                        st.error("Error generando el examen. Intenta de nuevo.")

        elif st.session_state.examen_activo and not st.session_state.examen_terminado:
            preguntas = st.session_state.preguntas_examen
            total = len(preguntas)

            respondidas = len(st.session_state.respuestas_examen)
            st.markdown(f"<p style='color:rgba(255,255,255,0.6)'>Progreso: {respondidas}/{total} preguntas respondidas</p>", unsafe_allow_html=True)
            st.progress(respondidas / total if total > 0 else 0)
            st.divider()

            for i, pregunta in enumerate(preguntas):
                tipo = pregunta.get("tipo")
                st.markdown(f"<p style='color:#00C9FF; font-weight:bold'>Pregunta {i+1} de {total}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:white; font-size:1.1em'>{pregunta['pregunta']}</p>", unsafe_allow_html=True)

                if tipo == "multiple":
                    opciones = pregunta.get("opciones", [])
                    resp = st.radio(
                        "Selecciona tu respuesta:",
                        opciones,
                        key=f"preg_{i}",
                        index=None
                    )
                    if resp:
                        letra = resp.split(")")[0].strip()
                        st.session_state.respuestas_examen[i] = letra

                elif tipo == "abierta":
                    resp = st.text_area(
                        "Escribe tu respuesta:",
                        key=f"preg_{i}",
                        height=100,
                        placeholder="Escribe aqui tu respuesta..."
                    )
                    if resp and resp.strip():
                        st.session_state.respuestas_examen[i] = resp.strip()

                elif tipo == "relacionar":
                    columna_a = pregunta.get("columna_a", [])
                    columna_b = pregunta.get("columna_b", [])
                    if f"columna_b_mezclada_{i}" not in st.session_state:
                        mezclada = columna_b.copy()
                        random.shuffle(mezclada)
                        st.session_state[f"columna_b_mezclada_{i}"] = mezclada
                    columna_b_mezclada = st.session_state[f"columna_b_mezclada_{i}"]

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("<p style='color:#92FE9D; font-weight:bold'>Columna A</p>", unsafe_allow_html=True)
                        for item in columna_a:
                            st.markdown(f"<p style='color:white; background:rgba(255,255,255,0.05); padding:8px; border-radius:8px; margin:4px 0'>📌 {item}</p>", unsafe_allow_html=True)
                    with col2:
                        st.markdown("<p style='color:#F59E0B; font-weight:bold'>Columna B</p>", unsafe_allow_html=True)
                        relaciones = {}
                        for j, item_a in enumerate(columna_a):
                            seleccion = st.selectbox(
                                f"'{item_a}' corresponde a:",
                                ["-- Selecciona --"] + columna_b_mezclada,
                                key=f"rel_{i}_{j}"
                            )
                            if seleccion != "-- Selecciona --":
                                relaciones[item_a] = seleccion
                        if len(relaciones) == len(columna_a):
                            st.session_state.respuestas_examen[i] = relaciones

                st.divider()

            respondidas_actual = len(st.session_state.respuestas_examen)
            if respondidas_actual == total:
                if st.button("✅ Entregar Examen", use_container_width=True):
                    with st.spinner("Calificando tu examen..."):
                        puntaje = 0
                        resultados = []

                        for i, pregunta in enumerate(preguntas):
                            tipo = pregunta.get("tipo")
                            resp_usuario = st.session_state.respuestas_examen.get(i)
                            correcta = pregunta.get("correcta")

                            if tipo == "multiple":
                                es_correcta = str(resp_usuario).strip().upper() == str(correcta).strip().upper()
                                if es_correcta:
                                    puntaje += 1
                                resultados.append({
                                    "pregunta": pregunta["pregunta"],
                                    "tipo": tipo,
                                    "tu_respuesta": resp_usuario,
                                    "correcta": correcta,
                                    "es_correcta": es_correcta
                                })

                            elif tipo == "abierta":
                                eval_prompt = f"""Evalua si esta respuesta es correcta o parcialmente correcta.
Pregunta: {pregunta['pregunta']}
Respuesta correcta esperada: {correcta}
Respuesta del estudiante: {resp_usuario}
Responde SOLO con este JSON: {{"correcta": true/false, "parcial": true/false, "feedback": "explicacion breve"}}"""
                                eval_resp = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=[{"role": "user", "content": eval_prompt}],
                                    max_tokens=200
                                )
                                try:
                                    eval_json = eval_resp.choices[0].message.content.replace("```json","").replace("```","").strip()
                                    eval_data = json.loads(eval_json)
                                    if eval_data.get("correcta"):
                                        puntaje += 1
                                        es_correcta = True
                                    elif eval_data.get("parcial"):
                                        puntaje += 0.5
                                        es_correcta = None
                                    else:
                                        es_correcta = False
                                    resultados.append({
                                        "pregunta": pregunta["pregunta"],
                                        "tipo": tipo,
                                        "tu_respuesta": resp_usuario,
                                        "correcta": correcta,
                                        "es_correcta": es_correcta,
                                        "feedback": eval_data.get("feedback", "")
                                    })
                                except:
                                    resultados.append({
                                        "pregunta": pregunta["pregunta"],
                                        "tipo": tipo,
                                        "tu_respuesta": resp_usuario,
                                        "correcta": correcta,
                                        "es_correcta": False,
                                        "feedback": ""
                                    })

                            elif tipo == "relacionar":
                                correctas_rel = correcta if isinstance(correcta, dict) else {}
                                resp_rel = resp_usuario if isinstance(resp_usuario, dict) else {}
                                aciertos = sum(1 for k, v in resp_rel.items() if correctas_rel.get(k) == v)
                                total_rel = len(correctas_rel)
                                if total_rel > 0:
                                    puntaje_rel = aciertos / total_rel
                                    puntaje += puntaje_rel
                                    es_correcta = aciertos == total_rel
                                else:
                                    es_correcta = False
                                resultados.append({
                                    "pregunta": pregunta["pregunta"],
                                    "tipo": tipo,
                                    "tu_respuesta": resp_rel,
                                    "correcta": correctas_rel,
                                    "es_correcta": es_correcta,
                                    "aciertos": aciertos,
                                    "total_rel": total_rel
                                })

                        nota = round((puntaje / total) * 20, 1)
                        st.session_state.resultado_examen = {
                            "nota": nota,
                            "puntaje": puntaje,
                            "total": total,
                            "resultados": resultados,
                            "materia": materia_examen
                        }
                        st.session_state.examen_activo = False
                        st.session_state.examen_terminado = True

                        try:
                            supabase.table("examenes").insert({
                                "usuario_id": usuario["id"],
                                "materia": materia_examen,
                                "pregunta": f"Examen completo - {total} preguntas",
                                "opciones": json.dumps(resultados),
                                "respuesta_correcta": str(nota),
                                "respuesta_usuario": str(puntaje),
                                "correcta": nota >= 11,
                                "fecha": datetime.now().isoformat()
                            }).execute()
                        except:
                            pass
                        st.rerun()
            else:
                st.warning(f"Faltan {total - respondidas_actual} preguntas por responder")

        elif st.session_state.examen_terminado and st.session_state.resultado_examen:
            resultado = st.session_state.resultado_examen
            nota = resultado["nota"]

            if nota >= 18:
                emoji_nota = "🏆"
                color_nota = "#92FE9D"
                mensaje = "Excelente! Eres un crack!"
            elif nota >= 14:
                emoji_nota = "⭐"
                color_nota = "#00C9FF"
                mensaje = "Muy bien! Sigue asi!"
            elif nota >= 11:
                emoji_nota = "✅"
                color_nota = "#F59E0B"
                mensaje = "Aprobaste! Puedes mejorar!"
            else:
                emoji_nota = "📚"
                color_nota = "#EF4444"
                mensaje = "Reprobaste. Sigue estudiando!"

            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.05); border:1px solid {color_nota}; border-radius:16px; padding:30px; text-align:center;'>
                <div style='font-size:4em'>{emoji_nota}</div>
                <div style='font-size:3em; font-weight:900; color:{color_nota}'>{nota}/20</div>
                <div style='font-size:1.2em; color:white; margin-top:10px'>{mensaje}</div>
                <div style='color:rgba(255,255,255,0.6); margin-top:5px'>{resultado['materia']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
            st.markdown("<h3 style='color:white'>Revision del examen:</h3>", unsafe_allow_html=True)

            for i, res in enumerate(resultado["resultados"]):
                if res["es_correcta"] == True:
                    icono = "✅"
                    color = "rgba(146,254,157,0.1)"
                    borde = "rgba(146,254,157,0.3)"
                elif res["es_correcta"] is None:
                    icono = "⚡"
                    color = "rgba(245,158,11,0.1)"
                    borde = "rgba(245,158,11,0.3)"
                else:
                    icono = "❌"
                    color = "rgba(239,68,68,0.1)"
                    borde = "rgba(239,68,68,0.3)"

                st.markdown(f"""
                <div style='background:{color}; border:1px solid {borde}; border-radius:12px; padding:15px; margin-bottom:10px;'>
                    <p style='color:white; font-weight:bold'>{icono} Pregunta {i+1}: {res['pregunta']}</p>
                    <p style='color:rgba(255,255,255,0.7); font-size:0.9em'>Tu respuesta: {res['tu_respuesta']}</p>
                    <p style='color:rgba(255,255,255,0.7); font-size:0.9em'>Respuesta correcta: {res['correcta']}</p>
                    {f"<p style='color:#F59E0B; font-size:0.85em'>{res.get('feedback','')}</p>" if res.get('feedback') else ''}
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            if st.button("🔄 Nuevo Examen", use_container_width=True):
                st.session_state.examen_activo = False
                st.session_state.examen_terminado = False
                st.session_state.preguntas_examen = []
                st.session_state.respuestas_examen = {}
                st.session_state.resultado_examen = None
                for key in list(st.session_state.keys()):
                    if key.startswith("columna_b_mezclada_") or key.startswith("rel_") or key.startswith("preg_"):
                        del st.session_state[key]
                st.rerun()

    # ===================== RANKING =====================
    elif seccion == "Ranking":
        st.markdown("<h1 style='text-align:center;'>🏆 Ranking de Estudiantes</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Compite con tus companeros y llega al top!</p>", unsafe_allow_html=True)
        st.divider()
        ranking = obtener_ranking()
        medallas = ["🥇", "🥈", "🥉"]
        for i, est in enumerate(ranking):
            medalla = medallas[i] if i < 3 else f"#{i+1}"
            es_yo = est["nombre"] == usuario["nombre"]
            color = "rgba(0,201,255,0.1)" if es_yo else "rgba(255,255,255,0.05)"
            borde = "1px solid rgba(0,201,255,0.5)" if es_yo else "1px solid rgba(255,255,255,0.1)"
            st.markdown(f"""
            <div style='background:{color}; border:{borde}; border-radius:16px;
                        padding:15px; margin-bottom:8px;'>
                <span style='font-size:1.5em'>{medalla}</span>
                <strong style='color:white; margin-left:10px'>{est['nombre']}</strong>
                {'<span style="color:#00C9FF; font-size:0.8em"> (Tu)</span>' if es_yo else ''}
                <span style='float:right; color:rgba(255,255,255,0.6)'>
                    💬 {est['total']} &nbsp; 🔥 {est['racha']} &nbsp; 🏅 {est['logros']}
                </span>
            </div>
            """, unsafe_allow_html=True)

    elif seccion == "Acerca de":
        st.markdown("<h1 style='text-align:center;'>Acerca de Tu Profe de Confianza</h1>", unsafe_allow_html=True)
        st.divider()
        st.markdown("""
        <div style='background:rgba(255,255,255,0.05); border:1px solid rgba(0,201,255,0.2); border-radius:16px; padding:25px;'>
            <h3 style='color:#00C9FF'>Nuestra Mision</h3>
            <p style='color:rgba(255,255,255,0.8)'>Hacer la educacion accesible para todos los estudiantes peruanos,
            con un tutor de IA disponible 24/7 que explica de forma simple y cercana.</p>
            <h3 style='color:#00C9FF'>Que ofrecemos</h3>
            <p style='color:rgba(255,255,255,0.8)'>✅ Tutor de Matematicas con explicaciones paso a paso</p>
            <p style='color:rgba(255,255,255,0.8)'>✅ Tutor de Ingles con pronunciacion y traduccion</p>
            <p style='color:rgba(255,255,255,0.8)'>✅ Analisis de tus documentos y libros</p>
            <p style='color:rgba(255,255,255,0.8)'>✅ Sistema de logros para motivarte</p>
            <p style='color:rgba(255,255,255,0.8)'>✅ Ranking de competencia entre estudiantes</p>
            <p style='color:rgba(255,255,255,0.8)'>✅ Registro de asistencia y racha diaria</p>
            <p style='color:rgba(255,255,255,0.8)'>✅ Historial de conversaciones guardado</p>
            <h3 style='color:#00C9FF'>Contacto</h3>
            <p style='color:rgba(255,255,255,0.8)'>Tienes sugerencias? Escribenos y mejoramos juntos.</p>
        </div>
        """, unsafe_allow_html=True)

    elif seccion == "Mis Logros":
        st.markdown("<h1 style='text-align:center;'>Mis Logros</h1>", unsafe_allow_html=True)
        st.divider()
        logros_ganados = obtener_logros_usuario(usuario["id"])
        st.markdown(f"<h3 style='color:white'>Tienes {len(logros_ganados)} de {len(LOGROS_DISPONIBLES)} logros 🏆</h3>", unsafe_allow_html=True)
        if racha > 0:
            st.markdown(f"""
            <div class='racha-card'>
                <div style='font-size:2em'>🔥</div>
                <div style='font-size:1.5em; font-weight:bold'>{racha} dias de racha</div>
                <div style='font-size:0.9em; opacity:0.9'>Sigue estudiando cada dia para no perderla!</div>
            </div>
            """, unsafe_allow_html=True)
        st.divider()
        cols = st.columns(3)
        for i, logro in enumerate(LOGROS_DISPONIBLES):
            with cols[i % 3]:
                if logro["nombre"] in logros_ganados:
                    st.markdown(f"""
                    <div class='logro-card'>
                        <div class='logro-emoji'>{logro['emoji']}</div>
                        <div class='logro-nombre'>{logro['nombre']}</div>
                        <div class='logro-desc'>{logro['descripcion']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='logro-card' style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.3)'>
                        <div class='logro-emoji'>🔒</div>
                        <div style='font-weight:bold; font-size:0.9em; margin-top:5px'>{logro['nombre']}</div>
                        <div style='font-size:0.75em; opacity:0.6'>{logro['descripcion']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    elif seccion == "Mis Estadisticas":
        st.markdown("<h1 style='text-align:center;'>Mis Estadisticas</h1>", unsafe_allow_html=True)
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='stat-card'><div class='stat-number'>{stats['total']}</div><div class='stat-label'>Total preguntas</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='stat-card'><div class='stat-number'>{stats['hoy']}</div><div class='stat-label'>Preguntas hoy</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='stat-card'><div class='stat-number'>{stats['semana']}</div><div class='stat-label'>Esta semana</div></div>", unsafe_allow_html=True)
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='stat-card'><div class='stat-number'>📐 {stats['matematicas']}</div><div class='stat-label'>Matematicas</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='stat-card'><div class='stat-number'>🇺🇸 {stats['ingles']}</div><div class='stat-label'>Ingles</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='stat-card'><div class='stat-number'>🔥 {stats['racha']}</div><div class='stat-label'>Dias de racha</div></div>", unsafe_allow_html=True)
        st.divider()
        if stats['total'] > 0:
            materia_favorita = "Matematicas" if stats['matematicas'] >= stats['ingles'] else "Ingles"
            st.success(f"Tu materia favorita es: **{materia_favorita}** 🎯")
            if stats['hoy'] == 0:
                st.warning("No has estudiado hoy. Abre el chat!")
            elif stats['hoy'] < 5:
                st.info(f"Llevas {stats['hoy']} preguntas hoy. Sigue asi!")
            else:
                st.success(f"Excelente! Llevas {stats['hoy']} preguntas hoy. Eres un crack!")
        else:
            st.info("Aun no tienes estadisticas. Ve al chat y empieza!")

    else:
        if "modo" not in st.session_state:
            st.session_state.modo = "Matematicas"
        modo = st.session_state.get("modo", "Matematicas")

        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.image("imagen2.png", use_container_width=True)

        st.markdown(f"""
        <div style='text-align:center; padding:10px 0'>
            <span style='font-size:1.1em; color:rgba(255,255,255,0.7)'>
            Estudiando: <strong style='color:#00C9FF'>{"📐 Matematicas" if modo == "Matematicas" else "🇺🇸 Ingles"}</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)
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
            - Pasos numerados en verde: <span style='color:#92FE9D; font-weight:bold'>Paso 1:</span>
            - Resultados finales en naranja: <span style='color:#F59E0B; font-weight:bold'>Resultado:</span>
            - Conceptos importantes en azul: <span style='color:#00C9FF; font-weight:bold'>concepto</span>
            Cuando escribas formulas usa LaTeX: $$formula$$
            Explicas de forma simple con ejemplos de la vida peruana.
            Cuando el usuario se equivoca lo animas y corriges con amabilidad."""
            sugerencias = [
                "Que es una integral?",
                "Explicame las derivadas",
                "Como resuelvo una ecuacion cuadratica?",
                "Que es el limite de una funcion?"
            ]
        else:
            system_prompt = """Eres Tu Profe de Confianza, un tutor de ingles
            para universitarios peruanos. Eres cercano y motivador.
            SIEMPRE usa este formato HTML en tus respuestas:
            - Palabras en ingles en azul: <span style='color:#00C9FF; font-weight:bold'>word</span>
            - Traduccion en espanol en verde: <span style='color:#92FE9D; font-weight:bold'>palabra</span>
            - Pronunciacion en morado: <span style='color:#C084FC; font-weight:bold'>/pronun/</span>
            - Ejemplos en naranja: <span style='color:#F59E0B'>example sentence</span>
            Estructura SIEMPRE tus respuestas asi:
            1. Palabra en ingles (azul)
            2. Traduccion (verde)
            3. Pronunciacion (morado)
            4. Ejemplo (naranja)
            Corriges errores con amabilidad."""
            sugerencias = [
                "Como me presento en ingles?",
                "Ensename los verbos mas usados",
                "Como pido la hora en ingles?",
                "Corrige mi pronunciacion"
            ]

        if texto_pdf:
            system_prompt += f"\n\nEl estudiante ha subido este documento:\n{texto_pdf}"

        if not st.session_state.historial:
            with st.chat_message("assistant"):
                if modo == "Matematicas":
                    st.write("Hola! Soy tu profe de confianza. Que tema de matematicas te esta costando?")
                else:
                    st.write("Hola! Soy tu profe de confianza. En que nivel de ingles estas?")

            st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.5); font-size:0.9em; margin-top:10px'>Preguntas frecuentes:</p>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            for i, sugerencia in enumerate(sugerencias):
                with col1 if i % 2 == 0 else col2:
                    if st.button(sugerencia, use_container_width=True, key=f"sug_{i}"):
                        st.session_state.historial.append({"role": "user", "content": sugerencia})
                        with st.spinner("Tu profe esta pensando..."):
                            respuesta = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "system", "content": system_prompt}] + st.session_state.historial[-10:]
                            )
                        texto = respuesta.choices[0].message.content
                        st.session_state.historial.append({"role": "assistant", "content": texto})
                        guardar_conversacion(usuario["id"], sugerencia, texto, modo)
                        stats = obtener_estadisticas(usuario["id"])
                        verificar_logros(usuario["id"], stats)
                        st.rerun()

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
                    messages=[{"role": "system", "content": system_prompt}] + st.session_state.historial[-10:]
                )

            texto = respuesta.choices[0].message.content
            st.session_state.historial.append({"role": "assistant", "content": texto})
            guardar_conversacion(usuario["id"], prompt, texto, modo)

            stats = obtener_estadisticas(usuario["id"])
            nuevos_logros = verificar_logros(usuario["id"], stats)
            for logro in nuevos_logros:
                st.balloons()
                st.success(f"🏆 Nuevo logro: {logro['emoji']} {logro['nombre']} - {logro['descripcion']}")

            with st.chat_message("assistant"):
                st.markdown(texto, unsafe_allow_html=True)
