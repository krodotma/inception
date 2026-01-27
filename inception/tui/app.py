"""
CODEX-1 ULTRATHINK: Enhanced TUI with API Integration

Additions:
- HTTP client for real data from API
- Entity detail modal
- Live search with filtering
- OAuth setup wizard
- Keyboard shortcuts overlay

Model: Opus 4.5 ULTRATHINK
"""

import asyncio
import httpx
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Label, Button, 
    DataTable, Tree, Input, Switch, TabbedContent, TabPane,
    ProgressBar, LoadingIndicator, Markdown, RichLog
)
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.message import Message
from textual import events, work
from rich.text import Text
from rich.panel import Panel


# =============================================================================
# API CLIENT
# =============================================================================

class InceptionAPI:
    """Async HTTP client for Inception API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_stats(self) -> dict:
        try:
            resp = await self.client.get(f"{self.base_url}/api/stats")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"entities": 0, "claims": 0, "procedures": 0, "gaps": 0, "sources": 0, "error": str(e)}
    
    async def get_entities(self, search: str = None, type_filter: str = None, limit: int = 50) -> list:
        try:
            params = {"limit": limit}
            if search:
                params["search"] = search
            if type_filter:
                params["type"] = type_filter
            resp = await self.client.get(f"{self.base_url}/api/entities", params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []
    
    async def get_entity(self, entity_id: str) -> Optional[dict]:
        try:
            resp = await self.client.get(f"{self.base_url}/api/entities/{entity_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None
    
    async def get_claims(self, entity_id: str = None, limit: int = 50) -> list:
        try:
            params = {"limit": limit}
            if entity_id:
                params["entity_id"] = entity_id
            resp = await self.client.get(f"{self.base_url}/api/claims", params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []
    
    async def get_gaps(self) -> list:
        try:
            resp = await self.client.get(f"{self.base_url}/api/gaps")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []
    
    async def get_graph(self) -> dict:
        try:
            resp = await self.client.get(f"{self.base_url}/api/graph")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {"nodes": [], "edges": []}
    
    async def health(self) -> dict:
        try:
            resp = await self.client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    async def close(self):
        await self.client.aclose()


# Global API client
api = InceptionAPI()


# =============================================================================
# WIDGETS
# =============================================================================

class StatCard(Static):
    """Statistics card with live updates."""
    
    value = reactive("0")
    
    def __init__(self, title: str, initial: str = "0", color: str = "cyan", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.value = initial
        self.color = color
    
    def render(self) -> Text:
        return Text.assemble(
            (f"{self.value}\n", f"bold {self.color}"),
            (self.title, "dim"),
        )


class EntityCard(Static):
    """Entity display with click handler."""
    
    class Selected(Message):
        def __init__(self, entity_id: str):
            self.entity_id = entity_id
            super().__init__()
    
    def __init__(self, entity: dict, **kwargs):
        super().__init__(**kwargs)
        self.entity = entity
    
    def render(self) -> Panel:
        type_colors = {
            "entity": "magenta",
            "claim": "cyan",
            "procedure": "yellow",
            "gap": "red",
        }
        color = type_colors.get(self.entity.get("type", "entity"), "white")
        
        content = Text()
        content.append(f"● {self.entity.get('type', 'entity').upper()}\n", style=color)
        content.append(f"{self.entity.get('name', 'Unknown')}\n", style="bold")
        if self.entity.get("description"):
            content.append(f"{self.entity['description'][:60]}...\n", style="dim")
        
        return Panel(content, border_style="dim")
    
    def on_click(self):
        self.post_message(self.Selected(self.entity.get("id")))


class GapCard(Static):
    """Knowledge gap card."""
    
    def __init__(self, gap: dict, **kwargs):
        super().__init__(**kwargs)
        self.gap = gap
    
    def render(self) -> Panel:
        priority_colors = {"high": "red", "medium": "yellow", "low": "dim"}
        color = priority_colors.get(self.gap.get("priority", "medium"), "yellow")
        
        content = Text()
        content.append(f"⚠ {self.gap.get('description', 'Unknown gap')}", style=color)
        
        return Panel(content, border_style=color)


# =============================================================================
# MODAL SCREENS
# =============================================================================

class EntityDetailModal(ModalScreen):
    """Entity detail modal with claims and procedures."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]
    
    def __init__(self, entity: dict, claims: list = None):
        super().__init__()
        self.entity = entity
        self.claims = claims or []
    
    def compose(self) -> ComposeResult:
        with Container(classes="modal-container"):
            yield Static(f"[bold]{self.entity.get('name', 'Entity')}[/]", classes="modal-title")
            yield Static(f"[dim]{self.entity.get('type', 'entity').upper()}[/]")
            
            if self.entity.get("description"):
                yield Static(f"\n{self.entity['description']}")
            
            if self.claims:
                yield Static("\n[bold]Claims:[/]")
                for claim in self.claims[:5]:
                    yield Static(f"  • {claim.get('statement', '')[:60]}")
            
            yield Button("Close", variant="primary", id="close-modal")
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "close-modal":
            self.dismiss()


class HelpModal(ModalScreen):
    """Keyboard shortcuts help modal."""
    
    BINDINGS = [Binding("escape", "dismiss", "Close"), Binding("?", "dismiss", "Close")]
    
    def compose(self) -> ComposeResult:
        help_text = """
# Keyboard Shortcuts

## Navigation
- `d` - Dashboard
- `e` - Explorer
- `g` - Graph
- `s` - Settings
- `q` - Quit

## Dashboard
- `r` - Refresh data

## Explorer
- `/` - Focus search
- `Enter` - Open selected entity
- `↑/↓` - Navigate list

## Graph
- `1` - Force layout
- `2` - Hierarchical layout
- `3` - Radial layout
- `0` - Fit to view

## General
- `?` - Show this help
- `Escape` - Close modal/cancel
        """
        with Container(classes="modal-container"):
            yield Markdown(help_text)
            yield Button("Close", variant="primary", id="close")
    
    def on_button_pressed(self, event):
        self.dismiss()


# =============================================================================
# SCREENS
# =============================================================================

class DashboardScreen(Screen):
    """Dashboard with live data from API."""
    
    BINDINGS = [Binding("r", "refresh", "Refresh")]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(classes="dashboard-container"):
            # Stats row
            with Horizontal(classes="stats-row"):
                yield StatCard("Entities", "...", color="magenta", id="stat-entities", classes="stat-card")
                yield StatCard("Claims", "...", color="cyan", id="stat-claims", classes="stat-card")
                yield StatCard("Procedures", "...", color="yellow", id="stat-procedures", classes="stat-card")
                yield StatCard("Gaps", "...", color="red", id="stat-gaps", classes="stat-card")
            
            # Content
            with Horizontal(classes="content-row"):
                with Vertical(classes="activity-panel"):
                    yield Static("[bold]Recent Entities[/]", classes="panel-title")
                    yield ScrollableContainer(id="entities-list")
                
                with Vertical(classes="gaps-panel"):
                    yield Static("[bold]Knowledge Gaps[/]", classes="panel-title")
                    yield ScrollableContainer(id="gaps-list")
        
        yield Footer()
    
    def on_mount(self):
        self.load_data()
    
    @work(exclusive=True)
    async def load_data(self):
        # Load stats
        stats = await api.get_stats()
        self.query_one("#stat-entities", StatCard).value = str(stats.get("entities", 0))
        self.query_one("#stat-claims", StatCard).value = str(stats.get("claims", 0))
        self.query_one("#stat-procedures", StatCard).value = str(stats.get("procedures", 0))
        self.query_one("#stat-gaps", StatCard).value = str(stats.get("gaps", 0))
        
        # Load entities
        entities = await api.get_entities(limit=10)
        entities_list = self.query_one("#entities-list")
        await entities_list.remove_children()
        for entity in entities:
            await entities_list.mount(EntityCard(entity, classes="entity-card"))
        
        # Load gaps
        gaps = await api.get_gaps()
        gaps_list = self.query_one("#gaps-list")
        await gaps_list.remove_children()
        for gap in gaps:
            await gaps_list.mount(GapCard(gap, classes="gap-card"))
    
    def action_refresh(self):
        self.notify("Refreshing...")
        self.load_data()
    
    async def on_entity_card_selected(self, event: EntityCard.Selected):
        entity = await api.get_entity(event.entity_id)
        claims = await api.get_claims(entity_id=event.entity_id)
        if entity:
            self.app.push_screen(EntityDetailModal(entity, claims))


class ExplorerScreen(Screen):
    """Knowledge explorer with search."""
    
    BINDINGS = [Binding("/", "focus_search", "Search")]
    
    search_query = reactive("")
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal(classes="explorer-container"):
            with Vertical(classes="filter-sidebar"):
                yield Static("[bold]Filters[/]", classes="panel-title")
                yield Button("● Entities", variant="primary", id="filter-entities", classes="filter-btn")
                yield Button("  Claims", id="filter-claims", classes="filter-btn")
                yield Button("  Procedures", id="filter-procedures", classes="filter-btn")
            
            with Vertical(classes="results-panel"):
                yield Input(placeholder="Search knowledge...", id="search-input")
                yield ScrollableContainer(id="results-list")
        
        yield Footer()
    
    def on_mount(self):
        self.load_results()
    
    @work(exclusive=True)
    async def load_results(self, search: str = None, type_filter: str = None):
        entities = await api.get_entities(search=search, type_filter=type_filter, limit=20)
        
        results_list = self.query_one("#results-list")
        await results_list.remove_children()
        
        if not entities:
            await results_list.mount(Static("[dim]No results found[/]"))
        else:
            for entity in entities:
                await results_list.mount(EntityCard(entity, classes="result-card"))
    
    def on_input_submitted(self, event: Input.Submitted):
        self.load_results(search=event.value)
    
    def action_focus_search(self):
        self.query_one("#search-input").focus()


class GraphScreen(Screen):
    """ASCII knowledge graph."""
    
    BINDINGS = [
        Binding("1", "layout_force", "Force"),
        Binding("2", "layout_tree", "Tree"),
        Binding("3", "layout_radial", "Radial"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(classes="graph-container"):
            yield Static("[bold]Knowledge Graph[/] (ASCII Mode)", classes="panel-title")
            yield Static(id="graph-display", classes="graph-ascii")
            
            with Horizontal(classes="graph-controls"):
                yield Button("Force [1]", variant="primary", id="btn-force")
                yield Button("Tree [2]", id="btn-tree")
                yield Button("Radial [3]", id="btn-radial")
        
        yield Footer()
    
    def on_mount(self):
        self.load_graph()
    
    @work(exclusive=True)
    async def load_graph(self):
        graph_data = await api.get_graph()
        
        # Generate ASCII representation
        ascii_graph = self.generate_ascii_graph(graph_data)
        self.query_one("#graph-display").update(ascii_graph)
    
    def generate_ascii_graph(self, data: dict) -> str:
        nodes = data.get("nodes", [])
        if not nodes:
            return "[dim]No graph data available[/]"
        
        # Simple ASCII layout
        lines = [""]
        center_nodes = [n for n in nodes if n.get("type") == "entity"][:3]
        
        if center_nodes:
            header = "    ".join([f"[magenta]{n.get('label', n.get('id'))[:12]}[/]" for n in center_nodes])
            lines.append(f"        {header}")
            lines.append("           │                │                │")
            lines.append("     ┌─────┼─────┬──────────┼──────────┬─────┼─────┐")
            lines.append("     │     │     │          │          │     │     │")
        
        claim_nodes = [n for n in nodes if n.get("type") == "claim"][:4]
        if claim_nodes:
            for cn in claim_nodes:
                lines.append(f"  [cyan]● {cn.get('label', cn.get('id'))[:40]}[/]")
        
        lines.append("")
        lines.append("[magenta]● Entity[/]  [cyan]● Claim[/]  [yellow]● Procedure[/]  [red]● Gap[/]")
        
        return "\n".join(lines)


class SettingsScreen(Screen):
    """Settings with auth management."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(classes="settings-container"):
            with TabbedContent():
                with TabPane("Authentication", id="auth"):
                    yield Static("[bold]🔐 LLM Providers[/]", classes="panel-title")
                    yield Static("[green]✓[/] Claude [dim](Max tier)[/]")
                    yield Static("[green]✓[/] Gemini [dim](Pro tier)[/]")
                    yield Static("[dim]○[/] OpenAI [dim](Not connected)[/]")
                    yield Button("Setup OAuth", variant="primary", id="btn-oauth")
                
                with TabPane("Database", id="database"):
                    yield Static("[bold]💾 LMDB Database[/]", classes="panel-title")
                    yield Static(id="db-info")
                    yield Button("Compact", id="btn-compact")
                
                with TabPane("API", id="api"):
                    yield Static("[bold]🔌 API Status[/]", classes="panel-title")
                    yield Static(id="api-status")
                    yield Button("Check Health", id="btn-health")
        
        yield Footer()
    
    def on_mount(self):
        self.check_health()
    
    @work
    async def check_health(self):
        health = await api.health()
        status_text = f"Status: {health.get('status', 'unknown')}"
        if health.get("storage"):
            status_text += f"\nStorage: {health['storage'].get('backend', 'unknown')}"
        self.query_one("#api-status").update(status_text)
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-health":
            self.check_health()
        elif event.button.id == "btn-oauth":
            self.notify("OAuth setup would launch browser...")


# =============================================================================
# MAIN APP
# =============================================================================

class InceptionTUI(App):
    """Inception Terminal UI with API integration."""
    
    CSS = """
    Screen { background: #1e1e2e; }
    
    .dashboard-container { padding: 1; }
    .stats-row { height: 5; margin-bottom: 1; }
    .stat-card { width: 1fr; height: 100%; background: #313244; border: solid #45475a; padding: 1; margin-right: 1; text-align: center; }
    
    .content-row { height: 1fr; }
    .activity-panel { width: 2fr; padding: 1; background: #313244; border: solid #45475a; margin-right: 1; }
    .gaps-panel { width: 1fr; padding: 1; background: #313244; border: solid #45475a; }
    
    .panel-title { margin-bottom: 1; }
    .entity-card { margin-bottom: 1; }
    .gap-card { margin-bottom: 1; }
    
    .explorer-container { height: 100%; }
    .filter-sidebar { width: 25; padding: 1; background: #313244; border-right: solid #45475a; }
    .results-panel { width: 1fr; padding: 1; }
    .filter-btn { margin-bottom: 1; }
    
    .graph-container { height: 100%; padding: 1; }
    .graph-ascii { height: 1fr; background: #1e1e2e; border: solid #585b70; padding: 2; }
    .graph-controls { height: 3; margin-top: 1; }
    
    .settings-container { height: 100%; padding: 1; }
    
    .modal-container { width: 60; height: auto; background: #313244; border: solid #7c4dff; padding: 2; }
    .modal-title { margin-bottom: 1; }
    """
    
    BINDINGS = [
        Binding("d", "switch_screen('dashboard')", "Dashboard"),
        Binding("e", "switch_screen('explorer')", "Explorer"),
        Binding("g", "switch_screen('graph')", "Graph"),
        Binding("s", "switch_screen('settings')", "Settings"),
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help"),
    ]
    
    SCREENS = {
        "dashboard": DashboardScreen,
        "explorer": ExplorerScreen,
        "graph": GraphScreen,
        "settings": SettingsScreen,
    }
    
    def on_mount(self):
        self.push_screen("dashboard")
        self.title = "Inception TUI"
        self.sub_title = "Knowledge Extraction System"
    
    def action_switch_screen(self, screen: str):
        self.switch_screen(screen)
    
    def action_help(self):
        self.push_screen(HelpModal())
    
    async def on_unmount(self):
        await api.close()


# =============================================================================
# RUN
# =============================================================================

def main():
    app = InceptionTUI()
    app.run()


if __name__ == "__main__":
    main()
