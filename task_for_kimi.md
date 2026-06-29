# Task Assignment: Kimi (Main Agent) — Opia CLI, Integration & Orchestration

> **Project:** Opia — OpenCode-Compatible AI CLI Agent  
> **My Domain:** Part 3 — CLI Interface, Integration, Orchestration, Packaging  
> **Source Spec:** `C:\Users\donpr\Dropbox\k\OP\Opia_Architecture_Engineering_Spec.pdf`

---

## 1. My Mission

Build the **user-facing layer** and **integration glue** of Opia. I own the CLI commands, the main entry point, the packaging, the integration tests, and the final orchestration that ties Hermes's provider system to Codex's plugin ecosystem. I make Opia **feel** like a cohesive product.

---

## 2. Directory Ownership

I own and must create:

```
opia/
├── __init__.py          # Package init, version
├── __main__.py          # Entry point: python -m opia
│
├── cli/                 # CLI commands (Hermes owns auth impl, I own CLI interface)
│   ├── __init__.py
│   ├── main.py          # Typer/Click root app
│   ├── login.py         # opia login <provider>
│   ├── logout.py        # opia logout [provider]
│   ├── providers.py     # opia provider list / use <provider>
│   ├── models.py        # opia models list
│   ├── session.py       # opia session show / clear
│   ├── chat.py          # opia chat [message] (--provider, --model, --file)
│   ├── tool.py          # opia tool <tool_name> [args...]
│   ├── plugin.py        # opia plugin list / install / load / unload
│   └── config.py        # opia config get / set
│
├── core/
│   └── orchestrator.py  # The bridge: connects auth → router → plugins → tools
│
├── tests/               # Integration tests (full-stack)
│   ├── conftest.py
│   ├── test_cli.py      # CLI command tests
│   ├── test_e2e.py      # End-to-end: login → chat → tool
│   └── test_integration.py  # Auth + Router + Plugin together
│
├── docs/                # User-facing documentation
│   ├── README.md
│   ├── INSTALL.md
│   ├── USAGE.md
│   └── ARCHITECTURE.md
│
pyproject.toml           # Poetry/PDM/hatch packaging
setup.py                 # Fallback entry
requirements.txt         # Lockfile
.gitignore
LICENSE
```

---

## 3. Technical Stack

- **CLI framework:** `typer` (Rich + Click + Python 3.6 type hints = best DX)
- **Async CLI:** `anyio` or `asyncio.run()` wrapping for async provider calls
- **Rich output:** `rich` for tables, panels, spinners, progress bars, Markdown rendering
- **Config persistence:** `pydantic-settings` + `toml` for user config (`~/.opia/config.toml`)
- **Packaging:** `pyproject.toml` with `poetry` or `hatch`
- **Testing:** `pytest` + `pytest-asyncio` + `pytest-cov` + `anyio` backend
- **Integration:** I connect `Hermes.auth` → `Hermes.router` → `Codex.plugins` → `Codex.tools`

---

## 4. Detailed Specifications

### 4.1 CLI Commands (All async-capable)

```bash
# Authentication
opia login <provider> [--key <api_key>]
opia logout [provider]
opia whoami

# Provider & Model Management
opia provider list
opia provider use <provider>
opia provider show <provider>
opia models list [--provider <provider>]
opia models show <model_id>

# Session
opia session show
opia session clear

# Chat (the main event)
opia chat ["<message>"] [--provider <provider>] [--model <model>] [--file <path>] [--stream]
opia chat --interactive          # REPL mode

# Tools
opia tool list
opia tool <tool_name> [args...]

# Plugins
opia plugin list
opia plugin install <source>
opia plugin load <plugin_id>
opia plugin unload <plugin_id>

# Config
opia config get <key>
opia config set <key> <value>
```

### 4.2 `cli/main.py` — Root Typer App

- Use `typer` with `rich` console for beautiful output
- Async support via `asyncio.run()` wrapper in each command
- Global `--verbose` / `--quiet` flags
- Global `--config` flag for custom config path
- Rich error handling with actionable suggestions

### 4.3 `core/orchestrator.py` — The Integration Bridge

This is my **masterpiece**. It wires everything together:

```python
class OpiaOrchestrator:
    """The central conductor. Connects Auth → Router → Plugins → Tools."""

    def __init__(self):
        self.auth = AuthManager()
        self.router = UnifiedChatRouter()
        self.plugins = PluginManager()
        self.models = ModelRegistry()

    async def initialize(self):
        """Load config, discover plugins, set active provider."""
        ...

    async def chat(self, message: str, **kwargs) -> str:
        """1. Resolve provider/model → 2. Load tools → 3. Call router → 4. Return response"""
        # Get available tools from plugin registry
        # Format them for the LLM (OpenAI/Anthropic function format)
        # Pass to router with tool definitions
        # If LLM requests tool call, execute via sandbox and return result
        ...

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Direct tool execution via plugin system."""
        ...
```

### 4.4 `tests/` — Integration Test Suite

- **Test CLI commands:** Use `typer.testing.CliRunner` for command testing
- **Test E2E flow:** `login` → `list models` → `chat` → `tool execute` → `logout`
- **Test integration:** AuthManager + Router + PluginManager working together
- **Mock external APIs:** Use `respx` (httpx mock) or `pytest-httpx` for provider API mocking
- **Target coverage:** 80%+ overall, 100% on CLI commands

### 4.5 `pyproject.toml` — Packaging

```toml
[project]
name = "opia"
version = "0.1.0"
description = "OpenCode-Compatible AI CLI Agent"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.12.0",
    "rich>=13.0",
    "httpx>=0.27",
    "keyring>=25.0",
    "cryptography>=42.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "aiofiles>=23.0",
    "anyio>=4.0",
    # ... (Hermes's deps + Codex's deps)
]

[project.scripts]
opia = "opia.cli.main:app"

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "pytest-cov", "respx", "ruff", "mypy"]
```

---

## 5. Integration Points (My Responsibility)

| Component | Owned By | My Integration Role |
|-----------|----------|---------------------|
| `AuthManager` | Hermes | Import, call `login/logout/whoami` from CLI commands |
| `UnifiedChatRouter` | Hermes | Import, call `chat()` from `opia chat` command; pass tool definitions |
| `ModelRegistry` | Hermes | Import, call `list_models()` from `opia models` command |
| `PluginManager` | Codex | Import, call `discover/load/unload` from `opia plugin` command |
| `PluginRegistry` | Codex | Import, call `get_tool/list_tools` from `opia tool` command |
| `BaseTool` | Codex | Import, use `execute()` for direct tool calls |
| `BaseProvider` | Hermes | Import only if needed for type hints |

---

## 6. Skills & Tools to Use

| Skill | Why | How to Use |
|-------|-----|------------|
| `swarm-coding` | Coordinate final integration with Hermes + Codex branches | Merge their work, resolve conflicts, run integration tests |
| `test-suite-architect` | Full integration test suite | Write comprehensive tests across auth + router + plugins |
| `test-driven-dev` | CLI commands need to be tested | Write CLI test first, then command implementation |
| `dev-guide-generator` | Generate setup/usage docs | Use to produce INSTALL.md and USAGE.md |
| `secure-code-review` | Final security pass on integration | Review how credentials flow from CLI → Auth → Router |
| `code-vuln-audit` | Final scan before release | Run on complete codebase |
| `github` MCP | Manage repo, create PRs, merge branches | `github__create_pull_request`, `github__merge_pull_request` |

---

## 7. Implementation Order

1. **Phase 1:** `pyproject.toml` + package structure + `__init__.py` + `__main__.py`
2. **Phase 2:** `cli/main.py` root Typer app with Rich console
3. **Phase 3:** Auth CLI commands (`login.py`, `logout.py`, `whoami`) — wraps Hermes
4. **Phase 4:** Provider/Model CLI commands (`providers.py`, `models.py`) — wraps Hermes
5. **Phase 5:** Session CLI (`session.py`) — wraps Hermes
6. **Phase 6:** `core/orchestrator.py` — THE integration piece (auth + router + plugins)
7. **Phase 7:** Chat CLI (`chat.py`) — the main user-facing command
8. **Phase 8:** Tool CLI (`tool.py`) — wraps Codex's plugin system
9. **Phase 9:** Plugin CLI (`plugin.py`) — wraps Codex's plugin manager
10. **Phase 10:** Config CLI (`config.py`) + `config.toml` persistence
11. **Phase 11:** Integration tests (`tests/`)
12. **Phase 12:** Documentation (`docs/`)
13. **Phase 13:** Final merge of Hermes + Codex branches, resolve conflicts, validate

---

## 8. Success Criteria (My Checklist)

- [ ] `pyproject.toml` is complete; `pip install -e .` works
- [ ] `opia --help` shows all commands with rich formatting
- [ ] `opia login groq` prompts for key, validates, stores, shows success
- [ ] `opia provider list` shows all providers with auth status ✓/✗
- [ ] `opia models list` shows available models with metadata
- [ ] `opia chat "Hello"` returns a response from the active provider
- [ ] `opia chat --interactive` launches a REPL with history
- [ ] `opia tool list` shows all available tools
- [ ] `opia tool filesystem read --path README.md` returns file content
- [ ] `opia plugin list` shows installed plugins
- [ ] `core/orchestrator.py` successfully bridges auth → router → plugins
- [ ] Integration tests pass: full E2E login → chat → tool → logout
- [ ] `pytest` suite achieves 80%+ coverage
- [ ] README.md explains installation, usage, and architecture
- [ ] Hermes + Codex branches are merged cleanly with no conflicts
- [ ] Final security audit passes (no hardcoded secrets, no credential leaks in logs)

---

## 9. What I Do NOT Build

- ❌ `providers/` — Hermes owns this
- ❌ `auth/` — Hermes owns this (I use it, don't build it)
- ❌ `models/` — Hermes owns this (I use it, don't build it)
- ❌ `router/` — Hermes owns this (I use it, don't build it)
- ❌ `plugins/` — Codex owns this (I use it, don't build it)
- ❌ Individual tool implementations — Codex owns these (I call them, don't build them)
- ❌ Provider adapters — Codex owns these

---

## 10. Git & Delivery

- I work on branch: `kimi/cli-and-integration`
- I merge `hermes/provider-system` and `codex/plugin-ecosystem` into my branch
- Final delivery is the `main` branch with all three parts integrated
- I write the final `README.md`, `ARCHITECTURE.md`, and release notes

---

## 11. Reference Document

Keep the spec PDF at hand:
`C:\Users\donpr\Dropbox\k\OP\Opia_Architecture_Engineering_Spec.pdf`

All pages are relevant, but especially Part 3 (Success Criteria) for my test planning.

---

**My role: The conductor. I don't play the instruments — I make the orchestra play together.**
