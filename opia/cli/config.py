"""Opia config command — get and set configuration values."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from opia.cli.main import _get_orchestrator

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="config", help="Get or set configuration values.", no_args_is_help=True)

OPIA_CONFIG = Path.home() / ".opia" / "config.toml"


def _load_config() -> dict:
    """Load config from ~/.opia/config.toml."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    if not OPIA_CONFIG.exists():
        return {}
    try:
        with open(OPIA_CONFIG, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _save_config(data: dict) -> None:
    """Save config to ~/.opia/config.toml."""
    import tomli_w
    OPIA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(OPIA_CONFIG, "wb") as f:
        tomli_w.dump(data, f)


def _get_nested(data: dict, key: str):
    """Get a nested config value by dot-path."""
    parts = key.split(".")
    for part in parts:
        if not isinstance(data, dict) or part not in data:
            return None
        data = data[part]
    return data


def _set_nested(data: dict, key: str, value):
    """Set a nested config value by dot-path."""
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in data or not isinstance(data[part], dict):
            data[part] = {}
        data = data[part]
    data[parts[-1]] = value


@app.command(name="get")
def config_get(
    key: Optional[str] = typer.Argument(
        None, help="Config key to retrieve (supports dot-path like 'provider.default')."
    ),
) -> None:
    """Get a configuration value, or list all config if no key is given."""
    data = _load_config()

    if key is None:
        # Show all config
        if not data:
            stdout_console.print("[dim]No custom config set.[/dim]")
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Key", style="bold")
        table.add_column("Value")
        _flatten_dict(data, table)
        stdout_console.print(table)
        return

    value = _get_nested(data, key)
    if value is None:
        stdout_console.print(f"[dim]Key '{key}' is not set.[/dim]")
    else:
        stdout_console.print(f"[bold]{key}[/bold] = {value}")


def _flatten_dict(data: dict, table: Table, prefix: str = ""):
    """Flatten nested dict into table rows."""
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            _flatten_dict(v, table, full_key)
        else:
            table.add_row(full_key, str(v))


@app.command(name="set")
def config_set(
    key: str = typer.Argument(..., help="Config key to set (supports dot-path)."),
    value: str = typer.Argument(..., help="Value to set."),
) -> None:
    """Set a configuration value."""
    data = _load_config()
    _set_nested(data, key, value)
    _save_config(data)
    stdout_console.print(Panel(
        f"[green]Set[/green] [bold]{key}[/bold] = [bold]{value}[/bold]",
        border_style="green",
    ))
