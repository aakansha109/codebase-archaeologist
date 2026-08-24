# The Codebase Archaeologist 🏛️🔍

An advanced Retrieval-Augmented Generation (RAG) & Vector Search engine designed for deep code exploration, technical debt analysis, and historical lineage querying across entire Git repositories. 

Instead of a generic "chat with code" tool, **The Codebase Archaeologist** ingests repositories by preserving AST logical boundaries (functions, classes, methods, structs), mining full Git commit evolution histories, and performing hybrid vector search (Qdrant dense vectors + BM25 sparse lexical matching) fused via Reciprocal Rank Fusion (RRF).

---

## ✨ Key Features

- **🔬 AST-Aware Code Chunking**: Intelligently chunks code along logical boundaries (Python `ast`, JS/TS/Go/Rust structural brace matching) rather than arbitrary line windows.
- **⏳ Git Lineage Mining**: Traces commit histories, author metadata, and historical diff logs per file to explain *why* architectural decisions were made over time.
- **🔀 Hybrid Retrieval (Dense + BM25 RRF)**: Merges Qdrant dense vector search (Google Gemini `text-embedding-004` or FastEmbed `BAAI/bge-small-en-v1.5`) with exact keyword search via BM25 and Reciprocal Rank Fusion.
- **📝 Semantic Diff Explainer**: Select any file and compare two historical commits to receive a natural-language AI code review explaining structural changes.
- **🖥️ Dual Interfaces**: High-performance interactive **Streamlit Web Application** + Developer-friendly **Typer CLI**.
- **🛡️ Memory-Optimized & Serverless Ready**: Lazy-loaded ML models and serverless TPU/GPU embedding offloading to stay within 1GB RAM limits on hosted platforms.

---

## 🏗️ Architecture

```
                                  ┌────────────────────────┐
                                  │   Git Repository URL   │
                                  └───────────┬────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
      ┌───────────────────────────┐                       ┌──────────────────────────┐
      │  ASTCodeParser (Py/TS/Go) │                       │   GitExtractor (Commit)  │
      └─────────────┬─────────────┘                       └────────────┬─────────────┘
                    │ (AST Code Chunks)                                │ (Commit Lineage)
                    └─────────────────────────┬────────────────────────┘
                                              ▼
                                 ┌─────────────────────────┐
                                 │   HybridVectorStore     │
                                 │  (Qdrant Dense + BM25)  │
                                 └────────────┬────────────┘
                                              │ (RRF Ranked Search)
                                              ▼
                                 ┌─────────────────────────┐
                                 │ CodeArchaeologist       │
                                 │ Synthesizer (Gemini/LLM)│
                                 └────────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
          ┌───────────────────────┐                       ┌───────────────────────┐
          │  Streamlit Dashboard  │                       │       Typer CLI       │
          └───────────────────────┘                       └───────────────────────┘
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- Git

### 1. Installation

```bash
# Clone repository
git clone https://github.com/aakansha109/codebase-archaeologist.git
cd codebase-archaeologist

# Install dependencies in editable mode
pip install -e .
```

### 2. Environment Setup

Copy `.env.example` to `.env` and set your API keys:

```bash
cp .env.example .env
```

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

---

## 💻 CLI Usage

The package provides a built-in command line interface (`archaeologist`):

```bash
# 1. Ingest a remote Git repository or local folder
archaeologist ingest https://github.com/paperclipai/paperclip

# 2. Ask architectural & historical questions
archaeologist ask "Why did we introduce Redis caching and how does authentication work?"

# 3. View commit timeline for a specific file
archaeologist timeline src/index.ts
```

---

## 🌐 Web Interface (Streamlit)

Launch the interactive dark-themed dashboard:

```bash
streamlit run app.py
```

The web dashboard features:
- **🏠 Welcome Hub**: Quick overview and repo excavation panel.
- **🏛️ Archaeological Search**: Interactive chat with AST code evidence cards and side-by-side snippet comparisons.
- **⏳ Git Lineage Timeline**: Filterable commit history timeline.
- **🔍 Semantic Diff Explainer**: Visual commit-to-commit difference review.
- **📊 Codebase Analytics**: Language breakdown charts and top AST file leaderboards.

---

## 🐳 Docker Deployment

You can build and run **The Codebase Archaeologist** using Docker:

```bash
# Build Docker image
docker build -t codebase-archaeologist .

# Run container
docker run -d -p 8501:8501 --env-file .env codebase-archaeologist
```

Access the app at `http://localhost:8501`.

---

## 🧪 Running Tests

Run the full pytest suite (13+ unit and integration tests):

```bash
pytest
```

---

## 📄 License

Licensed under the [MIT License](LICENSE).
