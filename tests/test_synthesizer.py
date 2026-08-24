import pytest
from archaeologist.query.synthesizer import CodeArchaeologistSynthesizer
from archaeologist.store.vector_store import SearchResult

def test_synthesizer_offline_fallback():
    synthesizer = CodeArchaeologistSynthesizer()
    
    mock_results = [
        SearchResult(
            chunk_id="app.py::main::L1-L10",
            file_path="app.py",
            name="main",
            chunk_type="function",
            language="python",
            content="def main(): print('hello')",
            start_line=1,
            end_line=10,
            score=0.045,
            metadata={},
            lineage=[{
                "commit_hash": "b2c3d4e5",
                "date": "2026-01-01",
                "author": "Alice",
                "message": "Add main function"
            }]
        )
    ]
    
    answer = synthesizer.synthesize("What does main do?", mock_results)
    assert "main" in answer
    assert "app.py" in answer
    assert "b2c3d4e5" in answer

def test_synthesizer_offline_briefing():
    synthesizer = CodeArchaeologistSynthesizer()
    stats = {"commits_mined": 10, "chunks_indexed": 25}
    top_files = [("src/main.py", 5), ("src/utils.py", 3)]
    recent_commits = [{"commit_hash": "c1a2b3", "author": "Bob", "message": "Refactor core"}]
    
    briefing = synthesizer.generate_briefing(stats, top_files, recent_commits)
    assert "Repository Excavation Briefing" in briefing
    assert "src/main.py" in briefing
    assert "c1a2b3" in briefing

def test_synthesizer_explain_diff():
    synthesizer = CodeArchaeologistSynthesizer()
    diff = "--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-print('hello')\n+print('world')"
    
    explanation = synthesizer.explain_diff("main.py", "hash1", "hash2", diff)
    assert "main.py" in explanation or "Diff Explanation" in explanation
