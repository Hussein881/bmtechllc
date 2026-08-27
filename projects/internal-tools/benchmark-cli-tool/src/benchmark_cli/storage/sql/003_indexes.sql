CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS document_chunks_search_vector_gin
    ON document_chunks USING gin (search_vector);

CREATE INDEX IF NOT EXISTS document_chunks_source_idx
    ON document_chunks (source_file, chunk_index);
