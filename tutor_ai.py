# Tu Profe de Confianza

Tutor educativo con IA para estudiantes peruanos (colegio, instituto y universidad),
enfocado en Matematicas e Ingles, con gamificacion (rachas, logros, ranking) y
un tutor que se **personaliza** segun la edad/grado/ciclo del alumno y su
progreso real en cada materia.

## Estructura del proyecto

```
tuprofedeconfianza/
├── app.py            # Punto de entrada: login/registro, sidebar, enrutamiento
├── database.py        # Todo lo que habla con Supabase (usuarios, conversaciones,
│                       #   asistencia, logros, ranking, perfil del alumno)
├── tutor_ai.py         # Prompts del tutor + personalizacion + actualizacion
│                       #   automatica del perfil del alumno tras cada respuesta
├── chat.py             # Pagina de Chat
├── examen.py           # Pagina de Modo Examen (genera, recibe y califica)
├── paginas.py          # Ranking, Mis Logros, Mis Estadisticas, Acerca de
├── logros_data.py       # Catalogo de logros disponibles
├── estilos.py           # CSS de la app
├── utils.py             # hash de contrasena, lectura de PDF, nivel del alumno
├── migracion.sql        # SQL para actualizar la base de datos en Supabase
├── requirements.txt
└── imagen*.png / icono*.png
```

## Configuracion (Supabase / Streamlit secrets)

En `.streamlit/secrets.toml` (o en la configuracion de secrets de Streamlit Cloud):

```toml
GROQ_API_KEY = "..."
SUPABASE_URL = "..."
SUPABASE_SERVICE_KEY = "..."
```

## Antes de correr la app por primera vez con estos cambios

Ejecuta `migracion.sql` en el SQL Editor de Supabase. Agrega las columnas
`edad`, `grado`, `ciclo` a `usuarios` y crea la tabla `perfil_alumno`
(necesaria para que el tutor "recuerde" el progreso de cada alumno).

## Que hace el sistema de personalizacion

1. Al registrarse, el alumno indica su **edad**, **nivel educativo** y
   **grado/ciclo**. Esto se inyecta en el prompt del tutor para adaptar el
   vocabulario y la complejidad de los ejemplos.
2. Despues de cada respuesta del tutor, un modelo pequeno (barato) analiza
   el intercambio y actualiza el **perfil de progreso** del alumno: temas
   que domina, temas donde tiene dificultad, y su nivel estimado.
3. En la siguiente pregunta, ese perfil se vuelve a inyectar al prompt, asi
   el tutor evita repetir explicaciones basicas de temas ya dominados y
   refuerza los temas dificiles.

Si algo falla en este proceso (limite de uso de la API, respuesta invalida,
etc.) el chat sigue funcionando normal - simplemente el perfil no se
actualiza en ese turno.
