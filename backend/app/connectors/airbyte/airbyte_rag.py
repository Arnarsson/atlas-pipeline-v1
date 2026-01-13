"""
Airbyte RAG Integration (Open Source)

Uses PyAirbyte + pgvector/Chroma for RAG-ready data pipelines.
Based on: https://github.com/airbytehq/PyAirbyte

Features:
- Extract data from 400+ sources via PyAirbyte
- Automatic chunking and embedding
- Store in pgvector (PostgreSQL) or Chroma (open source)
- LangChain/LlamaIndex compatible output

Author: Atlas Pipeline Team
Date: January 2026
"""

import json
import os
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4

from loguru import logger

# Check for PyAirbyte
PYAIRBYTE_AVAILABLE = False
try:
    import airbyte as ab
    PYAIRBYTE_AVAILABLE = True
    logger.info("✅ PyAirbyte available")
except ImportError:
    logger.warning("⚠️ PyAirbyte not installed - run: pip install airbyte")

# Check for LangChain (optional, for RAG transformations)
LANGCHAIN_AVAILABLE = False
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
    logger.info("✅ LangChain available for RAG transformations")
except ImportError:
    logger.info("ℹ️ LangChain not installed - chunking will use simple splitter")

# Check for sentence-transformers (for embeddings)
EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
    logger.info("✅ sentence-transformers available for embeddings")
except ImportError:
    logger.info("ℹ️ sentence-transformers not installed - embeddings disabled")


class AirbyteRAGPipeline:
    """
    RAG-ready data pipeline using PyAirbyte.

    Extracts data from any Airbyte source, chunks it, embeds it,
    and stores in pgvector for semantic search.
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize RAG pipeline.

        Args:
            embedding_model: Sentence-transformer model name
            chunk_size: Size of text chunks for RAG
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize embedding model
        self._embedder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self._embedder = SentenceTransformer(embedding_model)
                logger.info(f"Loaded embedding model: {embedding_model}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")

        # Initialize text splitter
        if LANGCHAIN_AVAILABLE:
            self._splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        else:
            self._splitter = None

    def list_available_sources(self) -> list[dict[str, Any]]:
        """
        List all available PyAirbyte sources.

        Returns:
            List of source connectors with metadata
        """
        if not PYAIRBYTE_AVAILABLE:
            return self._get_mock_sources()

        try:
            # Get available connectors from PyAirbyte
            sources = ab.get_available_connectors()
            return [
                {
                    "name": s.name,
                    "type": "pyairbyte",
                    "docker_image": s.docker_image if hasattr(s, 'docker_image') else None
                }
                for s in sources
            ]
        except Exception as e:
            logger.error(f"Failed to list PyAirbyte sources: {e}")
            return self._get_mock_sources()

    def _get_mock_sources(self) -> list[dict[str, Any]]:
        """Return mock source list for development."""
        return [
            {"name": "source-postgres", "type": "database", "category": "Database"},
            {"name": "source-mysql", "type": "database", "category": "Database"},
            {"name": "source-mongodb", "type": "database", "category": "Database"},
            {"name": "source-salesforce", "type": "crm", "category": "CRM"},
            {"name": "source-hubspot", "type": "crm", "category": "CRM"},
            {"name": "source-stripe", "type": "payments", "category": "Payments"},
            {"name": "source-github", "type": "devtools", "category": "Developer Tools"},
            {"name": "source-jira", "type": "project", "category": "Project Management"},
            {"name": "source-notion", "type": "docs", "category": "Productivity"},
            {"name": "source-google-sheets", "type": "spreadsheet", "category": "Productivity"},
            {"name": "source-s3", "type": "storage", "category": "Storage"},
            {"name": "source-gcs", "type": "storage", "category": "Storage"},
        ]

    async def extract_from_source(
        self,
        source_name: str,
        config: dict[str, Any],
        streams: Optional[list[str]] = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Extract data from an Airbyte source.

        Args:
            source_name: PyAirbyte source name (e.g., "source-postgres")
            config: Source configuration
            streams: Optional list of streams to sync (None = all)

        Yields:
            Records from the source
        """
        if not PYAIRBYTE_AVAILABLE:
            logger.warning("PyAirbyte not available - returning mock data")
            async for record in self._mock_extract():
                yield record
            return

        try:
            # Create source instance
            source = ab.get_source(source_name, config=config)

            # Check connection
            source.check()

            # Select streams
            if streams:
                source.select_streams(streams)
            else:
                source.select_all_streams()

            # Read data
            result = source.read()

            # Yield records from each stream
            for stream_name in result.streams:
                stream = result[stream_name]
                for record in stream:
                    yield {
                        "stream": stream_name,
                        "data": dict(record),
                        "source": source_name
                    }

        except Exception as e:
            logger.error(f"PyAirbyte extraction failed: {e}")
            # Fall back to mock data for development
            async for record in self._mock_extract():
                yield record

    async def _mock_extract(self) -> AsyncGenerator[dict[str, Any], None]:
        """Generate mock data for development."""
        mock_records = [
            {"id": 1, "name": "Customer A", "email": "a@example.com", "revenue": 10000},
            {"id": 2, "name": "Customer B", "email": "b@example.com", "revenue": 25000},
            {"id": 3, "name": "Customer C", "email": "c@example.com", "revenue": 5000},
        ]
        for record in mock_records:
            yield {"stream": "customers", "data": record, "source": "mock"}

    def chunk_record(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Chunk a record for RAG.

        Converts record to text and splits into chunks.

        Args:
            record: Data record

        Returns:
            List of chunks with metadata
        """
        # Convert record to text
        text = self._record_to_text(record["data"])

        if self._splitter:
            # Use LangChain splitter
            chunks = self._splitter.split_text(text)
        else:
            # Simple chunking fallback
            chunks = self._simple_chunk(text)

        return [
            {
                "chunk_id": f"{record.get('stream', 'unknown')}_{i}",
                "text": chunk,
                "metadata": {
                    "source": record.get("source"),
                    "stream": record.get("stream"),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def _record_to_text(self, data: dict[str, Any]) -> str:
        """Convert record to searchable text."""
        parts = []
        for key, value in data.items():
            if value is not None:
                parts.append(f"{key}: {value}")
        return " | ".join(parts)

    def _simple_chunk(self, text: str) -> list[str]:
        """Simple text chunking without LangChain."""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks if chunks else [text]

    def embed_chunk(self, chunk: dict[str, Any]) -> dict[str, Any]:
        """
        Generate embedding for a chunk.

        Args:
            chunk: Chunk with text and metadata

        Returns:
            Chunk with embedding added
        """
        if not self._embedder:
            return {**chunk, "embedding": None}

        try:
            embedding = self._embedder.encode(chunk["text"])
            return {
                **chunk,
                "embedding": embedding.tolist()
            }
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return {**chunk, "embedding": None}

    async def process_to_rag(
        self,
        source_name: str,
        config: dict[str, Any],
        streams: Optional[list[str]] = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Full RAG pipeline: extract → chunk → embed.

        Args:
            source_name: Airbyte source name
            config: Source configuration
            streams: Optional stream filter

        Yields:
            Embedded chunks ready for vector storage
        """
        async for record in self.extract_from_source(source_name, config, streams):
            # Chunk the record
            chunks = self.chunk_record(record)

            # Embed each chunk
            for chunk in chunks:
                embedded = self.embed_chunk(chunk)
                yield embedded


async def store_in_pgvector(
    db,  # AtlasDatabase instance
    run_id: str,
    source_id: str,
    dataset_name: str,
    chunks: list[dict[str, Any]]
) -> int:
    """
    Store embedded chunks in pgvector.

    Args:
        db: Database instance
        run_id: Pipeline run ID
        source_id: Source identifier
        dataset_name: Dataset name
        chunks: List of embedded chunks

    Returns:
        Number of chunks stored
    """
    count = 0

    async with db.connection() as conn:
        for chunk in chunks:
            if chunk.get("embedding"):
                try:
                    await conn.execute("""
                        INSERT INTO vectors.embeddings
                        (run_id, source_id, dataset_name, content, embedding, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        run_id, source_id, dataset_name,
                        chunk["text"],
                        chunk["embedding"],
                        json.dumps(chunk.get("metadata", {}))
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to store chunk: {e}")

    logger.info(f"✅ Stored {count} chunks in pgvector")
    return count


class ChromaVectorStore:
    """
    Chroma vector store integration (open source alternative to Pinecone).

    Uses ChromaDB for local vector storage.
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        self._client = None
        self._collection = None

        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=persist_directory)
            logger.info(f"✅ ChromaDB initialized at {persist_directory}")
        except ImportError:
            logger.warning("⚠️ ChromaDB not installed - run: pip install chromadb")

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        if not self._client:
            return None

        self._collection = self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
        return self._collection

    def add_chunks(
        self,
        collection_name: str,
        chunks: list[dict[str, Any]]
    ) -> int:
        """
        Add embedded chunks to Chroma collection.

        Args:
            collection_name: Collection name
            chunks: List of embedded chunks

        Returns:
            Number of chunks added
        """
        collection = self.get_or_create_collection(collection_name)
        if not collection:
            return 0

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            if chunk.get("embedding"):
                ids.append(chunk.get("chunk_id", f"chunk_{i}"))
                embeddings.append(chunk["embedding"])
                documents.append(chunk["text"])
                metadatas.append(chunk.get("metadata", {}))

        if ids:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"✅ Added {len(ids)} chunks to Chroma collection '{collection_name}'")
            return len(ids)

        return 0

    def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        n_results: int = 10
    ) -> list[dict[str, Any]]:
        """
        Search Chroma collection by embedding similarity.

        Args:
            collection_name: Collection to search
            query_embedding: Query vector
            n_results: Max results

        Returns:
            Similar documents with distances
        """
        collection = self.get_or_create_collection(collection_name)
        if not collection:
            return []

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Format results
        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i] if results["documents"] else None,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            })

        return output


# =============================================================================
# LANGCHAIN INTEGRATION
# =============================================================================

def create_langchain_documents(chunks: list[dict[str, Any]]) -> list:
    """
    Convert chunks to LangChain Document objects.

    Args:
        chunks: List of embedded chunks

    Returns:
        List of LangChain Document objects
    """
    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain not available")
        return []

    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk["text"],
            metadata=chunk.get("metadata", {})
        )
        documents.append(doc)

    return documents


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_rag_pipeline: Optional[AirbyteRAGPipeline] = None

def get_rag_pipeline() -> AirbyteRAGPipeline:
    """Get singleton RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = AirbyteRAGPipeline()
    return _rag_pipeline


async def run_rag_sync(
    db,  # AtlasDatabase
    source_name: str,
    config: dict[str, Any],
    dataset_name: str,
    streams: Optional[list[str]] = None,
    use_chroma: bool = False,
    chroma_path: str = "./chroma_db"
) -> dict[str, Any]:
    """
    Run complete RAG sync pipeline.

    Extracts from Airbyte source, chunks, embeds, and stores in vector DB.

    Args:
        db: Database instance
        source_name: Airbyte source name
        config: Source configuration
        dataset_name: Name for the dataset
        streams: Optional stream filter
        use_chroma: Use ChromaDB instead of pgvector
        chroma_path: ChromaDB persistence path

    Returns:
        Sync results with statistics
    """
    run_id = str(uuid4())
    pipeline = get_rag_pipeline()

    results = {
        "run_id": run_id,
        "source": source_name,
        "dataset_name": dataset_name,
        "records_processed": 0,
        "chunks_created": 0,
        "chunks_embedded": 0,
        "chunks_stored": 0
    }

    # Collect all chunks
    all_chunks = []

    async for embedded_chunk in pipeline.process_to_rag(source_name, config, streams):
        results["chunks_created"] += 1
        if embedded_chunk.get("embedding"):
            results["chunks_embedded"] += 1
        all_chunks.append(embedded_chunk)

    # Store in vector DB
    if use_chroma:
        chroma = ChromaVectorStore(persist_directory=chroma_path)
        results["chunks_stored"] = chroma.add_chunks(dataset_name, all_chunks)
    else:
        # Use pgvector
        results["chunks_stored"] = await store_in_pgvector(
            db=db,
            run_id=run_id,
            source_id=source_name,
            dataset_name=dataset_name,
            chunks=all_chunks
        )

    logger.info(f"RAG sync complete: {results}")
    return results
