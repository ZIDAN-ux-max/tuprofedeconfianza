-- ============================================================
-- Migracion 4 para "Tu Profe de Confianza"
-- Tabla de fragmentos: cada documento se parte en pedazos pequenos al
-- subirlo. Cuando el alumno pregunta algo, el sistema busca solo los
-- fragmentos mas relevantes a esa pregunta (no todo el documento entero).
-- Necesario para que la biblioteca escale a varios PDFs de varias paginas
-- cada uno sin disparar el tamano/costo de cada pregunta.
-- Ejecutar en Supabase: Panel -> SQL Editor -> New query -> pegar y correr
-- ============================================================

CREATE TABLE IF NOT EXISTS documento_chunks (
    id BIGSERIAL PRIMARY KEY,
    documento_id BIGINT NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    materia_general TEXT NOT NULL,
    curso TEXT NOT NULL,
    chunk_index INT NOT NULL,
    chunk_texto TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_materia_curso
    ON documento_chunks (materia_general, curso);
