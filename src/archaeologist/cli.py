import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from archaeologist.query.retriever import CodebaseRetriever
from archaeologist.query.synthesizer import CodeArchaeologistSynthesizer

app = typer.Typer(
    name="archaeologist",
    help="🏛️ The Codebase Archaeologist: Deep historical & structural RAG engine for git repositories.",
    add_completion=False
)
console = Console()

@app.command()
def ingest(
    target: str = typer.Argument(..., help="Repository URL (e.g. https://github.com/paperclipai/paperclip) or local path")
):
    """Ingest a Git repository, chunk code via AST, and index into Qdrant Hybrid Store."""
    console.print(Panel.fit(f"[bold cyan]🏛️ Ingesting Repository:[/bold cyan] {target}", border_style="cyan"))
    
    retriever = CodebaseRetriever()
    with console.status("[bold green]Mining git lineage & parsing AST...") as status:
        def update_status(msg):
            status.update(f"[bold green]{msg}")
        stats = retriever.ingest_repository(target, progress_callback=update_status)
        
    table = Table(title="✨ Ingestion Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold green")
    table.add_row("Repository Path", stats["repo_path"])
    table.add_row("Historical Commits Mined", str(stats["commits_mined"]))
    table.add_row("AST Code Chunks Indexed", str(stats["chunks_indexed"]))
    
    console.print(table)
    console.print("[bold green]✔ Ingestion complete! You can now run `archaeologist ask <question>`.[/bold green]")

@app.command()
def ask(
    question: str = typer.Argument(..., help="Historical or structural codebase question"),
    top_k: int = typer.Option(4, "--top-k", "-k", help="Number of evidence chunks to retrieve")
):
    """Ask an archaeological question about the ingested codebase."""
    console.print(f"\n[bold yellow]🔍 Querying Codebase Archaeologist:[/bold yellow] *\"{question}\"*\n")
    
    retriever = CodebaseRetriever()
    with console.status("[bold blue]Performing Hybrid Retrieval (Dense + BM25 RRF)..."):
        results = retriever.retrieve(question, top_k=top_k)
        
    if not results:
        console.print("[bold red]No relevant code chunks found. Did you run `archaeologist ingest` first?[/bold red]")
        raise typer.Exit(1)
        
    synthesizer = CodeArchaeologistSynthesizer()
    with console.status("[bold purple]Synthesizing historical architectural answer..."):
        answer = synthesizer.synthesize(question, results)
        
    console.print(Panel(Markdown(answer), title="[bold green]🏛️ Archaeological Analysis[/bold green]", border_style="green"))

@app.command()
def timeline(
    file_path: str = typer.Argument(..., help="Relative file path in repository (e.g., src/index.ts)")
):
    """View recent Git commit timeline for a specific file."""
    retriever = CodebaseRetriever()
    if not hasattr(retriever, "lineage_map") or not retriever.lineage_map:
        console.print("[bold yellow]Please run `archaeologist ingest <target>` first to load repository timeline.[/bold yellow]")
        raise typer.Exit(1)
        
    normalized = file_path.replace("\\", "/")
    commits = retriever.lineage_map.get(normalized, [])
    
    if not commits:
        console.print(f"[bold red]No recent commits recorded for `{normalized}`.[/bold red]")
        raise typer.Exit(1)
        
    table = Table(title=f"⏳ Lineage Timeline: {normalized}", show_header=True, header_style="bold blue")
    table.add_column("Commit Hash", style="cyan")
    table.add_column("Date", style="dim")
    table.add_column("Author", style="magenta")
    table.add_column("Message", style="white")
    
    for c in commits:
        table.add_row(c["commit_hash"], c["date"][:10], c["author"], c["message"][:60])
        
    console.print(table)

@app.command()
def eval():
    """Run automated RAG Triad benchmark evaluation (Context Precision, Recall, Faithfulness)."""
    console.print(Panel.fit("[bold magenta]📊 Executing Archaeological RAG Benchmark Evaluation...[/bold magenta]", border_style="magenta"))
    
    from evals.evaluate_rag import RAGEvaluator
    evaluator = RAGEvaluator()
    metrics = evaluator.evaluate_benchmark()
    
    table = Table(title="🏛️ Archaeological RAG Triad Benchmark Scores", show_header=True, header_style="bold green")
    table.add_column("Metric", style="cyan")
    table.add_column("Score / Value", style="bold yellow")
    
    table.add_row("Evaluated Queries", str(metrics["eval_count"]))
    table.add_row("Context Precision", f"{metrics['context_precision'] * 100:.1f}%")
    table.add_row("Context Recall", f"{metrics['context_recall'] * 100:.1f}%")
    table.add_row("RAG Triad F1-Score", f"{metrics['rag_triad_f1'] * 100:.1f}%")
    table.add_row("Average Search Latency", f"{metrics['avg_latency_sec']}s")
    
    console.print(table)

@app.command()
def health():
    """Audit codebase health, AST complexity, and technical debt risk."""
    console.print(Panel.fit("[bold cyan]🏥 Auditing Codebase Technical Debt & Health...[/bold cyan]", border_style="cyan"))
    
    retriever = CodebaseRetriever()
    from archaeologist.ingest.health_auditor import CodebaseHealthAuditor
    auditor = CodebaseHealthAuditor()
    chunks = list(retriever.store.chunks.values()) if hasattr(retriever.store, 'chunks') else []
    lineage_map = getattr(retriever.store, 'lineage_map', {})
    
    health_data = auditor.analyze_health(chunks, lineage_map)
    
    table = Table(title="🏥 Codebase Health & Technical Debt Scorecard", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold green")
    
    table.add_row("Health Index Score", f"{health_data['health_score']}/100")
    table.add_row("Risk Assessment Level", health_data['risk_level'])
    table.add_row("Average AST Chunk Size", f"{health_data['avg_chunk_lines']} lines")
    table.add_row("Oversized Chunks (>80 lines)", f"{health_data['oversized_chunks']} ({health_data.get('oversized_ratio_percent', 0)}%)")
    
    console.print(table)

@app.command()
def export(
    output: str = typer.Option("archaeology_report.md", "--output", "-o", help="Output report filepath (.md or .html)")
):
    """Export comprehensive archaeological technical report to disk."""
    console.print(f"[bold yellow]📝 Exporting Archaeological Report to:[/bold yellow] `{output}`")
    
    retriever = CodebaseRetriever()
    from archaeologist.ingest.health_auditor import CodebaseHealthAuditor
    from archaeologist.query.report_exporter import ArchaeologicalReportExporter
    
    chunks = list(retriever.store.chunks.values()) if hasattr(retriever.store, 'chunks') else []
    lineage_map = getattr(retriever.store, 'lineage_map', {})
    stats = getattr(retriever, 'stats', {"repo_path": "Codebase", "commits_mined": 0, "chunks_indexed": len(chunks), "files_parsed": 0})
    
    auditor = CodebaseHealthAuditor()
    health_data = auditor.analyze_health(chunks, lineage_map)
    
    synthesizer = CodeArchaeologistSynthesizer()
    dep_graph = getattr(retriever, 'dep_graph', None)
    diagram_code = synthesizer.generate_architecture_diagram(chunks, dep_graph)
    
    exporter = ArchaeologicalReportExporter()
    if output.endswith(".html"):
        content = exporter.generate_html_report(stats, chunks, health_data, diagram_code)
    else:
        content = exporter.generate_markdown_report(stats, chunks, health_data, diagram_code)
        
    with open(output, "w", encoding="utf-8") as f:
        f.write(content)
        
    console.print(f"[bold green]✔ Report successfully exported to `{output}`![/bold green]")

if __name__ == "__main__":
    app()
