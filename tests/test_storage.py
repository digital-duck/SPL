"""Tests for vector store backends: FAISS and ChromaDB.

Runs the same test suite against both backends via parametrize,
ensuring interface parity. Uses a tmp_path fixture for isolation.
"""

from __future__ import annotations
import pytest
from spl.storage import get_vector_store


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

def make_store(backend: str, tmp_path):
    """Create a fresh store for the given backend in an isolated directory."""
    return get_vector_store(backend, str(tmp_path))


# ---------------------------------------------------------------------------
# Parametrized backend tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("backend", ["faiss", "chroma"])
class TestVectorStoreBackend:

    def test_empty_count(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        assert store.count() == 0
        store.close()

    def test_add_single(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        doc_id = store.add("Python is a high-level programming language.", {"source": "test"})
        assert isinstance(doc_id, int)
        assert doc_id >= 1
        assert store.count() == 1
        store.close()

    def test_add_batch(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        texts = [
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning models require large datasets.",
            "SQL is a declarative language for databases.",
        ]
        ids = store.add_batch(texts, [{"i": i} for i in range(len(texts))])
        assert len(ids) == 3
        assert store.count() == 3
        store.close()

    def test_query_returns_results(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        store.add_batch([
            "Python is used for data science and AI.",
            "JavaScript is used for web development.",
            "SQL is used for database queries.",
        ])
        results = store.query("data science programming", top_k=2)
        assert len(results) == 2
        for r in results:
            assert "text" in r
            assert "score" in r
            assert "metadata" in r
            assert "tokens" in r
            assert "id" in r
        store.close()

    def test_query_top_k_capped_by_total(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        store.add("Only one document here.")
        results = store.query("document", top_k=10)
        assert len(results) == 1
        store.close()

    def test_query_empty_store(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        results = store.query("anything", top_k=5)
        assert results == []
        store.close()

    def test_delete(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        doc_id = store.add("Document to be deleted.")
        assert store.count() == 1
        result = store.delete(doc_id)
        assert result is True
        store.close()

    def test_tokens_field_populated(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        text = "A" * 100  # 100 chars → ~25 tokens (len // 4)
        store.add(text)
        results = store.query(text, top_k=1)
        assert results[0]["tokens"] > 0
        store.close()

    def test_metadata_roundtrip(self, backend, tmp_path):
        store = make_store(backend, tmp_path)
        meta = {"source": "wiki", "page": 42}
        store.add("Some text with metadata.", meta)
        results = store.query("text metadata", top_k=1)
        assert results[0]["metadata"].get("source") == "wiki"
        store.close()
