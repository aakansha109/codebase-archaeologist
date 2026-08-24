import pytest
from archaeologist.ingest.ast_parser import CodeChunk
from archaeologist.query.report_exporter import ArchaeologicalReportExporter

def test_report_exporter():
    exporter = ArchaeologicalReportExporter()
    stats = {"repo_path": "mock/repo", "commits_mined": 10, "chunks_indexed": 5, "files_parsed": 3}
    chunks = [
        CodeChunk(
            chunk_id="file1.py::fn1::L1-L10",
            file_path="file1.py",
            language="python",
            chunk_type="function",
            name="fn1",
            content="def fn1(): pass",
            start_line=1,
            end_line=10
        )
    ]
    health = {"health_score": 95, "risk_level": "Low Risk 🟢", "avg_chunk_lines": 10, "oversized_chunks": 0}
    diagram_code = "graph TD\n    A --> B"
    
    md = exporter.generate_markdown_report(stats, chunks, health, diagram_code)
    assert "# 🏛️ Archaeological Codebase Report" in md
    assert "mock/repo" in md
    assert "graph TD" in md
    
    html = exporter.generate_html_report(stats, chunks, health, diagram_code)
    assert "<html>" in html
    assert "mock/repo" in html
