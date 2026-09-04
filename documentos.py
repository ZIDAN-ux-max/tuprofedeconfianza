# -*- coding: utf-8 -*-
"""Biblioteca de documentos compartida: los alumnos suben PDFs (en lote),
organizados por materia y curso, y todos pueden verlos, descargarlos y
usarlos como contexto extra para el tutor en el Chat. Arriba de todo (fuera
de las pestañas) hay una seccion fija para el Silabo y la Ficha de
actividades evaluadas: son documentos privados, de a uno, que la IA usa
como contexto fijo del curso."""
import io
import streamlit as st

from database import guardar_documento, listar_cursos, listar_documentos, listar_ciclos, listar_carreras, usuario_subio_documento, eliminar_documento, eliminar_curso, eliminar_documentos, obtener_texto_documento, obtener_url_documento, obtener_textos_silabo_ficha_separados
from utils import extraer_texto_pdf, extraer_texto_pptx, extraer_texto_docx
from materias_data import MATERIAS_DISPONIBLES

LIMITE_CARACTERES_DOCUMENTO = 60000  # ~20 paginas por archivo. Ya no se manda todo al tutor de una:
# se parte en fragmentos y se busca solo lo relevante a cada pregunta (ver database.buscar_fragmentos_relevantes)

CSS_TARJETAS_PLAN = """
<style>
.plan-rapido-titulo {
    margin: 0 0 2px 0;
    font-size: 1.05em;
    font-weight: 600;
}
.plan-rapido-sub {
    margin: 0 0 8px 0;
    font-size: 0.78em;
    color: rgba(255,255,255,0.5);
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-silabo) {
    background: linear-gradient(135deg, rgba(0,201,255,0.10), rgba(146,254,157,0.04));
    border: 1px solid rgba(0,201,255,0.35) !important;
    border-radius: 12px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-ficha) {
    background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(192,132,252,0.05));
    border: 1px solid rgba(245,158,11,0.4) !important;
    border-radius: 12px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-silabo) [data-testid="stElementContainer"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-ficha) [data-testid="stElementContainer"] {
    margin-bottom: 2px !important;
}
.tarjeta-titulo {
    margin: 0 0 1px 0;
    font-size: 0.92em;
    font-weight: 600;
}
.tarjeta-sub {
    margin: 0 0 4px 0;
    font-size: 0.74em;
    color: rgba(255,255,255,0.5);
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-silabo) div[data-testid="stFileUploaderDropzone"] {
    border: 1.5px dashed rgba(0,201,255,0.5) !important;
    background: rgba(0,201,255,0.04) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-ficha) div[data-testid="stFileUploaderDropzone"] {
    border: 1.5px dashed rgba(245,158,11,0.55) !important;
    background: rgba(245,158,11,0.04) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-silabo) div[data-testid="stFileUploaderDropzone"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.marca-ficha) div[data-testid="stFileUploaderDropzone"] {
    min-height: 0 !important;
    padding: 6px 8px !important;
    border-radius: 8px !important;
}
</style>
"""


def _seccion_plan_rapido(usuario):
    """Seccion fija (fuera de las pestañas) para subir el Silabo y la Ficha
    de actividades evaluadas: son documentos privados, de a uno por curso,
    que le dan a la IA contexto fijo (en que semana/tema va el curso, cuando
    son las evaluaciones)."""
    st.markdown(CSS_TARJETAS_PLAN, unsafe_allow_html=True)

    st.markdown("<p class='plan-rapido-titulo'>🗓️ Sílabo y Ficha de actividades evaluadas</p>", unsafe_allow_html=True)
    st.markdown("<p class='plan-rapido-sub'>Documentos privados: la IA los usa para saber en qué semana/tema va tu curso y cuándo son tus evaluaciones.</p>", unsafe_allow_html=True)

    col_materia, col_curso = st.columns(2)
    with col_materia:
        materia_pr = st.selectbox("Materia", MATERIAS_DISPONIBLES, key="plan_top_materia")
    with col_curso:
        cursos_existentes_pr = listar_cursos(materia_pr)
        opciones_curso_pr = cursos_existentes_pr + ["+ Nuevo curso..."]
        seleccion_pr = st.selectbox("Curso", opciones_curso_pr, key="plan_top_curso_select") if cursos_existentes_pr else "+ Nuevo curso..."
        if seleccion_pr == "+ Nuevo curso...":
            curso_pr = st.text_input("Nombre del curso", key="plan_top_curso_nuevo", placeholder="ej: Ingles ING-101")
        else:
            curso_pr = seleccion_pr

    ya_hay_silabo, ya_hay_ficha = False, False
    if curso_pr and curso_pr.strip():
        texto_silabo_chk, texto_ficha_chk = obtener_textos_silabo_ficha_separados(materia_pr, curso_pr)
        ya_hay_silabo, ya_hay_ficha = bool(texto_silabo_chk), bool(texto_ficha_chk)

    col_silabo, col_ficha = st.columns(2)
    with col_silabo:
        with st.container(border=True):
            estado_silabo = "<span style='color:#43D69D; font-size:0.8em'>✅ Ya subido</span>" if ya_hay_silabo else "<span style='color:rgba(255,255,255,0.4); font-size:0.8em'>Sin subir todavía</span>"
            st.markdown(f"<div class='marca-silabo'></div><p class='tarjeta-titulo'>📘 Sílabo</p><p class='tarjeta-sub'>Plan de temas por semana</p>{estado_silabo}", unsafe_allow_html=True)
            archivo_silabo = st.file_uploader("Sílabo (PDF o Word)", type=["pdf", "docx"], key="plan_top_silabo", label_visibility="collapsed")
    with col_ficha:
        with st.container(border=True):
            estado_ficha = "<span style='color:#43D69D; font-size:0.8em'>✅ Ya subida</span>" if ya_hay_ficha else "<span style='color:rgba(255,255,255,0.4); font-size:0.8em'>Sin subir todavía</span>"
            st.markdown(f"<div class='marca-ficha'></div><p class='tarjeta-titulo'>🗓️ Ficha de actividades</p><p class='tarjeta-sub'>Fechas y pesos de evaluaciones</p>{estado_ficha}", unsafe_allow_html=True)
            archivo_ficha = st.file_uploader("Ficha de actividades evaluadas (PDF o Word)", type=["pdf", "docx"], key="plan_top_ficha", label_visibility="collapsed")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("Guardar Sílabo / Ficha", use_container_width=True, key="plan_top_guardar"):
        if not curso_pr or not curso_pr.strip():
            st.warning("Escribe o elige un curso primero")
        elif not archivo_silabo and not archivo_ficha:
            st.warning("Sube al menos el Sílabo o la Ficha de actividades")
        else:
            resultados = []
            if archivo_silabo:
                resultados.append(("Sílabo", _subir_uno(materia_pr, curso_pr, archivo_silabo, usuario, None, usuario.get("universidad"), usuario.get("carrera"), "silabo")))
            if archivo_ficha:
                resultados.append(("Ficha de actividades", _subir_uno(materia_pr, curso_pr, archivo_ficha, usuario, None, usuario.get("universidad"), usuario.get("carrera"), "ficha_evaluada")))

            for nombre, resultado in resultados:
                if resultado == "ok":
                    st.success(f"{nombre} guardado correctamente")
                elif resultado == "duplicado":
                    st.info(f"{nombre}: ya existía un documento con el mismo contenido")
                elif resultado == "vacio":
                    st.warning(f"{nombre}: tiene muy poco contenido, revisa que el PDF tenga texto seleccionable")
                else:
                    st.error(f"{nombre}: no se pudo subir, intenta de nuevo")


def _subir_uno(materia, curso, archivo, usuario, ciclo, universidad, carrera, tipo_documento):
    """Sube un solo archivo (usado para Sílabo y Ficha, que son de a uno)."""
    bytes_pdf = archivo.getvalue()
    if archivo.name.lower().endswith(".pptx"):
        texto = extraer_texto_pptx(io.BytesIO(bytes_pdf), max_caracteres=LIMITE_CARACTERES_DOCUMENTO)
    elif archivo.name.lower().endswith(".docx"):
        texto = extraer_texto_docx(io.BytesIO(bytes_pdf), max_caracteres=LIMITE_CARACTERES_DOCUMENTO)
    else:
        texto = extraer_texto_pdf(io.BytesIO(bytes_pdf), max_caracteres=LIMITE_CARACTERES_DOCUMENTO)
    if not texto:
        return "fallido"
    return guardar_documento(materia, curso, archivo.name, texto, usuario["nombre"], archivo_bytes=bytes_pdf, ciclo=ciclo, universidad=universidad, carrera=carrera, tipo_documento=tipo_documento)


def _seccion_subir(usuario):
    st.markdown("### 📤 Subir apuntes")
    st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:0.9em'>Puedes subir varios PDFs a la vez, todos del mismo curso.</p>", unsafe_allow_html=True)

    col_datos, col_archivos = st.columns([1, 2])

    with col_datos:
        materia = st.selectbox("Materia", MATERIAS_DISPONIBLES, key="doc_materia")

        cursos_existentes = listar_cursos(materia)
        opciones_curso = cursos_existentes + ["+ Nuevo curso..."]
        seleccion = st.selectbox("Curso", opciones_curso, key="doc_curso_select") if cursos_existentes else "+ Nuevo curso..."

        if seleccion == "+ Nuevo curso...":
            curso = st.text_input("Nombre del curso nuevo (ej: Mate 3, Ingles Tecnico)", key="doc_curso_nuevo")
        else:
            curso = seleccion

        ciclo = st.text_input("Ciclo (opcional, ej: 2026-1)", key="doc_ciclo")
        universidad = st.text_input(
            "Universidad o instituto (opcional)",
            value=usuario.get("universidad") or "",
            key="doc_universidad",
            help="Para que el Chat solo te muestre documentos de tu misma universidad, no mezclados con los de otras"
        )
        carrera = st.text_input(
            "Carrera (opcional, ej: Ing. Civil, Medicina)",
            value=usuario.get("carrera") or "",
            key="doc_carrera",
            help="Para ordenar la biblioteca y no mezclar documentos de otras carreras"
        )

    with col_archivos:
        archivos = st.file_uploader("Selecciona uno o varios PDFs, PPTX o Word", type=["pdf", "pptx", "docx"], accept_multiple_files=True, key="doc_archivos")

    if st.button("Subir a la biblioteca", use_container_width=True):
        if not curso or not curso.strip():
            st.warning("Escribe o elige un curso primero")
        elif not archivos:
            st.warning("Selecciona al menos un PDF")
        else:
            progreso = st.progress(0)
            subidos = 0
            duplicados = 0
            vacios = 0
            fallidos = 0
            for i, archivo in enumerate(archivos):
                resultado = _subir_uno(materia, curso, archivo, usuario, ciclo, universidad, carrera, "apunte")
                if resultado == "ok":
                    subidos += 1
                elif resultado == "duplicado":
                    duplicados += 1
                elif resultado == "vacio":
                    vacios += 1
                else:
                    fallidos += 1
                progreso.progress((i + 1) / len(archivos))
            if subidos:
                st.success(f"Se subieron {subidos} documento(s) a '{curso}' correctamente")
            if duplicados:
                st.info(f"{duplicados} documento(s) no se subieron porque ya existían (mismo contenido, aunque el nombre del archivo sea distinto)")
            if vacios:
                st.warning(f"{vacios} documento(s) no se subieron porque tienen muy poco contenido (portada suelta, hoja casi en blanco, etc.)")
            if fallidos:
                st.error(f"{fallidos} documento(s) fallaron. Verifica que el PDF tenga texto seleccionable (no solo imagenes escaneadas) o que el PPTX no este dañado.")


def _seccion_explorar(usuario):
    st.markdown("### 📚 Biblioteca")
    es_admin = bool(usuario.get("es_admin"))

    if not es_admin and not usuario_subio_documento(usuario["nombre"]):
        st.info("📤 Sube al menos un documento tuyo (con contenido real) para desbloquear la biblioteca de todos. Ve a la pestaña 'Subir'.")
        return

    busqueda = st.text_input("🔍 Buscar por curso o nombre de archivo", key="doc_busqueda", placeholder="ej: Estática, examen parcial...")

    materia_filtro = st.radio("Filtrar por materia", ["Todas"] + MATERIAS_DISPONIBLES, horizontal=True, key="doc_filtro")
    materia_query = None if materia_filtro == "Todas" else materia_filtro

    TIPOS_DOCUMENTO_LEGIBLE = {"silabo": "📘 Sílabo", "ficha_evaluada": "🗓️ Ficha de actividades", "apunte": "📄 Apunte"}
    tipo_filtro = st.radio("Filtrar por tipo", ["Todos"] + list(TIPOS_DOCUMENTO_LEGIBLE.values()), horizontal=True, key="doc_filtro_tipo")
    tipo_query = None if tipo_filtro == "Todos" else next(k for k, v in TIPOS_DOCUMENTO_LEGIBLE.items() if v == tipo_filtro)

    col_ciclo, col_carrera = st.columns(2)
    with col_ciclo:
        ciclos_disponibles = listar_ciclos(materia_query)
        ciclo_query = None
        if ciclos_disponibles:
            ciclo_filtro = st.selectbox("Filtrar por ciclo", ["Todos"] + ciclos_disponibles, key="doc_filtro_ciclo")
            ciclo_query = None if ciclo_filtro == "Todos" else ciclo_filtro
    with col_carrera:
        carreras_disponibles = listar_carreras(materia_query)
        carrera_query = None
        if carreras_disponibles:
            carrera_filtro = st.selectbox("Filtrar por carrera", ["Todas"] + carreras_disponibles, key="doc_filtro_carrera")
            carrera_query = None if carrera_filtro == "Todas" else carrera_filtro

    documentos = listar_documentos(materia_query, ciclo_query, carrera_query)
    if tipo_query:
        documentos = [d for d in documentos if (d.get("tipo_documento") or "apunte") == tipo_query]
    if busqueda and busqueda.strip():
        texto_buscado = busqueda.strip().lower()
        documentos = [
            d for d in documentos
            if texto_buscado in (d.get("curso") or "").lower() or texto_buscado in (d.get("nombre_archivo") or "").lower()
        ]
    if not documentos:
        if busqueda and busqueda.strip():
            st.info(f"No se encontró ningún documento que coincida con '{busqueda.strip()}'.")
        else:
            st.info("Todavia no hay documentos subidos. Sube el primero arriba.")
        return

    por_curso = {}
    for doc in documentos:
        etiqueta_ciclo = f" ({doc['ciclo']})" if doc.get("ciclo") else ""
        etiqueta_carrera = f" [{doc['carrera']}]" if doc.get("carrera") else ""
        clave = f"{doc['materia_general']} - {doc['curso']}{etiqueta_ciclo}{etiqueta_carrera}"
        por_curso.setdefault(clave, []).append(doc)

    for carpeta, docs in sorted(por_curso.items()):
        with st.expander(f"📁 {carpeta} ({len(docs)} documento{'s' if len(docs) != 1 else ''})"):
            if es_admin:
                clave_confirmacion = f"confirmar_borrar_curso_{carpeta}"
                col_titulo, col_borrar_todo = st.columns([4, 2])
                with col_borrar_todo:
                    if not st.session_state.get(clave_confirmacion):
                        if st.button("🗑️ Eliminar todo este curso", key=f"borrar_curso_{carpeta}"):
                            st.session_state[clave_confirmacion] = True
                            st.rerun()
                    else:
                        st.warning(f"¿Seguro? Se borrarán los {len(docs)} documentos de este curso.")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Si, borrar todo", key=f"confirmar_si_{carpeta}"):
                                eliminar_curso(docs[0]["materia_general"], docs[0]["curso"])
                                st.session_state[clave_confirmacion] = False
                                st.rerun()
                        with c2:
                            if st.button("Cancelar", key=f"confirmar_no_{carpeta}"):
                                st.session_state[clave_confirmacion] = False
                                st.rerun()

            seleccionados = []
            for doc in docs:
                if es_admin:
                    col0, col1, col2, col3, col4 = st.columns([0.4, 3.6, 1.3, 1.3, 0.7])
                else:
                    col1, col2, col3 = st.columns([4, 1.3, 1.3])

                if es_admin:
                    with col0:
                        marcado = st.checkbox("Seleccionar documento", key=f"sel_doc_{doc['id']}", label_visibility="collapsed")
                        if marcado:
                            seleccionados.append(doc["id"])
                with col1:
                    fecha = str(doc.get("fecha_subida", ""))[:10]
                    subio = doc.get("subido_por") or "Alguien"
                    emoji_tipo_doc = TIPOS_DOCUMENTO_LEGIBLE.get(doc.get("tipo_documento") or "apunte", "📄 Apunte").split(" ")[0]
                    st.markdown(f"{emoji_tipo_doc} **{doc['nombre_archivo']}** — subido por {subio} el {fecha}")
                with col2:
                    if st.button("👁️ Ver texto", key=f"ver_doc_{doc['id']}"):
                        st.session_state[f"mostrar_texto_{doc['id']}"] = not st.session_state.get(f"mostrar_texto_{doc['id']}", False)
                with col3:
                    url_pdf = obtener_url_documento(doc.get("storage_path"))
                    if url_pdf:
                        st.markdown(f"[📄 Abrir archivo]({url_pdf})")
                    else:
                        st.markdown("<span style='color:rgba(255,255,255,0.4); font-size:0.85em'>Sin archivo guardado</span>", unsafe_allow_html=True)
                if es_admin:
                    with col4:
                        if st.button("🗑️", key=f"del_doc_{doc['id']}", help="Eliminar este documento"):
                            eliminar_documento(doc["id"])
                            st.rerun()

                if st.session_state.get(f"mostrar_texto_{doc['id']}"):
                    texto_doc = obtener_texto_documento(doc["id"])
                    st.text_area("Texto extraido de este PDF", texto_doc, height=200, key=f"texto_area_{doc['id']}")

                st.markdown("<hr style='border-color:rgba(255,255,255,0.1); margin:8px 0'>", unsafe_allow_html=True)

            if es_admin and seleccionados:
                clave_confirmacion_sel = f"confirmar_borrar_seleccion_{carpeta}"
                st.markdown(f"**{len(seleccionados)} documento(s) seleccionado(s)**")
                if not st.session_state.get(clave_confirmacion_sel):
                    if st.button(f"🗑️ Eliminar los {len(seleccionados)} seleccionados", key=f"borrar_sel_{carpeta}"):
                        st.session_state[clave_confirmacion_sel] = True
                        st.rerun()
                else:
                    st.warning(f"¿Seguro que quieres borrar estos {len(seleccionados)} documentos?")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Si, borrar seleccionados", key=f"confirmar_sel_si_{carpeta}"):
                            eliminar_documentos(seleccionados)
                            st.session_state[clave_confirmacion_sel] = False
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key=f"confirmar_sel_no_{carpeta}"):
                            st.session_state[clave_confirmacion_sel] = False
                            st.rerun()


def mostrar_documentos(usuario):
    st.markdown("<h1 style='text-align:center;'>📚 Documentos</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Sube tus resumenes y apuntes - el tutor los usara como contexto cuando elijas el curso en el Chat</p>", unsafe_allow_html=True)
    st.divider()

    _seccion_plan_rapido(usuario)

    st.divider()

    tab1, tab2 = st.tabs(["📤 Subir", "📁 Explorar"])
    with tab1:
        _seccion_subir(usuario)
    with tab2:
        _seccion_explorar(usuario)
