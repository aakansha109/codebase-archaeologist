import os
from pathlib import Path
from git import Repo
from archaeologist.ingest.git_extractor import GitExtractor

def test_git_extractor_diff(tmp_path: Path):
    # Initialize a temporary git repository
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)
    
    # Configure mock git user
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")
        
    # Create a sample file and commit it
    file_path = repo_dir / "sample.py"
    file_path.write_text("print('Hello World')\n")
    repo.index.add(["sample.py"])
    commit_a = repo.index.commit("Initial commit")
    
    # Edit the file and commit again
    file_path.write_text("print('Hello World')\nprint('Goodbye World')\n")
    repo.index.add(["sample.py"])
    commit_b = repo.index.commit("Second commit")
    
    # Run GitExtractor
    extractor = GitExtractor(target=str(repo_dir))
    
    # Retrieve diff
    diff_text = extractor.get_file_diff("sample.py", commit_a.hexsha, commit_b.hexsha)
    
    # Assertions
    assert "Goodbye World" in diff_text
    assert "+print('Goodbye World')" in diff_text
