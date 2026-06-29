# -*- coding: utf-8 -*-
import streamlit as st
from groq import Groq
from supabase import create_client
import hashlib
import PyPDF2
import io
from datetime import datetime, timedelta

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
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stat-number {
        font-size: 2.5em;
        font-weight: bold;
        color: #1E3A8A;
    }
    .stat-label {
        color: #6B7280;
        font-size: 0.9em;
    }
    .logro-card {
        background: linear-gradient(135deg, #1E3A8A, #3B82F6);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        color: white;
        margin: 5px;
    }
    .logro-emoji {
        font-size: 2.5em;
    }
    .logro-nombre {
        font-weight: bold;
        font-size: 1em;
        margin-top: 5px;
    }
    .logro-desc {
        font-size: 0.8em;
        opacity: 0.9;
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
    return {
        "total": total,
        "matematicas": mate,
        "ingles": ingles,
        "hoy": hoy_count,
        "semana": semana_count
    }

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
            if stats[logro["condicion"]] >= logro["valor"]:
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
        seccion = st.radio("Menu", ["Chat", "Mis Estadisticas", "Mis Logros"])
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

    if seccion == "Mis Logros":
        st.image("imagen5.png", use_container_width=True)
        st.markdown("<h1 style='text-align:center; color:#1E3A8A;'>Mis Logros</h1>", unsafe_allow_html=True)
        st.divider()

        stats = obtener_estadisticas(usuario["id"])
        logros_ganados = obtener_logros_usuario(usuario["id"])

        st.markdown(f"### Tienes {len(logros_ganados)} de {len(LOGROS_DISPONIBLES)} logros 🏆")
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
                    <div class='logro-card' style='background: #D1D5DB; color: #6B7280;'>
                        <div class='logro-emoji'>🔒</div>
                        <div class='logro-nombre'>{logro['nombre']}</div>
                        <div class='logro-desc'>{logro['descripcion']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    elif seccion == "Mis Estadisticas":
        st.image("imagen5.png", use_container_width=True)
        st.markdown("<h1 style='text-align:center; color:#1E3A8A;'>Mis Estadisticas</h1>", unsafe_allow_html=True)
        st.divider()

        stats = obtener_estadisticas(usuario["id"])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{stats['total']}</div>
                <div class='stat-label'>Total preguntas</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{stats['hoy']}</div>
                <div class='stat-label'>Preguntas hoy</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{stats['semana']}</div>
                <div class='stat-label'>Esta semana</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number' style='color:#166534'>📐 {stats['matematicas']}</div>
                <div class='stat-label'>Preguntas de Matematicas</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number' style='color:#1D4ED8'>🇺🇸 {stats['ingles']}</div>
                <div class='stat-label'>Preguntas de Ingles</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        if stats['total'] > 0:
            materia_favorita = "Matematicas" if stats['matematicas'] >= stats['ingles'] else "Ingles"
            st.success(f"Tu materia favorita es: **{materia_favorita}** 🎯")
            if stats['hoy'] == 0:
                st.warning("No has estudiado hoy. Abre el chat y haz tu primera pregunta!")
            elif stats['hoy'] < 5:
                st.info(f"Llevas {stats['hoy']} preguntas hoy. Sigue asi!")
            else:
                st.success(f"Excelente! Llevas {stats['hoy']} preguntas hoy. Eres un crack!")
        else:
            st.info("Aun no tienes estadisticas. Ve al chat y empieza a estudiar!")

    else:
        if "modo" not in st.session_state:
            st.session_state.modo = "Matematicas"
        modo = st.session_state.get("modo", "Matematicas")

    col1, col2, col3 = st.columns([1,3,1])
    with col2:
        st.image("imagen2.png", use_container_width=True)
    
    st.markdown(f"""
    <div style='text-align:center; padding:10px 0'>
        <span style='font-size:1.1em; color:#6B7280'>
        Estudiando: <strong style='color:#1E3A8A'>{"📐 Matematicas" if modo == "Matematicas" else "🇺🇸 Ingles"}</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if modo == "Matematicas":
        sugerencias = [
            "¿Qué es una integral?",
            "Explícame las derivadas",
            "¿Cómo resuelvo una ecuación cuadrática?",
            "¿Qué es el límite de una función?"
        ]
    else:
        sugerencias = [
            "¿Cómo me presento en inglés?",
            "Enséñame los verbos más usados",
            "¿Cómo pido la hora en inglés?",
            "Corrige mi pronunciación"
        ]

    if not st.session_state.historial:
        st.markdown("<p style='text-align:center; color:#6B7280; font-size:0.9em'>Preguntas frecuentes:</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        for i, sugerencia in enumerate(sugerencias):
            with col1 if i % 2 == 0 else col2:
                if st.button(sugerencia, use_container_width=True, key=f"sug_{i}"):
                    st.session_state.historial.append({"role": "user", "content": sugerencia})
                    with st.spinner("Tu profe esta pensando..."):
                        respuesta = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": system_prompt}] + st.session_state.historial
                        )
                    texto = respuesta.choices[0].message.content
                    st.session_state.historial.append({"role": "assistant", "content": texto})
                    guardar_conversacion(usuario["id"], sugerencia, texto, modo)
                    stats = obtener_estadisticas(usuario["id"])
                    verificar_logros(usuario["id"], stats)
                    st.rerun()
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

            stats = obtener_estadisticas(usuario["id"])
            nuevos_logros = verificar_logros(usuario["id"], stats)
            for logro in nuevos_logros:
                st.balloons()
                st.success(f"🏆 Nuevo logro desbloqueado: {logro['emoji']} {logro['nombre']} - {logro['descripcion']}")

            with st.chat_message("assistant"):
                st.markdown(texto, unsafe_allow_html=True)
