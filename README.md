# Tu Profe de Confianza

Tutor educativo con IA para estudiantes peruanos (colegio, instituto y
universidad), con 5 materias (Matematicas, Ingles, Fisica, Quimica General,
Quimica Organica), filtradas segun la carrera del alumno. El tutor se
**personaliza** con la edad/grado/ciclo/carrera y con el progreso real de
cada alumno en cada materia.

## Funciones principales

- **Chat** - tutor de IA por materia, con memoria de progreso y opcion de
  conectar la conversacion a un curso de la biblioteca (usa tus documentos
  reales como contexto).
- **Modo Examen** - genera examenes de practica; puede basarse en el estilo
  real de examenes pasados subidos a la biblioteca.
- **Revisa mi Solucion** - el alumno escribe o sube una foto de su
  procedimiento, y el tutor encuentra el primer error paso a paso, sin dar
  la respuesta directa.
- **Formulario** - genera tarjetas cortas de formulas por curso, priorizando
  los temas donde el alumno tiene mas dificultad.
- **Documentos** - biblioteca compartida de PDFs (organizada por materia,
  curso y ciclo), con busqueda por relevancia para no mandarle al tutor mas
  contenido del necesario en cada pregunta.
- **Calendario** - fechas personales de examenes y entregas, con colores de
  urgencia.
- **Mis Estadisticas / Mis Logros / Ranking** - gamificacion basica.

## Estructura del proyecto

```
tuprofedeconfianza/
├── app.py             # Punto de entrada: login/registro, sidebar, enrutamiento
├── database.py         # Todo lo que habla con Supabase (usuarios, conversaciones,
│                        #   documentos, calendario, ranking, perfil del alumno, etc.)
├── tutor_ai.py          # Prompts del tutor, personalizacion, generacion de
│                        #   formulario, revision de soluciones, transcripcion de fotos
├── materias_data.py      # Catalogo de materias y que materias ve cada carrera
├── chat.py               # Pagina de Chat
├── examen.py              # Modo Examen (genera, recibe y califica)
├── documentos.py           # Biblioteca de documentos (subir/explorar)
├── formulario.py            # Generador de tarjetas de formulas
├── calendario.py             # Calendario personal de fechas
├── revision.py                # Revisa mi Solucion (texto o foto)
├── paginas.py                  # Ranking, Mis Logros, Mis Estadisticas, Acerca de
├── logros_data.py                # Catalogo de logros disponibles
├── estilos.py                     # CSS de la app
├── utils.py                        # hash de contrasena, lectura de PDF, LaTeX, fragmentos
├── requirements.txt
└── imagen*.png / icono*.png
```

## Configuracion (Supabase / Streamlit secrets)

En Streamlit Cloud, en la configuracion de "Secrets" de la app:

```toml
GROQ_API_KEY = "..."
SUPABASE_URL = "..."
SUPABASE_SERVICE_KEY = "..."
```

## Esquema de base de datos (Supabase)

Estas son las tablas que la app necesita. Si algo falla "sin razon aparente",
lo primero es comparar esta lista contra el Table Editor de Supabase.

```
usuarios: id, nombre, email, password, fecha_registro, edad, grado, ciclo,
          carrera, racha, ultima_visita, es_admin
conversaciones: usuario_id, mensaje, respuesta, materia, fecha
asistencia: usuario_id, fecha, racha, hora
logros: usuario_id, nombre, descripcion, emoji, fecha
perfil_alumno: usuario_id, materia, temas_dominados, temas_dificiles,
               nivel_estimado, ultimo_resumen, actualizado_en
documentos: materia_general, curso, ciclo, nombre_archivo, contenido_texto,
            subido_por, fecha_subida, storage_path
documento_chunks: documento_id, materia_general, curso, chunk_index, chunk_texto
examenes: usuario_id, materia, pregunta, opciones, respuesta_correcta,
          respuesta_usuario, correcta, fecha
eventos_calendario: id, usuario_id, materia, titulo, tipo, fecha, notas, creado_en
```

Tambien se necesita un bucket de Storage llamado `documentos-pdf` (publico),
para guardar los PDFs originales que se pueden descargar desde la biblioteca.

## Modelos de IA (Groq)

Definidos en `tutor_ai.py`:

- `MODELO_TUTOR = "openai/gpt-oss-120b"` - respuestas del tutor, examenes, revision de soluciones
- `MODELO_RESUMEN = "openai/gpt-oss-20b"` - actualizacion del perfil de progreso (mas barato)
- `MODELO_VISION = "qwen/qwen3.6-27b"` - lectura de fotos en "Revisa mi Solucion"

Si Groq anuncia otra descontinuacion de modelos, estas 3 lineas son las
unicas que hay que actualizar.

## Como funciona la personalizacion

1. Al registrarse, el alumno indica edad, nivel educativo, grado/ciclo y
   carrera. La carrera filtra que materias ve en el Chat.
2. Despues de cada respuesta, un modelo pequeno analiza el intercambio y
   actualiza el perfil de progreso del alumno (temas dominados/dificiles,
   nivel estimado). Ese perfil se vuelve a inyectar en cada pregunta nueva.
3. Si el alumno conecta el Chat a un curso de la biblioteca, se busca el
   fragmento mas relevante a esa pregunta especifica (no se manda todo el
   documento), usando similitud de texto (TF-IDF).

## Limitaciones conocidas

- Las opciones de opcion multiple en Modo Examen (`st.radio`) no pueden
  mostrar formulas en LaTeX renderizado - es una limitacion de ese
  componente de Streamlit, no un bug del codigo.
- Si un usuario cambia manualmente el tema a "Light" desde el menu de
  Streamlit (arriba a la derecha), algunos campos pueden perder contraste.
  Es un caso raro (la mayoria de usuarios no toca ese menu) y se decidio
  no arreglarlo por el riesgo de romper el tema oscuro por defecto.
