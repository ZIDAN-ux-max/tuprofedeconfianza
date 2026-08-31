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
from database import (
    listar_cursos, obtener_textos_silabo_ficha_separados, guardar_plan_estudio, obtener_plan_estudio,
    guardar_clase_horario, listar_horario_clases, eliminar_clase_horario,
    guardar_bloques_estudio, eliminar_bloques_estudio_futuros, eliminar_bloques_estudio_futuros_todos_los_cursos,
    listar_bloques_estudio, eliminar_bloques_estudio_de_otros_cursos, listar_planes_estudio,
)
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
    {{"semana": numero de semana en que cae, "nombre": "nombre de la evaluacion", "peso_porcentaje": numero (0 si no dice), "tipo": "tipo de evaluacion (examen escrito, video, cuestionario, etc.)", "fecha_exacta": "YYYY-MM-DD si el documento indica una fecha calendario exacta para esta evaluacion, o null si no la indica"}}
  ]
}}

Incluye TODAS las semanas que tengan tema mencionado, y TODAS las evaluaciones
que encuentres en la ficha (incluyendo las de 0%, como evaluaciones diagnosticas).

Para "fecha_exacta": la mayoria de evaluaciones continuas NO tienen fecha exacta
en el documento (solo semana), asi que en esos casos deja null. Pero el Examen
Parcial y el Examen Final SI suelen tener una fecha exacta indicada (porque no
caen en un dia fijo de clase) - si el documento la da, extraela.

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


def generar_bloques_estudio_del_dia(dia_semana, horario_clases, nivel_dificultad, tema, hora_desde=7*60, hora_hasta=22*60, minutos_maximos_del_dia=120, ocupados_extra=None):
    """Arma los bloques de estudio (con descansos) para UN dia, metidos
    solo en los huecos libres entre 'hora_desde' y 'hora_hasta' (en minutos
    desde medianoche, por defecto 7am-10pm), sin pisar las clases de ese
    dia NI los bloques de estudio de otros cursos que ya estaban guardados
    ahi ('ocupados_extra', lista de (inicio_min, fin_min)). No mete mas de
    'minutos_maximos_del_dia' de estudio real por dia (para no agotar al
    alumno, aunque tenga mas huecos libres).

    Devuelve una lista de bloques: [{"tipo": "estudio"/"descanso_corto"/
    "descanso_largo", "inicio_min": X, "fin_min": Y, "tema": "..."}]"""
    minutos_estudio, descanso_corto, bloques_antes_largo, descanso_largo = obtener_duracion_bloques(nivel_dificultad)

    ocupados = [
        (_hora_a_minutos(c["hora_inicio"]), _hora_a_minutos(c["hora_fin"]))
        for c in horario_clases if c["dia_semana"] == dia_semana
    ]
    ocupados += ocupados_extra or []
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


PALABRAS_CLASE_SECUNDARIA = ["labo", "lab", "practica", "práctica", "taller"]


def _dia_semana_del_curso(usuario_id, curso):
    """Busca en el horario de clases del alumno el bloque que corresponde a
    este curso, y devuelve su dia de la semana (0=Lunes). Si el curso tiene
    varios bloques (ej. teoria + laboratorio/practica), prioriza el que NO
    sea labo/practica, porque el examen se toma en la clase principal.
    Devuelve None si no encuentra ningun bloque con ese nombre."""
    if not usuario_id or not curso:
        return None
    clases = listar_horario_clases(usuario_id)
    candidatos = [c for c in clases if c.get("etiqueta") and curso.lower() in c["etiqueta"].lower()]
    if not candidatos:
        return None
    principal = next(
        (c for c in candidatos if not any(p in c["etiqueta"].lower() for p in PALABRAS_CLASE_SECUNDARIA)),
        None
    )
    return (principal or candidatos[0])["dia_semana"]


def calcular_horario_con_fechas(estructura, fecha_inicio_ciclo, usuario_id=None, curso=None, dias_anticipacion_estudio=5):
    """A partir de la estructura extraida (temas_por_semana, evaluaciones) y
    la fecha real en que empiezan las clases, calcula la fecha exacta de
    cada semana y arma un plan de estudio: para cada evaluacion, sugiere
    desde que fecha empezar a repasar y que temas cubre.

    La fecha de cada evaluacion se resuelve en este orden:
    1. Si la IA extrajo una fecha_exacta del documento, se usa esa.
    2. Si no, y la evaluacion es continua (no parcial/final), se usa el dia
       real de clase del curso (buscado en el horario de clases del alumno
       por 'usuario_id' + 'curso') dentro de esa semana.
    3. Si no hay match de curso, cae al calculo anterior: mismo dia de la
       semana que 'fecha_inicio_ciclo' (aproximado, puede estar desfasado)."""
    temas = {t["semana"]: t["tema"] for t in estructura.get("temas_por_semana", [])}
    evaluaciones = estructura.get("evaluaciones", [])

    def fecha_de_semana(numero_semana):
        # Semana 1 empieza en fecha_inicio_ciclo; cada semana siguiente suma 7 dias
        return fecha_inicio_ciclo + timedelta(weeks=numero_semana - 1)

    dia_semana_curso = _dia_semana_del_curso(usuario_id, curso)

    def es_aleatoria(ev):
        # Parcial y Final no caen el mismo dia que la clase - su fecha varia
        # dentro de la semana 8/16, asi que necesitan fecha_exacta del documento.
        nombre = ev.get("nombre", "").lower()
        return "parcial" in nombre or "final" in nombre

    plan = []
    semana_anterior_evaluada = 0
    for ev in sorted(evaluaciones, key=lambda e: e["semana"]):
        semana_eval = ev["semana"]
        fecha_exacta_txt = ev.get("fecha_exacta")

        if fecha_exacta_txt:
            try:
                fecha_eval = date.fromisoformat(fecha_exacta_txt)
            except ValueError:
                fecha_eval = fecha_de_semana(semana_eval)
        elif not es_aleatoria(ev) and dia_semana_curso is not None:
            inicio_semana = fecha_de_semana(semana_eval)
            offset = (dia_semana_curso - inicio_semana.weekday()) % 7
            fecha_eval = inicio_semana + timedelta(days=offset)
        else:
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


def generar_y_guardar_bloques(usuario_id, materia_general, curso, plan, nivel_dificultad, desde_fecha=None):
    """Calcula los bloques de estudio dia por dia para todo el rango activo
    del plan (desde 'desde_fecha' -- hoy por defecto -- hasta la ultima
    evaluacion), respetando el horario de clases Y los bloques de OTROS
    cursos ya guardados esos dias (no los pisa). Borra los bloques futuros
    viejos de este curso antes de guardar los nuevos (nunca toca el
    pasado). Devuelve (bloques_guardados, hubo_otros_cursos, rango_inicio, rango_fin)."""
    hoy = hoy_peru()
    desde_fecha = max(desde_fecha or hoy, hoy)

    ventanas = [p for p in plan if p["fecha_evaluacion"] >= desde_fecha]
    if not ventanas:
        eliminar_bloques_estudio_futuros(usuario_id, materia_general, curso, desde_fecha)
        return [], False, desde_fecha, desde_fecha

    rango_inicio = max(min(p["fecha_inicio_repaso"] for p in ventanas), desde_fecha)
    rango_fin = max(p["fecha_evaluacion"] for p in ventanas)

    horario_clases = listar_horario_clases(usuario_id)
    otros_bloques = listar_bloques_estudio(usuario_id, fecha_desde=rango_inicio, fecha_hasta=rango_fin)
    otros_bloques = [b for b in otros_bloques if b["curso"] != curso]
    hubo_otros_cursos = len(otros_bloques) > 0

    eliminar_bloques_estudio_futuros(usuario_id, materia_general, curso, desde_fecha)

    bloques_para_guardar = []
    fecha_actual = rango_inicio
    while fecha_actual <= rango_fin:
        evaluacion_del_dia = next(
            (p for p in plan if p["fecha_inicio_repaso"] <= fecha_actual <= p["fecha_evaluacion"]), None
        )
        if evaluacion_del_dia:
            tema_dia = ", ".join(evaluacion_del_dia["temas_a_repasar"][:2]) or evaluacion_del_dia["evaluacion"]
            ocupados_otros = [
                (_hora_a_minutos(b["hora_inicio"]), _hora_a_minutos(b["hora_fin"]))
                for b in otros_bloques if b["fecha"] == str(fecha_actual)
            ]
            bloques_dia = generar_bloques_estudio_del_dia(
                fecha_actual.weekday(), horario_clases, nivel_dificultad, tema_dia, ocupados_extra=ocupados_otros
            )
            for b in bloques_dia:
                bloques_para_guardar.append({
                    "fecha": fecha_actual,
                    "hora_inicio": _minutos_a_hora(b["inicio_min"]),
                    "hora_fin": _minutos_a_hora(b["fin_min"]),
                    "tipo": b["tipo"],
                    "tema": b["tema"],
                    "evaluacion": evaluacion_del_dia["evaluacion"] if b["tipo"] == "estudio" else None,
                })
        fecha_actual += timedelta(days=1)

    guardar_bloques_estudio(usuario_id, materia_general, curso, bloques_para_guardar)
    return bloques_para_guardar, hubo_otros_cursos, rango_inicio, rango_fin


def regenerar_todos_los_planes(usuario_id, desde_fecha=None):
    """Recalcula y reguarda los bloques de TODOS los cursos con plan
    guardado. Se usa cuando cambia el horario de clases del alumno, porque
    eso puede afectar los huecos libres de cualquier curso. Los cursos con
    la evaluacion mas cercana se procesan primero, asi tienen prioridad
    sobre los huecos frente a cursos cuya evaluacion todavia esta lejos."""
    hoy = hoy_peru()
    desde_fecha = desde_fecha or hoy
    eliminar_bloques_estudio_futuros_todos_los_cursos(usuario_id, desde_fecha)

    planes = listar_planes_estudio(usuario_id)
    con_prioridad = []
    for p in planes:
        estructura = p["estructura_json"]
        plan_calc = calcular_horario_con_fechas(
            estructura, date.fromisoformat(p["fecha_inicio_ciclo"]), usuario_id=usuario_id, curso=p["curso"]
        )
        futuras = [pl["fecha_evaluacion"] for pl in plan_calc if pl["fecha_evaluacion"] >= hoy]
        proxima = min(futuras) if futuras else date.max
        con_prioridad.append((proxima, p, plan_calc, estructura.get("nivel_dificultad", "intermedio")))

    for _, p, plan_calc, nivel in sorted(con_prioridad, key=lambda x: x[0]):
        generar_y_guardar_bloques(usuario_id, p["materia_general"], p["curso"], plan_calc, nivel, desde_fecha=desde_fecha)


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
                    with st.spinner("Ajustando tus horarios de estudio a este cambio..."):
                        regenerar_todos_los_planes(usuario["id"])
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
                with st.spinner("Ajustando tus horarios de estudio a este cambio..."):
                    regenerar_todos_los_planes(usuario["id"])
                st.rerun()


def _mostrar_bloques_de_hoy(usuario, plan, estructura, materia_general, curso):
    """Si hoy cae dentro de la ventana de repaso de alguna evaluacion,
    muestra el horario de bloques de estudio con hora exacta para hoy.
    Primero busca si ya hay bloques guardados para hoy (generados con
    generar_y_guardar_bloques); si no hay nada guardado, cae al calculo en
    vivo como respaldo (por ejemplo, si el guardado fallo a mitad de camino)."""
    hoy = hoy_peru()
    evaluacion_activa = next((p for p in plan if p["fecha_inicio_repaso"] <= hoy <= p["fecha_evaluacion"]), None)
    if not evaluacion_activa:
        return

    tema_hoy = ", ".join(evaluacion_activa["temas_a_repasar"][:2]) or evaluacion_activa["evaluacion"]
    guardados_hoy = listar_bloques_estudio(usuario["id"], fecha_desde=hoy, fecha_hasta=hoy, materia_general=materia_general, curso=curso)
    if guardados_hoy:
        bloques = [{
            "tipo": b["tipo"],
            "inicio_min": _hora_a_minutos(b["hora_inicio"]),
            "fin_min": _hora_a_minutos(b["hora_fin"]),
            "tema": b["tema"],
        } for b in guardados_hoy]
    else:
        horario_clases = listar_horario_clases(usuario["id"])
        dia_semana_hoy = hoy.weekday()  # 0=Lunes
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

    if _dia_semana_del_curso(usuario["id"], curso) is None:
        st.caption(
            f"⚠️ No encontramos '{curso}' en tu horario de clases (arriba en '🏫 Configurar mi horario de clases'). "
            "Escribe el nombre EXACTO del curso ahi (ej: si el curso se llama 'Fisica II', usa 'Fisica II', no solo 'Fisica'), "
            "asi las fechas de tus evaluaciones continuas son exactas. Mientras tanto, se usa una fecha aproximada."
        )

    plan_guardado = obtener_plan_estudio(usuario["id"], materia, curso)

    clave_conflicto = f"conflicto_bloques_{materia}_{curso}"
    info_conflicto = st.session_state.get(clave_conflicto)
    if info_conflicto:
        st.warning(
            f"Entre el {info_conflicto['rango_inicio'].strftime('%d/%m')} y el {info_conflicto['rango_fin'].strftime('%d/%m')}, "
            "algunos huecos ya estaban tomados por otro curso. Se generó este horario respetandolos (sin pisarlos)."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 Priorizar este curso (liberar esos huecos)", key=f"reemplazar_{materia}_{curso}", use_container_width=True):
                eliminar_bloques_estudio_de_otros_cursos(usuario["id"], curso, info_conflicto["rango_inicio"], info_conflicto["rango_fin"])
                nivel = plan_guardado["estructura_json"].get("nivel_dificultad", "intermedio")
                plan_recalc = calcular_horario_con_fechas(
                    plan_guardado["estructura_json"], date.fromisoformat(plan_guardado["fecha_inicio_ciclo"]),
                    usuario_id=usuario["id"], curso=curso
                )
                generar_y_guardar_bloques(usuario["id"], materia, curso, plan_recalc, nivel)
                del st.session_state[clave_conflicto]
                st.rerun()
        with col2:
            if st.button("✅ Dejar así (respetando el otro curso)", key=f"dejar_{materia}_{curso}", use_container_width=True):
                del st.session_state[clave_conflicto]
                st.rerun()

    if plan_guardado:
        st.caption(f"Ultimo plan generado para este curso, con inicio de ciclo el {plan_guardado['fecha_inicio_ciclo']}")
        plan = calcular_horario_con_fechas(
            plan_guardado["estructura_json"],
            date.fromisoformat(plan_guardado["fecha_inicio_ciclo"]),
            usuario_id=usuario["id"],
            curso=curso,
        )
        _mostrar_bloques_de_hoy(usuario, plan, plan_guardado["estructura_json"], materia, curso)
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
                    plan = calcular_horario_con_fechas(estructura, fecha_inicio, usuario_id=usuario["id"], curso=curso)
                    nivel = estructura.get("nivel_dificultad", "intermedio")
                    _, hubo_otros, rango_inicio, rango_fin = generar_y_guardar_bloques(usuario["id"], materia, curso, plan, nivel)
                    if hubo_otros:
                        st.session_state[f"conflicto_bloques_{materia}_{curso}"] = {"rango_inicio": rango_inicio, "rango_fin": rango_fin}
                    st.success("Horario generado")
                    _mostrar_plan(plan)
                    st.rerun()


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
