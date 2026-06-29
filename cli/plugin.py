"""Opia plugin command — list, install, load, and unload plugins."""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from opia.cli.main import _get_orchestrator, run_async

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="plugin", help="Manage plugins and adapters.", no_args_is_help=True)


@app.command(name="list")
def plugin_list() -> None:
    """List installed plugins."""
    orch = _get_orchestrator()
    plugins = orch.list_plugins()

    if not plugins:
        stdout_console.print(
            "[yellow]No plugins installed yet.[/yellow]\n"
            "[dim]The plugin ecosystem is still being built.[/dim]\n"
            "[dim]Install plugins with: [bold]opia plugin install <path_or_url>[/bold][/dim]"
        )
        return

    table = Table(title="Installed Plugins", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Version")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Tools", style="dim")

    for p in plugins:
        status = "[green]loaded[/green]" if p.loaded else "[dim]unloaded[/dim]"
        table.add_row(p.name, p.version, p.type, status, ", ".join(p.tools[:3]))

    stdout_console.print(table)


@app.command(name="install")
def plugin_install(
    source: str = typer.Argument(..., help="Plugin source: local path, git URL, or registry name."),
) -> None:
    """Install a plugin from a local path, git URL, or registry."""
    stdout_console.print(Panel(
        "[yellow]Plugin installation is not yet fully implemented.[/yellow]\n"
        "[dim]The plugin ecosystem is being built by the Codex agent.[/dim]\n\n"
        f"Source provided: [bold]{source}[/bold]\n\n"
        "When ready, plugins will be installed to: [bold]~/.opia/plugins/[/bold]",
        border_style="yellow",
    ))


@app.command(name="load")
def plugin_load(
    plugin_id: str = typer.Argument(..., help="Plugin ID to load."),
) -> None:
    """Load a previously installed plugin."""
    stdout_console.print(Panel(
        "[yellow]Plugin loading is not yet fully implemented.[/yellow]\n"
        "[dim]The plugin ecosystem is being built by the Codex agent.[/dim]",
        border_style="yellow",
    ))


@app.command(name="unload")
def plugin_unload(
    plugin_id: str = typer.Argument(..., help="Plugin ID to unload."),
) -> None:
    """Unload a loaded plugin."""
    stdout_console.print(Panel(
        "[yellow]Plugin unloading is not yet fully implemented.[/yellow]\n"
        "[dim]The plugin ecosystem is being built by the Codex agent.[/dim]",
        border_style="yellow",
    ))
