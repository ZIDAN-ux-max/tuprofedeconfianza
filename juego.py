# -*- coding: utf-8 -*-
"""Juego para desestresarse: cuentas sueltas de suma, resta, multiplicacion
y division, sin cronometro ni presion. Todo se genera aca mismo con numeros
al azar (no usa la IA), asi que es instantaneo y no gasta nada."""
import random

import streamlit as st

OPERACIONES = {
    "Suma (+)": "+",
    "Resta (−)": "-",
    "Multiplicación (×)": "*",
    "División (÷)": "/",
}

# Rangos de numeros por dificultad: "sumar" vale para sumas y restas;
# "factor_a" y "factor_b" para multiplicaciones y divisiones.
RANGOS = {
    "Fácil": {"sumar": (1, 20), "factor_a": (2, 5), "factor_b": (1, 10)},
    "Medio": {"sumar": (10, 99), "factor_a": (2, 9), "factor_b": (2, 12)},
    "Difícil": {"sumar": (50, 999), "factor_a": (6, 15), "factor_b": (6, 20)},
}

FRASES_ACIERTO = ["¡Bien! 🌿", "¡Exacto! ✨", "Perfecto 👌", "¡Eso es! 💪", "¡Muy bien! 🌟"]


def _generar_problema(operaciones, nivel):
    """Devuelve (texto, respuesta). La resta nunca da negativo y la
    division siempre es exacta (se arma al reves: cociente x divisor)."""
    r = RANGOS[nivel]
    op = random.choice(operaciones)
    if op == "+":
        a, b = random.randint(*r["sumar"]), random.randint(*r["sumar"])
        return f"{a} + {b}", a + b
    if op == "-":
        a, b = random.randint(*r["sumar"]), random.randint(*r["sumar"])
        a, b = max(a, b), min(a, b)
        return f"{a} − {b}", a - b
    if op == "*":
        a, b = random.randint(*r["factor_a"]), random.randint(*r["factor_b"])
        return f"{a} × {b}", a * b
    divisor, cociente = random.randint(*r["factor_a"]), random.randint(*r["factor_b"])
    return f"{divisor * cociente} ÷ {divisor}", cociente


def _generar_opciones(correcta):
    """4 opciones distintas y no negativas: la correcta + 3 cercanas."""
    opciones = {correcta}
    intentos = 0
    while len(opciones) < 4 and intentos < 50:
        intentos += 1
        candidata = correcta + random.choice([1, 2, 3, 5, 10]) * random.choice([-1, 1])
        if candidata >= 0:
            opciones.add(candidata)
    n = 1
    while len(opciones) < 4:  # caso raro (respuestas muy chicas): se completa con las siguientes
        opciones.add(correcta + n)
        n += 1
    lista = list(opciones)
    random.shuffle(lista)
    return lista


def _init_estado():
    por_defecto = {
        "juego_activo": False,
        "juego_aciertos": 0,
        "juego_errores": 0,
        "juego_racha": 0,
        "juego_mejor_racha": 0,
        "juego_n": 0,
        "juego_problema": None,
        "juego_opciones": [],
        "juego_mensaje": None,
        "juego_ops": ["+", "-", "*", "/"],
        "juego_nivel": "Fácil",
    }
    for clave, valor in por_defecto.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor


def _siguiente_problema():
    texto, respuesta = _generar_problema(st.session_state.juego_ops, st.session_state.juego_nivel)
    st.session_state.juego_problema = (texto, respuesta)
    st.session_state.juego_opciones = _generar_opciones(respuesta)
    st.session_state.juego_n += 1


def _responder(elegida):
    ss = st.session_state
    texto, correcta = ss.juego_problema
    if elegida == correcta:
        ss.juego_aciertos += 1
        ss.juego_racha += 1
        ss.juego_mejor_racha = max(ss.juego_mejor_racha, ss.juego_racha)
        ss.juego_mensaje = ("ok", random.choice(FRASES_ACIERTO))
    else:
        ss.juego_errores += 1
        ss.juego_racha = 0
        ss.juego_mensaje = ("casi", f"Casi 🙂 {texto} = {correcta}. ¡Seguimos!")
    _siguiente_problema()


def _tarjeta(contenido):
    return (
        "<div style='background:rgba(15,12,41,0.82); border:1px solid rgba(255,255,255,0.12); "
        f"border-radius:16px; padding:14px; margin:8px 0; text-align:center;'>{contenido}</div>"
    )


def _pantalla_inicio():
    ss = st.session_state
    total = ss.juego_aciertos + ss.juego_errores
    if total > 0:
        porcentaje = round(100 * ss.juego_aciertos / total)
        if porcentaje >= 80:
            frase = "¡Qué buen rato! 🌟"
        elif porcentaje >= 50:
            frase = "Bien ahí, cada cuenta suma 🌱"
        else:
            frase = "Lo importante es despejar la cabeza 🍃"
        st.markdown(
            _tarjeta(
                f"<strong style='color:#92FE9D'>Última partida</strong><br>"
                f"{ss.juego_aciertos} de {total} ({porcentaje}%) · mejor racha {ss.juego_mejor_racha}<br>"
                f"<span style='color:rgba(255,255,255,0.7)'>{frase}</span>"
            ),
            unsafe_allow_html=True,
        )

    etiquetas = st.multiselect(
        "¿Qué operaciones querés practicar?",
        list(OPERACIONES.keys()),
        default=list(OPERACIONES.keys()),
        key="juego_sel_ops",
    )
    nivel = st.select_slider("Dificultad", options=list(RANGOS.keys()), value="Fácil", key="juego_sel_nivel")

    if not etiquetas:
        st.warning("Elegí al menos una operación para empezar.")
        return
    if st.button("🎮 Empezar", use_container_width=True, key="juego_empezar"):
        ss.juego_ops = [OPERACIONES[e] for e in etiquetas]
        ss.juego_nivel = nivel
        ss.juego_aciertos = 0
        ss.juego_errores = 0
        ss.juego_racha = 0
        ss.juego_mejor_racha = 0
        ss.juego_mensaje = None
        ss.juego_activo = True
        _siguiente_problema()
        st.rerun()


def _pantalla_juego():
    ss = st.session_state

    def _dato(valor, etiqueta, color):
        return (
            f"<div><div style='font-size:1.6em; font-weight:800; color:{color}'>{valor}</div>"
            f"<div style='font-size:0.8em; color:rgba(255,255,255,0.7)'>{etiqueta}</div></div>"
        )

    st.markdown(
        "<div style='background:rgba(15,12,41,0.82); border:1px solid rgba(255,255,255,0.12); "
        "border-radius:16px; padding:14px; margin:8px 0; display:flex; justify-content:space-around; text-align:center;'>"
        + _dato(ss.juego_aciertos, "✅ Aciertos", "#92FE9D")
        + _dato(ss.juego_racha, "🔥 Racha", "#FFD166")
        + _dato(ss.juego_mejor_racha, "🏅 Mejor racha", "#00C9FF")
        + "</div>",
        unsafe_allow_html=True,
    )

    if ss.juego_mensaje:
        tipo, texto_mensaje = ss.juego_mensaje
        (st.success if tipo == "ok" else st.info)(texto_mensaje)

    texto, _ = ss.juego_problema
    st.markdown(
        "<div style='background:rgba(15,12,41,0.82); border:1px solid rgba(0,201,255,0.4); "
        "border-radius:20px; padding:30px; text-align:center; margin:12px 0;'>"
        f"<span style='font-size:3em; font-weight:800; color:#FFFFFF;'>{texto} = ?</span></div>",
        unsafe_allow_html=True,
    )

    elegida = None
    with st.container(key="juego_opciones"):
        for i, (col, opcion) in enumerate(zip(st.columns(4), ss.juego_opciones)):
            if col.button(str(opcion), key=f"juego_op_{ss.juego_n}_{i}", use_container_width=True):
                elegida = opcion
    if elegida is not None:
        _responder(elegida)
        st.rerun()

    if st.button("⏹️ Terminar", key="juego_terminar"):
        ss.juego_activo = False
        st.rerun()


def mostrar_juego():
    _init_estado()
    st.markdown("<h1 style='text-align:center;'>🎮 Juego para despejar la mente</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:rgba(255,255,255,0.6)'>"
        "Cuentas sueltas, sin cronómetro y sin presión. Solo para relajarte un rato.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<style>.st-key-juego_opciones button { min-height: 70px; } "
        ".st-key-juego_opciones button p { font-size: 1.7em; font-weight: 700; }</style>",
        unsafe_allow_html=True,
    )
    st.divider()
    if st.session_state.juego_activo:
        _pantalla_juego()
    else:
        _pantalla_inicio()
