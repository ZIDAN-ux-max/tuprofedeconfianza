-- ============================================================
-- Migracion para "Tu Profe de Confianza"
-- Ejecutar esto en Supabase: Panel -> SQL Editor -> New query -> pegar y correr
-- ============================================================

-- 1) Nuevos campos en la tabla de usuarios: edad, grado, ciclo
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS edad INTEGER;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS grado TEXT;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ciclo TEXT;

-- 2) Tabla nueva: perfil_alumno
-- Guarda, por alumno y materia, que temas domina, cuales le cuestan,
-- su nivel estimado y un resumen de la ultima sesion. Esto es lo que le
-- da "memoria" al tutor para personalizar sus respuestas.
CREATE TABLE IF NOT EXISTS perfil_alumno (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    materia TEXT NOT NULL,
    temas_dominados JSONB DEFAULT '[]'::jsonb,
    temas_dificiles JSONB DEFAULT '[]'::jsonb,
    nivel_estimado TEXT DEFAULT 'sin_evaluar',
    ultimo_resumen TEXT DEFAULT '',
    actualizado_en TIMESTAMPTZ DEFAULT now(),
    UNIQUE (usuario_id, materia)
);

-- Indice para buscar rapido el perfil de un alumno en una materia
CREATE INDEX IF NOT EXISTS idx_perfil_alumno_usuario_materia
    ON perfil_alumno (usuario_id, materia);
