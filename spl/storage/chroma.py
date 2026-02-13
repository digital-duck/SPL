"""ChromaDB-backed vector store for SPL RAG operations.

Provides semantic search via rag.query() using ChromaDB for similarity search.
ChromaDB handles persistence natively — no separate index file needed.

Requires: pip install chromadb
"""

from __future__ import annotations
import os
from typing import Any

try:
    import chromadb
    from chromadb import EmbeddingFunction, Embeddings
except ImportError:
    chromadb = None  # type: ignore
    EmbeddingFunction = object  # type: ignore


class _WrappedEmbeddingFn(EmbeddingFunction):
    """Adapts a single-text callable to ChromaDB's batch embedding interface."""

    def __init__(self, fn: Any):
        self._fn = fn

    def __call__(self, input: list[str]) -> Embeddings:  # noqa: A002
        return [self._fn(text) for text in input]


class ChromaStore:
    """ChromaDB vector store for SPL RAG operations.

    Drop-in alternative to VectorStore (FAISS). Same public interface:
    add(), add_batch(), query(), count(), delete(), close().

    Usage:
        store = ChromaStore(".spl/")
        store.add("Python is a programming language", {"source": "wiki"})
        results = store.query("What is Python?", top_k=3)

    ChromaDB persists automatically to <storage_dir>/chroma/.
    No separate metadata DB needed — ChromaDB stores documents and metadata together.
    """

    COLLECTION_NAME = "spl_documents"

    def __init__(
        self,
        storage_dir: str = ".spl",
        embedding_fn: Any = None,
    ):
        if chromadb is None:
            raise ImportError("chromadb is required: pip install chromadb")

        self.storage_dir = storage_dir
        chroma_dir = os.path.join(storage_dir, "chroma")
        os.makedirs(chroma_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(path=chroma_dir)

        # Use provided embedding fn (wrapped for ChromaDB), or ChromaDB default.
        # ChromaDB default uses all-MiniLM-L6-v2 if sentence-transformers is
        # installed, otherwise falls back gracefully.
        ef = _WrappedEmbeddingFn(embedding_fn) if embedding_fn else None
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "l2"},
        )

    @staticmethod
    def _clean_meta(metadata: dict | None) -> dict | None:
        """ChromaDB 1.x rejects empty dicts — convert {} to None."""
        if not metadata:
            return None
        return metadata

    def add(self, text: str, metadata: dict | None = None) -> int:
        """Add a document. Returns the document ID (1-based integer)."""
        doc_id = self._collection.count() + 1
        self._collection.add(
            documents=[text],
            ids=[str(doc_id)],
            metadatas=[self._clean_meta(metadata)],
        )
        return doc_id

    def add_batch(self, texts: list[str], metadatas: list[dict] | None = None) -> list[int]:
        """Add multiple documents at once. Returns list of IDs."""
        if metadatas is None:
            metadatas = [None] * len(texts)  # type: ignore[list-item]

        start_id = self._collection.count() + 1
        ids = list(range(start_id, start_id + len(texts)))

        self._collection.add(
            documents=texts,
            ids=[str(i) for i in ids],
            metadatas=[self._clean_meta(m) for m in metadatas],
        )
        return ids

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Search for similar documents.

        Returns list of dicts with 'id', 'text', 'metadata', 'score', 'tokens'.
        Score is L2 distance (lower = more similar), matching FAISS convention.
        """
        total = self._collection.count()
        if total == 0:
            return []

        k = min(top_k, total)
        results = self._collection.query(
            query_texts=[text],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for doc, meta, dist, id_ in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            results["ids"][0],
        ):
            output.append({
                "id": int(id_),
                "text": doc,
                "metadata": meta,
                "tokens": len(doc) // 4,
                "score": float(dist),
            })
        return output

    def count(self) -> int:
        """Return number of indexed documents."""
        return self._collection.count()

    def delete(self, doc_id: int) -> bool:
        """Delete a document by ID."""
        try:
            self._collection.delete(ids=[str(doc_id)])
            return True
        except Exception:
            return False

    def close(self):
        """No-op — ChromaDB persists automatically."""
        pass
