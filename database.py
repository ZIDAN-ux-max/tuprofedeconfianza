# -*- coding: utf-8 -*-
"""Capa de acceso a datos (Supabase). Todo lo que toca la base de datos vive aqui."""
import streamlit as st
from datetime import datetime, timedelta, date
from supabase import create_client

from utils import hash_password, dividir_en_fragmentos
from logros_data import LOGROS_DISPONIBLES

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])


# ===================== USUARIOS =====================

def login(email, password):
    result = supabase.table("usuarios").select("*").eq("email", email).eq("password", hash_password(password)).execute()
    if result.data:
        return result.data[0]
    return None


def registrar(nombre, email, password, edad=None, grado=None, ciclo=None):
    """Crea un usuario nuevo. edad/grado/ciclo son opcionales pero recomendados
    para que el tutor pueda personalizar mejor sus explicaciones."""
    try:
        payload = {
            "nombre": nombre,
            "email": email,
            "password": hash_password(password),
        }
        if edad:
            payload["edad"] = edad
        if grado:
            payload["grado"] = grado
        if ciclo:
            payload["ciclo"] = ciclo
        result = supabase.table("usuarios").insert(payload).execute()
        return result.data[0]
    except Exception:
        return None


# ===================== CONVERSACIONES =====================

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


# ===================== ASISTENCIA / RACHA =====================

def registrar_asistencia(usuario_id):
    try:
        hoy = date.today().isoformat()
        hora_actual = datetime.now().hour
        existe = supabase.table("asistencia").select("*").eq("usuario_id", usuario_id).eq("fecha", hoy).execute()
        if not existe.data:
            usuario = supabase.table("usuarios").select("*").eq("id", usuario_id).execute().data[0]
            ultima = usuario.get("ultima_visita")
            racha_actual = usuario.get("racha") or 0
            if ultima:
                ultima_date = date.fromisoformat(str(ultima).split("T")[0])
                diferencia = (date.today() - ultima_date).days
                if diferencia == 1:
                    racha_actual += 1
                elif diferencia > 1:
                    racha_actual = 1
            else:
                racha_actual = 1
            supabase.table("asistencia").insert({
                "usuario_id": usuario_id,
                "fecha": hoy,
                "racha": racha_actual,
                "hora": hora_actual
            }).execute()
            supabase.table("usuarios").update({
                "racha": racha_actual,
                "ultima_visita": hoy
            }).eq("id", usuario_id).execute()
        return supabase.table("usuarios").select("racha").eq("id", usuario_id).execute().data[0].get("racha", 0)
    except Exception:
        return 0


# ===================== ESTADISTICAS / RANKING =====================

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
        except Exception:
            pass
    try:
        racha_result = supabase.table("usuarios").select("racha").eq("id", usuario_id).execute()
        racha_val = racha_result.data[0].get("racha", 0) if racha_result.data else 0
    except Exception:
        racha_val = 0
    hora_actual = datetime.now().hour
    return {
        "total": total,
        "matematicas": mate,
        "ingles": ingles,
        "hoy": hoy_count,
        "semana": semana_count,
        "racha": racha_val,
        "hora": hora_actual,
        "pdfs": 0
    }


def obtener_ranking():
    try:
        result = supabase.table("conversaciones").select("usuario_id").execute()
        conteo = {}
        for c in result.data:
            uid = c["usuario_id"]
            conteo[uid] = conteo.get(uid, 0) + 1
        ranking = []
        for uid, total in sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]:
            usuario = supabase.table("usuarios").select("nombre, racha").eq("id", uid).execute()
            if usuario.data:
                logros = supabase.table("logros").select("nombre").eq("usuario_id", uid).execute()
                ranking.append({
                    "nombre": usuario.data[0]["nombre"],
                    "total": total,
                    "racha": usuario.data[0].get("racha", 0),
                    "logros": len(logros.data)
                })
        return ranking
    except Exception as e:
        # TEMPORAL: mostramos el error real en vez de esconderlo, para poder
        # diagnosticar por que el ranking sale vacio. Quitar el st.error
        # despues de encontrar y arreglar la causa.
        import streamlit as st
        st.error(f"Error en obtener_ranking: {e}")
        return []


# ===================== LOGROS =====================

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
            condicion = logro["condicion"]
            valor = logro["valor"]
            if condicion == "hora":
                if valor == 7 and stats["hora"] < 7:
                    otorgar_logro(usuario_id, logro)
                    nuevos_logros.append(logro)
                elif valor == 23 and stats["hora"] >= 23:
                    otorgar_logro(usuario_id, logro)
                    nuevos_logros.append(logro)
            elif condicion in stats and stats[condicion] >= valor:
                otorgar_logro(usuario_id, logro)
                nuevos_logros.append(logro)
    return nuevos_logros


# ===================== PERFIL DEL ALUMNO (NUEVO) =====================
# Esta es la capa de "memoria" que permite que el tutor se adapte al alumno
# en vez de responder siempre lo mismo. Requiere la tabla perfil_alumno
# (ver migracion.sql).

def obtener_perfil_alumno(usuario_id, materia):
    """Devuelve el perfil de progreso del alumno para una materia, o uno vacio
    si todavia no existe."""
    try:
        result = supabase.table("perfil_alumno").select("*").eq("usuario_id", usuario_id).eq("materia", materia).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return {
        "temas_dominados": [],
        "temas_dificiles": [],
        "nivel_estimado": "sin_evaluar",
        "ultimo_resumen": ""
    }


def guardar_perfil_alumno(usuario_id, materia, perfil):
    """Crea o actualiza (upsert) el perfil de progreso del alumno en una materia."""
    try:
        existente = supabase.table("perfil_alumno").select("id").eq("usuario_id", usuario_id).eq("materia", materia).execute()
        payload = {
            "usuario_id": usuario_id,
            "materia": materia,
            "temas_dominados": perfil.get("temas_dominados", []),
            "temas_dificiles": perfil.get("temas_dificiles", []),
            "nivel_estimado": perfil.get("nivel_estimado", "sin_evaluar"),
            "ultimo_resumen": perfil.get("ultimo_resumen", ""),
            "actualizado_en": datetime.now().isoformat()
        }
        if existente.data:
            supabase.table("perfil_alumno").update(payload).eq("id", existente.data[0]["id"]).execute()
        else:
            supabase.table("perfil_alumno").insert(payload).execute()
    except Exception:
        pass


# ===================== BIBLIOTECA DE DOCUMENTOS (NUEVO) =====================
# Documentos (PDFs) compartidos entre todos los alumnos, organizados por
# materia general (Matematicas/Ingles) y curso especifico (ej: "Mate 3").
# El texto extraido se usa como contexto extra para el tutor cuando el
# alumno elige ese curso en el Chat.

def guardar_documento(materia_general, curso, nombre_archivo, contenido_texto, subido_por):
    """Guarda el documento y ademas lo parte en fragmentos pequenos
    (documento_chunks) para poder buscar despues solo lo relevante a cada
    pregunta, en vez de mandar el PDF completo cada vez."""
    try:
        curso = curso.strip()
        result = supabase.table("documentos").insert({
            "materia_general": materia_general,
            "curso": curso,
            "nombre_archivo": nombre_archivo,
            "contenido_texto": contenido_texto,
            "subido_por": subido_por
        }).execute()
        documento_id = result.data[0]["id"]

        fragmentos = dividir_en_fragmentos(contenido_texto)
        filas_chunks = [
            {
                "documento_id": documento_id,
                "materia_general": materia_general,
                "curso": curso,
                "chunk_index": i,
                "chunk_texto": frag
            }
            for i, frag in enumerate(fragmentos)
        ]
        if filas_chunks:
            supabase.table("documento_chunks").insert(filas_chunks).execute()
        return True
    except Exception:
        return False


def listar_cursos(materia_general):
    """Devuelve la lista de cursos unicos ya creados para una materia,
    para poder mostrarlos como sugerencia al subir o elegir curso."""
    try:
        result = supabase.table("documentos").select("curso").eq("materia_general", materia_general).execute()
        cursos = sorted(set(d["curso"] for d in result.data))
        return cursos
    except Exception:
        return []


def listar_documentos(materia_general=None):
    """Lista todos los documentos, opcionalmente filtrados por materia,
    agrupables luego por curso en la UI."""
    try:
        query = supabase.table("documentos").select("id, materia_general, curso, nombre_archivo, subido_por, fecha_subida")
        if materia_general:
            query = query.eq("materia_general", materia_general)
        result = query.order("curso").execute()
        return result.data
    except Exception:
        return []


def buscar_fragmentos_relevantes(materia_general, curso, pregunta, top_n=6):
    """Busca, entre TODOS los fragmentos de los documentos de ese curso,
    solo los mas relacionados con la pregunta del alumno (usando similitud
    de texto TF-IDF). Esto es lo que permite tener 10 PDFs de 10 paginas
    cada uno sin mandarle todo eso al tutor en cada mensaje."""
    try:
        result = supabase.table("documento_chunks").select("chunk_texto").eq("materia_general", materia_general).eq("curso", curso).execute()
        chunks = [c["chunk_texto"] for c in result.data]
        if not chunks:
            return ""

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(max_features=5000)
        matriz = vectorizer.fit_transform(chunks + [pregunta])
        similitudes = cosine_similarity(matriz[-1], matriz[:-1])[0]

        indices_top = similitudes.argsort()[::-1][:top_n]
        seleccionados = [chunks[i] for i in indices_top if similitudes[i] > 0]

        if not seleccionados:
            return ""
        return "\n\n---\n\n".join(seleccionados)
    except Exception:
        return ""


def eliminar_documento(documento_id):
    """Borra el documento. Los fragmentos asociados se borran solos
    (ON DELETE CASCADE en documento_chunks)."""
    try:
        supabase.table("documentos").delete().eq("id", documento_id).execute()
        return True
    except Exception:
        return False
