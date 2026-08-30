# -*- coding: utf-8 -*-
"""Genera un horario de estudio personalizado a partir del silabo y la
ficha de evaluacion de un curso: extrae la estructura (temas por semana,
fechas y pesos de evaluaciones) y, con la fecha de inicio de clases, calcula
el calendario real de fechas. Archivo separado de calendario.py a proposito
(evita chocar con cambios en paralelo)."""
import json
from datetime import timedelta, date, time as time_type

import streamlit as st

from tutor_ai import client, MODELO_RESUMEN
from database import listar_cursos, obtener_textos_silabo_ficha_separados, guardar_plan_estudio, obtener_plan_estudio, guardar_clase_horario, listar_horario_clases, eliminar_clase_horario
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
  "nivel_dificultad": "basico", "intermedio" o "avanzado" segun la profundidad real del curso (ej: 'Matematicas I' o 'Quimica General' suelen ser basico/intermedio; 'Matematicas III', 'Fisica II', 'Quimica Organica' suelen ser avanzado - juzga por el contenido real, no solo el numero romano),
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


BLOQUES_POR_NIVEL = {
    # (minutos_estudio, minutos_descanso_corto, bloques_antes_de_descanso_largo, minutos_descanso_largo)
    "basico": (25, 5, 4, 20),
    "intermedio": (30, 7, 4, 20),
    "avanzado": (35, 10, 3, 25),
}


def obtener_duracion_bloques(nivel_dificultad):
    """Devuelve (minutos_estudio, minutos_descanso_corto,
    bloques_antes_de_descanso_largo, minutos_descanso_largo) segun el nivel
    del curso. Los numeros salen de evidencia real (revision 2025 en BMC
    Medical Education, ~5270 participantes): bloques mas largos rinden
    mejor en materias densas, y un descanso con tiempo fijo rinde mejor
    que dejarlo a criterio del alumno en el momento."""
    return BLOQUES_POR_NIVEL.get(nivel_dificultad, BLOQUES_POR_NIVEL["intermedio"])


def _restar_ocupado(inicio_min, fin_min, ocupados_del_dia):
    """A partir de un rango libre del dia (en minutos desde medianoche) y
    una lista de bloques ocupados (clases), devuelve los sub-rangos que
    quedan realmente libres."""
    libres = [(inicio_min, fin_min)]
    for oc_inicio, oc_fin in ocupados_del_dia:
        nuevos_libres = []
        for li, lf in libres:
            if oc_fin <= li or oc_inicio >= lf:
                nuevos_libres.append((li, lf))  # no se cruzan
                continue
            if oc_inicio > li:
                nuevos_libres.append((li, oc_inicio))
            if oc_fin < lf:
                nuevos_libres.append((oc_fin, lf))
        libres = nuevos_libres
    return libres


def generar_bloques_estudio_del_dia(dia_semana, horario_clases, nivel_dificultad, tema, hora_desde=7*60, hora_hasta=22*60, minutos_maximos_del_dia=120):
    """Arma los bloques de estudio (con descansos) para UN dia, metidos
    solo en los huecos libres entre 'hora_desde' y 'hora_hasta' (en minutos
    desde medianoche, por defecto 7am-10pm), sin pisar las clases de ese
    dia. No mete mas de 'minutos_maximos_del_dia' de estudio real por dia
    (para no agotar al alumno, aunque tenga mas huecos libres).

    Devuelve una lista de bloques: [{"tipo": "estudio"/"descanso_corto"/
    "descanso_largo", "inicio_min": X, "fin_min": Y, "tema": "..."}]"""
    minutos_estudio, descanso_corto, bloques_antes_largo, descanso_largo = obtener_duracion_bloques(nivel_dificultad)

    ocupados = [
        (_hora_a_minutos(c["hora_inicio"]), _hora_a_minutos(c["hora_fin"]))
        for c in horario_clases if c["dia_semana"] == dia_semana
    ]
    huecos_libres = _restar_ocupado(hora_desde, hora_hasta, ocupados)

    bloques = []
    minutos_estudiados_hoy = 0
    contador_bloques_seguidos = 0

    for li, lf in huecos_libres:
        cursor = li
        while cursor + minutos_estudio <= lf and minutos_estudiados_hoy + minutos_estudio <= minutos_maximos_del_dia:
            bloques.append({"tipo": "estudio", "inicio_min": cursor, "fin_min": cursor + minutos_estudio, "tema": tema})
            cursor += minutos_estudio
            minutos_estudiados_hoy += minutos_estudio
            contador_bloques_seguidos += 1

            if minutos_estudiados_hoy >= minutos_maximos_del_dia:
                break

            # Decidir si toca descanso corto o largo, y si entra en el hueco
            es_descanso_largo = contador_bloques_seguidos >= bloques_antes_largo
            duracion_descanso = descanso_largo if es_descanso_largo else descanso_corto
            if cursor + duracion_descanso > lf:
                break  # no entra ni el descanso en lo que queda del hueco, se corta aca

            bloques.append({"tipo": "descanso_largo" if es_descanso_largo else "descanso_corto", "inicio_min": cursor, "fin_min": cursor + duracion_descanso, "tema": None})
            cursor += duracion_descanso
            if es_descanso_largo:
                contador_bloques_seguidos = 0

    return bloques


def _hora_a_minutos(hora_str):
    """Convierte 'HH:MM' o 'HH:MM:SS' a minutos desde medianoche."""
    partes = str(hora_str).split(":")
    return int(partes[0]) * 60 + int(partes[1])


def _minutos_a_hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


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


DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]


def _seccion_horario_clases(usuario):
    """Que el alumno cargue su horario semanal de clases (dia/hora), para
    despues poder armar bloques de estudio solo en los huecos libres."""
    st.markdown("#### 🏫 Tu horario de clases")
    st.caption("Cargalo una vez, asi el horario de estudio se arma solo en tus huecos libres, sin pisar tus clases.")

    clases = listar_horario_clases(usuario["id"])
    if clases:
        for c in clases:
            col1, col2 = st.columns([5, 1])
            with col1:
                etiqueta_txt = f" - {c['etiqueta']}" if c.get("etiqueta") else ""
                st.markdown(f"<span style='color:white'>{DIAS_SEMANA[c['dia_semana']]} {c['hora_inicio'][:5]} - {c['hora_fin'][:5]}{etiqueta_txt}</span>", unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_clase_{c['id']}"):
                    eliminar_clase_horario(c["id"])
                    st.rerun()

    with st.form("form_agregar_clase", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            dia_legible = st.selectbox("Dia", DIAS_SEMANA, key="clase_dia")
        with col2:
            hora_inicio = st.time_input("Desde", value=time_type(8, 0), key="clase_inicio")
        with col3:
            hora_fin = st.time_input("Hasta", value=time_type(10, 0), key="clase_fin")
        etiqueta = st.text_input("Curso (opcional, ej: Fisica II)", key="clase_etiqueta")
        if st.form_submit_button("+ Agregar bloque de clase"):
            if hora_fin <= hora_inicio:
                st.warning("La hora de fin debe ser despues de la de inicio.")
            else:
                dia_num = DIAS_SEMANA.index(dia_legible)
                guardar_clase_horario(usuario["id"], dia_num, hora_inicio, hora_fin, etiqueta or None)
                st.rerun()


def _mostrar_bloques_de_hoy(usuario, plan, estructura):
    """Si hoy cae dentro de la ventana de repaso de alguna evaluacion,
    muestra el horario de bloques de estudio con hora exacta para hoy,
    respetando el horario de clases del alumno."""
    hoy = hoy_peru()
    evaluacion_activa = next((p for p in plan if p["fecha_inicio_repaso"] <= hoy <= p["fecha_evaluacion"]), None)
    if not evaluacion_activa:
        return

    horario_clases = listar_horario_clases(usuario["id"])
    dia_semana_hoy = hoy.weekday()  # 0=Lunes
    tema_hoy = ", ".join(evaluacion_activa["temas_a_repasar"][:2]) or evaluacion_activa["evaluacion"]
    nivel = estructura.get("nivel_dificultad", "intermedio")
    bloques = generar_bloques_estudio_del_dia(dia_semana_hoy, horario_clases, nivel, tema_hoy)

    st.markdown(
        f"<div style='background:rgba(0,201,255,0.08); border:1px solid rgba(0,201,255,0.3); "
        f"border-radius:12px; padding:14px 18px; margin-bottom:14px;'>"
        f"<strong style='color:#00C9FF'>📚 Hoy toca repasar para: {evaluacion_activa['evaluacion']}</strong>",
        unsafe_allow_html=True
    )
    if not bloques:
        st.caption("No encontramos huecos libres hoy segun tu horario de clases (o todavia no lo cargaste arriba).")
    else:
        emojis = {"estudio": "📖", "descanso_corto": "☕", "descanso_largo": "🛋️"}
        for b in bloques:
            etiqueta = "Estudio" if b["tipo"] == "estudio" else ("Descanso corto" if b["tipo"] == "descanso_corto" else "Descanso largo")
            texto_tema = f" - {b['tema']}" if b["tema"] else ""
            st.markdown(f"{emojis[b['tipo']]} **{_minutos_a_hora(b['inicio_min'])} - {_minutos_a_hora(b['fin_min'])}**: {etiqueta}{texto_tema}")
    st.markdown("</div>", unsafe_allow_html=True)


def mostrar_horario_estudio_contenido(usuario):
    """El contenido en si (sin titulo propio), para poder usarse tanto en
    su propia pagina como embebido dentro de una pestaña de Calendario."""
    with st.expander("🏫 Configurar mi horario de clases (una sola vez)"):
        _seccion_horario_clases(usuario)

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
        _mostrar_bloques_de_hoy(usuario, plan, plan_guardado["estructura_json"])
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
