import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import git
from archaeologist.config import settings

class CommitInfo(BaseModel):
    """Represents historical context from a Git commit."""
    commit_hash: str
    author: str
    date: str
    message: str
    files_changed: List[str]

class GitExtractor:
    """Clones repositories and extracts Git commit timeline and file lineage."""
    
    def __init__(self, target: str):
        self.target = target
        self.repo: Optional[git.Repo] = None
        self.repo_path: Optional[Path] = None
        self.file_commit_map: Dict[str, List[CommitInfo]] = {}
        
        # Auto-initialize repo if target is a local path
        if not (target.startswith("http://") or target.startswith("https://") or target.startswith("git@")):
            path = Path(target).resolve()
            if path.exists() and (path / ".git").exists():
                try:
                    self.repo = git.Repo(path)
                    self.repo_path = path
                except Exception:
                    pass

    def prepare_repo(self) -> Path:
        """Clones URL if remote, or opens local path, handling directory corruptions and permissions."""
        if self.target.startswith("http://") or self.target.startswith("https://") or self.target.startswith("git@"):
            repo_name = self.target.rstrip("/").split("/")[-1].replace(".git", "")
            local_dir = settings.REPOS_DIR / repo_name
            
            def remove_readonly(func, path, _):
                import stat
                try:
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                except Exception:
                    pass
            
            if local_dir.exists():
                try:
                    self.repo = git.Repo(local_dir)
                    self.repo.remotes.origin.pull()
                    self.repo_path = local_dir
                except Exception:
                    try:
                        shutil.rmtree(local_dir, onerror=remove_readonly)
                    except Exception:
                        pass
                    self.repo = None
            
            if not self.repo or not local_dir.exists():
                try:
                    settings.REPOS_DIR.mkdir(parents=True, exist_ok=True)
                    self.repo = git.Repo.clone_from(self.target, local_dir, depth=30)
                    self.repo_path = local_dir
                except Exception as e:
                    raise RuntimeError(f"Failed to clone repository {self.target}: {e}")
        else:
            path = Path(self.target).resolve()
            if not path.exists():
                raise FileNotFoundError(f"Repository path {path} does not exist.")
            self.repo = git.Repo(path)
            self.repo_path = path
            
        return self.repo_path

    def mine_commit_history(self, max_commits: int = 300) -> List[CommitInfo]:
        """Extracts recent commit timeline and builds file lineage mapping."""
        if not self.repo:
            self.prepare_repo()
            
        commits_data: List[CommitInfo] = []
        self.file_commit_map = {}
        
        try:
            for commit in self.repo.iter_commits(max_count=max_commits):
                try:
                    # High-performance, low-memory files list retrieval bypassing stats diff parsing
                    files_str = self.repo.git.diff_tree(commit.hexsha, no_commit_id=True, name_only=True, r=True)
                    files = [f.strip() for f in files_str.strip().split("\n") if f.strip()] if files_str else []
                except Exception:
                    files = []
                dt = datetime.fromtimestamp(commit.authored_date).isoformat()
                
                info = CommitInfo(
                    commit_hash=commit.hexsha[:8],
                    author=commit.author.name or "Unknown",
                    date=dt,
                    message=commit.message.strip(),
                    files_changed=files
                )
                commits_data.append(info)
                
                for f in files:
                    normalized_f = f.replace("\\", "/")
                    if normalized_f not in self.file_commit_map:
                        self.file_commit_map[normalized_f] = []
                    # Keep top 5 most recent commits per file
                    if len(self.file_commit_map[normalized_f]) < 5:
                        self.file_commit_map[normalized_f].append(info)
        except Exception as e:
            print(f"Warning during git extraction: {e}")
            
        return commits_data

    def get_file_lineage(self, rel_file_path: str) -> List[CommitInfo]:
        """Returns recent commits that modified a specific file, with dynamic git log fallback."""
        normalized = rel_file_path.replace("\\", "/")
        if normalized in self.file_commit_map:
            return self.file_commit_map[normalized]
            
        if not self.repo:
            return []
            
        try:
            commits = []
            # Fallback to dynamic lookup for older files
            for commit in self.repo.iter_commits(paths=normalized, max_count=5):
                dt = datetime.fromtimestamp(commit.authored_date).isoformat()
                commits.append(CommitInfo(
                    commit_hash=commit.hexsha[:8],
                    author=commit.author.name or "Unknown",
                    date=dt,
                    message=commit.message.strip(),
                    files_changed=[normalized]
                ))
            return commits
        except Exception:
            return []

    def get_file_diff(self, rel_file_path: str, commit_a: str, commit_b: str) -> str:
        """Retrieves raw Git diff content for a specific file between two commits."""
        if not self.repo:
            return ""
        try:
            normalized = rel_file_path.replace("\\", "/")
            diff_text = self.repo.git.diff(commit_a, commit_b, "--", normalized)
            return diff_text
        except Exception as e:
            return f"Error retrieving diff: {e}"
