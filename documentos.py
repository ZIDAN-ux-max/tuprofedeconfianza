# -*- coding: utf-8 -*-
"""Biblioteca de documentos compartida: los alumnos suben PDFs (en lote),
organizados por materia y curso, y todos pueden verlos y usarlos como
contexto extra para el tutor en el Chat."""
import streamlit as st

from database import guardar_documento, listar_cursos, listar_documentos, eliminar_documento
from utils import extraer_texto_pdf

LIMITE_CARACTERES_DOCUMENTO = 60000  # ~20 paginas por archivo. Ya no se manda todo al tutor de una:
# se parte en fragmentos y se busca solo lo relevante a cada pregunta (ver database.buscar_fragmentos_relevantes)


def _seccion_subir(usuario):
    st.markdown("### 📤 Subir documentos")
    st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:0.9em'>Puedes subir varios PDFs a la vez, todos del mismo curso.</p>", unsafe_allow_html=True)

    materia = st.selectbox("Materia", ["Matematicas", "Ingles"], key="doc_materia")

    cursos_existentes = listar_cursos(materia)
    opciones_curso = cursos_existentes + ["+ Nuevo curso..."]
    seleccion = st.selectbox("Curso", opciones_curso, key="doc_curso_select") if cursos_existentes else "+ Nuevo curso..."

    if seleccion == "+ Nuevo curso...":
        curso = st.text_input("Nombre del curso nuevo (ej: Mate 3, Ingles Tecnico)", key="doc_curso_nuevo")
    else:
        curso = seleccion

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
                texto = extraer_texto_pdf(archivo, max_caracteres=LIMITE_CARACTERES_DOCUMENTO)
                if texto:
                    ok = guardar_documento(materia, curso, archivo.name, texto, usuario["nombre"])
                    if ok:
                        subidos += 1
                progreso.progress((i + 1) / len(archivos))
            if subidos == len(archivos):
                st.success(f"Se subieron los {subidos} documentos a '{curso}' correctamente")
            elif subidos > 0:
                st.warning(f"Se subieron {subidos} de {len(archivos)} documentos. Algunos fallaron (revisa que no sean PDFs escaneados sin texto).")
            else:
                st.error("No se pudo subir ningun documento. Verifica que los PDFs tengan texto seleccionable (no solo imagenes escaneadas).")


def _seccion_explorar():
    st.markdown("### 📚 Biblioteca")
    materia_filtro = st.radio("Filtrar por materia", ["Todas", "Matematicas", "Ingles"], horizontal=True, key="doc_filtro")
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
            for doc in docs:
                col1, col2 = st.columns([5, 1])
                with col1:
                    fecha = str(doc.get("fecha_subida", ""))[:10]
                    subio = doc.get("subido_por") or "Alguien"
                    st.markdown(f"📄 **{doc['nombre_archivo']}** — subido por {subio} el {fecha}")
                with col2:
                    if st.button("🗑️", key=f"del_doc_{doc['id']}", help="Eliminar este documento"):
                        eliminar_documento(doc["id"])
                        st.rerun()


def mostrar_documentos(usuario):
    st.markdown("<h1 style='text-align:center;'>📚 Documentos</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:rgba(255,255,255,0.6)'>Sube tus resumenes y apuntes - el tutor los usara como contexto cuando elijas el curso en el Chat</p>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2 = st.tabs(["📤 Subir", "📁 Explorar"])
    with tab1:
        _seccion_subir(usuario)
    with tab2:
        _seccion_explorar()
