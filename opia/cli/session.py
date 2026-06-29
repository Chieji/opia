"""Opia session commands — show and clear the active session."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from opia.cli.main import _get_orchestrator

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="session", help="Show or clear the active session.")


@app.command(name="show")
def session_show() -> None:
    """Display the current active session details."""
    orch = _get_orchestrator()
    info = orch.auth.whoami()

    if info["status"] == "anonymous":
        stdout_console.print(Panel(
            "[yellow]No active session.[/yellow]\n"
            "Run [bold]opia login <provider>[/bold] to authenticate.",
            title="Session",
            border_style="yellow",
        ))
        return

    table = Table(show_header=False, title="Active Session")
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("Provider", info["provider"])
    table.add_row("Model", info["model"] or "[dim]default[/dim]")
    table.add_row("Status", f"[bold]{info['auth_status']}[/bold]")
    if info.get("last_used"):
        table.add_row("Last Used", info["last_used"])
    if info.get("created_at"):
        table.add_row("Created", info["created_at"])

    stdout_console.print(table)


@app.command(name="clear")
def session_clear(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Clear the active session (does not delete credentials)."""
    orch = _get_orchestrator()

    if not yes:
        from rich.prompt import Confirm
        if not Confirm.ask("Clear the active session?"):
            stdout_console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    orch.auth._session.clear()
    stdout_console.print(Panel(
        "[green]Session cleared.[/green] Credentials are still stored.",
        border_style="green",
    ))
