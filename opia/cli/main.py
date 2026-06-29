"""Opia CLI root — Typer app with Rich console, async support, and global flags."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from opia import __version__

# Rich console for beautiful output
console = Console(stderr=True)
stdout_console = Console()

# Shared state
app_state: dict = {}


def _get_orchestrator():
    """Lazy-load the orchestrator (avoids import overhead on --help)."""
    from opia.core.orchestrator import OpiaOrchestrator
    if "orchestrator" not in app_state:
        app_state["orchestrator"] = OpiaOrchestrator()
    return app_state["orchestrator"]


# ───────────────────────────────────────────────
# Typer app with async helper
# ───────────────────────────────────────────────

app = typer.Typer(
    name="opia",
    help="Opia — OpenCode-Compatible AI CLI Agent",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def run_async(coro):
    """Run an async coroutine from a sync Typer command."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import nest_asyncio
    nest_asyncio.apply()
    return loop.run_until_complete(coro)


# ───────────────────────────────────────────────
# Global callback — version, verbosity
# ───────────────────────────────────────────────


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", is_flag=True, help="Show version and exit."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", help="Enable verbose output."
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress non-error output."
    ),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to custom config file."
    ),
) -> None:
    """Opia — OpenCode-Compatible AI CLI Agent."""
    if version:
        stdout_console.print(f"[bold cyan]Opia[/bold cyan] [dim]v{__version__}[/dim]")
        raise typer.Exit(0)

    app_state["verbose"] = verbose
    app_state["quiet"] = quiet
    app_state["config_path"] = config_path

    if quiet:
        console.quiet = True
        stdout_console.quiet = True


# ───────────────────────────────────────────────
# Sub-command imports (register them)
# ───────────────────────────────────────────────

from opia.cli import login, logout, providers, models, session, chat, tool, plugin, config  # noqa: E402

app.add_typer(login.app, name="login", help="Authenticate with an AI provider.")
app.add_typer(logout.app, name="logout", help="Remove stored credentials.")
app.add_typer(providers.app, name="provider", help="Manage AI providers.")
app.add_typer(models.app, name="models", help="Discover and list available models.")
app.add_typer(session.app, name="session", help="Show or clear the active session.")
app.add_typer(chat.app, name="chat", help="Send messages to the active AI provider.")
app.add_typer(tool.app, name="tool", help="Execute built-in or plugin tools.")
app.add_typer(plugin.app, name="plugin", help="Manage plugins and adapters.")
app.add_typer(config.app, name="config", help="Get or set configuration values.")


# ───────────────────────────────────────────────
# whoami  (top-level convenience)
# ───────────────────────────────────────────────


@app.command(name="whoami")
def whoami_cmd() -> None:
    """Show the current active provider and session status."""
    orch = _get_orchestrator()
    info = orch.auth.whoami()

    if info["status"] == "anonymous":
        stdout_console.print(Panel(
            "[yellow]Not authenticated[/yellow]\n"
            "Run [bold]opia login <provider>[/bold] to get started.",
            title="Opia Session",
            border_style="yellow",
        ))
        return

    status_color = "green" if info.get("auth_status") == "authenticated" else "red"
    table_text = Text()
    table_text.append(f"Provider: ", style="dim")
    table_text.append(f"{info['provider']}\n", style="bold cyan")
    table_text.append(f"Model:    ", style="dim")
    table_text.append(f"{info['model'] or 'default'}\n", style="bold")
    table_text.append(f"Status:   ", style="dim")
    table_text.append(f"{info['auth_status']}\n", style=f"bold {status_color}")
    if info.get("last_used"):
        table_text.append(f"Last used: ", style="dim")
        table_text.append(f"{info['last_used']}", style="italic")

    stdout_console.print(Panel(table_text, title="Opia Session", border_style="cyan"))
