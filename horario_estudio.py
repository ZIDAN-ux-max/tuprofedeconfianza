# -*- coding: utf-8 -*-
"""Genera un horario de estudio personalizado a partir del silabo y la
ficha de evaluacion de un curso: extrae la estructura (temas por semana,
fechas y pesos de evaluaciones) y, con la fecha de inicio de clases, calcula
el calendario real de fechas. Archivo separado de calendario.py a proposito
(evita chocar con cambios en paralelo)."""
import json
from datetime import timedelta, date

import streamlit as st

from tutor_ai import client, MODELO_RESUMEN
from database import listar_cursos, obtener_textos_silabo_ficha_separados, guardar_plan_estudio, obtener_plan_estudio
from materias_data import materias_de_carrera
from utils import hoy_peru


def extraer_estructura_curso(texto_silabo, texto_ficha):
    """Le pide a la IA que lea el silabo y la ficha de evaluacion y devuelva
    una estructura clara: cuantas semanas tiene el ciclo, que tema se ve
    cada semana, y en que semana cae cada evaluacion (con su peso y tipo).
    Devuelve un dict, o None si algo fallo."""
    material = f"SILABO:\n{texto_silabo[:4000]}\n\nFICHA DE EVALUACION:\n{texto_ficha[:3000]}"

    prompt = f"""Lee este silabo y ficha de evaluacion de un curso universitario, y extrae
su estructura en JSON. Presta atencion a los numeros de semana exactos que
aparecen en los documentos (no los inventes).

Devuelve SOLO este JSON, sin texto extra:
{{
  "total_semanas": numero total de semanas del ciclo (normalmente 16, usa lo que diga el documento),
  "temas_por_semana": [
    {{"semana": 1, "tema": "nombre corto del tema de esa semana (max 10 palabras)"}}
  ],
  "evaluaciones": [
    {{"semana": numero de semana en que cae, "nombre": "nombre de la evaluacion", "peso_porcentaje": numero (0 si no dice), "tipo": "tipo de evaluacion (examen escrito, video, cuestionario, etc.)"}}
  ]
}}

Incluye TODAS las semanas que tengan tema mencionado, y TODAS las evaluaciones
que encuentres en la ficha (incluyendo las de 0%, como evaluaciones diagnosticas).

Material del curso:
{material}
"""
    try:
        respuesta = client.chat.completions.create(
            model=MODELO_RESUMEN,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1800,
            response_format={"type": "json_object"}
        )
        return json.loads(respuesta.choices[0].message.content)
    except Exception:
        return None


def calcular_horario_con_fechas(estructura, fecha_inicio_ciclo, dias_anticipacion_estudio=5):
    """A partir de la estructura extraida (temas_por_semana, evaluaciones) y
    la fecha real en que empiezan las clases, calcula la fecha exacta de
    cada semana y arma un plan de estudio: para cada evaluacion, sugiere
    desde que fecha empezar a repasar y que temas cubre.

    Asume que cada semana dura 7 dias, empezando en 'fecha_inicio_ciclo'
    (que deberia ser el primer dia de clases, semana 1).

    No usa IA - es puro calculo, asi que el resultado es 100% predecible."""
    temas = {t["semana"]: t["tema"] for t in estructura.get("temas_por_semana", [])}
    evaluaciones = estructura.get("evaluaciones", [])

    def fecha_de_semana(numero_semana):
        # Semana 1 empieza en fecha_inicio_ciclo; cada semana siguiente suma 7 dias
        return fecha_inicio_ciclo + timedelta(weeks=numero_semana - 1)

    plan = []
    semana_anterior_evaluada = 0
    for ev in sorted(evaluaciones, key=lambda e: e["semana"]):
        semana_eval = ev["semana"]
        fecha_eval = fecha_de_semana(semana_eval)
        fecha_inicio_repaso = fecha_eval - timedelta(days=dias_anticipacion_estudio)

        # Temas cubiertos desde la ultima evaluacion hasta esta (los que hay que repasar)
        temas_a_repasar = [
            temas[s] for s in sorted(temas.keys())
            if semana_anterior_evaluada < s <= semana_eval
        ]

        plan.append({
            "evaluacion": ev["nombre"],
            "tipo": ev.get("tipo", ""),
            "peso_porcentaje": ev.get("peso_porcentaje", 0),
            "semana": semana_eval,
            "fecha_evaluacion": fecha_eval,
            "fecha_inicio_repaso": fecha_inicio_repaso,
            "temas_a_repasar": temas_a_repasar,
        })
        semana_anterior_evaluada = semana_eval

    return plan


def _mostrar_plan(plan):
    """Dibuja el plan de estudio como tarjetas, una por evaluacion."""
    hoy = hoy_peru()
    for p in plan:
        pasado = p["fecha_evaluacion"] < hoy
        color_borde = "rgba(255,255,255,0.15)" if pasado else "#00C9FF"
        temas_txt = ", ".join(p["temas_a_repasar"]) if p["temas_a_repasar"] else "Repaso general (sin temas nuevos)"
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.04); border-left:4px solid {color_borde}; "
            f"border-radius:10px; padding:14px 18px; margin-bottom:10px; opacity:{0.5 if pasado else 1}'>"
            f"<strong style='color:white'>{p['evaluacion']}</strong> "
            f"<span style='color:#92FE9D'>({p['peso_porcentaje']}%)</span>"
            f"<br><span style='color:rgba(255,255,255,0.6); font-size:0.9em'>{p['tipo']} · Semana {p['semana']}</span>"
            f"<br><span style='color:#F59E0B; font-weight:bold'>📅 {p['fecha_evaluacion'].strftime('%d/%m/%Y')}</span>"
            f"<br><span style='color:rgba(255,255,255,0.6); font-size:0.85em'>Empieza a repasar desde el {p['fecha_inicio_repaso'].strftime('%d/%m')}: {temas_txt}</span>"
            f"</div>",
            unsafe_allow_html=True
        )


def mostrar_horario_estudio_contenido(usuario):
    """El contenido en si (sin titulo propio), para poder usarse tanto en
    su propia pagina como embebido dentro de una pestaña de Calendario."""
    materias = materias_de_carrera(usuario.get("carrera")) or ["Matematicas"]
    materia = st.selectbox("Materia", materias, key="horario_materia")
    cursos = listar_cursos(materia)
    if not cursos:
        st.info("Todavia no hay cursos con documentos en esta materia. Sube el sílabo y la ficha primero en Documentos.")
        return
    curso = st.selectbox("Curso", cursos, key="horario_curso")

    plan_guardado = obtener_plan_estudio(usuario["id"], materia, curso)
    if plan_guardado:
        st.caption(f"Ultimo plan generado para este curso, con inicio de ciclo el {plan_guardado['fecha_inicio_ciclo']}")
        plan = calcular_horario_con_fechas(plan_guardado["estructura_json"], date.fromisoformat(plan_guardado["fecha_inicio_ciclo"]))
        _mostrar_plan(plan)
        st.divider()

    fecha_inicio = st.date_input("¿Que dia empezaron las clases de este curso?", key="horario_fecha_inicio")

    if st.button("✨ Generar horario de estudio", use_container_width=True):
        texto_silabo, texto_ficha = obtener_textos_silabo_ficha_separados(materia, curso)
        if not texto_silabo and not texto_ficha:
            st.warning("No encontramos un sílabo o ficha de evaluación subidos para este curso. Sube alguno primero en Documentos, marcandolo con el tipo correcto.")
        else:
            with st.spinner("Leyendo el sílabo y la ficha, armando tu horario..."):
                estructura = extraer_estructura_curso(texto_silabo, texto_ficha)
                if not estructura or not estructura.get("evaluaciones"):
                    st.error("No se pudo extraer la estructura del curso (puede ser un corte momentaneo del servicio). Intenta de nuevo.")
                else:
                    guardar_plan_estudio(usuario["id"], materia, curso, fecha_inicio, estructura)
                    plan = calcular_horario_con_fechas(estructura, fecha_inicio)
                    st.success("Horario generado")
                    _mostrar_plan(plan)


def mostrar_horario_estudio(usuario):
    """Pagina independiente (menu lateral 'Horario de Estudio')."""
    st.markdown("<h1 style='text-align:center;'>🗓️ Horario de Estudio</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:rgba(255,255,255,0.6)'>"
        "A partir del sílabo y la ficha de evaluación de tu curso, armamos las fechas reales "
        "de cada evaluación y qué repasar antes de cada una.</p>",
        unsafe_allow_html=True
    )
    st.divider()
    mostrar_horario_estudio_contenido(usuario)
