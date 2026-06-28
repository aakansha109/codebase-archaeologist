import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rank_bm25 import BM25Okapi
from archaeologist.config import settings
from archaeologist.ingest.ast_parser import CodeChunk

class SearchResult(BaseModel):
    """Result returned from hybrid search combining semantic and exact matches."""
    chunk_id: str
    file_path: str
    name: str
    chunk_type: str
    content: str
    start_line: int
    end_line: int
    score: float
    metadata: Dict[str, Any]
    lineage: List[Dict[str, Any]]

class HybridVectorStore:
    """Combines Qdrant dense vector search with BM25 sparse keyword search via RRF."""
    
    def __init__(self, collection_name: str = settings.COLLECTION_NAME):
        self.collection_name = collection_name
        
        import os
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            self.client = QdrantClient(path=str(settings.QDRANT_PATH))
            
        self.chunks: Dict[str, CodeChunk] = {}
        self.bm25: Optional[BM25Okapi] = None
        self.chunk_ids: List[str] = []
        
        # Initialize fastembed embedding model if available
        try:
            from fastembed import TextEmbedding
            self.embedder = list(TextEmbedding(model_name=settings.EMBEDDING_MODEL))[0] if False else TextEmbedding(model_name=settings.EMBEDDING_MODEL)
        except Exception:
            self.embedder = None
            
        self._init_collection()
        self._load_cache()

    def _load_cache(self):
        """Loads chunks, metadata, and git lineage from local cache or scrolls Qdrant for stateless recovery."""
        self.lineage_map = {}
        cache_path = settings.QDRANT_PATH / "chunks_cache.json"
        
        loaded = False
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = {cid: CodeChunk(**val) for cid, val in data.items()}
                    self.chunk_ids = list(self.chunks.keys())
                    corpus_tokens = [self._tokenize(chunk.name + " " + chunk.content) for chunk in self.chunks.values()]
                    if corpus_tokens:
                        self.bm25 = BM25Okapi(corpus_tokens)
                    loaded = True
            except Exception as e:
                print(f"Warning: Failed to load chunks cache: {e}")
                
        # Cloud/Serverless recovery fallback: reconstruct index from Qdrant DB scroll
        if not loaded:
            try:
                collections = [c.name for c in self.client.get_collections().collections]
                if self.collection_name in collections:
                    offset = None
                    all_chunks = {}
                    while True:
                        records, next_offset = self.client.scroll(
                            collection_name=self.collection_name,
                            limit=100,
                            with_payload=True,
                            with_vectors=False,
                            offset=offset
                        )
                        for r in records:
                            payload = r.payload
                            if payload and "chunk_id" in payload:
                                cid = payload["chunk_id"]
                                chunk_data = {
                                    "chunk_id": cid,
                                    "file_path": payload["file_path"],
                                    "language": payload["language"],
                                    "chunk_type": payload["chunk_type"],
                                    "name": payload["name"],
                                    "content": payload["content"],
                                    "start_line": payload["start_line"],
                                    "end_line": payload["end_line"],
                                    "docstring": payload.get("docstring"),
                                    "metadata": payload.get("metadata", {})
                                }
                                all_chunks[cid] = CodeChunk(**chunk_data)
                                self.lineage_map[payload["file_path"]] = payload.get("lineage", [])
                        offset = next_offset
                        if not offset:
                            break
                    
                    if all_chunks:
                        self.chunks = all_chunks
                        self.chunk_ids = list(self.chunks.keys())
                        corpus_tokens = [self._tokenize(chunk.name + " " + chunk.content) for chunk in self.chunks.values()]
                        self.bm25 = BM25Okapi(corpus_tokens)
                        print(f"Successfully recovered {len(all_chunks)} chunks from Qdrant DB!")
            except Exception as e:
                print(f"Warning: Failed to recover state from Qdrant DB: {e}")
                
        lineage_cache_path = settings.QDRANT_PATH / "lineage_cache.json"
        if not self.lineage_map and lineage_cache_path.exists():
            try:
                with open(lineage_cache_path, "r", encoding="utf-8") as f:
                    self.lineage_map = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load lineage cache: {e}")

    def _init_collection(self):
        """Creates Qdrant collection if not exists."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=settings.DENSE_VECTOR_SIZE, distance=Distance.COSINE)
            )

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for BM25 keyword matching."""
        # Split on whitespace and snake/camel case transitions
        tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
        return tokens

    def ingest_chunks(self, chunks: List[CodeChunk], lineage_map: Dict[str, Any], extractor: Optional[Any] = None):
        """Indexes code chunks into Qdrant (dense) and BM25 (sparse) after clearing previous repository data."""
        if not chunks:
            return
            
        # Reset database and memory state to start fresh with the new repository
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._init_collection()
        
        self.chunks = {}
        self.chunk_ids = []
        self.lineage_map = {}
        self.bm25 = None
        
        points = []
        corpus_tokens = []
        
        # Prepare embeddings
        texts_to_embed = [f"{c.name}\n{c.docstring or ''}\n{c.content[:500]}" for c in chunks]
        
        embeddings = []
        if self.embedder:
            try:
                embeddings = list(self.embedder.embed(texts_to_embed))
            except Exception as e:
                print(f"Warning embedding failed, using dummy vectors: {e}")
                embeddings = [[0.0] * settings.DENSE_VECTOR_SIZE for _ in chunks]
        else:
            embeddings = [[0.0] * settings.DENSE_VECTOR_SIZE for _ in chunks]
            
        for i, chunk in enumerate(chunks):
            self.chunks[chunk.chunk_id] = chunk
            self.chunk_ids.append(chunk.chunk_id)
            
            # BM25 tokens
            tokens = self._tokenize(chunk.name + " " + chunk.content)
            corpus_tokens.append(tokens)
            
            # Lineage
            lineage = [c.model_dump() if hasattr(c, 'model_dump') else c for c in lineage_map.get(chunk.file_path, [])]
            
            # Qdrant point
            payload = chunk.model_dump()
            payload["lineage"] = lineage
            
            # Integer ID hash for Qdrant point ID
            point_id = abs(hash(chunk.chunk_id)) % (2**63 - 1)
            points.append(PointStruct(
                id=point_id,
                vector=list(embeddings[i]),
                payload=payload
            ))
            
        # Upload points to Qdrant
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
            
        # Build BM25 index
        if corpus_tokens:
            self.bm25 = BM25Okapi(corpus_tokens)

        # Save to cache file on disk
        cache_path = settings.QDRANT_PATH / "chunks_cache.json"
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                serialized = {cid: chunk.model_dump() for cid, chunk in self.chunks.items()}
                json.dump(serialized, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save chunks cache: {e}")
            
        # Save lineage map to disk cache
        self.lineage_map = {
            file_path: [c.model_dump() if hasattr(c, 'model_dump') else c for c in commits]
            for file_path, commits in lineage_map.items()
        }
        lineage_cache_path = settings.QDRANT_PATH / "lineage_cache.json"
        try:
            with open(lineage_cache_path, "w", encoding="utf-8") as f:
                json.dump(self.lineage_map, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save lineage cache: {e}")

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Performs Reciprocal Rank Fusion (RRF) search over Dense and Sparse results."""
        if not self.chunks:
            return []
            
        rrf_scores: Dict[str, float] = {}
        k = 60  # RRF constant
        
        # 1. Dense Retrieval
        dense_results = []
        if self.embedder:
            try:
                query_vec = list(self.embedder.embed([query]))[0]
                dense_hits = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=list(query_vec),
                    limit=top_k * 2
                )
                for rank, hit in enumerate(dense_hits):
                    cid = hit.payload.get("chunk_id")
                    if cid:
                        dense_results.append(cid)
                        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank + 1))
            except Exception as e:
                pass
                
        # 2. Sparse (BM25) Keyword Retrieval
        if self.bm25 and self.chunk_ids:
            query_tokens = self._tokenize(query)
            bm25_scores = self.bm25.get_scores(query_tokens)
            # Get top indices
            top_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k * 2]
            for rank, idx in enumerate(top_indices):
                if bm25_scores[idx] > 0:
                    cid = self.chunk_ids[idx]
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank + 1))
                    
        # Sort combined RRF scores
        ranked_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]
        
        results = []
        for cid in ranked_cids:
            chunk = self.chunks.get(cid)
            if chunk:
                lineage = self.lineage_map.get(chunk.file_path, [])
                results.append(SearchResult(
                    chunk_id=chunk.chunk_id,
                    file_path=chunk.file_path,
                    name=chunk.name,
                    chunk_type=chunk.chunk_type,
                    content=chunk.content,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    score=round(rrf_scores[cid], 4),
                    metadata=chunk.metadata,
                    lineage=lineage
                ))
                
        return results
