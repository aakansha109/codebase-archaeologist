# The Codebase Archaeologist 🔍

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://codebase-archaeologists.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Supabase pgvector](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Tests Passing](https://img.shields.io/badge/Tests-19%2F19%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](https://pytest.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **An advanced AST-aware Code Intelligence & Architectural Retrieval-Augmented Generation (RAG) platform that excavates entire Git repositories to uncover technical debt, historical lineage, and design evolution.**

👉 **[Launch Live Cloud Application](https://codebase-archaeologists.streamlit.app/)** 🎈

---

## 🌟 Overview

Traditional "Chat with your Code" tools treat source code like plain prose text—blindly slicing files into arbitrary 500-character windows and losing function boundaries, callers, and historical context.

**The Codebase Archaeologist** approaches code comprehension like an archaeological excavation:
1. **Understands Code Structure**: Parses Abstract Syntax Trees (AST) across **Python, TypeScript, JavaScript, Go, Rust, and Java**, preserving execution units (functions, classes, methods, structs).
2. **Traces Git Lineage**: Mines commit logs, historical diffs, and line-range blame (`git log -L`) to reveal *why* decisions were made.
3. **Multi-Index Hybrid Retrieval**: Fuses dense semantic vector embeddings (Google Gemini `text-embedding-004`) with sparse lexical matching (BM25) via **Reciprocal Rank Fusion (RRF)** and cross-encoder symbol reranking.
4. **Persistent Cloud Memory**: Backed by **Supabase PostgreSQL (`pgvector`)** with HNSW indexing for long-term cloud persistence.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Target Git Repository                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│       AST Code Parser         │               │     Git Lineage Extractor     │
│  • Python AST & Brace Matcher │               │  • Historical Commits & Diffs │
│  • Caller/Callee Dep Graphs   │               │  • Line-Range Blame Engine    │
└───────────────┬───────────────┘               └───────────────┬───────────────┘
                │ (Logical AST Chunks)                          │ (Commit Lineage)
                └───────────────────────┬───────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Hybrid Multi-Index Vector Store                   │
│   • Supabase PostgreSQL (pgvector HNSW) / Embedded Qdrant Vector DB   │
│   • Sparse BM25 Keyword Indexing                                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Reciprocal Rank Fusion + 2-Stage Rerank)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     HyDE Query Expansion & Synthesizer                 │
│      Google Gemini 1.5 Flash Architectural Explanation Engine         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
┌───────────────────────────────┐               ┌───────────────────────────────┐
│      Streamlit Cloud App      │               │       Headless REST API       │
│  • Interactive Visual Studio  │               │  • FastAPI Backend Server     │
│  • Mermaid.js Architecture    │               │  • Next.js 14 Web Frontend    │
│  • Technical Debt Auditor     │               │  • Typer CLI Toolkit          │
└───────────────────────────────┘               └───────────────────────────────┘
```

---

## ✨ Core Engineering Highlights

### 🔬 1. AST-Aware Code Parsing & Dependency Graphs
* Replaces naive fixed-token chunking with structural AST parsing.
* Extracts classes, methods, docstrings, argument signatures, and line boundaries for Python, JavaScript, TypeScript, Go, Rust, Java, and C/C++.
* Automatically constructs caller/callee dependency graphs (`dependency_graph.py`) to map function interactions across modules.

### ⏳ 2. Git Lineage Mining & Line-Range Blame
* Performs historical git diff mining and line-range blame tracing (`git log -L <start>,<end>:<file>`).
* Maps current functions to their exact origins, authorship history, and evolution rationale.

### 🔀 3. Two-Stage Hybrid Retrieval & Cross-Encoder Reranking
* **Stage 1 (Hybrid RRF)**: Combines dense vector similarity (Gemini `text-embedding-004` or FastEmbed `BAAI/bge-small-en-v1.5`) with sparse keyword matching (BM25 Okapi) using Reciprocal Rank Fusion ($k=60$).
* **Stage 2 (Reranking)**: Cross-encoder style term-density scoring and exact symbol overlap boosting ($+0.05$ symbol bonus) to ensure high-precision code retrieval.

### 🔮 4. Hypothetical Document Embeddings (HyDE)
* Expands developer questions into hallucinated ideal code snippets before searching, bridging the semantic gap between conceptual natural-language questions and actual implementation syntax.

### 🏥 5. Codebase Health Auditor & Technical Debt Scoring
* Identifies architectural "god files", hotspots with high churn, orphaned modules with zero callers, and untyped functions.
* Generates an automated **Codebase Health & Risk Score (0-100)** with prioritized refactoring recommendations.

### ☁️ 6. Cloud Persistence with Supabase `pgvector`
* Persists vector embeddings and metadata in Supabase PostgreSQL using 768-dimensional `vector(768)` columns and HNSW cosine similarity search.
* Logs historical user queries and synthesized architectural answers in `excavation_history` for persistent recall without repeating LLM costs.

### 📊 7. Automated Mermaid.js Architecture Diagrams
* Automatically inspects module dependencies and exports live, renderable **Mermaid.js Component Architecture Diagrams**.

---

## 🛠️ Technology Stack

| Domain | Technologies |
| :--- | :--- |
| **Language & Core** | Python 3.10+, AST (`ast`), GitPython, Pydantic v2 |
| **Vector Databases** | **Supabase (`pgvector` HNSW)**, **Qdrant Cloud** |
| **AI & Embeddings** | **Google Gemini 1.5 Flash**, `text-embedding-004`, FastEmbed |
| **Lexical Search** | Rank-BM25 Okapi |
| **Interfaces** | Streamlit Community Cloud, Next.js 14, FastAPI, Typer CLI |
| **Visualizations** | Altair, Mermaid.js, Rich terminal renderer |
| **Testing & CI/CD** | Pytest, GitHub Actions CI/CD |

---

## 🚀 Quickstart Guide

### Option A: Use the Live Web Application
Visit the live, hosted application without installing anything locally:  
👉 **[codebase-archaeologists.streamlit.app](https://codebase-archaeologists.streamlit.app/)**

---

### Option B: Run Locally

#### 1. Clone the Repository
```bash
git clone https://github.com/aakansha109/codebase-archaeologist.git
cd codebase-archaeologist
```

#### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

#### 3. Set Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash

# Optional: Supabase Cloud Persistence
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

#### 4. Launch the Interactive Streamlit App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 💻 Developer CLI Toolkit

The Codebase Archaeologist includes a full-featured CLI:

```bash
# Ingest and excavate a Git repository
archaeologist ingest https://github.com/paperclipai/paperclip

# Ask an architectural question
archaeologist query "How does authentication work?" --top-k 4

# Run a technical debt and codebase health audit
archaeologist health

# Export a comprehensive Markdown excavation briefing
archaeologist export --output report.md

# Run RAG Triad benchmark evaluation
archaeologist eval --question "How does AST parsing work?"
```

---

## ⚡ REST API Server (FastAPI)

Launch the headless production REST API:
```bash
uvicorn archaeologist.api.server:app --host 0.0.0.0 --port 8000
```

Interactive OpenAPI Swagger documentation is available at `http://localhost:8000/docs`:
* `POST /api/v1/ingest` - Clone, chunk, mine lineage, and index repository
* `POST /api/v1/query` - Perform HyDE hybrid search and Gemini architectural synthesis
* `GET /api/v1/health` - Retrieve technical debt risk score and hotspots
* `GET /api/v1/diagram` - Generate Mermaid.js architecture diagram code

---

## 🧪 Automated Test Suite

The codebase maintains automated unit and integration tests across AST parsing, vector stores, git extraction, dependency analysis, and API endpoints:

```bash
pytest -v
```

```text
============================= test session starts =============================
collected 19 items

tests/test_api.py .............. PASSED                                  [ 10%]
tests/test_ast_parser.py ....... PASSED                                  [ 31%]
tests/test_cli.py .............. PASSED                                  [ 42%]
tests/test_dependency_graph.py . PASSED                                  [ 47%]
tests/test_git_extractor.py .... PASSED                                  [ 52%]
tests/test_health_auditor.py ... PASSED                                  [ 57%]
tests/test_report_exporter.py .. PASSED                                  [ 63%]
tests/test_retriever.py ........ PASSED                                  [ 68%]
tests/test_supabase_store.py ... PASSED                                  [ 73%]
tests/test_synthesizer.py ...... PASSED                                  [ 89%]
tests/test_vector_store.py ..... PASSED                                  [100%]

======================= 19 passed in 10.40s =======================
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

Developed with ❤️ by [Aakansha Sharma](https://github.com/aakansha109).
