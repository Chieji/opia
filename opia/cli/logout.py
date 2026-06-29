"""Opia logout command — remove stored credentials."""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from opia.cli.main import _get_orchestrator, run_async

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="logout", help="Remove stored credentials.")


@app.command(name="")
def logout_cmd(
    provider: Optional[str] = typer.Argument(
        None, help="Provider to logout from (omit for all)."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt."
    ),
) -> None:
    """Remove stored credentials for a provider (or all providers)."""
    orch = _get_orchestrator()

    targets = [provider] if provider else None
    target_label = provider if provider else "all providers"

    if not yes:
        from rich.prompt import Confirm
        if not Confirm.ask(f"Remove credentials for {target_label}?"):
            stdout_console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    run_async(orch.auth.logout(targets[0] if targets else None))

    stdout_console.print(Panel(
        f"[green]Logged out from [bold]{target_label}[/bold].[/green]",
        border_style="green",
    ))
