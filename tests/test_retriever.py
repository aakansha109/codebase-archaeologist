import pytest
from pathlib import Path
from git import Repo
from archaeologist.query.retriever import CodebaseRetriever
from archaeologist.store.vector_store import HybridVectorStore

def test_retriever_ingest_and_retrieve(tmp_path: Path, monkeypatch):
    # Setup mock git repo
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)
    
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test Developer")
        cw.set_value("user", "email", "dev@example.com")
        
    py_file = repo_dir / "service.py"
    py_file.write_text("def run_service():\n    return 'OK'\n")
    
    ts_file = repo_dir / "client.ts"
    ts_file.write_text("export function connectClient() {\n    return true;\n}\n")
    
    repo.index.add(["service.py", "client.ts"])
    repo.index.commit("Initial mock commit")
    
    qdrant_dir = tmp_path / "qdrant_db"
    from archaeologist.config import settings
    monkeypatch.setattr(settings, "QDRANT_PATH", qdrant_dir)
    
    store = HybridVectorStore(collection_name="test_retriever_col")
    retriever = CodebaseRetriever(store=store)
    
    stats = retriever.ingest_repository(str(repo_dir))
    assert stats["commits_mined"] >= 1
    assert stats["chunks_indexed"] >= 2
    assert stats["files_parsed"] >= 2
    
    # Retrieve query
    results = retriever.retrieve("service runner", top_k=2)
    assert len(results) > 0
    names = [r.name for r in results]
    assert "run_service" in names
