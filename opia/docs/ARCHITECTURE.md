# Architecture

## Overview

Opia is a three-layer architecture designed for modularity, extensibility, and provider-agnosticism.

```
┌─────────────────────────────────────────────┐
│  LAYER 3: CLI & User Interface              │
│  ┌─────────────────────────────────────┐    │
│  │ Typer CLI + Rich Console           │    │
│  │ opia login, chat, tool, plugin ...│    │
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  LAYER 2: Orchestrator (Integration)        │
│  ┌─────────────────────────────────────┐    │
│  │ OpiaOrchestrator                   │    │
│  │ Auth → Router → Plugins → Tools     │    │
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  LAYER 1: Core Systems                      │
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

## Layer 1: Core Systems

### Provider System (`opia/providers/`)

Each provider implements `BaseProvider`:

```python
class BaseProvider(ABC):
    name: str
    base_url: str

    async def authenticate(self, credential: str) -> bool
    async def list_models(self) -> list[ModelInfo]
    async def chat(self, messages, model, **kwargs) -> ChatResponse
    async def embeddings(self, input, model, **kwargs) -> EmbeddingsResponse
    async def validate_credentials(self, credential: str) -> bool
```

**Supported providers:** OpenAI, Anthropic, Groq, Mistral, OpenRouter, Gemini, Fireworks, Together, DeepSeek.

### Authentication (`opia/auth/`)

Credential resolution order (highest priority first):

1. **System Keychain** — macOS Keychain, Linux Secret Service, Windows Credential Manager
2. **Encrypted file** — `~/.opia/credentials.enc` (AES-256-GCM via PBKDF2)
3. **Environment variables** — `GROQ_API_KEY`, `OPENAI_API_KEY`, etc.

All credentials are validated against the provider's `/models` endpoint before storage. Invalid credentials are never persisted.

### Session (`opia/auth/session.py`)

Tracks active provider and model in `~/.opia/session.json` (no credentials stored).

### Model Registry (`opia/models/`)

Discovers and caches available models with 1-hour TTL.

### Unified Router (`opia/router/chat.py`)

The single entry point for all chat requests. Handles:
- Provider resolution (arg → session → error)
- Credential loading
- Model selection
- Retry logic (3 attempts with exponential backoff)
- Response normalization

## Layer 2: Orchestrator (`opia/core/orchestrator.py`)

The integration bridge that connects all subsystems:

```python
class OpiaOrchestrator:
    auth: AuthManager
    router: UnifiedChatRouter
    models: ModelRegistry

    async def chat(messages, provider, model) -> ChatResponse
    async def chat_stream(messages, provider, model) -> AsyncIterator[ChatChunk]
    async def list_models(provider) -> list[ModelInfo]
    async def discover_providers() -> list[ProviderInfo]
    def list_tools() -> list[ToolInfo]
    def list_plugins() -> list[PluginInfo]
    async def execute_tool(name, **kwargs) -> ToolResult
```

The orchestrator is **plugin-aware but not plugin-dependent**. If the plugin system (built by Codex) is not yet available, it gracefully degrades.

## Layer 3: CLI (`opia/cli/`)

Built on **Typer** with **Rich** for output:

- `main.py` — Root app with global flags, async wrapper, shared state
- `login.py` — `opia login <provider> [--key]`
- `logout.py` — `opia logout [provider]`
- `providers.py` — `opia provider list / use / show`
- `models.py` — `opia models list / show`
- `session.py` — `opia session show / clear`
- `chat.py` — `opia chat [message] [--provider] [--model] [--file] [--stream] [--interactive]`
- `tool.py` — `opia tool list / <name> [args]`
- `plugin.py` — `opia plugin list / install / load / unload`
- `config.py` — `opia config get / set`

### Async Commands

All CLI commands wrap async operations via `asyncio.run()`:

```python
def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return loop.run_until_complete(coro)
```

### REPL Mode

The interactive chat mode uses `readline` for history and `rich.prompt` for input, with `rich.live` for streaming output.

## Plugin Ecosystem (`opia/plugins/` — built by Codex)

### Adapters

- **MCP adapter** — stdio, HTTP, SSE transport for Model Context Protocol
- **Codex adapter** — OpenAI Codex CLI plugin compatibility
- **Claude adapter** — Claude Code plugin compatibility
- **OpenClaw adapter** — OpenClaw agent extension compatibility
- **Native adapter** — Direct Opia plugin loading

### Built-in Tools

- filesystem, terminal, search, git, web, editor, task_manager

## Data Flow

```
User → CLI → Orchestrator → Router → Provider → LLM API
                ↓
            Auth Manager (loads credentials)
                ↓
            Plugin Manager (loads tools if needed)
                ↓
            Tool Sandbox (executes tool calls)
```

## Security Model

1. **Credential storage** — Never plaintext; encrypted at rest
2. **Permission system** — Each plugin/tool declares required permissions
3. **Sandbox** — Plugin execution with explicit allowlists
4. **Audit logging** — Every tool execution logged with plugin_id, tool, args, result

## Build by Agent

- **Hermes Agent** — Layer 1 (providers, auth, models, router)
- **Codex Agent** — Layer 1 (plugins, adapters, tools, sandbox)
- **Kimi Agent** — Layer 2 + Layer 3 (orchestrator, CLI, tests, docs)
