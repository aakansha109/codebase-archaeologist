import pytest
from archaeologist.ingest.ast_parser import CodeChunk
from archaeologist.ingest.health_auditor import CodebaseHealthAuditor

def test_codebase_health_auditor():
    auditor = CodebaseHealthAuditor()
    chunks = [
        CodeChunk(
            chunk_id="f1.py::fn1::L1-L10",
            file_path="f1.py",
            language="python",
            chunk_type="function",
            name="fn1",
            content="def fn1(): pass",
            start_line=1,
            end_line=10
        ),
        CodeChunk(
            chunk_id="f2.py::BigClass::L1-L120",
            file_path="f2.py",
            language="python",
            chunk_type="class",
            name="BigClass",
            content="class BigClass:\n" + "    pass\n" * 115,
            start_line=1,
            end_line=120
        )
    ]
    lineage_map = {"f2.py": ["commit1", "commit2", "commit3", "commit4", "commit5"]}
    
    health = auditor.analyze_health(chunks, lineage_map)
    assert "health_score" in health
    assert health["total_chunks"] == 2
    assert health["oversized_chunks"] == 1
    assert len(health["churn_hotspots"]) == 1
