import re
from typing import List, Dict, Set, Any
from archaeologist.ingest.ast_parser import CodeChunk

class CodeDependencyGraph:
    """Indexes symbol declarations, module imports, and caller/callee cross-references."""
    
    def __init__(self, chunks: List[CodeChunk] = None):
        self.symbol_map: Dict[str, CodeChunk] = {}
        self.file_imports: Dict[str, Set[str]] = {}
        self.call_graph: Dict[str, Set[str]] = {}
        if chunks:
            self.build_graph(chunks)

    def build_graph(self, chunks: List[CodeChunk]):
        """Constructs the in-memory dependency graph across all AST code chunks."""
        self.symbol_map = {chunk.name: chunk for chunk in chunks if chunk.name}
        self.file_imports = {}
        self.call_graph = {}

        # 1. Parse imports per file
        import_regex = re.compile(
            r'(?:import\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]|'
            r'from\s+([a-zA-Z0-9_.]+)\s+import|'
            r'import\s+([a-zA-Z0-9_.]+)|'
            r'require\([\'"]([^\'"]+)[\'"]\))'
        )

        for chunk in chunks:
            if chunk.file_path not in self.file_imports:
                self.file_imports[chunk.file_path] = set()
            
            for match in import_regex.finditer(chunk.content):
                imp = next((g for g in match.groups() if g is not None), None)
                if imp:
                    self.file_imports[chunk.file_path].add(imp)

        # 2. Build cross-reference call graph between symbol definitions
        all_symbol_names = set(self.symbol_map.keys())
        for name, chunk in self.symbol_map.items():
            self.call_graph[name] = set()
            for other_name in all_symbol_names:
                if name != other_name and len(other_name) > 2:
                    # Check if symbol appears in chunk content
                    if re.search(r'\b' + re.escape(other_name) + r'\b', chunk.content):
                        self.call_graph[name].add(other_name)

    def get_related_symbols(self, symbol_name: str, file_path: str = "") -> Dict[str, List[str]]:
        """Returns related dependencies (callers and callees) for a target symbol."""
        callees = list(self.call_graph.get(symbol_name, set()))[:5]
        callers = [
            caller for caller, targets in self.call_graph.items()
            if symbol_name in targets and caller != symbol_name
        ][:5]
        
        file_deps = list(self.file_imports.get(file_path, set()))[:5] if file_path else []
        
        return {
            "callees": callees,
            "callers": callers,
            "file_imports": file_deps
        }
