"""Opia models commands — list and show available models."""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from opia.cli.main import _get_orchestrator, run_async

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="models", help="Discover and list available models.", no_args_is_help=True)


@app.command(name="list")
def models_list(
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Filter by provider."
    ),
) -> None:
    """List available models (dynamically fetched from providers)."""
    orch = _get_orchestrator()

    stdout_console.print("[dim]Fetching models from providers…[/dim]\n")

    models = run_async(orch.list_models(provider))

    if not models:
        stdout_console.print(
            "[yellow]No models found.[/yellow] "
            "[dim]Try logging in first: [bold]opia login <provider>[/bold][/dim]"
        )
        return

    table = Table(title="Available Models", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Provider", style="dim")
    table.add_column("Context", justify="right")
    table.add_column("Streaming", justify="center")
    table.add_column("Vision", justify="center")

    for m in models:
        stream = "[green]✓[/green]" if m.supports_streaming else "[red]✗[/red]"
        vision = "[green]✓[/green]" if m.supports_vision else "[red]✗[/red]"
        table.add_row(
            m.id,
            m.name,
            m.provider,
            str(m.context_length),
            stream,
            vision,
        )

    stdout_console.print(table)
    stdout_console.print(f"\n[dim]Total: {len(models)} models[/dim]")


@app.command(name="show")
def models_show(
    model_id: str = typer.Argument(..., help="Model ID to inspect."),
) -> None:
    """Show detailed information about a specific model."""
    orch = _get_orchestrator()
    m = orch.get_model(model_id)

    if not m:
        stdout_console.print(f"[red]Model not found: {model_id}[/red]")
        raise typer.Exit(1)

    table = Table(show_header=False, title=f"Model: {m.id}")
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("ID", m.id)
    table.add_row("Name", m.name)
    table.add_row("Provider", m.provider)
    table.add_row("Context Length", str(m.context_length))
    table.add_row("Streaming", "Yes" if m.supports_streaming else "No")
    table.add_row("Vision", "Yes" if m.supports_vision else "No")
    if m.metadata:
        table.add_row("Metadata", str(m.metadata))

    stdout_console.print(table)
