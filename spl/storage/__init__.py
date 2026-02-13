"""Storage backends for SPL: SQLite memory store and vector stores (FAISS, ChromaDB)."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spl.storage.vector import VectorStore
    from spl.storage.chroma import ChromaStore


def get_vector_store(
    backend: str = "faiss",
    storage_dir: str = ".spl",
    **kwargs,
) -> "VectorStore | ChromaStore":
    """Factory: return a vector store for the requested backend.

    Args:
        backend:     "faiss" (default) or "chroma"
        storage_dir: path to the .spl/ project directory
        **kwargs:    passed to the store constructor (e.g. embedding_fn)

    Raises:
        ValueError:   unknown backend name
        ImportError:  backend dependency not installed
    """
    if backend == "chroma":
        from spl.storage.chroma import ChromaStore
        return ChromaStore(storage_dir, **kwargs)
    elif backend == "faiss":
        from spl.storage.vector import VectorStore
        return VectorStore(storage_dir, **kwargs)
    else:
        raise ValueError(f"Unknown vector backend '{backend}'. Choose 'faiss' or 'chroma'.")
