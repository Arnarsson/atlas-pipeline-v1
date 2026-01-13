-- Enable pgvector extension for AI/RAG vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is enabled
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
