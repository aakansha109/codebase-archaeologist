from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from archaeologist.query.retriever import CodebaseRetriever
from archaeologist.query.synthesizer import CodeArchaeologistSynthesizer
from archaeologist.ingest.health_auditor import CodebaseHealthAuditor

app = FastAPI(
    title="🏛️ Codebase Archaeologist REST API",
    description="Headless RAG & Vector Search API for Git repository AST chunking, lineage querying, and health auditing.",
    version="0.2.0"
)

# Global shared retriever instance
retriever = CodebaseRetriever()

class IngestRequest(BaseModel):
    target: str = Field(..., json_schema_extra={"example": "https://github.com/paperclipai/paperclip"}, description="Git repo URL or local path")

class QueryRequest(BaseModel):
    question: str = Field(..., json_schema_extra={"example": "How does authentication work?"}, description="Codebase architectural question")
    top_k: Optional[int] = Field(default=4, description="Top evidence chunks to retrieve")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Codebase Archaeologist REST API",
        "docs_url": "/docs"
    }

@app.post("/api/v1/ingest")
def ingest_repository(req: IngestRequest):
    """Ingests a Git repository into Qdrant Hybrid Store."""
    try:
        stats = retriever.ingest_repository(req.target)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/query")
def query_codebase(req: QueryRequest):
    """Performs HyDE RRF search and synthesizes an architectural explanation."""
    try:
        results = retriever.retrieve(req.question, top_k=req.top_k or 4)
        if not results:
            return {"answer": "No relevant code chunks found.", "evidence": []}
            
        synthesizer = CodeArchaeologistSynthesizer()
        answer = synthesizer.synthesize(req.question, results)
        
        evidence_data = [r.model_dump() if hasattr(r, 'model_dump') else r for r in results]
        return {
            "question": req.question,
            "answer": answer,
            "evidence": evidence_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
def get_codebase_health():
    """Computes technical debt risk score and codebase health metrics."""
    try:
        auditor = CodebaseHealthAuditor()
        chunks = list(retriever.store.chunks.values()) if hasattr(retriever.store, 'chunks') else []
        lineage_map = getattr(retriever.store, 'lineage_map', {})
        health_data = auditor.analyze_health(chunks, lineage_map)
        return health_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
