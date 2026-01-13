"""Atlas AI Module - Embeddings and AI Agent Access."""

from app.ai.embeddings import (
    EmbeddingService,
    get_embedding_service,
    embed_and_store,
    semantic_search,
)

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "embed_and_store",
    "semantic_search",
]
