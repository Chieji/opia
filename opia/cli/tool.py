"""Opia tool command — list and execute built-in or plugin tools."""
from __future__ import annotations

from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from opia.cli.main import _get_orchestrator, run_async

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="tool", help="Execute built-in or plugin tools.", no_args_is_help=True)


@app.command(name="list")
def tool_list() -> None:
    """List all available tools."""
    orch = _get_orchestrator()
    tools = orch.list_tools()

    if not tools:
        stdout_console.print(
            "[yellow]No tools available yet.[/yellow]\n"
            "[dim]The plugin ecosystem is still being built.[/dim]"
        )
        return

    table = Table(title="Available Tools", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Permissions", style="dim")
    table.add_column("Plugin", style="dim")

    for t in tools:
        table.add_row(
            t.name,
            t.description,
            ", ".join(t.permissions[:3]) + ("…" if len(t.permissions) > 3 else ""),
            t.plugin_name or "[dim]builtin[/dim]",
        )

    stdout_console.print(table)


@app.command(name="")
def tool_exec(
    tool_name: str = typer.Argument(..., help="Tool name to execute."),
    args: Optional[List[str]] = typer.Argument(
        None, help="Tool arguments as key=value pairs."
    ),
) -> None:
    """Execute a tool with the given arguments."""
    orch = _get_orchestrator()

    # Parse key=value arguments
    kwargs = {}
    if args:
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                kwargs[key] = value

    try:
        result = run_async(orch.execute_tool(tool_name, **kwargs))
        stdout_console.print(Panel(
            f"[green]Tool [bold]{tool_name}[/bold] executed successfully.[/green]\n\n"
            f"{result}",
            border_style="green",
        ))
    except Exception as e:
        stdout_console.print(Panel(
            f"[red]Tool [bold]{tool_name}[/bold] failed:[/red] {e}",
            border_style="red",
        ))
        raise typer.Exit(1)
