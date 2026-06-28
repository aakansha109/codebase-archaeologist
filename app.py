import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import altair as alt
from archaeologist.query.retriever import CodebaseRetriever
from archaeologist.query.synthesizer import CodeArchaeologistSynthesizer

st.set_page_config(
    page_title="The Codebase Archaeologist 🏛️",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Custom CSS Styling (Dark Theme, Glassmorphism, Neon Accents, Custom Font)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700&family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Background & Typography */
    .stApp {
        background: linear-gradient(135deg, #09090e 0%, #120e2e 50%, #09090e 100%);
        color: #f8fafc;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Custom headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Title Styling */
    .hero-title {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.15rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(129, 140, 248, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(129, 140, 248, 0.15);
    }
    
    /* Key Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Space Grotesk', sans-serif;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
        font-weight: 600;
    }
    
    /* Evidence Badge */
    .badge {
        background: linear-gradient(135deg, #38bdf8, #6366f1);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Timeline styling */
    .timeline-container {
        padding-left: 10px;
        margin-top: 1.5rem;
    }
    .timeline-item {
        border-left: 2px solid rgba(129, 140, 248, 0.3);
        padding-left: 1.5rem;
        position: relative;
        padding-bottom: 1.5rem;
    }
    .timeline-item:last-child {
        border-left: 2px solid transparent;
    }
    .timeline-dot {
        width: 12px;
        height: 12px;
        background: #818cf8;
        border-radius: 50%;
        position: absolute;
        left: -7px;
        top: 6px;
        box-shadow: 0 0 10px #818cf8, 0 0 20px #818cf8;
        transition: all 0.3s ease;
    }
    .timeline-item:hover .timeline-dot {
        background: #38bdf8;
        box-shadow: 0 0 12px #38bdf8, 0 0 25px #38bdf8;
        transform: scale(1.2);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(9, 9, 14, 0.85) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    /* Tabs custom border styling */
    div[data-baseweb="tab-list"] {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #818cf8 !important;
        border-bottom-color: #818cf8 !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_retriever():
    return CodebaseRetriever()

# Initialize Session State
if "retriever" not in st.session_state:
    st.session_state.retriever = get_retriever()

# Auto-detect cached database
if "ingested" not in st.session_state:
    if st.session_state.retriever.store.chunks:
        st.session_state.ingested = True
        st.session_state.stats = {
            "commits_mined": len(st.session_state.retriever.store.lineage_map.values()) or "300 (Cached)",
            "chunks_indexed": len(st.session_state.retriever.store.chunks)
        }
    else:
        st.session_state.ingested = False

if "stats" not in st.session_state:
    st.session_state.stats = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_results" not in st.session_state:
    st.session_state.last_results = []

# Sidebar - Ingestion Controls
with st.sidebar:
    st.markdown("### ⚙️ Repository Excavation")
    repo_input = st.text_input(
        "Target Repository URL or Path",
        value="https://github.com/paperclipai/paperclip",
        help="Git URL or local folder path"
    )
    
    if st.button("🚀 Excavate & Index", use_container_width=True, type="primary"):
        with st.status(" Excavating codebase...", expanded=True) as status:
            st.write("Cloning repository & mining Git commit lineage...")
            stats = st.session_state.retriever.ingest_repository(
                repo_input,
                progress_callback=lambda m: st.write(f"⏳ {m}")
            )
            st.session_state.stats = stats
            st.session_state.ingested = True
            status.update(label="✔ Excavation Complete!", state="complete", expanded=False)
            st.success("Codebase successfully indexed into Qdrant!")
            
    if st.session_state.ingested and st.session_state.stats:
        st.markdown("---")
        st.markdown("#### 📊 Current Metrics")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.stats.get("commits_mined", 0)}</div>
                <div class="metric-label">Commits Mined</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.stats.get("chunks_indexed", 0)}</div>
                <div class="metric-label">AST Chunks</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Background Auto-Briefing Generation
        chunks = list(st.session_state.retriever.store.chunks.values())
        if chunks and "briefing" not in st.session_state:
            file_chunk_counts = {}
            for chunk in chunks:
                file_chunk_counts[chunk.file_path] = file_chunk_counts.get(chunk.file_path, 0) + 1
            top_files = sorted(file_chunk_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            commits = []
            if st.session_state.retriever.extractor:
                try:
                    commits = st.session_state.retriever.extractor.mine_commit_history(max_commits=10)
                except Exception:
                    pass
            if not commits and st.session_state.retriever.store.lineage_map:
                unique_commits = {}
                for file_path, file_commits in st.session_state.retriever.store.lineage_map.items():
                    for c in file_commits:
                        unique_commits[c["commit_hash"]] = c
                commits = sorted(unique_commits.values(), key=lambda x: x.get("date", ""), reverse=True)[:10]
                
            synthesizer = CodeArchaeologistSynthesizer()
            with st.spinner("Analyzing repository briefing..."):
                briefing_text = synthesizer.generate_briefing(st.session_state.stats, top_files, commits)
                st.session_state.briefing = briefing_text
                
        # Export Report Button
        if "briefing" in st.session_state:
            report_text = f"""# Archaeological Excavation Report: {repo_input}

## Repository Summary
- **Commits Mined**: {st.session_state.stats.get("commits_mined", 0)}
- **AST Chunks Mined**: {st.session_state.stats.get("chunks_indexed", 0)}

## Executive Briefing
{st.session_state.briefing}

## Q&A Exploration History
"""
            for msg in st.session_state.chat_history:
                role_name = "User" if msg["role"] == "user" else "Archaeologist Assistant"
                report_text += f"\n### {role_name}\n{msg['content']}\n"
                
            st.markdown("---")
            st.download_button(
                label="📥 Export Archaeology Report",
                data=report_text,
                file_name="archaeology_report.md",
                mime="text/markdown",
                use_container_width=True
            )

# Main Hero Header
st.markdown('<div class="hero-title">The Codebase Archaeologist 🏛️</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Uncover technical debt, architectural evolution, and historical context across entire Git repositories.</div>', unsafe_allow_html=True)

if not st.session_state.ingested:
    st.info("👈 Please click **Excavate & Index** in the sidebar to ingest `https://github.com/paperclipai/paperclip` or your chosen repository.")
else:
    # Set up Tabs
    tab_search, tab_timeline, tab_diff, tab_analytics = st.tabs([
        "🏛️ Archaeological Search", 
        "⏳ Git Lineage Timeline", 
        "🔍 Semantic Diff Explainer",
        "📊 Codebase Analytics"
    ])
    
    # ------------------ TAB 1: SEARCH & CHAT ------------------
    with tab_search:
        if "briefing" in st.session_state:
            with st.expander("🏛️ View Excavation Briefing", expanded=True):
                st.markdown(st.session_state.briefing)
                
        # Query Interface
        query = st.chat_input("Ask an archaeological question (e.g. 'Why did we choose Redis or make architectural changes?')")
        
        # Display Chat History
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "evidence" in msg and msg["evidence"]:
                    with st.expander("🔍 View Retrieved AST Evidence & Lineage"):
                        for ev in msg["evidence"]:
                            st.markdown(f"""
                            <div class="glass-card">
                                <span class="badge">{ev.chunk_type.upper()} • Score: {ev.score}</span>
                                <h4><code>{ev.name}</code> in <em>{ev.file_path}</em> (L{ev.start_line}-{ev.end_line})</h4>
                                <p><strong>⏳ Recent Commit Lineage:</strong></p>
                                <ul>
                            """ + "".join([f"<li><code>{c['commit_hash']}</code> ({c['date'][:10]}): {c['message']}</li>" for c in ev.lineage[:3]]) + f"""
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            st.code(ev.content[:800], language=ev.language)
                            
        if query:
            # Add user query
            st.session_state.chat_history.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
                
            with st.chat_message("assistant"):
                with st.spinner("Excavating evidence & synthesizing historical answer..."):
                    results = st.session_state.retriever.retrieve(query, top_k=4)
                    synthesizer = CodeArchaeologistSynthesizer()
                    answer = synthesizer.synthesize(query, results)
                    st.session_state.last_results = results
                    
                st.markdown(answer)
                
                if results:
                    with st.expander("🔍 View Retrieved AST Evidence & Lineage", expanded=True):
                        for ev in results:
                            st.markdown(f"""
                            <div class="glass-card">
                                <span class="badge">{ev.chunk_type.upper()} • Score: {ev.score}</span>
                                <h4><code>{ev.name}</code> in <em>{ev.file_path}</em> (L{ev.start_line}-{ev.end_line})</h4>
                                <p><strong>⏳ Recent Commit Lineage:</strong></p>
                                <ul>
                            """ + "".join([f"<li><code>{c['commit_hash']}</code> ({c['date'][:10]}): {c['message']}</li>" for c in ev.lineage[:3]]) + f"""
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            st.code(ev.content[:800], language=ev.language)
                            
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "evidence": results
                })
                
        # Side-by-Side Comparison of last search results
        if st.session_state.last_results:
            st.markdown("---")
            st.markdown("### ⚖️ Side-by-Side AST Comparison")
            res_names = [f"{r.name} ({r.chunk_type})" for r in st.session_state.last_results]
            
            comp_col1, comp_col2 = st.columns(2)
            with comp_col1:
                choice1 = st.selectbox("Select Left Chunk", res_names, index=0, key="left_choice")
            with comp_col2:
                choice2 = st.selectbox("Select Right Chunk", res_names, index=min(1, len(res_names)-1), key="right_choice")
                
            chunk1 = next(r for r in st.session_state.last_results if f"{r.name} ({r.chunk_type})" == choice1)
            chunk2 = next(r for r in st.session_state.last_results if f"{r.name} ({r.chunk_type})" == choice2)
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown(f"""
                <div class="glass-card" style="border-top: 4px solid #38bdf8;">
                    <span class="badge" style="background:#38bdf8;">{chunk1.chunk_type.upper()}</span>
                    <h4><code>{chunk1.name}</code></h4>
                    <p style="font-size:0.9rem; color:#94a3b8;"><strong>File</strong>: <code>{chunk1.file_path}</code> (L{chunk1.start_line}-{chunk1.end_line})</p>
                    <p style="font-size:0.9rem; color:#94a3b8;"><strong>RRF Score</strong>: <code style="color:#38bdf8; font-weight:bold;">{chunk1.score}</code></p>
                </div>
                """, unsafe_allow_html=True)
                st.code(chunk1.content, language=chunk1.language)
            with col_c2:
                st.markdown(f"""
                <div class="glass-card" style="border-top: 4px solid #a855f7;">
                    <span class="badge" style="background:#a855f7;">{chunk2.chunk_type.upper()}</span>
                    <h4><code>{chunk2.name}</code></h4>
                    <p style="font-size:0.9rem; color:#94a3b8;"><strong>File</strong>: <code>{chunk2.file_path}</code> (L{chunk2.start_line}-{chunk2.end_line})</p>
                    <p style="font-size:0.9rem; color:#94a3b8;"><strong>RRF Score</strong>: <code style="color:#a855f7; font-weight:bold;">{chunk2.score}</code></p>
                </div>
                """, unsafe_allow_html=True)
                st.code(chunk2.content, language=chunk2.language)
                
    # ------------------ TAB 2: GIT LINEAGE TIMELINE ------------------
    with tab_timeline:
        st.markdown("### ⏳ Repository Commit Timeline")
        st.markdown("Browse through the overall historical commits mined from the repository.")
        
        commits = []
        if st.session_state.retriever.extractor:
            try:
                commits = st.session_state.retriever.extractor.mine_commit_history(max_commits=100)
            except Exception:
                pass
                
        if not commits and st.session_state.retriever.store.lineage_map:
            # Fallback to cached lineage map
            unique_commits = {}
            for file_path, file_commits in st.session_state.retriever.store.lineage_map.items():
                for c in file_commits:
                    unique_commits[c["commit_hash"]] = c
            commits = sorted(unique_commits.values(), key=lambda x: x.get("date", ""), reverse=True)
            
        if commits:
            search_timeline = st.text_input("🔍 Filter commits by message or author...")
            
            st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
            count = 0
            for c in commits:
                msg = c.message if hasattr(c, 'message') else c.get('message', '')
                author = c.author if hasattr(c, 'author') else c.get('author', '')
                commit_hash = c.commit_hash if hasattr(c, 'commit_hash') else c.get('commit_hash', '')
                date = c.date if hasattr(c, 'date') else c.get('date', '')
                files_changed = c.files_changed if hasattr(c, 'files_changed') else c.get('files_changed', [])
                
                if search_timeline:
                    if search_timeline.lower() not in msg.lower() and search_timeline.lower() not in author.lower():
                        continue
                        
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div style="font-weight:bold; color:#f8fafc; font-size:1.1rem; font-family:'Space Grotesk', sans-serif;">{msg}</div>
                    <div style="font-size:0.85rem; color:#94a3b8; margin: 4px 0;">
                        <code>{commit_hash}</code> • {date[:10]} • by <strong>{author}</strong>
                    </div>
                    <div style="font-size:0.8rem; color:#818cf8;">
                        📁 {len(files_changed)} files modified
                    </div>
                </div>
                """, unsafe_allow_html=True)
                count += 1
                if count >= 30:  # Display top 30
                    break
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No commit lineage history is currently available. Excavate the repository first.")
            
    # ------------------ TAB 3: SEMANTIC DIFF EXPLAINER ------------------
    with tab_diff:
        st.markdown("### 🔍 Semantic Diff Explainer")
        st.markdown("Select a file and compare two historical commits to get a natural language AI explanation of what changed and why.")
        
        chunks = list(st.session_state.retriever.store.chunks.values())
        if chunks:
            unique_files = sorted(list(set(c.file_path for c in chunks)))
            selected_file = st.selectbox("Select File to Audit", unique_files, key="diff_file_select")
            
            # Fetch commits
            commits = []
            if st.session_state.retriever.extractor:
                try:
                    commits = st.session_state.retriever.extractor.mine_commit_history(max_commits=100)
                except Exception:
                    pass
            if not commits and st.session_state.retriever.store.lineage_map:
                unique_commits = {}
                for file_path, file_commits in st.session_state.retriever.store.lineage_map.items():
                    for c in file_commits:
                        unique_commits[c["commit_hash"]] = c
                commits = sorted(unique_commits.values(), key=lambda x: x.get("date", ""), reverse=True)
                
            if commits:
                commit_options = [f"{c.commit_hash if hasattr(c, 'commit_hash') else c.get('commit_hash', '')} - {c.message[:50] if hasattr(c, 'message') else c.get('message', '')[:50]}" for c in commits]
                
                col_a, col_b = st.columns(2)
                with col_a:
                    commit_a_choice = st.selectbox("Compare from (Commit A - Older)", commit_options, index=min(1, len(commit_options)-1), key="diff_commit_a")
                with col_b:
                    commit_b_choice = st.selectbox("Compare to (Commit B - Newer)", commit_options, index=0, key="diff_commit_b")
                    
                hash_a = commit_a_choice.split(" - ")[0]
                hash_b = commit_b_choice.split(" - ")[0]
                
                if st.button("🔍 Explain Differences", type="primary", use_container_width=True):
                    with st.spinner("Extracting git diff..."):
                        diff_text = ""
                        if st.session_state.retriever.extractor:
                            diff_text = st.session_state.retriever.extractor.get_file_diff(selected_file, hash_a, hash_b)
                        else:
                            diff_text = "Error: Local git repository extractor is not available in cloud fallback."
                            
                    if diff_text and not diff_text.startswith("Error"):
                        st.markdown("#### 📝 AI Semantic Explanation")
                        synthesizer = CodeArchaeologistSynthesizer()
                        with st.spinner("Synthesizing code review..."):
                            explanation = synthesizer.explain_diff(selected_file, hash_a, hash_b, diff_text)
                        st.markdown(f'<div class="glass-card" style="border-left: 4px solid #a855f7;">{explanation}</div>', unsafe_allow_html=True)
                        
                        with st.expander("📝 View Raw Diff Code"):
                            st.code(diff_text, language="diff")
                    else:
                        st.error(f"Could not retrieve diff or file was not present: {diff_text or 'No changes detected.'}")
            else:
                st.warning("No commits found to compare.")
        else:
            st.warning("No chunks available. Index a repository first.")

    # ------------------ TAB 4: CODEBASE ANALYTICS ------------------
    with tab_analytics:
        st.markdown("### 📊 Codebase Structure & Language Distribution")
        
        chunks = list(st.session_state.retriever.store.chunks.values())
        if chunks:
            # Compute distribution values
            lang_counts = {}
            type_counts = {}
            unique_files = set()
            total_lines = 0
            
            for chunk in chunks:
                lang_counts[chunk.language] = lang_counts.get(chunk.language, 0) + 1
                type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1
                unique_files.add(chunk.file_path)
                total_lines += (chunk.end_line - chunk.start_line + 1)
                
            # Row 1: Key Summary Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(unique_files)}</div>
                    <div class="metric-label">Unique Files</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(chunks)}</div>
                    <div class="metric-label">AST Code Chunks</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_lines}</div>
                    <div class="metric-label">Lines of Code Indexed</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                top_lang = max(lang_counts.items(), key=lambda x: x[1])[0] if lang_counts else "None"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #c084fc; background: linear-gradient(90deg, #c084fc, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{top_lang.upper()}</div>
                    <div class="metric-label">Primary Language</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("---")
            
            # Row 2: Charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("#### 🌐 Languages Breakdown")
                lang_df = pd.DataFrame([{"Language": k.upper(), "Count": v} for k, v in lang_counts.items()])
                lang_chart = alt.Chart(lang_df).mark_arc(innerRadius=50, cornerRadius=4).encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Language", type="nominal", scale=alt.Scale(scheme="darkmulti")),
                    tooltip=["Language", "Count"]
                ).properties(height=280)
                st.altair_chart(lang_chart, use_container_width=True)
                
            with chart_col2:
                st.markdown("#### 🧩 Structural AST Node Types")
                type_df = pd.DataFrame([{"Type": k.upper(), "Count": v} for k, v in type_counts.items()])
                type_chart = alt.Chart(type_df).mark_bar(cornerRadius=4).encode(
                    x=alt.X("Count:Q", title="Chunk Count"),
                    y=alt.Y("Type:N", sort="-x", title="AST Chunk Type"),
                    color=alt.Color("Type:N", legend=None, scale=alt.Scale(scheme="purples")),
                    tooltip=["Type", "Count"]
                ).properties(height=280)
                st.altair_chart(type_chart, use_container_width=True)
                
            st.markdown("---")
            
            # Row 3: Leaderboard
            st.markdown("#### 🏆 Leaderboard: Top Files by AST Chunks")
            file_chunk_counts = {}
            for chunk in chunks:
                file_chunk_counts[chunk.file_path] = file_chunk_counts.get(chunk.file_path, 0) + 1
            top_files = sorted(file_chunk_counts.items(), key=lambda x: x[1], reverse=True)[:6]
            
            leader_df = pd.DataFrame(top_files, columns=["File Path", "AST Chunks"])
            st.table(leader_df)
        else:
            st.warning("No codebase chunks are currently loaded in the store cache. Excavate a repository to view analytics.")
