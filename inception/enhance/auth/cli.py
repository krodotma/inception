"""
CLI commands for OAuth authentication management.

Provides the 'inception auth' command group:
- inception auth setup [provider]
- inception auth status
- inception auth logout [provider]
"""

import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from inception.enhance.auth import OAuthManager

console = Console()


@click.group(name="auth")
def auth_cli():
    """Manage LLM provider authentication (OAuth)."""
    pass


@auth_cli.command(name="setup")
@click.argument("provider", required=False, default=None)
def auth_setup(provider: str | None):
    """
    Set up authentication for LLM providers.
    
    Opens browser for OAuth login flow.
    
    \b
    Examples:
        inception auth setup           # Setup all providers
        inception auth setup claude    # Setup Claude only
        inception auth setup gemini    # Setup Gemini only
    """
    async def _setup():
        manager = OAuthManager()
        
        providers = [provider] if provider else ["claude", "gemini", "openai"]
        
        for p in providers:
            console.print(f"\n[bold cyan]Setting up {p.upper()}...[/bold cyan]")
            
            try:
                # Check availability first
                if not await manager.providers[p].is_available():
                    console.print(f"[yellow]⚠️  {p} is not reachable, skipping[/yellow]")
                    continue
                
                console.print("Opening browser for authentication...")
                token = await manager.setup(p)
                
                tier_color = {
                    "free": "white",
                    "pro": "green",
                    "max": "blue",
                    "ultra": "magenta",
                    "enterprise": "gold1",
                }.get(token.tier.value, "white")
                
                console.print(
                    f"[bold green]✓[/bold green] {p.upper()} authenticated "
                    f"[{tier_color}]({token.tier.value.upper()} tier)[/{tier_color}]"
                )
                
            except Exception as e:
                console.print(f"[red]✗ {p} failed: {e}[/red]")
    
    asyncio.run(_setup())


@auth_cli.command(name="status")
def auth_status():
    """
    Show authentication status for all providers.
    
    Displays connection status, tier, and available models.
    """
    async def _status():
        manager = OAuthManager()
        status = await manager.status()
        
        table = Table(title="🔐 Authentication Status", border_style="cyan")
        table.add_column("Provider", style="bold")
        table.add_column("Status")
        table.add_column("Tier")
        table.add_column("Expires")
        table.add_column("Models")
        
        for name, info in status.items():
            # Status
            if info["authenticated"] and not info["is_expired"]:
                status_text = "[green]✓ Connected[/green]"
            elif info["authenticated"] and info["is_expired"]:
                status_text = "[yellow]⚠ Expired[/yellow]"
            else:
                status_text = "[dim]○ Not connected[/dim]"
            
            # Tier
            tier = info.get("tier", "—")
            tier_color = {
                "free": "white",
                "pro": "green",
                "max": "blue",
                "ultra": "magenta",
            }.get(tier, "dim")
            tier_text = f"[{tier_color}]{tier.upper() if tier else '—'}[/{tier_color}]"
            
            # Expiry
            expires = info.get("expires_at", "—")
            if expires and expires != "—":
                expires = expires.split("T")[0]  # Just date
            
            # Models
            models = info.get("models", [])
            models_text = ", ".join(models[:3]) + ("..." if len(models) > 3 else "") if models else "—"
            
            table.add_row(
                name.upper(),
                status_text,
                tier_text,
                str(expires),
                models_text,
            )
        
        console.print()
        console.print(table)
        console.print()
        
        # Tips
        if not any(s["authenticated"] and not s["is_expired"] for s in status.values()):
            console.print(Panel(
                "[yellow]No active authentication.[/yellow]\n\n"
                "Run [bold]inception auth setup[/bold] to connect your LLM providers.",
                title="💡 Tip",
                border_style="yellow"
            ))
    
    asyncio.run(_status())


@auth_cli.command(name="logout")
@click.argument("provider", required=False, default=None)
@click.option("--all", "logout_all", is_flag=True, help="Logout from all providers")
def auth_logout(provider: str | None, logout_all: bool):
    """
    Logout from LLM providers.
    
    \b
    Examples:
        inception auth logout claude   # Logout from Claude
        inception auth logout --all    # Logout from all providers
    """
    async def _logout():
        manager = OAuthManager()
        
        if logout_all:
            provider_arg = None
        elif not provider:
            console.print("[red]Specify a provider or use --all[/red]")
            return
        else:
            provider_arg = provider
        
        await manager.logout(provider_arg)
        
        if logout_all:
            console.print("[green]✓ Logged out from all providers[/green]")
        else:
            console.print(f"[green]✓ Logged out from {provider}[/green]")
    
    asyncio.run(_logout())


@auth_cli.command(name="refresh")
@click.argument("provider", required=False, default=None)
def auth_refresh(provider: str | None):
    """
    Refresh authentication tokens.
    
    \b
    Examples:
        inception auth refresh         # Refresh all tokens
        inception auth refresh claude  # Refresh Claude only
    """
    async def _refresh():
        manager = OAuthManager()
        
        providers = [provider] if provider else ["claude", "gemini", "openai"]
        
        for p in providers:
            try:
                token = await manager.get_token(p)
                
                if not token.is_expired:
                    console.print(f"[green]✓ {p} token is valid[/green]")
                else:
                    new_token = await manager.providers[p].refresh(token)
                    manager.storage.store(p, new_token)
                    console.print(f"[green]✓ {p} token refreshed[/green]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠ {p}: {e}[/yellow]")
    
    asyncio.run(_refresh())


# Register with main CLI
def register_auth_cli(main_cli: click.Group):
    """Register auth commands with main CLI."""
    main_cli.add_command(auth_cli)
