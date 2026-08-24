import pytest
from archaeologist.ingest.ast_parser import CodeChunk
from archaeologist.ingest.dependency_graph import CodeDependencyGraph

def test_code_dependency_graph():
    chunks = [
        CodeChunk(
            chunk_id="db.py::Database::L1-L10",
            file_path="db.py",
            language="python",
            chunk_type="class",
            name="Database",
            content="import os\nclass Database:\n    def query(self):\n        pass",
            start_line=1,
            end_line=10
        ),
        CodeChunk(
            chunk_id="auth.py::login::L1-L15",
            file_path="auth.py",
            language="python",
            chunk_type="function",
            name="login",
            content="from db import Database\ndef login():\n    db = Database()\n    db.query()",
            start_line=1,
            end_line=15
        )
    ]

    graph = CodeDependencyGraph(chunks)
    assert "Database" in graph.symbol_map
    assert "login" in graph.symbol_map
    
    deps = graph.get_related_symbols("Database", "db.py")
    assert "login" in deps["callers"]
    
    auth_deps = graph.get_related_symbols("login", "auth.py")
    assert "Database" in auth_deps["callees"]
