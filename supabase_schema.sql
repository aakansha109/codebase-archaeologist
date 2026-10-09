-- Enable pgvector extension in Supabase
CREATE EXTENSION IF NOT EXISTS vector;

-- Code Chunks & AST Metadata Table
CREATE TABLE IF NOT EXISTS code_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    language TEXT NOT NULL,
    chunk_type TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    start_line INT NOT NULL,
    end_line INT NOT NULL,
    docstring TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    lineage JSONB DEFAULT '[]'::jsonb,
    embedding vector(768), -- Matches Google Gemini text-embedding-004
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for HNSW Vector Cosine Similarity Search
CREATE INDEX IF NOT EXISTS code_chunks_embedding_idx 
ON code_chunks USING hnsw (embedding vector_cosine_ops);

-- Similarity Matching Function (RPC endpoint)
CREATE OR REPLACE FUNCTION match_code_chunks(
    query_embedding vector(768),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    chunk_id TEXT,
    file_path TEXT,
    language TEXT,
    chunk_type TEXT,
    name TEXT,
    content TEXT,
    start_line INT,
    end_line INT,
    docstring TEXT,
    metadata JSONB,
    lineage JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.chunk_id,
        c.file_path,
        c.language,
        c.chunk_type,
        c.name,
        c.content,
        c.start_line,
        c.end_line,
        c.docstring,
        c.metadata,
        c.lineage,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM code_chunks c
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
