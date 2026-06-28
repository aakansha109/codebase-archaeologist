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

    def generate_briefing(self, stats: dict, top_files: List[tuple], recent_commits: List[dict]) -> str:
        """Generates an auto-generated structural and historical 'Archaeologist's Briefing' on load."""
        files_str = "\n".join([f"- `{f[0]}` ({f[1]} chunks)" for f in top_files[:3]])
        commits_str = "\n".join([f"- `[{c['commit_hash'] if isinstance(c, dict) else c.commit_hash}]` {c['message'][:60] if isinstance(c, dict) else c.message[:60]}" for c in recent_commits[:3]])
        
        offline_briefing = (
            "### 🏛️ Repository Excavation Briefing (Offline)\n\n"
            f"**Mined Commits**: {stats.get('commits_mined', 0)} | **AST Chunks**: {stats.get('chunks_indexed', 0)}\n\n"
            f"#### Top Active Files:\n{files_str}\n\n"
            f"#### Recent Commits Mined:\n{commits_str}\n\n"
            "*(Note: Export GEMINI_API_KEY for a deep, AI-synthesized architectural summary!)*"
        )
        
        if not self.llm or self.provider != "gemini":
            return offline_briefing
            
        top_files_text = "\n".join([f"- {f[0]} ({f[1]} AST chunks)" for f in top_files])
        commits_text = "\n".join([f"- [{c['commit_hash'] if isinstance(c, dict) else c.commit_hash}] by {c['author'] if isinstance(c, dict) else c.author}: {c['message'] if isinstance(c, dict) else c.message}" for c in recent_commits[:5]])
        
        prompt = (
            "You are 'The Codebase Archaeologist'. Analyze the following repository excavation stats, "
            "top active files (with AST chunks count), and recent git commits to generate a professional, "
            "insightful 2-3 paragraph 'Repository Excavation Briefing' for a software architect onboarding to the project.\n\n"
            f"**Excavation Stats**: Mined Commits: {stats.get('commits_mined', 0)}, AST Chunks: {stats.get('chunks_indexed', 0)}\n\n"
            f"**Top Indexed Files**:\n{top_files_text}\n\n"
            f"**Recent Commits**:\n{commits_text}\n\n"
            "Format your response in beautiful, clean Markdown. Keep it structured, engaging, and professional."
        )
        
        import time
        for attempt in range(4):
            try:
                response = self.llm.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                if attempt < 3:
                    time.sleep(2.0 ** attempt)
                else:
                    # Fallback to offline briefing with a warning note
                    return (
                        "### 🏛️ Repository Excavation Briefing (Offline Fallback)\n\n"
                        "⚠️ *Gemini API is temporarily experiencing high demand (503). Showing local fallback briefing:*\n\n"
                        f"**Mined Commits**: {stats.get('commits_mined', 0)} | **AST Chunks**: {stats.get('chunks_indexed', 0)}\n\n"
                        f"#### Top Active Files:\n{files_str}\n\n"
                        f"#### Recent Commits Mined:\n{commits_str}"
                    )

    def explain_diff(self, file_path: str, commit_a: str, commit_b: str, diff_content: str) -> str:
        """Explains a Git diff in natural language."""
        if not diff_content.strip() or diff_content.startswith("Error retrieving diff"):
            return "No valid diff content to analyze."
            
        offline_explanation = (
            "### 🔍 Diff Explanation (Offline fallback)\n\n"
            "**Offline Mode**: Export a live API key to get a deep semantic explanation of the changes.\n\n"
            f"Showing raw diff characters length: {len(diff_content)}"
        )
        
        if not self.llm or self.provider != "gemini":
            return offline_explanation
            
        prompt = (
            "You are a senior software engineer conducting a code review and auditing git history. "
            f"Explain the following Git diff for the file `{file_path}` between commit `{commit_a}` and commit `{commit_b}` "
            "in clear, natural developer language. Summarize: \n"
            "1. What changed logically/structurally.\n"
            "2. Why the change was made (infer from the code structure and any context).\n"
            "3. Any architectural implications or potential issues.\n\n"
            f"**Raw Git Diff**:\n```diff\n{diff_content[:3000]}\n```"
        )
        
        import time
        for attempt in range(4):
            try:
                response = self.llm.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                if attempt < 3:
                    time.sleep(2.0 ** attempt)
                else:
                    return (
                        "### 🔍 Diff Explanation (Offline Fallback)\n\n"
                        "⚠️ *Gemini API is temporarily experiencing high demand (503). Showing raw git diff:*\n\n"
                        f"```diff\n{diff_content[:2000]}\n```"
                    )
