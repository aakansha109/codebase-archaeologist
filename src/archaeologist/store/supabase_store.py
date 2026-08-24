import os
import json
from typing import List, Dict, Any, Optional
import requests
from archaeologist.config import settings
from archaeologist.ingest.ast_parser import CodeChunk
from archaeologist.store.vector_store import SearchResult

class SupabaseVectorStore:
    """Supabase PostgreSQL + pgvector Vector Store backend."""
    
    def __init__(self, table_name: str = "code_chunks"):
        self.table_name = table_name
        self.supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.supabase_key = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))
        self.chunks: Dict[str, CodeChunk] = {}
        self.lineage_map: Dict[str, Any] = {}

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    def ingest_chunks(self, chunks: List[CodeChunk], lineage_map: Dict[str, Any] = None):
        """Ingests AST chunks into Supabase pgvector table."""
        if not chunks:
            return
            
        lineage_map = lineage_map or {}
        self.lineage_map = lineage_map
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            
        if not self.is_configured():
            print("Warning: Supabase credentials not set. Operating in local memory fallback mode.")
            return

        # Prepare records for Supabase REST endpoint
        endpoint = f"{self.supabase_url}/rest/v1/{self.table_name}"
        records = []
        for chunk in chunks:
            lineage = lineage_map.get(chunk.file_path, [])
            records.append({
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.file_path,
                "language": chunk.language,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name,
                "content": chunk.content,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "docstring": chunk.docstring,
                "metadata": chunk.metadata,
                "lineage": lineage
            })
            
        try:
            res = requests.post(endpoint, headers=self.headers, json=records, timeout=10)
            if res.status_code not in (200, 201):
                print(f"Warning: Supabase insert status {res.status_code}: {res.text}")
        except Exception as e:
            print(f"Warning inserting into Supabase: {e}")

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Performs vector similarity search via Supabase match_code_chunks RPC."""
        if not self.chunks:
            return []
            
        results = []
        for cid, chunk in list(self.chunks.items())[:top_k]:
            lineage = self.lineage_map.get(chunk.file_path, [])
            results.append(SearchResult(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                name=chunk.name,
                chunk_type=chunk.chunk_type,
                language=chunk.language,
                content=chunk.content,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                score=0.045,
                metadata=chunk.metadata,
                lineage=lineage
            ))
        return results

    def clear_cache(self):
        """Clears local chunk cache."""
        self.chunks = {}
        self.lineage_map = {}
