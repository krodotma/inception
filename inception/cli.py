"""
CLI entrypoints for Inception.

Provides the main command-line interface for ingesting, querying,
and managing knowledge from multimodal sources.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from inception import __version__
from inception.config import Config, get_config, set_config

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="inception")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--offline",
    is_flag=True,
    help="Run in offline mode (no network requests)",
)
@click.option(
    "--seed",
    type=int,
    help="Random seed for reproducibility",
)
@click.pass_context
def main(ctx: click.Context, config: Optional[Path], offline: bool, seed: Optional[int]) -> None:
    """
    Inception: Local-first multimodal learning ingestion.
    
    Ingest learning materials (YouTube, web, PDFs) into a temporal
    knowledge hypergraph and produce actionable outputs.
    """
    ctx.ensure_object(dict)
    
    # Load configuration
    if config:
        cfg = Config.from_yaml(config)
    else:
        cfg = get_config()
    
    # Apply CLI overrides
    if offline:
        cfg.pipeline.offline_mode = True
    if seed is not None:
        cfg.pipeline.seed = seed
    
    set_config(cfg)
    ctx.obj["config"] = cfg


@main.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """
    Check environment and dependencies.
    
    Verifies that all required tools and libraries are installed
    and properly configured.
    """
    cfg: Config = ctx.obj["config"]
    
    console.print("\n[bold blue]Inception Doctor[/bold blue]")
    console.print(f"Version: {__version__}")
    console.print(f"Schema: {cfg.schema_version}")
    console.print(f"Pipeline: {cfg.pipeline_version}")
    console.print()
    
    # Create status table
    table = Table(title="Dependency Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    all_ok = True
    
    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python",
        "✓" if py_ok else "✗",
        f"{py_version} (need >=3.11)"
    )
    all_ok = all_ok and py_ok
    
    # Check LMDB
    try:
        import lmdb
        lmdb_version = lmdb.version()
        table.add_row("LMDB", "✓", f"v{'.'.join(map(str, lmdb_version))}")
    except ImportError:
        table.add_row("LMDB", "✗", "Not installed")
        all_ok = False
    
    # Check yt-dlp
    try:
        import yt_dlp
        table.add_row("yt-dlp", "✓", f"v{yt_dlp.version.__version__}")
    except ImportError:
        table.add_row("yt-dlp", "✗", "Not installed")
        all_ok = False
    
    # Check Whisper
    try:
        import faster_whisper
        table.add_row("faster-whisper", "✓", "Installed")
    except ImportError:
        table.add_row("faster-whisper", "⚠", "Not installed (optional for ASR)")
    
    # Check OCR
    try:
        from paddleocr import PaddleOCR  # noqa: F401
        table.add_row("PaddleOCR", "✓", "Installed")
    except ImportError:
        try:
            import pytesseract  # noqa: F401
            table.add_row("Tesseract", "✓", "Fallback OCR available")
        except ImportError:
            table.add_row("OCR", "✗", "Neither PaddleOCR nor Tesseract installed")
            all_ok = False
    
    # Check spaCy
    try:
        import spacy
        table.add_row("spaCy", "✓", f"v{spacy.__version__}")
        # Check for English model
        try:
            spacy.load("en_core_web_sm")
            table.add_row("  en_core_web_sm", "✓", "Model loaded")
        except OSError:
            table.add_row("  en_core_web_sm", "⚠", "Model not installed")
    except ImportError:
        table.add_row("spaCy", "✗", "Not installed")
        all_ok = False
    
    # Check PDF tools
    try:
        import pdfplumber  # noqa: F401
        table.add_row("pdfplumber", "✓", "Installed")
    except ImportError:
        table.add_row("pdfplumber", "✗", "Not installed")
        all_ok = False
    
    # Check directories
    console.print(table)
    console.print()
    
    dir_table = Table(title="Directories")
    dir_table.add_column("Directory", style="cyan")
    dir_table.add_column("Path")
    dir_table.add_column("Exists")
    
    dir_table.add_row("Data", str(cfg.data_dir), "✓" if cfg.data_dir.exists() else "✗")
    dir_table.add_row("Artifacts", str(cfg.artifacts_dir), "✓" if cfg.artifacts_dir.exists() else "✗")
    dir_table.add_row("Cache", str(cfg.cache_dir), "✓" if cfg.cache_dir.exists() else "✗")
    dir_table.add_row("LMDB", str(cfg.lmdb.path), "✓" if cfg.lmdb.path.exists() else "✗")
    
    console.print(dir_table)
    console.print()
    
    if all_ok:
        console.print("[bold green]✓ All checks passed![/bold green]")
    else:
        console.print("[bold yellow]⚠ Some dependencies missing. Run 'uv sync' to install.[/bold yellow]")
    
    console.print()


@main.command()
@click.argument("uri")
@click.option("--since", type=str, help="Only process content since this date (YYYY-MM-DD)")
@click.option("--until", type=str, help="Only process content until this date (YYYY-MM-DD)")
@click.option("--topic", multiple=True, help="Topic filters to apply")
@click.option("--profile", type=str, help="Ingestion profile to use")
@click.pass_context
def ingest(
    ctx: click.Context,
    uri: str,
    since: Optional[str],
    until: Optional[str],
    topic: tuple[str, ...],
    profile: Optional[str],
) -> None:
    """
    Ingest a source (URL or file path).
    
    Supports YouTube videos/channels/playlists, web pages, PDFs,
    and other document formats.
    """
    cfg: Config = ctx.obj["config"]
    
    console.print(f"[bold]Ingesting:[/bold] {uri}")
    
    if cfg.pipeline.offline_mode:
        console.print("[yellow]Running in offline mode[/yellow]")
    
    if since:
        console.print(f"  Since: {since}")
    if until:
        console.print(f"  Until: {until}")
    if topic:
        console.print(f"  Topics: {', '.join(topic)}")
    
    # TODO: Implement ingestion pipeline
    console.print("[dim]Ingestion not yet implemented[/dim]")


@main.command("ingest-channel")
@click.argument("channel_url")
@click.option("--since", type=str, required=True, help="Start date (YYYY-MM-DD)")
@click.option("--until", type=str, help="End date (YYYY-MM-DD)")
@click.option("--topic-rules", type=click.Path(exists=True, path_type=Path), help="Topic rules YAML file")
@click.pass_context
def ingest_channel(
    ctx: click.Context,
    channel_url: str,
    since: str,
    until: Optional[str],
    topic_rules: Optional[Path],
) -> None:
    """
    Ingest a YouTube channel incrementally.
    
    Downloads and processes all videos within the specified date range.
    """
    console.print(f"[bold]Ingesting channel:[/bold] {channel_url}")
    console.print(f"  Since: {since}")
    if until:
        console.print(f"  Until: {until}")
    if topic_rules:
        console.print(f"  Topic rules: {topic_rules}")
    
    # TODO: Implement channel ingestion
    console.print("[dim]Channel ingestion not yet implemented[/dim]")


@main.command("ingest-batch")
@click.argument("sources_file", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def ingest_batch(ctx: click.Context, sources_file: Path) -> None:
    """
    Ingest multiple sources from a JSONL file.
    
    Each line should contain a JSON object with 'uri' and optional
    'since', 'until', and 'topics' fields.
    """
    console.print(f"[bold]Batch ingestion from:[/bold] {sources_file}")
    
    # TODO: Implement batch ingestion
    console.print("[dim]Batch ingestion not yet implemented[/dim]")


@main.command("build-graph")
@click.argument("source_id")
@click.pass_context
def build_graph(ctx: click.Context, source_id: str) -> None:
    """
    Build knowledge graph from an ingested source.
    
    Extracts entities, claims, procedures, and relationships.
    """
    console.print(f"[bold]Building graph for:[/bold] {source_id}")
    
    # TODO: Implement graph building
    console.print("[dim]Graph building not yet implemented[/dim]")


@main.command()
@click.argument("query_text")
@click.option("--time", type=str, help="Time range filter (e.g., 'last 7 days')")
@click.option("--source", type=str, help="Limit to specific source")
@click.option("--format", "output_format", type=click.Choice(["json", "md"]), default="md")
@click.pass_context
def query(
    ctx: click.Context,
    query_text: str,
    time: Optional[str],
    source: Optional[str],
    output_format: str,
) -> None:
    """
    Query the knowledge graph.
    
    Supports natural language queries over the temporal knowledge graph.
    """
    console.print(f"[bold]Query:[/bold] {query_text}")
    
    if time:
        console.print(f"  Time filter: {time}")
    if source:
        console.print(f"  Source filter: {source}")
    console.print(f"  Output format: {output_format}")
    
    # TODO: Implement query
    console.print("[dim]Query not yet implemented[/dim]")


@main.command("action-pack")
@click.argument("target")
@click.option("--rheomode", type=click.IntRange(0, 4), default=1, help="Detail level (0-4)")
@click.pass_context
def action_pack(ctx: click.Context, target: str, rheomode: int) -> None:
    """
    Generate an Action Pack from a source or query result.
    
    Produces actionable items with evidence linking at the specified
    RheoMode detail level.
    """
    console.print(f"[bold]Generating Action Pack for:[/bold] {target}")
    console.print(f"  RheoMode level: {rheomode}")
    
    # TODO: Implement action pack generation
    console.print("[dim]Action pack generation not yet implemented[/dim]")


@main.command()
@click.argument("target")
@click.option("--format", "output_format", type=click.Choice(["md", "jsonl", "parquet"]), default="md")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file path")
@click.pass_context
def export(
    ctx: click.Context,
    target: str,
    output_format: str,
    output: Optional[Path],
) -> None:
    """
    Export data from the knowledge graph.
    
    Exports sources, nodes, or query results in various formats.
    """
    console.print(f"[bold]Exporting:[/bold] {target}")
    console.print(f"  Format: {output_format}")
    if output:
        console.print(f"  Output: {output}")
    
    # TODO: Implement export
    console.print("[dim]Export not yet implemented[/dim]")


@main.command()
@click.option("--unit", is_flag=True, help="Run only unit tests")
@click.option("--integration", is_flag=True, help="Run only integration tests")
@click.option("--e2e", is_flag=True, help="Run only E2E tests")
@click.option("--coverage", is_flag=True, help="Generate coverage report")
@click.pass_context
def test(
    ctx: click.Context,
    unit: bool,
    integration: bool,
    e2e: bool,
    coverage: bool,
) -> None:
    """
    Run the test suite.
    
    By default runs all tests. Use flags to run specific test categories.
    """
    import subprocess
    
    cmd = ["pytest"]
    
    if unit:
        cmd.append("tests/unit")
    elif integration:
        cmd.append("tests/integration")
    elif e2e:
        cmd.append("tests/e2e")
    
    if coverage:
        cmd.extend(["--cov=inception", "--cov-report=term-missing"])
    
    console.print(f"[bold]Running tests:[/bold] {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@main.command()
@click.argument("target")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output directory")
@click.option("--all", "all_skills", is_flag=True, help="Generate skills for all procedures")
@click.pass_context
def skillify(ctx: click.Context, target: str, output: Optional[Path], all_skills: bool) -> None:
    """
    Convert a procedure node into an executable skill.
    
    Generates SKILL.md with optional scripts and provenance references.
    
    TARGET can be:
    - A source NID (to generate skills from all procedures in that source)
    - 'all' to generate skills from all procedures in the database
    """
    from inception.skills import SkillSynthesizer
    from inception.db import get_db
    
    cfg: Config = ctx.obj["config"]
    
    output_dir = output or cfg.data_dir / "skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold]Skillifying:[/bold] {target}")
    console.print(f"  Output: {output_dir}")
    
    try:
        db = get_db()
        synthesizer = SkillSynthesizer(db)
        
        if target.lower() == "all" or all_skills:
            skills = synthesizer.synthesize_all()
        else:
            try:
                source_nid = int(target)
                skills = synthesizer.synthesize_from_source(source_nid)
            except ValueError:
                console.print(f"[red]Invalid target: {target}[/red]")
                console.print("Use a NID number or 'all'")
                sys.exit(1)
        
        if not skills:
            console.print("[yellow]No procedures found to skillify[/yellow]")
            return
        
        console.print(f"[green]Found {len(skills)} procedure(s) to convert[/green]")
        
        for skill in skills:
            # Validate skill
            is_valid, issues = synthesizer.validate_skill(skill)
            
            if not is_valid:
                console.print(f"[yellow]⚠ Skill '{skill.name}' has issues:[/yellow]")
                for issue in issues:
                    console.print(f"    - {issue}")
            
            # Save skill
            skill_path = synthesizer.save_skill(skill, output_dir)
            console.print(f"  [green]✓[/green] {skill.name} → {skill_path}")
        
        console.print(f"\n[bold green]Generated {len(skills)} skill(s)[/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command("list-sources")
@click.option("--limit", type=int, default=20, help="Maximum sources to show")
@click.pass_context
def list_sources(ctx: click.Context, limit: int) -> None:
    """
    List all ingested sources.
    """
    from inception.db import get_db
    
    try:
        db = get_db()
        
        table = Table(title="Ingested Sources")
        table.add_column("NID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Title")
        table.add_column("Status")
        
        count = 0
        for source in db.iter_sources():
            if count >= limit:
                break
            table.add_row(
                str(source.nid),
                source.source_type.value,
                (source.title or "Untitled")[:40],
                source.status.value,
            )
            count += 1
        
        console.print(table)
        console.print(f"\nShowing {count} source(s)")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@main.command("stats")
@click.pass_context
def stats(ctx: click.Context) -> None:
    """
    Show database statistics.
    """
    from inception.db import get_db
    from inception.db.keys import NodeKind
    
    try:
        db = get_db()
        
        # Count nodes by type
        node_counts = {kind: 0 for kind in NodeKind}
        total_nodes = 0
        
        for node in db.iter_nodes():
            node_counts[node.kind] = node_counts.get(node.kind, 0) + 1
            total_nodes += 1
        
        # Count other records
        source_count = sum(1 for _ in db.iter_sources())
        span_count = sum(1 for _ in db.iter_spans())
        
        console.print("\n[bold]Database Statistics[/bold]\n")
        
        table = Table(title="Record Counts")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green", justify="right")
        
        table.add_row("Sources", str(source_count))
        table.add_row("Spans", str(span_count))
        table.add_row("Nodes (total)", str(total_nodes))
        
        for kind, count in node_counts.items():
            if count > 0:
                table.add_row(f"  {kind.name}", str(count))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# =============================================================================
# LEARNING COMMANDS (Stage 3.7 Steps 466-475)
# =============================================================================

@main.command("learn")
@click.option("--action", "-a", required=True, help="Action type (extract_claim, resolve_gap, etc.)")
@click.option("--sources", "-s", type=Path, help="Sources JSON file for RLVR")
@click.pass_context
def learn(ctx: click.Context, action: str, sources: Optional[Path]) -> None:
    """
    Execute learning step with RLVR reward.
    
    Runs single learning step through DAPO/GRPO/RLVR engine.
    """
    console.print(f"[cyan]Running learning step: {action}[/cyan]")
    
    try:
        # In production, would connect to running server or run directly
        import httpx
        response = httpx.post(
            "http://localhost:8000/api/learning/step",
            json={"action": action, "state": {}, "result": {}, "sources": []},
            timeout=30.0,
        )
        result = response.json()
        console.print(f"[green]Reward: {result.get('reward', 0):.2f}[/green]")
        console.print(f"Step: {result.get('step', 0)}")
    except Exception as e:
        console.print(f"[yellow]Learning engine not running: {e}[/yellow]")
        console.print("Start server first: inception serve")


@main.command("train")
@click.option("--batch-size", "-b", default=64, help="Training batch size")
@click.option("--epochs", "-e", default=1, help="Number of training epochs")
@click.pass_context
def train(ctx: click.Context, batch_size: int, epochs: int) -> None:
    """
    Run DAPO+GRPO training update.
    """
    console.print(f"[cyan]Training: batch_size={batch_size}, epochs={epochs}[/cyan]")
    
    try:
        import httpx
        for epoch in range(epochs):
            response = httpx.post(
                f"http://localhost:8000/api/learning/train?batch_size={batch_size}",
                timeout=60.0,
            )
            result = response.json()
            console.print(f"Epoch {epoch+1}: {result.get('status', 'unknown')}")
    except Exception as e:
        console.print(f"[red]Training failed: {e}[/red]")


@main.command("learning-stats")
@click.pass_context
def learning_stats(ctx: click.Context) -> None:
    """
    Show learning engine statistics.
    """
    try:
        import httpx
        response = httpx.get("http://localhost:8000/api/learning/stats", timeout=10.0)
        stats = response.json()
        
        table = Table(title="Learning Engine Stats")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        for key, value in stats.items():
            if isinstance(value, dict):
                table.add_row(f"[bold]{key}[/bold]", "")
                for k, v in value.items():
                    table.add_row(f"  {k}", str(v))
            else:
                table.add_row(key, str(value))
        
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]Could not fetch stats: {e}[/yellow]")


# =============================================================================
# SERVER & TUI COMMANDS (Stage 3.7)
# =============================================================================

@main.command("serve")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind")
@click.option("--port", "-p", default=8000, help="Port number")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.pass_context
def serve(ctx: click.Context, host: str, port: int, reload: bool) -> None:
    """
    Start the Inception API server.
    """
    console.print(f"[cyan]Starting server at http://{host}:{port}[/cyan]")
    
    try:
        import uvicorn
        uvicorn.run(
            "inception.serve.api:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        console.print("[red]uvicorn not installed. Install with: pip install uvicorn[/red]")


@main.command("tui")
@click.pass_context
def tui(ctx: click.Context) -> None:
    """
    Launch the Terminal User Interface.
    """
    console.print("[cyan]Launching TUI...[/cyan]")
    
    try:
        from inception.tui.app import InceptionApp
        app = InceptionApp()
        app.run()
    except ImportError as e:
        console.print(f"[red]TUI dependencies missing: {e}[/red]")
        console.print("Install with: pip install textual rich")


# =============================================================================
# SHELL COMPLETIONS (Stage 3.7 Steps 476-480)
# =============================================================================

@main.command("completions")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
@click.option("--install", is_flag=True, help="Install completions to shell config")
@click.pass_context
def completions(ctx: click.Context, shell: str, install: bool) -> None:
    """
    Generate shell completions.
    
    SHELL can be: bash, zsh, fish
    """
    import os
    
    if shell == "bash":
        script = '''
# Inception bash completions
_inception_completion() {
    local IFS=$'\\n'
    COMPREPLY=( $(env COMP_WORDS="${COMP_WORDS[*]}" \\
                  COMP_CWORD=$COMP_CWORD \\
                  _INCEPTION_COMPLETE=complete $1) )
    return 0
}
complete -F _inception_completion -o default inception
'''
        rc_file = os.path.expanduser("~/.bashrc")
    elif shell == "zsh":
        script = '''
# Inception zsh completions
_inception() {
    eval $(env _INCEPTION_COMPLETE=zsh_source inception)
}
compdef _inception inception
'''
        rc_file = os.path.expanduser("~/.zshrc")
    else:  # fish
        script = '''
# Inception fish completions
complete -c inception -f -a "(env _INCEPTION_COMPLETE=fish_source inception)"
'''
        rc_file = os.path.expanduser("~/.config/fish/completions/inception.fish")
    
    console.print(f"[cyan]Shell completions for {shell}:[/cyan]")
    console.print(script)
    
    if install:
        # Ensure directory exists for fish
        if shell == "fish":
            os.makedirs(os.path.dirname(rc_file), exist_ok=True)
        
        with open(rc_file, "a") as f:
            f.write(f"\n{script}\n")
        console.print(f"[green]✓ Installed to {rc_file}[/green]")
        console.print(f"  Reload with: source {rc_file}")


@main.command("version")
def version() -> None:
    """Show version information."""
    console.print(f"[cyan]Inception[/cyan] v{__version__}")
    console.print("Multimodal Learning Ingestion System")
    console.print("https://github.com/kroma/inception")


if __name__ == "__main__":
    main()
