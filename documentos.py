# -*- coding: utf-8 -*-
"""Biblioteca de documentos compartida: los alumnos suben PDFs (en lote),
organizados por materia y curso, y todos pueden verlos, descargarlos y
usarlos como contexto extra para el tutor en el Chat."""
import io
import streamlit as st

from database import guardar_documento, listar_cursos, listar_documentos, eliminar_documento, eliminar_curso, eliminar_documentos, obtener_texto_documento, obtener_url_documento
from utils import extraer_texto_pdf
from materias_data import MATERIAS_DISPONIBLES

LIMITE_CARACTERES_DOCUMENTO = 60000  # ~20 paginas por archivo. Ya no se manda todo al tutor de una:
# se parte en fragmentos y se busca solo lo relevante a cada pregunta (ver database.buscar_fragmentos_relevantes)


def _seccion_subir(usuario):
    st.markdown("### 📤 Subir documentos")
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

    with col_archivos:
        archivos = st.file_uploader("Selecciona uno o varios PDFs", type=["pdf"], accept_multiple_files=True, key="doc_archivos")

    if st.button("Subir a la biblioteca", use_container_width=True):
        if not curso or not curso.strip():
            st.warning("Escribe o elige un curso primero")
        elif not archivos:
            st.warning("Selecciona al menos un PDF")
        else:
            progreso = st.progress(0)
            subidos = 0
            for i, archivo in enumerate(archivos):
                bytes_pdf = archivo.getvalue()
                texto = extraer_texto_pdf(io.BytesIO(bytes_pdf), max_caracteres=LIMITE_CARACTERES_DOCUMENTO)
                if texto:
                    ok = guardar_documento(materia, curso, archivo.name, texto, usuario["nombre"], archivo_bytes=bytes_pdf)
                    if ok:
                        subidos += 1
                progreso.progress((i + 1) / len(archivos))
            if subidos == len(archivos):
                st.success(f"Se subieron los {subidos} documentos a '{curso}' correctamente")
            elif subidos > 0:
                st.warning(f"Se subieron {subidos} de {len(archivos)} documentos. Algunos fallaron (revisa que no sean PDFs escaneados sin texto).")
            else:
                st.error("No se pudo subir ningun documento. Verifica que los PDFs tengan texto seleccionable (no solo imagenes escaneadas).")


def _seccion_explorar(usuario):
    st.markdown("### 📚 Biblioteca")
    es_admin = bool(usuario.get("es_admin"))
    materia_filtro = st.radio("Filtrar por materia", ["Todas"] + MATERIAS_DISPONIBLES, horizontal=True, key="doc_filtro")
    materia_query = None if materia_filtro == "Todas" else materia_filtro

    documentos = listar_documentos(materia_query)
    if not documentos:
        st.info("Todavia no hay documentos subidos. Sube el primero arriba.")
        return

    por_curso = {}
    for doc in documentos:
        clave = f"{doc['materia_general']} - {doc['curso']}"
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
                        marcado = st.checkbox("", key=f"sel_doc_{doc['id']}", label_visibility="collapsed")
                        if marcado:
                            seleccionados.append(doc["id"])
                with col1:
                    fecha = str(doc.get("fecha_subida", ""))[:10]
                    subio = doc.get("subido_por") or "Alguien"
                    st.markdown(f"📄 **{doc['nombre_archivo']}** — subido por {subio} el {fecha}")
                with col2:
                    if st.button("👁️ Ver texto", key=f"ver_doc_{doc['id']}"):
                        st.session_state[f"mostrar_texto_{doc['id']}"] = not st.session_state.get(f"mostrar_texto_{doc['id']}", False)
                with col3:
                    url_pdf = obtener_url_documento(doc.get("storage_path"))
                    if url_pdf:
                        st.markdown(f"[⬇️ Descargar PDF]({url_pdf})")
                    else:
                        st.markdown("<span style='color:rgba(255,255,255,0.4); font-size:0.85em'>Sin PDF guardado</span>", unsafe_allow_html=True)
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

    tab1, tab2 = st.tabs(["📤 Subir", "📁 Explorar"])
    with tab1:
        _seccion_subir(usuario)
    with tab2:
        _seccion_explorar(usuario)
