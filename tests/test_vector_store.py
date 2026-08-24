import pytest
from pathlib import Path
from archaeologist.ingest.ast_parser import CodeChunk
from archaeologist.store.vector_store import HybridVectorStore, SearchResult

def test_vector_store_ingest_and_search(tmp_path: Path, monkeypatch):
    # Use temporary Qdrant directory
    qdrant_dir = tmp_path / "qdrant_db"
    from archaeologist.config import settings
    monkeypatch.setattr(settings, "QDRANT_PATH", qdrant_dir)
    
    store = HybridVectorStore(collection_name="test_collection")
    
    chunks = [
        CodeChunk(
            chunk_id="file1.py::calculate_total::L1-L10",
            file_path="file1.py",
            language="python",
            chunk_type="function",
            name="calculate_total",
            content="def calculate_total(items):\n    return sum(items)",
            start_line=1,
            end_line=10
        ),
        CodeChunk(
            chunk_id="file2.py::AuthHandler::L1-L20",
            file_path="file2.py",
            language="python",
            chunk_type="class",
            name="AuthHandler",
            content="class AuthHandler:\n    def authenticate(self, user):\n        return True",
            start_line=1,
            end_line=20
        )
    ]
    
    lineage_map = {
        "file1.py": [{"commit_hash": "a1b2c3d4", "date": "2026-01-01", "author": "Alice", "message": "Initial totals"}],
        "file2.py": [{"commit_hash": "e5f6g7h8", "date": "2026-01-02", "author": "Bob", "message": "Add AuthHandler"}]
    }
    
    store.ingest_chunks(chunks, lineage_map)
    assert len(store.chunks) == 2
    assert store.bm25 is not None
    
    # Perform Search
    results = store.search("authenticate user", top_k=2)
    assert len(results) > 0
    assert isinstance(results[0], SearchResult)
    top_names = [r.name for r in results]
    assert "AuthHandler" in top_names

def test_vector_store_clear_cache(tmp_path: Path, monkeypatch):
    qdrant_dir = tmp_path / "qdrant_db"
    from archaeologist.config import settings
    monkeypatch.setattr(settings, "QDRANT_PATH", qdrant_dir)
    
    store = HybridVectorStore(collection_name="test_clear_collection")
    chunks = [
        CodeChunk(
            chunk_id="sample.py::sample_fn::L1-L5",
            file_path="sample.py",
            language="python",
            chunk_type="function",
            name="sample_fn",
            content="def sample_fn(): pass",
            start_line=1,
            end_line=5
        )
    ]
    store.ingest_chunks(chunks, lineage_map={})
    assert len(store.chunks) == 1
    
    store.clear_cache()
    assert len(store.chunks) == 0
    assert store.bm25 is None
    assert len(store.chunk_ids) == 0
