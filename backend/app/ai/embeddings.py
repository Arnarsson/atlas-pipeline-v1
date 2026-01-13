"""
Atlas AI Embeddings Module

Vector embeddings for semantic search and AI agent access.
Supports OpenAI, local models (sentence-transformers), or pgvector.

Author: Atlas Pipeline Team
Date: January 2026
"""

import hashlib
import json
import os
from typing import Any, Optional
from uuid import UUID

from loguru import logger

# Embedding configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")  # "openai", "local", "none"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = 1536  # OpenAI default

# Try to import embedding libraries
_sentence_transformers_available = False
_openai_available = False

try:
    from sentence_transformers import SentenceTransformer
    _sentence_transformers_available = True
    logger.info("✅ sentence-transformers available for local embeddings")
except ImportError:
    logger.warning("⚠️ sentence-transformers not installed - local embeddings disabled")

try:
    import openai
    _openai_available = True
    logger.info("✅ OpenAI library available")
except ImportError:
    logger.warning("⚠️ OpenAI library not installed")


class EmbeddingService:
    """
    Generate embeddings for data records.

    Supports:
    - OpenAI embeddings (text-embedding-3-small/large)
    - Local embeddings (sentence-transformers)
    - No embeddings (fallback)
    """

    def __init__(self, provider: str = EMBEDDING_PROVIDER):
        self.provider = provider
        self._model = None
        self._openai_client = None

        if provider == "openai" and OPENAI_API_KEY and _openai_available:
            self._openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logger.info(f"Using OpenAI embeddings ({EMBEDDING_MODEL})")
        elif provider == "local" and _sentence_transformers_available:
            # Use a small, fast model for local embeddings
            model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self._model = SentenceTransformer(model_name)
            logger.info(f"Using local embeddings ({model_name})")
        else:
            logger.warning("No embedding provider available - embeddings disabled")
            self.provider = "none"

    def embed_text(self, text: str) -> Optional[list[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if unavailable
        """
        if not text or self.provider == "none":
            return None

        try:
            if self.provider == "openai" and self._openai_client:
                response = self._openai_client.embeddings.create(
                    input=text,
                    model=EMBEDDING_MODEL
                )
                return response.data[0].embedding

            elif self.provider == "local" and self._model:
                embedding = self._model.encode(text)
                return embedding.tolist()

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None

        return None

    def embed_record(self, record: dict[str, Any]) -> Optional[list[float]]:
        """
        Generate embedding for a data record.

        Converts record to text representation and embeds it.

        Args:
            record: Dictionary record

        Returns:
            Embedding vector or None
        """
        # Convert record to searchable text
        text_parts = []
        for key, value in record.items():
            if value is not None:
                text_parts.append(f"{key}: {value}")

        text = " | ".join(text_parts)
        return self.embed_text(text)

    def embed_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.provider == "none":
            return [None] * len(texts)

        try:
            if self.provider == "openai" and self._openai_client:
                response = self._openai_client.embeddings.create(
                    input=texts,
                    model=EMBEDDING_MODEL
                )
                return [item.embedding for item in response.data]

            elif self.provider == "local" and self._model:
                embeddings = self._model.encode(texts)
                return [emb.tolist() for emb in embeddings]

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [None] * len(texts)

        return [None] * len(texts)


async def embed_and_store(
    db,  # AtlasDatabase instance
    run_id: str,
    source_id: str,
    dataset_name: str,
    records: list[dict[str, Any]],
    embedding_service: Optional[EmbeddingService] = None
) -> int:
    """
    Embed records and store in vector table.

    Args:
        db: Database instance
        run_id: Pipeline run ID
        source_id: Source identifier
        dataset_name: Dataset name
        records: Records to embed
        embedding_service: Embedding service instance

    Returns:
        Number of embeddings stored
    """
    if not embedding_service or embedding_service.provider == "none":
        logger.info("Embeddings disabled - skipping vector storage")
        return 0

    count = 0

    async with db.connection() as conn:
        for i, record in enumerate(records):
            try:
                # Convert record to text for embedding
                text_parts = []
                for key, value in record.items():
                    if value is not None:
                        text_parts.append(f"{key}: {value}")
                content = " | ".join(text_parts)

                # Generate embedding
                embedding = embedding_service.embed_text(content)

                if embedding:
                    # Store in vector table
                    await conn.execute("""
                        INSERT INTO vectors.embeddings
                        (run_id, source_id, dataset_name, record_id, content, embedding, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, UUID(run_id), source_id, dataset_name, i,
                        content, embedding, json.dumps({"record_index": i}))
                    count += 1

            except Exception as e:
                logger.error(f"Failed to embed record {i}: {e}")
                continue

    logger.info(f"✅ Stored {count} embeddings in vectors.embeddings")
    return count


async def semantic_search(
    db,  # AtlasDatabase instance
    query: str,
    dataset_name: Optional[str] = None,
    limit: int = 10,
    embedding_service: Optional[EmbeddingService] = None
) -> list[dict[str, Any]]:
    """
    Search data using semantic similarity.

    Args:
        db: Database instance
        query: Search query text
        dataset_name: Optional dataset filter
        limit: Max results
        embedding_service: Embedding service

    Returns:
        List of matching records with similarity scores
    """
    if not embedding_service or embedding_service.provider == "none":
        logger.warning("Embeddings disabled - cannot perform semantic search")
        return []

    # Embed query
    query_embedding = embedding_service.embed_text(query)
    if not query_embedding:
        return []

    async with db.connection() as conn:
        try:
            # Use pgvector cosine distance for similarity
            if dataset_name:
                rows = await conn.fetch("""
                    SELECT
                        content,
                        metadata,
                        run_id,
                        dataset_name,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM vectors.embeddings
                    WHERE dataset_name = $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                """, query_embedding, dataset_name, limit)
            else:
                rows = await conn.fetch("""
                    SELECT
                        content,
                        metadata,
                        run_id,
                        dataset_name,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM vectors.embeddings
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                """, query_embedding, limit)

            return [
                {
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "run_id": str(row["run_id"]),
                    "dataset_name": row["dataset_name"],
                    "similarity": float(row["similarity"])
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []


# Singleton embedding service
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
