# Opia — OpenCode-Compatible AI CLI Agent

> An extensible, multi-provider AI CLI agent with a modular plugin ecosystem.

---

## Overview

**Opia** is a next-generation AI CLI agent designed to be **provider-agnostic** and **extensible**. It combines:

- **Multi-provider LLM support** — OpenAI, Anthropic, Groq, Mistral, OpenRouter, Gemini, Fireworks, Together, DeepSeek
- **Secure credential management** — Keychain → Encrypted file → Environment variables
- **Dynamic model discovery** — Automatically fetch and cache available models
- **Unified request routing** — One interface for all providers
- **Plugin ecosystem** — MCP, Codex CLI, Claude Code, OpenClaw, and native plugins
- **Built-in tools** — Filesystem, Terminal, Git, Search, Web, Editor, Task Manager
- **Beautiful CLI** — Rich output, interactive REPL, streaming responses

---

## Quick Start

```bash
# Install
pip install opia

# Authenticate with a provider
opia login groq
# or use an env key
export GROQ_API_KEY="sk-..."

# Chat with the AI
opia chat "What is the capital of France?"

# Interactive REPL
opia chat --interactive

# List providers
opia provider list

# List models
opia models list

# Check your session
opia whoami
```

---

## Features

### 🔐 Multi-Provider Authentication

Opia supports 9 major LLM providers out of the box. Credentials are stored securely:

1. **System Keychain** (macOS Keychain, Linux Secret Service, Windows Credential Manager)
2. **Encrypted local file** (`~/.opia/credentials.enc` — AES-256-GCM)
3. **Environment variables** (e.g., `GROQ_API_KEY`)

```bash
opia login groq           # Interactive prompt
opia login openai --key sk-...  # Inline key
opia provider use groq    # Set active provider
opia logout groq          # Remove credentials
```

### 🤖 Model Discovery

Opia dynamically fetches available models from each provider, caching them for 1 hour:

```bash
opia models list              # All models across all providers
opia models list --provider groq   # Filter by provider
opia models show llama-3.3-70b-versatile  # Model details
```

### 💬 Chat & Streaming

```bash
opia chat "Explain quantum computing"
opia chat --stream "Write me a poem"
opia chat --file code.py "Review this code"
```

**Interactive REPL mode:**

```bash
$ opia chat --interactive
Opia Chat v0.1.0
Provider: groq  Model: default
Type your message, or :quit / :exit to leave.

You> Hello!

Groq (llama-3.3-70b-versatile):
Hello! How can I help you today?

You> :help
Commands:
  :quit, :exit  — Leave the chat
  :clear        — Clear conversation history
  :help         — Show this help

You> :quit
Goodbye.
```

### 🔧 Built-in Tools

Opia includes 7 first-party tools:

| Tool | Capabilities |
|------|-------------|
| **filesystem** | Read, write, patch, move, search, watch |
| **terminal** | Execute shell commands, stream output, background jobs |
| **search** | Code search, semantic search, workspace indexing |
| **git** | Status, diff, commit, branch, log, patch generation |
| **web** | HTTP requests, web search, API exploration |
| **editor** | Multi-file refactoring, formatting, diagnostics |
| **task_manager** | Planning, checkpoints, task graphs, progress tracking |

### 🔌 Plugin Ecosystem

Opia supports multiple plugin formats:

- **MCP** — Model Context Protocol (stdio, HTTP, SSE)
- **Codex** — OpenAI Codex CLI plugins
- **Claude** — Claude Code plugins
- **OpenClaw** — OpenClaw agent extensions
- **Native** — Opia-first plugins

```bash
opia plugin list
opia plugin install /path/to/plugin
opia plugin load my-plugin
```

---

## Architecture

Opia is built in three layers:

```
┌─────────────────────────────────────────────┐
│  CLI Layer (typer + rich)                   │
│  opia login, opia chat, opia tool ...       │
├─────────────────────────────────────────────┤
│  Orchestrator (integration bridge)            │
│  Auth → Router → Plugins → Tools            │
├─────────────────────────────────────────────┤
│  Core Layer                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Providers│ │ Auth     │ │ Plugins  │    │
│  │ (9 LLMs) │ │ Manager  │ │ (MCP...) │    │
│  └──────────┘ └──────────┘ └──────────┘    │
│  ┌──────────┐ ┌──────────┐                   │
│  │ Models   │ │ Router   │                   │
│  │ Registry │ │ Chat     │                   │
│  └──────────┘ └──────────┘                   │
└─────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design.

---

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

**Quick install:**

```bash
pip install opia
```

**Development install:**

```bash
git clone https://github.com/Chieji/opia.git
cd opia
pip install -e ".[dev]"
pytest
```

---

## Usage

See [USAGE.md](USAGE.md) for the complete command reference.

---

## Configuration

User config is stored in `~/.opia/config.toml`:

```bash
opia config get                 # Show all config
opia config get provider.default
opia config set provider.default groq
opia config set chat.temperature 0.8
```

---

## Supported Providers

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-opus-20240229` |
| Groq | `GROQ_API_KEY` | `llama-3.3-70b-versatile` |
| Mistral | `MISTRAL_API_KEY` | `mistral-large-latest` |
| OpenRouter | `OPENROUTER_API_KEY` | `openai/gpt-4o` |
| Gemini | `GEMINI_API_KEY` | `gemini-2.0-flash` |
| Fireworks | `FIREWORKS_API_KEY` | `accounts/fireworks/models/llama-v3p1-405b-instruct` |
| Together | `TOGETHER_API_KEY` | `togethercomputer/llama-3-70b-instruct` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` |

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=opia --cov-report=html

# Lint
ruff check .
ruff format .

# Type check
mypy opia
```

---

## License

MIT — see [LICENSE](../LICENSE) for details.

---

## Contributors

- **Hermes Agent** — Authentication & Provider System
- **Codex Agent** — Tooling & Plugin Ecosystem
- **Kimi Agent** — CLI, Integration & Orchestration
