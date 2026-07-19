# -*- coding: utf-8 -*-
"""Modo Examen: genera un examen con IA, recibe las respuestas del alumno
y las califica (automatico para opcion multiple/relacionar, con IA para
preguntas abiertas)."""
import json
import random
from datetime import datetime
import streamlit as st

from tutor_ai import client, MODELO_TUTOR
from database import supabase

PROMPT_EXAMEN_TEMPLATE = """Crea un examen de {materia} para universitarios peruanos con EXACTAMENTE este formato JSON y nada mas:
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


def _init_estado_examen():
    for clave, valor in [
        ("examen_activo", False),
        ("preguntas_examen", []),
        ("respuestas_examen", {}),
        ("examen_terminado", False),
        ("resultado_examen", None),
    ]:
        if clave not in st.session_state:
            st.session_state[clave] = valor


def _generar_examen(materia_examen):
    prompt_examen = PROMPT_EXAMEN_TEMPLATE.format(materia=materia_examen)
    respuesta_examen = client.chat.completions.create(
        model=MODELO_TUTOR,
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
    except Exception:
        st.error("Error generando el examen. Intenta de nuevo.")


def _pantalla_inicio(materia_examen):
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
            _generar_examen(materia_examen)


def _pantalla_preguntas():
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
            resp = st.radio("Selecciona tu respuesta:", opciones, key=f"preg_{i}", index=None)
            if resp:
                st.session_state.respuestas_examen[i] = resp.split(")")[0].strip()

        elif tipo == "abierta":
            resp = st.text_area("Escribe tu respuesta:", key=f"preg_{i}", height=100, placeholder="Escribe aqui tu respuesta...")
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
                    seleccion = st.selectbox(f"'{item_a}' corresponde a:", ["-- Selecciona --"] + columna_b_mezclada, key=f"rel_{i}_{j}")
                    if seleccion != "-- Selecciona --":
                        relaciones[item_a] = seleccion
                if len(relaciones) == len(columna_a):
                    st.session_state.respuestas_examen[i] = relaciones

        st.divider()

    respondidas_actual = len(st.session_state.respuestas_examen)
    if respondidas_actual == total:
        if st.button("✅ Entregar Examen", use_container_width=True):
            with st.spinner("Calificando tu examen..."):
                _calificar_examen(preguntas, total)
    else:
        st.warning(f"Faltan {total - respondidas_actual} preguntas por responder")


def _calificar_examen(preguntas, total):
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
            resultados.append({"pregunta": pregunta["pregunta"], "tipo": tipo, "tu_respuesta": resp_usuario, "correcta": correcta, "es_correcta": es_correcta})

        elif tipo == "abierta":
            eval_prompt = f"""Evalua si esta respuesta es correcta o parcialmente correcta.
Pregunta: {pregunta['pregunta']}
Respuesta correcta esperada: {correcta}
Respuesta del estudiante: {resp_usuario}
Responde SOLO con este JSON: {{"correcta": true/false, "parcial": true/false, "feedback": "explicacion breve"}}"""
            eval_resp = client.chat.completions.create(model=MODELO_TUTOR, messages=[{"role": "user", "content": eval_prompt}], max_tokens=200)
            try:
                eval_json = eval_resp.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                eval_data = json.loads(eval_json)
                if eval_data.get("correcta"):
                    puntaje += 1
                    es_correcta = True
                elif eval_data.get("parcial"):
                    puntaje += 0.5
                    es_correcta = None
                else:
                    es_correcta = False
                resultados.append({"pregunta": pregunta["pregunta"], "tipo": tipo, "tu_respuesta": resp_usuario, "correcta": correcta, "es_correcta": es_correcta, "feedback": eval_data.get("feedback", "")})
            except Exception:
                resultados.append({"pregunta": pregunta["pregunta"], "tipo": tipo, "tu_respuesta": resp_usuario, "correcta": correcta, "es_correcta": False, "feedback": ""})

        elif tipo == "relacionar":
            correctas_rel = correcta if isinstance(correcta, dict) else {}
            resp_rel = resp_usuario if isinstance(resp_usuario, dict) else {}
            aciertos = sum(1 for k, v in resp_rel.items() if correctas_rel.get(k) == v)
            total_rel = len(correctas_rel)
            if total_rel > 0:
                puntaje += aciertos / total_rel
                es_correcta = aciertos == total_rel
            else:
                es_correcta = False
            resultados.append({"pregunta": pregunta["pregunta"], "tipo": tipo, "tu_respuesta": resp_rel, "correcta": correctas_rel, "es_correcta": es_correcta, "aciertos": aciertos, "total_rel": total_rel})

    nota = round((puntaje / total) * 20, 1)
    st.session_state.resultado_examen = {"nota": nota, "puntaje": puntaje, "total": total, "resultados": resultados, "materia": st.session_state.get("materia_examen_actual", "")}
    st.session_state.examen_activo = False
    st.session_state.examen_terminado = True

    try:
        supabase.table("examenes").insert({
            "usuario_id": st.session_state.usuario["id"],
            "materia": st.session_state.resultado_examen["materia"],
            "pregunta": f"Examen completo - {total} preguntas",
            "opciones": json.dumps(resultados),
            "respuesta_correcta": str(nota),
            "respuesta_usuario": str(puntaje),
            "correcta": nota >= 11,
            "fecha": datetime.now().isoformat()
        }).execute()
    except Exception:
        pass
    st.rerun()


def _pantalla_resultado():
    resultado = st.session_state.resultado_examen
    nota = resultado["nota"]

    if nota >= 18:
        emoji_nota, color_nota, mensaje = "🏆", "#92FE9D", "Excelente! Eres un crack!"
    elif nota >= 14:
        emoji_nota, color_nota, mensaje = "⭐", "#00C9FF", "Muy bien! Sigue asi!"
    elif nota >= 11:
        emoji_nota, color_nota, mensaje = "✅", "#F59E0B", "Aprobaste! Puedes mejorar!"
    else:
        emoji_nota, color_nota, mensaje = "📚", "#EF4444", "Reprobaste. Sigue estudiando!"

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
        if res["es_correcta"] is True:
            icono, color, borde = "✅", "rgba(146,254,157,0.1)", "rgba(146,254,157,0.3)"
        elif res["es_correcta"] is None:
            icono, color, borde = "⚡", "rgba(245,158,11,0.1)", "rgba(245,158,11,0.3)"
        else:
            icono, color, borde = "❌", "rgba(239,68,68,0.1)", "rgba(239,68,68,0.3)"

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


def mostrar_modo_examen(usuario):
    """Punto de entrada del Modo Examen, llamado desde app.py."""
    st.markdown("<h1 style='text-align:center;'>📝 Modo Examen</h1>", unsafe_allow_html=True)
    st.divider()

    materia_examen = st.selectbox("Elige la materia del examen", ["Matematicas", "Ingles"])
    st.session_state.materia_examen_actual = materia_examen
    st.session_state.usuario = usuario  # usado por _calificar_examen para guardar el resultado

    _init_estado_examen()

    if not st.session_state.examen_activo and not st.session_state.examen_terminado:
        _pantalla_inicio(materia_examen)
    elif st.session_state.examen_activo and not st.session_state.examen_terminado:
        _pantalla_preguntas()
    elif st.session_state.examen_terminado and st.session_state.resultado_examen:
        _pantalla_resultado()

