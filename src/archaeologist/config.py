import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment configurations
load_dotenv()
load_dotenv(Path.cwd() / ".env.local")
load_dotenv(Path.cwd().parent / "neural-portfolio" / ".env.local")

class Settings(BaseModel):
    """Configuration settings for Codebase Archaeologist."""
    
    # Paths
    BASE_DIR: Path = Field(default_factory=lambda: Path.cwd())
    QDRANT_PATH: Path = Field(default_factory=lambda: Path.cwd() / "qdrant_db")
    REPOS_DIR: Path = Field(default_factory=lambda: Path.cwd() / "repos")
    
    # Vector DB & Search Settings
    COLLECTION_NAME: str = "codebase_archaeology"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    DENSE_VECTOR_SIZE: int = 384
    
    # Chunking thresholds
    MAX_CHUNK_LINES: int = 250
    MIN_CHUNK_LINES: int = 3
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # Options: gemini, openai, ollama
    GEMINI_MODEL: str = "gemini-3.5-flash"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_MODEL: str = "llama3"

settings = Settings()

# Ensure directories exist
settings.QDRANT_PATH.mkdir(parents=True, exist_ok=True)
settings.REPOS_DIR.mkdir(parents=True, exist_ok=True)
