CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS document_chunks_metadata_gin
    ON document_chunks USING gin (metadata jsonb_path_ops);

CREATE INDEX IF NOT EXISTS document_chunks_source_idx
    ON document_chunks (source_file, chunk_index);

CREATE INDEX IF NOT EXISTS document_chunks_text_fts
    ON document_chunks USING gin (to_tsvector('english', chunk_text));
