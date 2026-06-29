"""Opia chat command — send messages to the active AI provider."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from opia.cli.main import _get_orchestrator, run_async
from opia.providers.base import Message

console = Console(stderr=True)
stdout_console = Console()

app = typer.Typer(name="chat", help="Send messages to the active AI provider.", no_args_is_help=True)


@app.command(name="")
def chat_cmd(
    message: Optional[str] = typer.Argument(
        None, help="Message to send (omit for interactive mode)."
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Override provider for this request."
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Override model for this request."
    ),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Attach a file (read as text and append to message)."
    ),
    stream: bool = typer.Option(
        False, "--stream", "-s", help="Stream the response in real-time."
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Launch an interactive REPL session."
    ),
) -> None:
    """Send a message to the active AI provider, or start an interactive REPL."""
    orch = _get_orchestrator()

    if interactive or message is None:
        _interactive_repl(orch, provider, model)
        return

    # Build messages
    messages: List[Message] = []
    content = message

    if file and file.exists():
        try:
            file_content = file.read_text(encoding="utf-8")
            content += f"\n\n[File: {file.name}]\n{file_content}"
        except Exception as e:
            stdout_console.print(f"[red]Failed to read file {file}: {e}[/red]")
            raise typer.Exit(1)

    messages.append(Message(role="user", content=content))

    # Show a spinner while the request is in flight
    from rich.status import Status
    with Status("[dim]Thinking…[/dim]", console=stdout_console) as status:
        try:
            if stream:
                _stream_chat(orch, messages, provider, model)
            else:
                response = run_async(orch.chat(
                    messages=messages,
                    provider=provider,
                    model=model,
                ))
                status.stop()
                stdout_console.print(Markdown(response.content))
        except Exception as e:
            status.stop()
            stdout_console.print(Panel(
                f"[red]Chat failed:[/red] {e}",
                border_style="red",
            ))
            raise typer.Exit(1)


def _stream_chat(orch, messages, provider, model):
    """Stream chat response with live rendering."""
    full_text = ""
    with Live(console=stdout_console, refresh_per_second=10) as live:
        async def _do_stream():
            nonlocal full_text
            async for chunk in await orch.chat_stream(
                messages=messages,
                provider=provider,
                model=model,
            ):
                full_text += chunk.content
                live.update(Markdown(full_text))
                if chunk.done:
                    break

        asyncio.get_event_loop().run_until_complete(_do_stream())


def _interactive_repl(orch, default_provider, default_model):
    """Interactive REPL with history and rich formatting."""
    import readline

    orch = _get_orchestrator()
    info = orch.auth.whoami()

    if info["status"] == "anonymous":
        stdout_console.print(Panel(
            "[yellow]Not authenticated.[/yellow]\n"
            "Run [bold]opia login <provider>[/bold] first.",
            border_style="yellow",
        ))
        raise typer.Exit(1)

    provider = default_provider or info.get("provider", "")
    model = default_model or info.get("model", "")

    stdout_console.print(Panel(
        f"[bold cyan]Opia Chat[/bold cyan]  [dim]v0.1.0[/dim]\n"
        f"Provider: [bold]{provider}[/bold]  Model: [bold]{model or 'default'}[/bold]\n"
        f"[dim]Type your message, or [bold]:quit[/bold] / [bold]:exit[/bold] to leave.[/dim]",
        border_style="cyan",
    ))

    messages: List[Message] = []

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
        except (EOFError, KeyboardInterrupt):
            stdout_console.print("\n[dim]Goodbye.[/dim]")
            break

        if user_input.strip().lower() in (":quit", ":exit", ":q"):
            stdout_console.print("[dim]Goodbye.[/dim]")
            break

        if user_input.strip().startswith(":"):
            # Handle REPL commands
            cmd = user_input.strip()[1:].lower()
            if cmd == "clear":
                messages.clear()
                stdout_console.print("[dim]Conversation cleared.[/dim]")
                continue
            if cmd == "help":
                stdout_console.print(
                    "[bold]Commands:[/bold]\n"
                    "  :quit, :exit  — Leave the chat\n"
                    "  :clear        — Clear conversation history\n"
                    "  :help         — Show this help\n"
                )
                continue
            stdout_console.print(f"[red]Unknown command: {cmd}[/red]")
            continue

        messages.append(Message(role="user", content=user_input))

        from rich.status import Status
        with Status("[dim]Thinking…[/dim]", console=stdout_console) as status:
            try:
                response = run_async(orch.chat(
                    messages=messages,
                    provider=provider,
                    model=model,
                ))
                status.stop()
                messages.append(Message(role="assistant", content=response.content))

                stdout_console.print(f"\n[bold cyan]{response.provider}[/bold cyan] ([dim]{response.model}[/dim]):")
                stdout_console.print(Markdown(response.content))
            except Exception as e:
                status.stop()
                stdout_console.print(f"[red]Error: {e}[/red]")
