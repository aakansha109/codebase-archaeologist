import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CodeChunk(BaseModel):
    """Represents a semantically bounded chunk of source code."""
    chunk_id: str
    file_path: str
    language: str
    chunk_type: str  # function, class, method, module_block
    name: str
    content: str
    docstring: Optional[str] = None
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ASTCodeParser:
    """Parses codebases using AST for Python and structural regex fallback for JS/TS."""
    
    def parse_file(self, file_path: Path, relative_to: Path) -> List[CodeChunk]:
        """Reads a file and chunks it based on language."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return []
            
        rel_path = str(file_path.relative_to(relative_to)).replace("\\", "/")
        ext = file_path.suffix.lower()
        
        js_patterns = [
            (r"\bclass\s+([a-zA-Z0-9_]+)", "class"),
            (r"\binterface\s+([a-zA-Z0-9_]+)", "interface"),
            (r"\btype\s+([a-zA-Z0-9_]+)\s*=", "type"),
            (r"\bfunction\s+([a-zA-Z0-9_]+)\b", "function"),
            (r"\bconst\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>", "function"),
        ]
        
        go_patterns = [
            (r"func\s+(?:\(.*?\)\s*)?([a-zA-Z0-9_]+)\s*\(", "function"),
            (r"type\s+([a-zA-Z0-9_]+)\s+(?:struct|interface)\b", "type"),
        ]
        
        rust_patterns = [
            (r"\bstruct\s+([a-zA-Z0-9_]+)", "struct"),
            (r"\benum\s+([a-zA-Z0-9_]+)", "enum"),
            (r"\btrait\s+([a-zA-Z0-9_]+)", "trait"),
            (r"\bfn\s+([a-zA-Z0-9_]+)", "function"),
            (r"\bimpl(?:\s+.*?)?\s+([a-zA-Z0-9_]+)\b", "impl"),
            (r"\bmod\s+([a-zA-Z0-9_]+)\s*\{", "module"),
        ]
        
        if ext == ".py":
            return self._parse_python(content, rel_path)
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return self._parse_brace_language(content, rel_path, ext[1:], js_patterns)
        elif ext == ".go":
            return self._parse_brace_language(content, rel_path, "go", go_patterns)
        elif ext == ".rs":
            return self._parse_brace_language(content, rel_path, "rust", rust_patterns)
        else:
            return self._parse_generic(content, rel_path, ext[1:] if ext else "text")

    def _parse_python(self, content: str, rel_path: str) -> List[CodeChunk]:
        chunks: List[CodeChunk] = []
        lines = content.splitlines(keepends=True)
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._parse_generic(content, rel_path, "python")
            
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", len(lines))
                
                # Extract exact lines (1-indexed)
                snippet = "".join(lines[start-1:end])
                docstring = ast.get_docstring(node)
                chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
                
                chunk_id = f"{rel_path}::{node.name}::L{start}-L{end}"
                chunks.append(CodeChunk(
                    chunk_id=chunk_id,
                    file_path=rel_path,
                    language="python",
                    chunk_type=chunk_type,
                    name=node.name,
                    content=snippet,
                    docstring=docstring,
                    start_line=start,
                    end_line=end,
                    metadata={"args": [a.arg for a in getattr(node.args, 'args', [])]} if hasattr(node, 'args') else {}
                ))
                
                # If it's a class, also extract individual methods
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            m_start = getattr(item, "lineno", start)
                            m_end = getattr(item, "end_lineno", end)
                            m_snippet = "".join(lines[m_start-1:m_end])
                            m_doc = ast.get_docstring(item)
                            chunks.append(CodeChunk(
                                chunk_id=f"{rel_path}::{node.name}.{item.name}::L{m_start}-L{m_end}",
                                file_path=rel_path,
                                language="python",
                                chunk_type="method",
                                name=f"{node.name}.{item.name}",
                                content=m_snippet,
                                docstring=m_doc,
                                start_line=m_start,
                                end_line=m_end,
                                metadata={"parent_class": node.name}
                            ))
                            
        # If no functions/classes found or small file, add module block
        if not chunks and content.strip():
            chunks.append(CodeChunk(
                chunk_id=f"{rel_path}::module::L1-L{len(lines)}",
                file_path=rel_path,
                language="python",
                chunk_type="module",
                name=Path(rel_path).stem,
                content=content,
                start_line=1,
                end_line=len(lines)
            ))
            
        return chunks

    def _find_block_boundary(self, lines: List[str], start_idx: int) -> int:
        """Finds the ending line index (0-indexed) of a brace-bounded block."""
        brace_count = 0
        started = False
        in_multiline_comment = False
        
        for j in range(start_idx, len(lines)):
            line = lines[j]
            k = 0
            while k < len(line):
                # Handle multi-line comments
                if in_multiline_comment:
                    if k < len(line) - 1 and line[k] == '*' and line[k+1] == '/':
                        in_multiline_comment = False
                        k += 2
                    else:
                        k += 1
                    continue
                
                if k < len(line) - 1 and line[k] == '/' and line[k+1] == '*':
                    in_multiline_comment = True
                    k += 2
                    continue
                if k < len(line) - 1 and line[k] == '/' and line[k+1] == '/':
                    break
                    
                # Handle string literals
                if line[k] in ['"', "'", '`']:
                    quote = line[k]
                    k += 1
                    while k < len(line) and line[k] != quote:
                        if line[k] == '\\':
                            k += 2
                        else:
                            k += 1
                    k += 1
                    continue
                    
                if line[k] == '{':
                    started = True
                    brace_count += 1
                elif line[k] == '}':
                    brace_count -= 1
                    if started and brace_count <= 0:
                        return j
                k += 1
                
        return len(lines) - 1

    def _parse_brace_language(self, content: str, rel_path: str, lang: str, patterns: List[tuple]) -> List[CodeChunk]:
        """Generic brace-matching structural chunker for JS/TS, Go, and Rust."""
        chunks: List[CodeChunk] = []
        lines = content.splitlines(keepends=True)
        compiled_patterns = [(re.compile(pat), ctype) for pat, ctype in patterns]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            matched = False
            for pattern, chunk_type in compiled_patterns:
                match = pattern.search(line)
                if match:
                    name = match.group(1)
                    start_line = i + 1
                    end_idx = self._find_block_boundary(lines, i)
                    end_line = end_idx + 1
                    
                    # Ensure snippet is non-empty
                    snippet = "".join(lines[i:end_line])
                    chunk_id = f"{rel_path}::{name}::L{start_line}-L{end_line}"
                    chunks.append(CodeChunk(
                        chunk_id=chunk_id,
                        file_path=rel_path,
                        language=lang,
                        chunk_type=chunk_type,
                        name=name,
                        content=snippet,
                        start_line=start_line,
                        end_line=end_line
                    ))
                    i = end_line - 1
                    matched = True
                    break
            if not matched:
                i += 1
                
        if not chunks and content.strip():
            return self._parse_generic(content, rel_path, lang)
        return chunks

    def _parse_generic(self, content: str, rel_path: str, lang: str) -> List[CodeChunk]:
        """Simple line-window chunker for unsupported or plain text files."""
        lines = content.splitlines()
        chunk_size = 150
        chunks = []
        
        for i in range(0, len(lines), chunk_size):
            window = lines[i:i+chunk_size]
            if not window:
                continue
            start = i + 1
            end = i + len(window)
            chunks.append(CodeChunk(
                chunk_id=f"{rel_path}::chunk_{start}::L{start}-L{end}",
                file_path=rel_path,
                language=lang,
                chunk_type="text_window",
                name=f"{Path(rel_path).stem}_L{start}_{end}",
                content="\n".join(window),
                start_line=start,
                end_line=end
            ))
        return chunks
