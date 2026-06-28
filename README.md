# Showpiece 1: The Codebase Archaeologist 🏛️🔍

An advanced RAG & Vector Search engine designed for deep code exploration and historical lineage querying. Instead of a basic "chat with my codebase" tool, **The Codebase Archaeologist** ingests entire Git repositories (AST code chunks, commit history, and PR context) to answer complex architectural and historical questions.

## ✨ Key Features

- **AST Code Chunking**: Uses Python's native `ast` parser to intelligently chunk code along logical boundaries (functions, classes, methods), preserving signatures, docstrings, and line numbers.
- **Git History Mining**: Extracts commit metadata, diff logs, and file modification histories via `GitPython` to understand *why* code changed over time.
- **Hybrid Vector Search**: Combines semantic embedding search (via Qdrant & FastEmbed) with exact keyword search (BM25) using Reciprocal Rank Fusion (RRF).
- **Dual Interface**: Includes both a developer-friendly terminal CLI (`Rich` + `Typer`) and an interactive visual web dashboard (`Streamlit`).

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -e .
```

### 2. Run CLI
```bash
# Ingest a repository
archaeologist ingest https://github.com/paperclipai/paperclip

# Ask an archaeological question
archaeologist ask "Why did we choose Redis or make architectural changes in this repo?"
```

### 3. Launch Web Dashboard
```bash
streamlit run app.py
```
