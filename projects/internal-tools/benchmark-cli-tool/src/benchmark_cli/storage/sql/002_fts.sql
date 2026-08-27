-- Upgrade databases created before search_vector was a stored generated column.
ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED;

DROP INDEX IF EXISTS document_chunks_text_fts;
DROP INDEX IF EXISTS document_chunks_metadata_gin;
