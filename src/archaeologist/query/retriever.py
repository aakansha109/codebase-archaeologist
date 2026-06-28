import os
from pathlib import Path
from typing import List, Dict, Any
from archaeologist.config import settings
from archaeologist.ingest.ast_parser import ASTCodeParser, CodeChunk
from archaeologist.ingest.git_extractor import GitExtractor
from archaeologist.store.vector_store import HybridVectorStore, SearchResult

class CodebaseRetriever:
    """Orchestrates ingestion of code files + Git history and multi-index query retrieval."""
    
    def __init__(self, store: HybridVectorStore = None):
        self.store = store or HybridVectorStore()
        self.parser = ASTCodeParser()
        self.extractor: GitExtractor = None

    def ingest_repository(self, target: str, progress_callback=None) -> Dict[str, Any]:
        """Clones repo, parses AST chunks, mines commit lineage, and indexes into Qdrant."""
        if progress_callback:
            progress_callback("Mining Git repository and commit lineage...")
            
        self.extractor = GitExtractor(target)
        repo_path = self.extractor.prepare_repo()
        commits = self.extractor.mine_commit_history()
        lineage_map = self.extractor.file_commit_map
        
        if progress_callback:
            progress_callback(f"Parsed {len(commits)} historical commits. Chunking code files via AST...")
            
        all_chunks: List[CodeChunk] = []
        valid_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".md"}
        exclude_dirs = {
            "node_modules", "dist", "build", "__pycache__", "tests", "docs",
            "screenshots", "docker", "releases", "report", "evals", "scripts",
            ".git", ".github", ".agents", ".claude", "public"
        }
        
        file_count = 0
        max_files = 150
        
        for root, dirs, files in os.walk(repo_path):
            # Ignore hidden, build, test, and config folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in exclude_dirs]
            for file in files:
                if file_count >= max_files:
                    break
                file_path = Path(root) / file
                if file_path.suffix.lower() in valid_extensions:
                    try:
                        chunks = self.parser.parse_file(file_path, relative_to=repo_path)
                        all_chunks.extend(chunks)
                        file_count += 1
                    except Exception as e:
                        pass
            if file_count >= max_files:
                break
                        
        if progress_callback:
            progress_callback(f"Generated {len(all_chunks)} AST code chunks. Indexing into Qdrant Hybrid Store...")
            
        self.store.ingest_chunks(all_chunks, lineage_map)
        
        # Re-populate lineage in search results during lookup
        self.lineage_map = lineage_map
        
        stats = {
            "repo_path": str(repo_path),
            "commits_mined": len(commits),
            "chunks_indexed": len(all_chunks)
        }
        if progress_callback:
            progress_callback("Ingestion complete!")
        return stats

    def retrieve(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Retrieves top matches and attaches Git lineage dynamically at query time."""
        results = self.store.search(query, top_k=top_k)
        
        # Load GitExtractor if not present (subsequent CLI executions)
        if not self.extractor:
            repo_name = "paperclip"
            local_dir = settings.REPOS_DIR / repo_name
            if local_dir.exists():
                self.extractor = GitExtractor(str(local_dir))
                
        for r in results:
            if not r.lineage and self.extractor:
                try:
                    r.lineage = [c.model_dump() if hasattr(c, 'model_dump') else c 
                                 for c in self.extractor.get_file_lineage(r.file_path)]
                except Exception:
                    pass
        return results

    def clear_cache(self):
        """Delegates cache clearing to the vector store."""
        self.store.clear_cache()
        self.extractor = None
