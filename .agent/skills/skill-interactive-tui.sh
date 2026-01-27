#!/bin/bash
# skill-interactive-tui.sh
# Terminal UI for knowledge graph exploration
#
# SUBAGENT: SONNET (UX Specialist)
# TIER: 4 - Operations
#
# "For skill-interactive-tui.sh, I'm thinking of a textual + rich interface:
# - Tree view for source → spans → nodes
# - Inline evidence preview
# - Quick actions (export, explore gap, find contradictions)
# - Keyboard-driven navigation"
# - SONNET, Round 3

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Interactive terminal UI for exploring the knowledge graph.

Options:
    --source <nid>      Focus on specific source
    --search <query>    Start with search results
    --help              Show this help message

Keyboard Shortcuts:
    j/k     Navigate up/down
    Enter   Expand/collapse node
    e       Export selected item
    g       Explore gap (if gap selected)
    c       Find contradictions
    /       Search
    q       Quit

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            FOCUS_SOURCE="$2"
            shift 2
            ;;
        --search)
            INITIAL_SEARCH="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

echo "=== Interactive TUI ==="
echo ""
echo "This feature requires the textual library."
echo ""

# Check if textual is available
cd "$PROJECT_ROOT"
if uv run python -c "import textual" 2>/dev/null; then
    echo "Textual is available. Launching TUI..."
    echo ""
    echo "TUI not yet implemented."
    echo "This is a placeholder for the enhancement."
else
    echo "Textual not installed."
    echo ""
    echo "To install:"
    echo "  uv add textual"
    echo ""
    echo "Alternative: Use the Rich-based simple explorer:"
    uv run python -c "
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel

console = Console()

try:
    from inception.db import get_db
    from inception.db.keys import NodeKind
    
    db = get_db()
    
    # Build tree
    tree = Tree('[bold]📚 Inception Knowledge Graph[/bold]')
    
    sources = list(db.iter_sources())
    if sources:
        src_branch = tree.add(f'[cyan]Sources ({len(sources)})[/cyan]')
        for src in sources[:5]:
            src_branch.add(f'[{src.nid}] {src.title or src.uri[:30]}')
        if len(sources) > 5:
            src_branch.add(f'... and {len(sources) - 5} more')
    
    nodes = list(db.iter_nodes())
    if nodes:
        entity_count = sum(1 for n in nodes if n.kind == NodeKind.ENTITY)
        claim_count = sum(1 for n in nodes if n.kind == NodeKind.CLAIM)
        proc_count = sum(1 for n in nodes if n.kind == NodeKind.PROCEDURE)
        gap_count = sum(1 for n in nodes if n.kind == NodeKind.GAP)
        
        node_branch = tree.add(f'[cyan]Nodes ({len(nodes)})[/cyan]')
        if entity_count:
            node_branch.add(f'[green]Entities: {entity_count}[/green]')
        if claim_count:
            node_branch.add(f'[blue]Claims: {claim_count}[/blue]')
        if proc_count:
            node_branch.add(f'[yellow]Procedures: {proc_count}[/yellow]')
        if gap_count:
            node_branch.add(f'[red]Gaps: {gap_count}[/red]')
    
    console.print(Panel(tree, title='Knowledge Graph Overview'))
    console.print()
    console.print('[dim]Full TUI coming soon. Run: inception explore[/dim]')
    
except Exception as e:
    console.print(f'[red]Database not available: {e}[/red]')
    console.print('[dim]Run: inception doctor[/dim]')
" 2>/dev/null || echo "Could not display overview. Database may not be initialized."
fi

echo ""
echo "Done. Full TUI enhancement pending implementation."
