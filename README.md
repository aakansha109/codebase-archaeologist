 The Codebase Archaeologist 🏛️🔍

An advanced RAG & Vector Search engine designed for deep code exploration and historical lineage querying. Instead of a basic "chat with my codebase" tool, **The Codebase Archaeologist** ingests entire Git repositories (AST code chunks, commit history, and PR context) to answer complex architectural and historical questions.

## ✨ Key Features

- **AST Code Chunking**: Uses Python's native `ast` parser to intelligently chunk code along logical boundaries (functions, classes, methods), preserving signatures, docstrings, and line numbers.
- **Git History Mining**: Extracts commit metadata, diff logs, and file modification histories via `GitPython` to understand *why* code changed over time.
- **Hybrid Vector Search**: Combines semantic embedding search (via Qdrant & FastEmbed) with exact keyword search (BM25) using Reciprocal Rank Fusion (RRF).


