'use client';

import { useState } from 'react';
import { Search, Database, GitCommit, ShieldAlert, Cpu, Layers, Sparkles, Terminal, FileCode, CheckCircle2, AlertCircle } from 'lucide-react';

interface EvidenceChunk {
  chunk_id: string;
  file_path: string;
  name: string;
  chunk_type: string;
  language: string;
  content: string;
  start_line: number;
  end_line: number;
  score: number;
  lineage: Array<{ commit_hash: string; message: string; author: string; date: string }>;
}

export default function Home() {
  const [targetRepo, setTargetRepo] = useState('https://github.com/paperclipai/paperclip');
  const [ingesting, setIngesting] = useState(false);
  const [ingestedStats, setIngestedStats] = useState<any>(null);
  
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [answer, setAnswer] = useState('');
  const [evidence, setEvidence] = useState<EvidenceChunk[]>([]);
  
  const [ingestError, setIngestError] = useState('');
  
  const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  let formattedUrl = (rawApiUrl.startsWith('http://') || rawApiUrl.startsWith('https://'))
    ? rawApiUrl
    : `https://${rawApiUrl}`;
  const API_URL = formattedUrl.replace(/\/+$/, '');

  const handleIngest = async () => {
    const cleanRepo = targetRepo.trim();
    if (!cleanRepo) return;
    setIngesting(true);
    setIngestedStats(null);
    setIngestError('');
    try {
      const res = await fetch(`${API_URL}/api/v1/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: cleanRepo }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server returned ${res.status}: ${errText}`);
      }
      const data = await res.json();
      if (data.success) {
        setIngestedStats(data.stats);
      } else {
        setIngestError(data.detail || 'Ingestion failed.');
      }
    } catch (e: any) {
      console.error(e);
      setIngestError(e.message || 'Failed to connect to backend API server. Make sure Railway backend URL is configured.');
    } finally {
      setIngesting(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setSearching(true);
    setAnswer('');
    setEvidence([]);
    try {
      const res = await fetch(`${API_URL}/api/v1/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query, top_k: 4 }),
      });
      const data = await res.json();
      setAnswer(data.answer || 'No architectural synthesis available.');
      setEvidence(data.evidence || []);
    } catch (e) {
      console.error(e);
      setAnswer('Failed to query backend. Ensure Python API server is running.');
    } finally {
      setSearching(false);
    }
  };

  return (
    <main className="min-h-screen max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Top Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2 text-sky-400 text-sm font-semibold tracking-wider uppercase mb-1">
            <Sparkles className="w-4 h-4" /> Next.js + Supabase pgvector Architecture
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
            The Codebase Archaeologist 🏛️
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            AST-aware logical code chunking, git lineage mining, and RRF vector retrieval.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          FastAPI Backend: <code className="text-sky-400 font-mono">{API_URL}</code>
        </div>
      </header>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Repository Excavation Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-sky-400" /> Excavate Repository
            </h2>
            <p className="text-xs text-slate-400">
              Enter a public Git URL or local folder path to chunk AST nodes and index into Supabase pgvector.
            </p>
            <div className="space-y-3">
              <input
                type="text"
                value={targetRepo}
                onChange={(e) => setTargetRepo(e.target.value)}
                placeholder="https://github.com/user/repo"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-500 font-mono"
              />
              <button
                onClick={handleIngest}
                disabled={ingesting}
                className="w-full bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold py-2 px-4 rounded-lg text-sm transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {ingesting ? (
                  <>
                    <Cpu className="w-4 h-4 animate-spin" /> Indexing AST & Commits...
                  </>
                ) : (
                  <>
                    <Terminal className="w-4 h-4" /> Start Ingestion
                  </>
                )}
              </button>
            </div>

            {ingestError && (
              <div className="bg-red-950/80 border border-red-500/40 rounded-lg p-3 text-xs text-red-300 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div>{ingestError}</div>
              </div>
            )}

            {ingestedStats && (
              <div className="bg-slate-900/90 border border-emerald-500/30 rounded-lg p-4 space-y-2 text-xs">
                <div className="flex items-center gap-2 text-emerald-400 font-bold">
                  <CheckCircle2 className="w-4 h-4" /> Repository Successfully Excavated!
                </div>
                <div className="text-slate-300 font-mono space-y-1 pt-1">
                  <div>Commits Mined: <span className="text-white font-bold">{ingestedStats.commits_mined}</span></div>
                  <div>AST Chunks: <span className="text-white font-bold">{ingestedStats.chunks_indexed}</span></div>
                  <div>Files Parsed: <span className="text-white font-bold">{ingestedStats.files_parsed}</span></div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Archaeological Query & Synthesis */}
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleSearch} className="glass-panel p-4 rounded-xl border border-slate-800 flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask an architectural question (e.g. How does authentication work?)..."
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
            />
            <button
              type="submit"
              disabled={searching}
              className="bg-sky-500 hover:bg-sky-400 text-white px-5 py-2 rounded-lg font-semibold text-sm transition flex items-center gap-2 disabled:opacity-50"
            >
              {searching ? <Cpu className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Search
            </button>
          </form>

          {/* AI Explanation Card */}
          {answer && (
            <div className="glass-panel p-6 rounded-xl border border-indigo-500/30 space-y-3">
              <h3 className="text-base font-bold text-indigo-300 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" /> Architectural Explanation
              </h3>
              <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
                {answer}
              </div>
            </div>
          )}

          {/* Retrieved Evidence Cards */}
          {evidence.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-sky-400" /> AST Code Evidence ({evidence.length} Chunks)
              </h3>
              <div className="grid grid-cols-1 gap-4">
                {evidence.map((item, idx) => (
                  <div key={idx} className="glass-panel p-5 rounded-xl border-l-4 border-l-sky-400 border-slate-800 space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded font-mono uppercase font-bold">
                        {item.chunk_type}
                      </span>
                      <span className="text-slate-400 font-mono">Score: {item.score}</span>
                    </div>
                    <div className="font-mono text-base font-bold text-white">
                      {item.name}
                    </div>
                    <div className="text-xs text-slate-400 flex items-center gap-2 font-mono">
                      <FileCode className="w-3.5 h-3.5 text-slate-500" /> {item.file_path} (L{item.start_line}-{item.end_line})
                    </div>
                    {item.lineage && item.lineage.length > 0 && (
                      <div className="pt-2 border-t border-slate-800/80 text-xs text-purple-400 font-mono space-y-1">
                        <div className="flex items-center gap-1 text-slate-300 font-sans font-semibold">
                          <GitCommit className="w-3.5 h-3.5 text-purple-400" /> Evolution History:
                        </div>
                        {item.lineage.slice(0, 2).map((c, i) => (
                          <div key={i} className="truncate">
                            <span className="text-sky-400">{c.commit_hash}</span>: {c.message}
                          </div>
                        ))}
                      </div>
                    )}
                    <pre className="bg-slate-950 p-3 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800/80">
                      <code>{item.content}</code>
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
