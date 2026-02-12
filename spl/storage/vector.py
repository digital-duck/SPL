"""FAISS-backed vector store for SPL RAG operations.

Provides semantic search via rag.query() using FAISS for similarity search
and SQLite for document metadata. Both file-based and portable.
"""

from __future__ import annotations
import json
import os
import sqlite3
from typing import Any

import numpy as np

# FAISS is optional but required for RAG functionality
try:
    import faiss
except ImportError:
    faiss = None  # type: ignore


class VectorStore:
    """FAISS + SQLite vector store for SPL RAG operations.

    Usage:
        store = VectorStore(".spl/")
        store.add("Python is a programming language", {"source": "wiki"})
        results = store.query("What is Python?", top_k=3)
    """

    def __init__(
        self,
        storage_dir: str = ".spl",
        embedding_dim: int = 384,
        embedding_fn: Any = None,
    ):
        if faiss is None:
            raise ImportError("faiss-cpu is required for RAG: pip install faiss-cpu")

        self.storage_dir = storage_dir
        self.embedding_dim = embedding_dim
        self.index_path = os.path.join(storage_dir, "vectors.faiss")
        self.meta_path = os.path.join(storage_dir, "vectors_meta.db")

        os.makedirs(storage_dir, exist_ok=True)

        # Initialize or load FAISS index
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatL2(embedding_dim)

        # Initialize metadata SQLite
        self._meta_conn = sqlite3.connect(self.meta_path)
        self._meta_conn.row_factory = sqlite3.Row
        self._init_meta_schema()

        # Embedding function (defaults to simple hash-based for prototype)
        self._embed_fn = embedding_fn or self._default_embedding

    def _init_meta_schema(self):
        self._meta_conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                metadata JSON,
                embedding_model TEXT DEFAULT 'default',
                tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self._meta_conn.commit()

    def add(self, text: str, metadata: dict | None = None) -> int:
        """Add a document to the vector store.

        Returns the document ID.
        """
        # Generate embedding
        embedding = self._embed_fn(text)
        embedding = np.array([embedding], dtype=np.float32)

        # Add to FAISS
        self.index.add(embedding)
        doc_id = self.index.ntotal  # 1-based after add

        # Store metadata
        self._meta_conn.execute(
            "INSERT INTO documents (id, text, metadata, tokens) VALUES (?, ?, ?, ?)",
            (doc_id, text, json.dumps(metadata or {}), len(text) // 4)
        )
        self._meta_conn.commit()

        # Persist FAISS index
        faiss.write_index(self.index, self.index_path)

        return doc_id

    def add_batch(self, texts: list[str], metadatas: list[dict] | None = None) -> list[int]:
        """Add multiple documents at once."""
        if metadatas is None:
            metadatas = [{}] * len(texts)

        ids = []
        embeddings = []
        for text in texts:
            emb = self._embed_fn(text)
            embeddings.append(emb)

        embeddings_np = np.array(embeddings, dtype=np.float32)
        start_id = self.index.ntotal + 1
        self.index.add(embeddings_np)

        for i, (text, meta) in enumerate(zip(texts, metadatas)):
            doc_id = start_id + i
            self._meta_conn.execute(
                "INSERT INTO documents (id, text, metadata, tokens) VALUES (?, ?, ?, ?)",
                (doc_id, text, json.dumps(meta), len(text) // 4)
            )
            ids.append(doc_id)

        self._meta_conn.commit()
        faiss.write_index(self.index, self.index_path)
        return ids

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Search for similar documents.

        Returns list of dicts with 'text', 'metadata', 'score', 'tokens'.
        """
        if self.index.ntotal == 0:
            return []

        embedding = self._embed_fn(text)
        embedding = np.array([embedding], dtype=np.float32)

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            doc_id = int(idx) + 1  # FAISS uses 0-based, our DB uses 1-based
            row = self._meta_conn.execute(
                "SELECT text, metadata, tokens FROM documents WHERE id = ?",
                (doc_id,)
            ).fetchone()
            if row:
                results.append({
                    "id": doc_id,
                    "text": row["text"],
                    "metadata": json.loads(row["metadata"]),
                    "tokens": row["tokens"],
                    "score": float(dist),
                })

        return results

    def count(self) -> int:
        """Return number of indexed documents."""
        return self.index.ntotal

    def delete(self, doc_id: int) -> bool:
        """Delete a document by ID (metadata only; FAISS rebuild needed for full delete)."""
        cursor = self._meta_conn.execute(
            "DELETE FROM documents WHERE id = ?", (doc_id,)
        )
        self._meta_conn.commit()
        return cursor.rowcount > 0

    def _default_embedding(self, text: str) -> list[float]:
        """Simple deterministic embedding for prototype.

        Uses character-level hashing to create a fixed-dimension vector.
        Replace with sentence-transformers or OpenRouter embeddings for production.
        """
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        for i, char in enumerate(text.lower()):
            idx = ord(char) % self.embedding_dim
            vec[idx] += 1.0 / (1 + i * 0.01)
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def close(self):
        """Close connections and save index."""
        if self.index.ntotal > 0:
            faiss.write_index(self.index, self.index_path)
        self._meta_conn.close()
