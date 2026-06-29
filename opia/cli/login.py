"""Opia login command — authenticate with an AI provider."""
from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from opia.cli.main import _get_orchestrator, run_async

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="login", help="Authenticate with an AI provider.", no_args_is_help=True)


@app.command(name="")
def login_cmd(
    provider: str = typer.Argument(..., help="Provider name (e.g., openai, groq, anthropic)."),
    key: Optional[str] = typer.Option(
        None, "--key", "-k", help="API key (or set env var)."
    ),
) -> None:
    """Authenticate with an AI provider and store credentials securely."""

    # Show available providers if the user types something ambiguous
    orch = _get_orchestrator()
    providers = asyncio.get_event_loop().run_until_complete(
        orch.discover_providers()
    )
    provider_names = [p.name for p in providers]

    if provider not in provider_names:
        stdout_console.print(
            f"[red]Unknown provider: {provider}[/red]"
        )
        stdout_console.print("Available providers: " + ", ".join(f"[cyan]{p}[/cyan]" for p in provider_names))
        raise typer.Exit(1)

    # Prompt for key if not provided
    credential = key
    if not credential:
        env_var = f"{provider.upper()}_API_KEY"
        import os
        credential = os.environ.get(env_var)
        if not credential:
            credential = Prompt.ask(
                f"Enter your [bold]{provider}[/bold] API key", password=True
            )

    if not credential or not credential.strip():
        stdout_console.print("[red]No API key provided.[/red]")
        raise typer.Exit(1)

    stdout_console.print(f"[dim]Validating credentials with {provider}…[/dim]")

    result = run_async(orch.auth.login(provider, key=credential))

    if result:
        stdout_console.print(Panel(
            f"[green]Successfully authenticated with [bold]{provider}[/bold][/green]",
            border_style="green",
        ))
    else:
        stdout_console.print(Panel(
            f"[red]Invalid credentials for [bold]{provider}[/bold].[/red]\n"
            "Check your API key and try again.",
            border_style="red",
        ))
        raise typer.Exit(1)
