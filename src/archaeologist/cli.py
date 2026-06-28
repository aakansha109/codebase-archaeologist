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

if __name__ == "__main__":
    app()
