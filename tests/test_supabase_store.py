import pytest
from archaeologist.ingest.ast_parser import CodeChunk
from archaeologist.store.supabase_store import SupabaseVectorStore

def test_supabase_vector_store():
    store = SupabaseVectorStore(table_name="test_code_chunks")
    assert not store.is_configured()  # Should default to false without SUPABASE_URL env
    
    chunks = [
        CodeChunk(
            chunk_id="test.py::main::L1-L5",
            file_path="test.py",
            language="python",
            chunk_type="function",
            name="main",
            content="def main(): pass",
            start_line=1,
            end_line=5
        )
    ]
    store.ingest_chunks(chunks)
    assert len(store.chunks) == 1
    
    results = store.search("main", top_k=1)
    assert len(results) == 1
    assert results[0].name == "main"
