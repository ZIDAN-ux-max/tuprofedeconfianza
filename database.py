# -*- coding: utf-8 -*-
"""Capa de acceso a datos (Supabase). Todo lo que toca la base de datos vive aqui."""
import streamlit as st
import re
import unicodedata
from datetime import datetime, timedelta, date
from supabase import create_client

from utils import hash_password, dividir_en_fragmentos, hash_texto, ahora_peru, hoy_peru
from logros_data import LOGROS_DISPONIBLES

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

MIN_CARACTERES_DOCUMENTO = 300  # ~50-60 palabras. Filtra portadas sueltas, hojas
# casi en blanco o PDFs sin contenido real; un examen o apunte normal de 1 pagina
# ya supera esto de sobra.


# ===================== USUARIOS =====================

def login(email, password):
    email = email.strip().lower()
    result = supabase.table("usuarios").select("*").ilike("email", email).eq("password", hash_password(password)).execute()
    if result.data:
        return result.data[0]
    return None


def registrar(nombre, email, password, edad=None, grado=None, ciclo=None, carrera=None, universidad=None):
    """Crea un usuario nuevo. edad/grado/ciclo/carrera/universidad son
    opcionales pero recomendados para que el tutor pueda personalizar mejor
    sus explicaciones, filtrar las materias relevantes, y para que el Chat
    solo muestre documentos de la propia universidad y ciclo del alumno.
    Devuelve (usuario, error): error es None si salio bien, o "email"/"nombre"/
    "cupo_lleno" segun cual haya fallado."""
    try:
        limpiar_usuarios_inactivos()
        total = supabase.table("usuarios").select("id", count="exact").execute()
        if (total.count or 0) >= 100:
            return None, "cupo_lleno"

        email = email.strip().lower()
        nombre = nombre.strip()

        if supabase.table("usuarios").select("id").ilike("email", email).execute().data:
            return None, "email"
        if supabase.table("usuarios").select("id").ilike("nombre", nombre).execute().data:
            return None, "nombre"

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
        if carrera:
            payload["carrera"] = carrera
        if universidad:
            payload["universidad"] = universidad.strip()
        result = supabase.table("usuarios").insert(payload).execute()
        return result.data[0], None
    except Exception:
        return None, "otro"


# ===================== CONVERSACIONES =====================

def guardar_conversacion(usuario_id, mensaje, respuesta, materia):
    supabase.table("conversaciones").insert({
        "usuario_id": usuario_id,
        "mensaje": mensaje,
        "respuesta": respuesta,
        "materia": materia,
        "fecha": ahora_peru().isoformat()
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
        hoy = hoy_peru().isoformat()
        hora_actual = ahora_peru().hour
        existe = supabase.table("asistencia").select("*").eq("usuario_id", usuario_id).eq("fecha", hoy).execute()
        if not existe.data:
            usuario = supabase.table("usuarios").select("*").eq("id", usuario_id).execute().data[0]
            ultima = usuario.get("ultima_visita")
            racha_actual = usuario.get("racha") or 0
            if ultima:
                ultima_date = date.fromisoformat(str(ultima).split("T")[0])
                diferencia = (hoy_peru() - ultima_date).days
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


def limpiar_usuarios_inactivos():
    """Borra usuarios rotativos (es_fijo=false) que llevan mas de 30 dias
    sin usar la app, liberando su cupo. No toca a los usuarios fijos."""
    try:
        limite = (hoy_peru() - timedelta(days=30)).isoformat()
        supabase.table("usuarios").delete().eq("es_fijo", False).lt("ultima_visita", limite).execute()
    except Exception:
        pass


# ===================== ESTADISTICAS / RANKING =====================

def obtener_estadisticas(usuario_id):
    result = supabase.table("conversaciones").select("*").eq("usuario_id", usuario_id).execute()
    total = len(result.data)

    conteo_por_materia = {}
    for c in result.data:
        m = c.get("materia", "Otro")
        conteo_por_materia[m] = conteo_por_materia.get(m, 0) + 1

    hoy = ahora_peru().date()
    semana = ahora_peru() - timedelta(days=7)
    hoy_count = 0
    semana_count = 0
    for c in result.data:
        try:
            if c.get("fecha"):
                fecha = datetime.fromisoformat(str(c["fecha"]).replace("Z", "+00:00"))
                fecha = fecha.replace(tzinfo=None)  # se compara como hora local, sin importar si el dato viejo era UTC o el nuevo es Peru
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
    hora_actual = ahora_peru().hour
    return {
        "total": total,
        "por_materia": conteo_por_materia,
        # se mantienen por compatibilidad con partes del codigo que ya usaban estas claves
        "matematicas": conteo_por_materia.get("Matematicas", 0),
        "ingles": conteo_por_materia.get("Ingles", 0),
        "hoy": hoy_count,
        "semana": semana_count,
        "racha": racha_val,
        "hora": hora_actual,
        "pdfs": 0
    }


def obtener_ranking(usuario_id=None, top=30):
    """Ranking combinado: puntos de tareas cumplidas + puntos de logros +
    una fraccion de los mensajes de chat (para que seguir preguntando siga
    sumando, sin que aplaste el esfuerzo de la disciplina diaria).

    Devuelve (lista_top, mi_posicion). 'lista_top' son los primeros 'top'
    puestos. 'mi_posicion' es None si no se paso usuario_id o si ese
    usuario ya esta dentro de 'lista_top'; si esta mas abajo, es un dict
    con su puesto y puntos exactos, para poder mostrarlo aparte."""
    try:
        conv = supabase.table("conversaciones").select("usuario_id").execute()
        conteo_chat = {}
        for c in conv.data:
            uid = c["usuario_id"]
            conteo_chat[uid] = conteo_chat.get(uid, 0) + 1

        tareas = supabase.table("tareas_diarias").select("usuario_id, puntos").eq("completado", True).execute()
        puntos_tareas = {}
        for t in tareas.data:
            uid = t["usuario_id"]
            puntos_tareas[uid] = puntos_tareas.get(uid, 0) + (t.get("puntos") or 1)

        logros_puntos_por_nombre = {l["nombre"]: l.get("puntos", 0) for l in LOGROS_DISPONIBLES}
        logros = supabase.table("logros").select("usuario_id, nombre").execute()
        puntos_logros = {}
        cant_logros = {}
        for l in logros.data:
            uid = l["usuario_id"]
            puntos_logros[uid] = puntos_logros.get(uid, 0) + logros_puntos_por_nombre.get(l["nombre"], 0)
            cant_logros[uid] = cant_logros.get(uid, 0) + 1

        todos_ids = set(conteo_chat) | set(puntos_tareas) | set(puntos_logros)

        calculado = []
        for uid in todos_ids:
            pc = conteo_chat.get(uid, 0) // 3
            pt = puntos_tareas.get(uid, 0)
            pl = puntos_logros.get(uid, 0)
            calculado.append((uid, pc + pt + pl, pc, pt, pl))
        calculado.sort(key=lambda x: x[1], reverse=True)

        ranking = []
        for uid, total_puntos, pc, pt, pl in calculado[:top]:
            usuario = supabase.table("usuarios").select("nombre, racha").eq("id", uid).execute()
            if usuario.data:
                ranking.append({
                    "nombre": usuario.data[0]["nombre"],
                    "total": conteo_chat.get(uid, 0),
                    "racha": usuario.data[0].get("racha", 0),
                    "logros": cant_logros.get(uid, 0),
                    "puntos": total_puntos,
                    "puntos_tareas": pt,
                    "puntos_logros": pl
                })

        mi_posicion = None
        if usuario_id and usuario_id not in [uid for uid, *_ in calculado[:top]]:
            for i, (uid, total_puntos, pc, pt, pl) in enumerate(calculado):
                if uid == usuario_id:
                    mi_posicion = {"puesto": i + 1, "puntos": total_puntos, "de_total": len(calculado)}
                    break

        return ranking, mi_posicion
    except Exception:
        return [], None


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
        "fecha": ahora_peru().isoformat()
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


def obtener_temas_debiles(usuario_id, materias):
    """Junta los temas_dificiles guardados en el perfil del alumno para
    cada una de sus materias. Devuelve {materia: [temas]} solo con las
    materias que tienen al menos un tema dificil registrado."""
    resultado = {}
    for materia in materias:
        perfil = obtener_perfil_alumno(usuario_id, materia)
        temas = perfil.get("temas_dificiles") or []
        if temas:
            resultado[materia] = temas
    return resultado


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
            "actualizado_en": ahora_peru().isoformat()
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

BUCKET_DOCUMENTOS = "documentos-pdf"


def _sanear_para_storage(texto):
    """Supabase Storage rechaza tildes, enies, espacios y varios simbolos en
    las rutas (error 'InvalidKey'). Esto convierte el texto a algo seguro
    para usar como nombre de archivo/carpeta, SOLO para la ruta de Storage
    (el nombre 'bonito' que ve el alumno en la biblioteca no se toca)."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^A-Za-z0-9._-]+", "_", texto)
    return texto.strip("_") or "archivo"


def obtener_textos_silabo_ficha_separados(materia_general, curso, limite_cada_uno=4000):
    """Trae el texto del silabo y de la ficha de evaluacion POR SEPARADO
    (no combinados como obtener_texto_silabo), con mas espacio cada uno -
    pensada para una extraccion puntual (una sola vez), no para meterse en
    cada mensaje del Chat. Devuelve (texto_silabo, texto_ficha)."""
    try:
        result = supabase.table("documentos").select("contenido_texto, tipo_documento").eq("materia_general", materia_general).eq("curso", curso).in_("tipo_documento", ["silabo", "ficha_evaluada"]).execute()
        if not result.data:
            return "", ""
        texto_silabo = "\n\n".join(d["contenido_texto"] for d in result.data if d.get("tipo_documento") == "silabo" and d.get("contenido_texto"))[:limite_cada_uno]
        texto_ficha = "\n\n".join(d["contenido_texto"] for d in result.data if d.get("tipo_documento") == "ficha_evaluada" and d.get("contenido_texto"))[:limite_cada_uno]
        return texto_silabo, texto_ficha
    except Exception:
        return "", ""


def obtener_texto_silabo(materia_general, curso, limite_caracteres=1800):
    """Trae el texto de los documentos marcados como 'silabo' o
    'ficha_evaluada' de este curso, para dárselo siempre al tutor como
    contexto fijo (en que semana/tema esta el curso, fechas y pesos de
    evaluacion), sin depender de que la pregunta del alumno coincida con
    ese texto por similitud. Limitado en tamaño para no gastar de mas el
    presupuesto de tokens de la IA. Devuelve las dos partes etiquetadas
    por separado, para que la IA sepa distinguir una de la otra."""
    try:
        result = supabase.table("documentos").select("contenido_texto, tipo_documento").eq("materia_general", materia_general).eq("curso", curso).in_("tipo_documento", ["silabo", "ficha_evaluada"]).execute()
        if not result.data:
            return ""
        textos_silabo = [d["contenido_texto"] for d in result.data if d.get("tipo_documento") == "silabo" and d.get("contenido_texto")]
        textos_ficha = [d["contenido_texto"] for d in result.data if d.get("tipo_documento") == "ficha_evaluada" and d.get("contenido_texto")]

        limite_por_parte = limite_caracteres // 2 if (textos_silabo and textos_ficha) else limite_caracteres
        partes = []
        if textos_silabo:
            partes.append("--- SILABO (cronograma, temas por semana) ---\n" + "\n\n".join(textos_silabo)[:limite_por_parte])
        if textos_ficha:
            partes.append("--- FICHA DE EVALUACION (rubricas, fechas y pesos) ---\n" + "\n\n".join(textos_ficha)[:limite_por_parte])
        return "\n\n".join(partes)
    except Exception:
        return ""


def guardar_documento(materia_general, curso, nombre_archivo, contenido_texto, subido_por, archivo_bytes=None, ciclo=None, universidad=None, carrera=None, tipo_documento="apunte"):
    """Guarda el documento (metadata + texto), lo parte en fragmentos pequenos
    (documento_chunks) para busqueda por relevancia, y si se paso el PDF
    original en bytes, lo sube a Supabase Storage para poder descargarlo
    despues desde la biblioteca. 'ciclo', 'universidad' y 'carrera' son
    etiquetas para filtrar en la biblioteca y en el selector de curso del
    Chat (asi no se mezclan documentos de distintas universidades/carreras
    con el mismo nombre de curso) - no afectan la busqueda del tutor en si,
    que sigue siendo por materia+curso.

    Devuelve "ok" si se guardo, "duplicado" si ya existia un documento con
    el mismo contenido (mismo texto, aunque cambie el nombre del archivo),
    "vacio" si el texto extraido es muy corto para ser un documento real
    (menos de MIN_CARACTERES_DOCUMENTO caracteres, ej: portada suelta o
    PDF casi en blanco), o False si fallo la subida."""
    try:
        curso = curso.strip()
        if len((contenido_texto or "").strip()) < MIN_CARACTERES_DOCUMENTO:
            return "vacio"
        storage_path = None
        contenido_hash = hash_texto(contenido_texto)

        ya_existe = supabase.table("documentos").select("id").eq("contenido_hash", contenido_hash).limit(1).execute()
        if ya_existe.data:
            return "duplicado"

        if archivo_bytes:
            import uuid
            ruta_materia = _sanear_para_storage(materia_general)
            ruta_curso = _sanear_para_storage(curso)
            ruta_archivo = _sanear_para_storage(nombre_archivo)
            storage_path = f"{ruta_materia}/{ruta_curso}/{uuid.uuid4().hex}_{ruta_archivo}"
            content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation" if nombre_archivo.lower().endswith(".pptx") else "application/pdf"
            try:
                supabase.storage.from_(BUCKET_DOCUMENTOS).upload(
                    storage_path, archivo_bytes, {"content-type": content_type}
                )
            except Exception:
                storage_path = None  # si falla la subida del archivo, seguimos igual guardando el texto (la UI ya avisa "Sin PDF guardado" cuando corresponde)

        result = supabase.table("documentos").insert({
            "materia_general": materia_general,
            "curso": curso,
            "ciclo": ciclo.strip() if ciclo else None,
            "universidad": universidad.strip() if universidad else None,
            "carrera": carrera.strip() if carrera else None,
            "tipo_documento": tipo_documento,
            "nombre_archivo": nombre_archivo,
            "contenido_texto": contenido_texto,
            "contenido_hash": contenido_hash,
            "subido_por": subido_por,
            "storage_path": storage_path
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
        return "ok"
    except Exception:
        return False


def obtener_url_documento(storage_path):
    """Devuelve la URL publica para descargar el PDF original desde Storage,
    o None si ese documento no tiene archivo guardado (documentos subidos
    antes de esta funcion)."""
    if not storage_path:
        return None
    try:
        return supabase.storage.from_(BUCKET_DOCUMENTOS).get_public_url(storage_path)
    except Exception:
        return None


def listar_cursos(materia_general, universidad=None, ciclo=None):
    """Devuelve la lista de cursos unicos ya creados para una materia, para
    poder mostrarlos como sugerencia al subir o elegir curso. Si se pasan
    universidad/ciclo, filtra solo a los cursos de esa universidad y ciclo
    (para que el selector del Chat no mezcle documentos de otras
    universidades que casualmente pusieron el mismo nombre de curso)."""
    try:
        query = supabase.table("documentos").select("curso").eq("materia_general", materia_general)
        if universidad:
            query = query.eq("universidad", universidad)
        if ciclo:
            query = query.eq("ciclo", ciclo)
        result = query.execute()
        cursos = sorted(set(d["curso"] for d in result.data))
        return cursos
    except Exception:
        return []


def usuario_subio_documento(nombre_usuario):
    """True si este usuario ya subio al menos un documento valido (paso el
    filtro de contenido minimo). Se usa para desbloquear la Biblioteca:
    incentiva a que suban material antes de poder ver el de los demas."""
    try:
        result = supabase.table("documentos").select("id").eq("subido_por", nombre_usuario).limit(1).execute()
        return bool(result.data)
    except Exception:
        return False


def listar_documentos(materia_general=None, ciclo=None, carrera=None):
    """Lista todos los documentos, opcionalmente filtrados por materia y/o
    ciclo y/o carrera, agrupables luego por curso en la UI."""
    try:
        query = supabase.table("documentos").select("id, materia_general, curso, ciclo, carrera, nombre_archivo, subido_por, fecha_subida, storage_path")
        if materia_general:
            query = query.eq("materia_general", materia_general)
        if ciclo:
            query = query.eq("ciclo", ciclo)
        if carrera:
            query = query.eq("carrera", carrera)
        result = query.order("curso").execute()
        return result.data
    except Exception:
        return []


def listar_ciclos(materia_general=None):
    """Devuelve la lista de ciclos unicos ya usados (ej: '2026-1'), para
    mostrarlos como filtro en la biblioteca."""
    try:
        query = supabase.table("documentos").select("ciclo")
        if materia_general:
            query = query.eq("materia_general", materia_general)
        result = query.execute()
        return sorted(set(d["ciclo"] for d in result.data if d.get("ciclo")))
    except Exception:
        return []


def listar_carreras(materia_general=None):
    """Devuelve la lista de carreras unicas ya usadas (ej: 'Ing. Civil'),
    para mostrarlas como filtro en la biblioteca."""
    try:
        query = supabase.table("documentos").select("carrera")
        if materia_general:
            query = query.eq("materia_general", materia_general)
        result = query.execute()
        return sorted(set(d["carrera"] for d in result.data if d.get("carrera")))
    except Exception:
        return []


def obtener_texto_documento(documento_id):
    """Trae el texto extraido de un documento especifico bajo demanda
    (no se trae en listar_documentos para no cargar todo de una)."""
    try:
        result = supabase.table("documentos").select("contenido_texto").eq("id", documento_id).execute()
        if result.data:
            return result.data[0]["contenido_texto"]
    except Exception:
        pass
    return ""


def obtener_muestra_estilo_curso(materia_general, curso, limite_caracteres=8000):
    """Trae una muestra representativa de los documentos de un curso (por
    ejemplo, examenes pasados), tomando fragmentos de VARIOS documentos
    distintos en vez de solo el primero, para que el Modo Examen pueda
    generar preguntas nuevas con el mismo estilo/dificultad/formato real,
    sin copiar preguntas literales de un solo documento."""
    try:
        result = supabase.table("documento_chunks").select("documento_id, chunk_index, chunk_texto").eq("materia_general", materia_general).eq("curso", curso).order("documento_id").order("chunk_index").execute()
        if not result.data:
            return ""

        por_documento = {}
        for c in result.data:
            por_documento.setdefault(c["documento_id"], []).append(c["chunk_texto"])

        partes = []
        total = 0
        # tomamos 1-2 fragmentos de CADA documento (no todo de uno solo),
        # asi la muestra representa varios examenes/temas distintos
        for doc_id, chunks in por_documento.items():
            for chunk in chunks[:2]:
                if total + len(chunk) > limite_caracteres:
                    break
                partes.append(chunk)
                total += len(chunk)
            if total >= limite_caracteres:
                break

        return "\n\n---\n\n".join(partes)
    except Exception:
        return ""


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


def eliminar_curso(materia_general, curso):
    """Borra TODOS los documentos de un curso especifico de una sola vez
    (util para reemplazar en bloque en vez de borrar documento por documento).
    Tambien intenta borrar sus archivos en Storage; sus fragmentos se borran
    solos por el ON DELETE CASCADE."""
    try:
        docs = supabase.table("documentos").select("storage_path").eq("materia_general", materia_general).eq("curso", curso).execute()
        rutas = [d["storage_path"] for d in docs.data if d.get("storage_path")]
        if rutas:
            try:
                supabase.storage.from_(BUCKET_DOCUMENTOS).remove(rutas)
            except Exception:
                pass
        supabase.table("documentos").delete().eq("materia_general", materia_general).eq("curso", curso).execute()
        return True
    except Exception:
        return False


def eliminar_documentos(ids_documentos):
    """Borra varios documentos especificos de una sola vez (los que el
    alumno selecciono a mano con casillas en la biblioteca, ej: 10 de 20)."""
    if not ids_documentos:
        return False
    try:
        docs = supabase.table("documentos").select("storage_path").in_("id", ids_documentos).execute()
        rutas = [d["storage_path"] for d in docs.data if d.get("storage_path")]
        if rutas:
            try:
                supabase.storage.from_(BUCKET_DOCUMENTOS).remove(rutas)
            except Exception:
                pass
        supabase.table("documentos").delete().in_("id", ids_documentos).execute()
        return True
    except Exception:
        return False


# ===================== CALENDARIO PERSONAL (NUEVO) =====================
# A diferencia de la biblioteca de documentos (compartida), el calendario
# es personal: cada alumno solo ve y administra sus propios eventos.

def guardar_evento(usuario_id, titulo, fecha, tipo="Otro", materia=None, notas=None):
    try:
        supabase.table("eventos_calendario").insert({
            "usuario_id": usuario_id,
            "titulo": titulo.strip(),
            "tipo": tipo,
            "fecha": str(fecha),
            "materia": materia,
            "notas": notas.strip() if notas else None
        }).execute()
        return True
    except Exception:
        return False


def listar_eventos(usuario_id):
    """Devuelve los eventos del alumno ordenados por fecha mas cercana primero."""
    try:
        result = supabase.table("eventos_calendario").select("*").eq("usuario_id", usuario_id).order("fecha").execute()
        return result.data
    except Exception:
        return []


def eliminar_evento(evento_id):
    try:
        supabase.table("eventos_calendario").delete().eq("id", evento_id).execute()
        return True
    except Exception:
        return False


# ===================== MI DIA / TAREAS DIARIAS (NUEVO) =====================
# Lista de tareas de texto libre que cada alumno arma para su propio dia
# (ej: gym, leer, tender la cama). Personal, no se comparte entre alumnos.

def agregar_tarea(usuario_id, texto, fecha=None, puntos=1):
    try:
        supabase.table("tareas_diarias").insert({
            "usuario_id": usuario_id,
            "texto": texto.strip(),
            "fecha": str(fecha) if fecha else str(hoy_peru()),
            "puntos": puntos
        }).execute()
        return True
    except Exception:
        return False


def listar_tareas_dia(usuario_id, fecha=None):
    """Devuelve las tareas del alumno para un dia dado (hoy por defecto)."""
    try:
        f = str(fecha) if fecha else str(hoy_peru())
        result = supabase.table("tareas_diarias").select("*").eq("usuario_id", usuario_id).eq("fecha", f).order("creado_en").execute()
        return result.data
    except Exception:
        return []


def marcar_tarea(tarea_id, completado):
    try:
        supabase.table("tareas_diarias").update({"completado": completado}).eq("id", tarea_id).execute()
        return True
    except Exception:
        return False


def eliminar_tarea(tarea_id):
    try:
        supabase.table("tareas_diarias").delete().eq("id", tarea_id).execute()
        return True
    except Exception:
        return False


def listar_tareas_rango(usuario_id, fecha_inicio, fecha_fin):
    """Devuelve todas las tareas del alumno entre dos fechas (inclusive),
    para armar la tabla semanal y calcular la bateria de cada dia."""
    try:
        result = (
            supabase.table("tareas_diarias")
            .select("*")
            .eq("usuario_id", usuario_id)
            .gte("fecha", str(fecha_inicio))
            .lte("fecha", str(fecha_fin))
            .order("fecha")
            .order("creado_en")
            .execute()
        )
        return result.data
    except Exception:
        return []


# ===================== MI RANGO (TEMPORADA) =====================
# Rango personal que sube durante una temporada academica fija (vacaciones
# -> fin de las 16 semanas de clases), igual para todos los alumnos (no por
# curso individual). Se actualizan estas 3 constantes a mano cada vez que
# empieza una temporada nueva:

FECHA_INICIO_TEMPORADA = date(2026, 8, 17)   # inicio del ciclo 2026-2
FECHA_FIN_TEMPORADA = date(2026, 12, 7)      # fin estimado de las 16 semanas de clases
NUMERO_TEMPORADA = 1                         # sube en 1 cada vez que actualices las fechas de arriba

# 10 tiers, del mas comun al mas raro. Los umbrales son un punto de partida:
# ajustalos cuando veas cuantos puntos gana realmente un alumno constante
# en una temporada completa. El 4to valor es el nombre del archivo de imagen
# en la carpeta rangos_img/ (usado en paginas.py).
RANGOS = [
    (0, "Bronce", "Novato", "rango_01_bronce.png"),
    (40, "Plata", "Estudiante", "rango_02_plata.png"),
    (100, "Oro", "Aprendiz", "rango_03_oro.png"),
    (180, "Diamante", "Avanzado", "rango_04_diamante.png"),
    (280, "Maestro", "Experto", "rango_05_maestro.png"),
    (420, "Élite", "Disciplinado", "rango_06_elite.png"),
    (600, "Gran Maestro", "Estratégico", "rango_07_granmaestro.png"),
    (850, "Leyenda", "Dominante", "rango_08_leyenda.png"),
    (1200, "Inmortal", "Sabio", "rango_09_inmortal.png"),
    (1700, "Dios del Conocimiento", "Supremo", "rango_10_dios.png"),
]

CAIDA_SOFT_RESET = 2  # cuantos tiers baja como maximo al empezar una temporada nueva


def _indice_tier(puntos):
    """Devuelve el indice (0 a 9) del tier que corresponde a esta cantidad
    de puntos."""
    idx = 0
    for i, (umbral, _nombre, _sub, _img) in enumerate(RANGOS):
        if puntos >= umbral:
            idx = i
    return idx


def _indice_por_nombre(nombre_rango):
    for i, (_umbral, nombre, _sub, _img) in enumerate(RANGOS):
        if nombre == nombre_rango:
            return i
    return 0


def calcular_rango(puntos):
    """Nombre del tier segun los puntos (sin considerar soft reset)."""
    return RANGOS[_indice_tier(puntos)][1]


def obtener_insignia_por_puntos(puntos):
    """Devuelve (nombre, imagen) del tier que corresponde a estos puntos,
    para mostrar la insignia en pantallas que no necesitan el resto del
    calculo de temporada (ej: Ranking, que usa puntos de toda la vida)."""
    _umbral, nombre, _sub, imagen = RANGOS[_indice_tier(puntos)]
    return nombre, imagen


def progreso_siguiente_rango(puntos):
    """Devuelve (puntos_que_faltan, nombre_siguiente_tier), o None si ya
    esta en el tier maximo."""
    idx = _indice_tier(puntos)
    if idx >= len(RANGOS) - 1:
        return None
    umbral_siguiente, nombre_siguiente, _sub, _img = RANGOS[idx + 1]
    return umbral_siguiente - puntos, nombre_siguiente


def obtener_puntos_trimestre(usuario_id, fecha_inicio, fecha_fin):
    """Suma los puntos (chat/3 + tareas cumplidas + logros) de un usuario
    dentro de un rango de fechas."""
    try:
        fin_dia_completo = f"{fecha_fin}T23:59:59"

        conv = (
            supabase.table("conversaciones").select("id")
            .eq("usuario_id", usuario_id)
            .gte("fecha", str(fecha_inicio)).lte("fecha", fin_dia_completo)
            .execute()
        )
        puntos_chat = len(conv.data) // 3

        tareas = (
            supabase.table("tareas_diarias").select("puntos")
            .eq("usuario_id", usuario_id).eq("completado", True)
            .gte("fecha", str(fecha_inicio)).lte("fecha", str(fecha_fin))
            .execute()
        )
        puntos_tareas = sum((t.get("puntos") or 1) for t in tareas.data)

        logros_puntos_por_nombre = {l["nombre"]: l.get("puntos", 0) for l in LOGROS_DISPONIBLES}
        logros = (
            supabase.table("logros").select("nombre")
            .eq("usuario_id", usuario_id)
            .gte("fecha", str(fecha_inicio)).lte("fecha", fin_dia_completo)
            .execute()
        )
        puntos_logros = sum(logros_puntos_por_nombre.get(l["nombre"], 0) for l in logros.data)

        return puntos_chat + puntos_tareas + puntos_logros
    except Exception:
        return 0


def obtener_mi_rango(usuario_id):
    """Progreso de la temporada actual (fija, igual para todos: vacaciones
    -> fin de las 16 semanas de clases) mas el historial de temporadas ya
    cerradas. Si la temporada activa (segun FECHA_INICIO/FIN_TEMPORADA)
    todavia no se guardo en el historial y ya paso su fecha de fin, la
    cierra sola en este momento (sin cron). Al empezar una temporada nueva,
    el alumno arranca en su tier anterior menos CAIDA_SOFT_RESET (nunca
    mas abajo que Tier I), no siempre desde cero."""
    hoy = hoy_peru()

    try:
        historial = (
            supabase.table("rangos_historial").select("*")
            .eq("usuario_id", usuario_id)
            .order("anio").order("trimestre")
            .execute().data
        )
    except Exception:
        historial = []

    anio_temporada = FECHA_INICIO_TEMPORADA.year
    ya_guardado_actual = any(h["anio"] == anio_temporada and h["trimestre"] == NUMERO_TEMPORADA for h in historial)

    fin_para_calculo = min(hoy, FECHA_FIN_TEMPORADA)
    puntos_actual = obtener_puntos_trimestre(usuario_id, FECHA_INICIO_TEMPORADA, fin_para_calculo)
    idx_por_puntos = _indice_tier(puntos_actual)

    # temporadas anteriores a la activa (para el soft reset)
    anteriores = [h for h in historial if not (h["anio"] == anio_temporada and h["trimestre"] == NUMERO_TEMPORADA)]
    idx_piso = 0
    if anteriores:
        idx_piso = max(0, _indice_por_nombre(anteriores[-1]["rango"]) - CAIDA_SOFT_RESET)

    idx_final = max(idx_por_puntos, idx_piso)
    _umbral_actual, rango_actual, subtitulo_actual, imagen_actual = RANGOS[idx_final]

    if hoy > FECHA_FIN_TEMPORADA and not ya_guardado_actual:
        try:
            supabase.table("rangos_historial").insert({
                "usuario_id": usuario_id,
                "anio": anio_temporada,
                "trimestre": NUMERO_TEMPORADA,
                "puntos_totales": puntos_actual,
                "rango": rango_actual
            }).execute()
            historial.append({"anio": anio_temporada, "trimestre": NUMERO_TEMPORADA, "puntos_totales": puntos_actual, "rango": rango_actual})
        except Exception:
            pass

    siguiente = progreso_siguiente_rango(puntos_actual)

    return {
        "anio": anio_temporada,
        "trimestre": NUMERO_TEMPORADA,
        "temporada_inicio": FECHA_INICIO_TEMPORADA,
        "temporada_fin": FECHA_FIN_TEMPORADA,
        "puntos": puntos_actual,
        "rango": rango_actual,
        "subtitulo": subtitulo_actual,
        "imagen": imagen_actual,
        "indice_tier": idx_final,
        "siguiente_faltan": siguiente[0] if siguiente else None,
        "siguiente_nombre": siguiente[1] if siguiente else None,
        "historial": historial
    }


# ===================== PLAN DE ESTUDIO =====================

def guardar_plan_estudio(usuario_id, materia_general, curso, fecha_inicio_ciclo, estructura):
    """Guarda (o reemplaza, si ya existia uno para este curso) el plan de
    estudio de un alumno: la fecha de inicio de ciclo que dio, y la
    estructura ya extraida del silabo/ficha (para no volver a llamar a la
    IA cada vez que se muestra el plan)."""
    try:
        existente = supabase.table("planes_estudio").select("id").eq("usuario_id", usuario_id).eq("materia_general", materia_general).eq("curso", curso).execute()
        datos = {
            "usuario_id": usuario_id,
            "materia_general": materia_general,
            "curso": curso,
            "fecha_inicio_ciclo": str(fecha_inicio_ciclo),
            "estructura_json": estructura,
            "actualizado_en": ahora_peru().isoformat()
        }
        if existente.data:
            supabase.table("planes_estudio").update(datos).eq("id", existente.data[0]["id"]).execute()
        else:
            supabase.table("planes_estudio").insert(datos).execute()
        return True
    except Exception:
        return False


def obtener_plan_estudio(usuario_id, materia_general, curso):
    """Trae el plan de estudio ya guardado de este alumno para este curso,
    o None si todavia no genero uno."""
    try:
        result = supabase.table("planes_estudio").select("*").eq("usuario_id", usuario_id).eq("materia_general", materia_general).eq("curso", curso).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def guardar_preferencia_calendario(usuario_id, fondo, intensidad):
    """Guarda la preferencia de tema visual (fondo) e intensidad del color
    del Calendario, para que quede igual la proxima vez que el alumno entre."""
    try:
        supabase.table("usuarios").update({
            "pref_calendario_fondo": fondo,
            "pref_calendario_intensidad": intensidad
        }).eq("id", usuario_id).execute()
        return True
    except Exception:
        return False


# ===================== HORARIO DE CLASES =====================

def guardar_clase_horario(usuario_id, dia_semana, hora_inicio, hora_fin, etiqueta=None):
    """Agrega un bloque de clase al horario semanal del alumno.
    dia_semana: 0=Lunes ... 6=Domingo."""
    try:
        supabase.table("horario_clases").insert({
            "usuario_id": usuario_id,
            "dia_semana": dia_semana,
            "hora_inicio": str(hora_inicio),
            "hora_fin": str(hora_fin),
            "etiqueta": etiqueta
        }).execute()
        return True
    except Exception:
        return False


def editar_clase_horario(clase_id, dia_semana, hora_inicio, hora_fin, etiqueta=None):
    """Edita un bloque de clase existente (en vez de borrar y volver a
    crear). dia_semana: 0=Lunes ... 6=Domingo."""
    try:
        supabase.table("horario_clases").update({
            "dia_semana": dia_semana,
            "hora_inicio": str(hora_inicio),
            "hora_fin": str(hora_fin),
            "etiqueta": etiqueta
        }).eq("id", clase_id).execute()
        return True
    except Exception:
        return False


def listar_horario_clases(usuario_id):
    """Trae todos los bloques de clase del alumno, ordenados por dia y hora."""
    try:
        result = supabase.table("horario_clases").select("*").eq("usuario_id", usuario_id).order("dia_semana").order("hora_inicio").execute()
        return result.data
    except Exception:
        return []


def eliminar_clase_horario(clase_id):
    try:
        supabase.table("horario_clases").delete().eq("id", clase_id).execute()
        return True
    except Exception:
        return False


# ===================== BLOQUES DE ESTUDIO (persistidos) =====================

def guardar_bloques_estudio(usuario_id, materia_general, curso, bloques):
    """Guarda en bloque una lista de bloques de estudio ya calculados, para
    no tener que recalcularlos cada vez que se muestran. Cada bloque es un
    dict con: fecha, hora_inicio, hora_fin (str 'HH:MM'), tipo
    ('estudio'/'descanso_corto'/'descanso_largo'), tema, evaluacion."""
    if not bloques:
        return True
    try:
        filas = [{
            "usuario_id": usuario_id,
            "materia_general": materia_general,
            "curso": curso,
            "fecha": str(b["fecha"]),
            "hora_inicio": b["hora_inicio"],
            "hora_fin": b["hora_fin"],
            "tipo": b["tipo"],
            "tema": b.get("tema"),
            "evaluacion": b.get("evaluacion"),
        } for b in bloques]
        supabase.table("bloques_estudio").insert(filas).execute()
        return True
    except Exception:
        return False


def eliminar_bloques_estudio_futuros(usuario_id, materia_general, curso, desde_fecha):
    """Borra los bloques guardados de este curso desde 'desde_fecha' en
    adelante (nunca toca los dias que ya pasaron), antes de regenerarlos."""
    try:
        supabase.table("bloques_estudio").delete() \
            .eq("usuario_id", usuario_id).eq("materia_general", materia_general).eq("curso", curso) \
            .gte("fecha", str(desde_fecha)).execute()
        return True
    except Exception:
        return False


def eliminar_bloques_estudio_futuros_todos_los_cursos(usuario_id, desde_fecha):
    """Igual que arriba pero para TODOS los cursos del alumno. Se usa cuando
    cambia el horario de clases, porque un cambio ahi puede afectar los
    huecos libres de cualquier curso, no solo uno."""
    try:
        supabase.table("bloques_estudio").delete() \
            .eq("usuario_id", usuario_id).gte("fecha", str(desde_fecha)).execute()
        return True
    except Exception:
        return False


def listar_bloques_estudio(usuario_id, fecha_desde=None, fecha_hasta=None, materia_general=None, curso=None):
    """Trae los bloques de estudio ya guardados de un alumno, con filtros
    opcionales de rango de fecha y/o curso. Vacio si todavia no genero
    ninguno (en ese caso, la pantalla debe caer al calculo en vivo)."""
    try:
        query = supabase.table("bloques_estudio").select("*").eq("usuario_id", usuario_id)
        if fecha_desde:
            query = query.gte("fecha", str(fecha_desde))
        if fecha_hasta:
            query = query.lte("fecha", str(fecha_hasta))
        if materia_general:
            query = query.eq("materia_general", materia_general)
        if curso:
            query = query.eq("curso", curso)
        result = query.order("fecha").order("hora_inicio").execute()
        return result.data
    except Exception:
        return []


def eliminar_bloques_estudio_de_otros_cursos(usuario_id, curso_a_mantener, fecha_desde, fecha_hasta):
    """Borra los bloques de estudio de todos los cursos del alumno EXCEPTO
    'curso_a_mantener', dentro del rango de fechas dado. Se usa cuando el
    alumno decide priorizar un curso sobre los que ya tenian ese hueco
    reservado (boton 'reemplazar')."""
    try:
        supabase.table("bloques_estudio").delete() \
            .eq("usuario_id", usuario_id).neq("curso", curso_a_mantener) \
            .gte("fecha", str(fecha_desde)).lte("fecha", str(fecha_hasta)).execute()
        return True
    except Exception:
        return False


def listar_planes_estudio(usuario_id):
    """Trae todos los planes de estudio guardados de un alumno (uno por
    curso), para poder regenerarlos en cascada si cambia el horario de
    clases."""
    try:
        result = supabase.table("planes_estudio").select("*").eq("usuario_id", usuario_id).execute()
        return result.data
    except Exception:
        return []
