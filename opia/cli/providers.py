"""Opia provider commands — list, use, and show providers."""
from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from opia.cli.main import _get_orchestrator, run_async

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="provider", help="Manage AI providers.", no_args_is_help=True)


@app.command(name="list")
def provider_list() -> None:
    """List all configured providers and their auth status."""
    orch = _get_orchestrator()
    providers = run_async(orch.discover_providers())

    table = Table(title="Configured Providers", show_header=True, header_style="bold cyan")
    table.add_column("Provider", style="bold")
    table.add_column("Display Name")
    table.add_column("Auth", justify="center")
    table.add_column("Default Model", style="dim")
    table.add_column("OAuth", justify="center")

    for p in providers:
        auth_icon = "[green]✓[/green]" if p.has_credentials else "[red]✗[/red]"
        oauth_icon = "[dim]✓[/dim]" if p.supports_oauth else "[dim]—[/dim]"
        active = "[bold yellow]*[/bold yellow] " if p.name == orch.auth._session.active_provider else ""
        table.add_row(
            active + p.name,
            p.display_name,
            auth_icon,
            p.default_model,
            oauth_icon,
        )

    stdout_console.print(table)
    if not any(p.has_credentials for p in providers):
        stdout_console.print(
            "\n[dim]No providers authenticated. Run[/dim] [bold]opia login <provider>[/bold] [dim]to start.[/dim]"
        )


@app.command(name="use")
def provider_use(
    provider: str = typer.Argument(..., help="Provider name to set as active."),
) -> None:
    """Set the active provider for subsequent requests."""
    orch = _get_orchestrator()
    providers = run_async(orch.discover_providers())
    names = [p.name for p in providers]

    if provider not in names:
        stdout_console.print(f"[red]Unknown provider: {provider}[/red]")
        stdout_console.print("Available: " + ", ".join(f"[cyan]{n}[/cyan]" for n in names))
        raise typer.Exit(1)

    cfg = next((p for p in providers if p.name == provider), None)
    if cfg:
        orch.auth._session.set_active(provider, cfg.default_model)
        stdout_console.print(Panel(
            f"[green]Active provider set to [bold]{provider}[/bold][/green]\n"
            f"Default model: [dim]{cfg.default_model}[/dim]",
            border_style="green",
        ))


@app.command(name="show")
def provider_show(
    provider: str = typer.Argument(..., help="Provider name to inspect."),
) -> None:
    """Show detailed information about a provider."""
    from opia.config.loader import load_providers_config
    cfg = load_providers_config()
    if provider not in cfg.providers:
        stdout_console.print(f"[red]Unknown provider: {provider}[/red]")
        raise typer.Exit(1)

    p = cfg.providers[provider]
    orch = _get_orchestrator()
    has_cred = orch.auth._session.active_provider == provider

    table = Table(show_header=False, title=f"Provider: {p.name}")
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("Name", p.name)
    table.add_row("Base URL", p.base_url)
    table.add_row("Auth Type", p.auth_type)
    table.add_row("Env Var", p.env_var)
    table.add_row("Default Model", p.default_model)
    table.add_row("OAuth", "Yes" if p.supports_oauth else "No")
    table.add_row("Authenticated", "[green]Yes[/green]" if has_cred else "[red]No[/red]")

    stdout_console.print(table)
