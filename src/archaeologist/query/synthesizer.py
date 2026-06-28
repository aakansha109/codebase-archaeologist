import os
from typing import List
from archaeologist.config import settings
from archaeologist.store.vector_store import SearchResult

class CodeArchaeologistSynthesizer:
    """Synthesizes historical code lineage and AST snippets into architectural explanations."""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.llm = self._init_llm()

    def _init_llm(self):
        """Initializes LLM backend if API keys are present."""
        if self.provider == "gemini" and (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            try:
                from google import genai
                # genai.Client automatically picks up GEMINI_API_KEY
                return genai.Client()
            except Exception as e:
                print(f"Error initializing GenAI Client: {e}")
                pass
        elif self.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.2)
            except Exception:
                pass
        return None

    def synthesize(self, query: str, context_results: List[SearchResult]) -> str:
        """Generates the archaeological response."""
        if not context_results:
            return "No relevant code chunks or commit lineage found for this query."
            
        # Format context blocks
        formatted_blocks = []
        for i, res in enumerate(context_results, 1):
            lineage_text = "No commit history found."
            if res.lineage:
                commits = [f"[{c['commit_hash']}] {c['date'][:10]} by {c['author']}: {c['message']}" for c in res.lineage[:3]]
                lineage_text = "\n    ".join(commits)
                
            block = (
                f"### Evidence {i}: {res.name} ({res.chunk_type})\n"
                f"- **File**: `{res.file_path}` (Lines {res.start_line}-{res.end_line})\n"
                f"- **Hybrid Score**: {res.score}\n"
                f"- **Recent Commit Lineage**:\n    {lineage_text}\n"
                f"- **Code Snippet**:\n```python\n{res.content[:800]}\n```"
            )
            formatted_blocks.append(block)
            
        context_str = "\n\n".join(formatted_blocks)
        
        system_prompt = (
            "You are 'The Codebase Archaeologist', an expert senior software engineer and software historian. "
            "Your job is to answer historical and structural context questions about a code repository based on retrieved AST code snippets and Git commit lineage.\n\n"
            "Guidelines:\n"
            "1. Analyze the provided code chunks, docstrings, and commit messages.\n"
            "2. Explain *why* certain architectural choices exist or map out dependencies accurately.\n"
            "3. Cite specific filenames, line numbers, and commit hashes as evidence.\n"
            "4. Keep the tone professional, insightful, and concise."
        )
        
        user_prompt = f"Question: {query}\n\nRetrieved Codebase Evidence:\n{context_str}\n\nProvide your archaeological analysis:"
        
        if self.llm:
            try:
                if self.provider == "gemini":
                    import time
                    for attempt in range(4):
                        try:
                            # Using official google-genai SDK model inference
                            response = self.llm.models.generate_content(
                                model=settings.GEMINI_MODEL,
                                contents=system_prompt + "\n\n" + user_prompt,
                            )
                            return response.text
                        except Exception as e:
                            print(f"Error during Gemini LLM invoke (attempt {attempt+1}/4): {e}")
                            if attempt < 3:
                                time.sleep(1.5 ** attempt)
                            else:
                                raise e
                else:
                    response = self.llm.invoke([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ])
                    return response.content
            except Exception as e:
                print(f"Error during LLM invoke: {e}")
                pass
                
        # Fallback offline synthesis
        analysis = [
            f"🏛️ **Offline Archaeological Analysis** for query: *\"{query}\"*",
            "\n*(Note: LLM API key not detected; displaying direct synthesis of retrieved AST code & Git lineage)*\n",
            "### 🔍 Key Structural Findings & Lineage Evidence:"
        ]
        for i, res in enumerate(context_results, 1):
            latest_commit = res.lineage[0]['message'] if res.lineage else "No recent commit message recorded"
            commit_hash = res.lineage[0]['commit_hash'] if res.lineage else "N/A"
            analysis.append(
                f"**{i}. `{res.name}` in `{res.file_path}` (L{res.start_line}-{res.end_line})**\n"
                f"   - **Context**: {res.chunk_type.capitalize()} matching exact keyword/semantic profile (Score: {res.score}).\n"
                f"   - **Historical Commit Snapshot (`{commit_hash}`)**: *\"{latest_commit}\"*"
            )
        analysis.append("\n💡 **Conclusion**: The architectural footprint spans the modules highlighted above. To unlock AI-powered deep semantic explanations, export `GEMINI_API_KEY` or `OPENAI_API_KEY`.")
        return "\n".join(analysis)
