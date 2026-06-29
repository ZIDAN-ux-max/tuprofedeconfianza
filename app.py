# === HEADER PRINCIPAL (CHAT) ===
st.image("imagen5.png", use_container_width=True)
st.markdown(
    "<h1 style='text-align:center; color:#1E3A8A;'>Tu Profe de Confianza</h1>",
    unsafe_allow_html=True
)
st.divider()

# Reemplazo pedido: antes eran 2 columnas con iconos; ahora logo centrado con márgenes
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("imagen2.png", use_container_width=True)

st.markdown(
    f"""
    <div style='text-align:center; padding:10px 0'>
        <span style='font-size:1.1em; color:#6B7280'>
            Estudiando:
            <strong style='color:#1E3A8A'>
                {"📐 Matematicas" if modo == "Matematicas" else "🇺🇸 Ingles"}
            </strong>
        </span>
    </div>
    """,
    unsafe_allow_html=True
)
st.divider()

# === SUGERENCIAS (PREGUNTAS FRECUENTES) ===
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

# Solo mostrar sugerencias cuando el historial está vacío
if not st.session_state.historial:
    st.markdown(
        "<p style='text-align:center; color:#6B7280; font-size:0.9em'>Preguntas frecuentes:</p>",
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    for i, sugerencia in enumerate(sugerencias):
        with (c1 if i % 2 == 0 else c2):
            if st.button(sugerencia, use_container_width=True, key=f"sug_{modo}_{i}"):
                # Simula un mensaje del usuario
                st.session_state.historial.append({"role": "user", "content": sugerencia})

                # Llama al modelo
                with st.spinner("Tu profe esta pensando..."):
                    respuesta = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": system_prompt}] + st.session_state.historial
                    )

                texto = respuesta.choices[0].message.content

                # Guarda respuesta en historial
                st.session_state.historial.append({"role": "assistant", "content": texto})

                # Persistencia + logros
                guardar_conversacion(usuario["id"], sugerencia, texto, modo)
                stats = obtener_estadisticas(usuario["id"])
                verificar_logros(usuario["id"], stats)

                # Recargar para que ya aparezca el chat con la conversación
                st.rerun()

    st.divider()
