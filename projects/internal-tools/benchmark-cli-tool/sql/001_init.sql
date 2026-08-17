CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id              BIGSERIAL     PRIMARY KEY,
    source_file     TEXT          NOT NULL,
    chunk_index     INTEGER       NOT NULL,
    chunk_text      TEXT          NOT NULL,
    content_sha256  CHAR(64)      NOT NULL,
    token_count     INTEGER       NOT NULL,
    embedding       vector(1536)  NOT NULL,
    metadata        JSONB         NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT document_chunks_source_chunk_uniq UNIQUE (source_file, chunk_index),
    CONSTRAINT document_chunks_hash_uniq         UNIQUE (content_sha256),
    CONSTRAINT document_chunks_text_nonempty     CHECK (length(btrim(chunk_text)) > 0),
    CONSTRAINT document_chunks_tokens_sane       CHECK (token_count BETWEEN 1 AND 2000)
);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS document_chunks_touch ON document_chunks;
CREATE TRIGGER document_chunks_touch
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
