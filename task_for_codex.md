# Task Assignment: Codex Agent — Opia Tooling & Plugin Ecosystem

> **Project:** Opia — OpenCode-Compatible AI CLI Agent  
> **Your Domain:** Part 2 — Tooling & Plugin Ecosystem (The Execution Engine)  
> **Source Spec:** `C:\Users\donpr\Dropbox\k\OP\Opia_Architecture_Engineering_Spec.pdf`

---

## 1. Your Mission

Build the **execution engine** of Opia. You own the plugin system, all external adapters, the sandbox, and the built-in tools. Your work is what makes Opia an **agent** rather than just a chat client. **Hermes** provides the LLM provider layer you will call; **Kimi** provides the CLI that exposes your tools to users.

---

## 2. Directory Ownership

You own and must create everything under:

```
opia/
└── plugins/
    ├── manager.py          # Plugin discovery, installation, permission management
    ├── registry.py         # PluginRegistry (loaded plugins, metadata lookup)
    ├── loader.py           # Runtime load/unload of plugins (hot-pluggable)
    ├── sandbox.py          # Permission-based sandbox for plugin execution
    │
    ├── adapters/           # External ecosystem compatibility layers
    │   ├── mcp.py          # Model Context Protocol (MCP) adapter
    │   ├── codex.py        # OpenAI Codex CLI adapter
    │   ├── claude.py       # Claude Code adapter
    │   ├── openclaw.py     # OpenClaw adapter
    │   └── native.py       # Native Opia plugin adapter
    │
    └── builtin/            # First-party built-in tools (each is a plugin)
        ├── filesystem.py     # Read, write, patch, move, search, watch
        ├── terminal.py       # Shell execution, streaming, background jobs
        ├── search.py         # Code search, semantic search, workspace indexing
        ├── git.py            # Git operations (status, diff, commit, branch, etc.)
        ├── web.py            # HTTP requests, web search, browser automation
        ├── editor.py         # Multi-file refactoring, formatting, diagnostics
        └── task_manager.py   # Planning, checkpoints, task graphs, progress tracking
```

---

## 3. Technical Stack

- **Language:** Python 3.11+
- **Async:** `asyncio` throughout — all tools are async
- **Plugin discovery:** JSON manifest (`plugin.json`) in each plugin directory
- **MCP transport:** `stdio` (subprocess) + `HTTP/SSE` (server) + `websocket`
- **Sandbox:** `subprocess` with `preexec_fn` (Linux), `subprocess` with env isolation (all platforms)
- **Permissions:** Explicit allowlist model (no implicit access)
- **Schema:** `pydantic` for tool input/output validation
- **HTTP client:** `httpx` (for web tool, MCP HTTP transport)
- **Git:** `GitPython` or shell `git` via subprocess
- **Search:** `ripgrep` wrapper + `tree-sitter` for semantic indexing (optional v2)
- **Filesystem:** `aiofiles` for async file I/O

---

## 4. Detailed Specifications

### 4.1 `plugins/manager.py` — PluginManager

The central authority for plugin lifecycle.

```python
class PluginManager:
    async def discover(self, paths: list[str]) -> list[PluginInfo]:
        """Scan directories for plugin.json manifests."""
        ...

    async def install(self, source: str) -> PluginInfo:
        """Install from: local path, git URL, or registry."""
        ...

    async def load(self, plugin_id: str) -> LoadedPlugin:
        """Load plugin into memory. Validate permissions."""
        ...

    async def unload(self, plugin_id: str) -> bool:
        """Hot-unload a plugin."""
        ...

    async def get_permissions(self, plugin_id: str) -> list[str]:
        """Return granted permissions for a plugin."""
        ...

    async def grant_permission(self, plugin_id: str, permission: str) -> bool:
        """User-granted permission. Auditable."""
        ...
```

### 4.2 `plugins/registry.py` — PluginRegistry

- In-memory registry of loaded plugins
- `get_tool(name: str) -> BaseTool` — lookup by tool name
- `list_tools() -> list[ToolInfo]` — all available tools
- `get_plugin_by_tool(name: str) -> PluginInfo` — reverse lookup
- `get_adapter(name: str) -> BaseAdapter` — get MCP/Codex/Claude/OpenClaw adapter

### 4.3 `plugins/loader.py` — PluginLoader

- Import plugin modules dynamically (importlib)
- Handle plugin isolation (separate Python path if needed)
- Graceful failure: if one plugin fails to load, others continue
- Dependency resolution: plugins can declare dependencies on other plugins

### 4.4 `plugins/sandbox.py` — Sandbox

- **Permission model:** Each plugin has explicit `permissions: list[str]`
- **Execution modes:**
  - `unrestricted` — Only for built-in tools (fully trusted)
  - `restricted` — Subprocess with env isolation, no network, no filesystem outside workspace
  - `network` — Restricted + allowed HTTP hosts
- **Audit log:** Every tool execution is logged with plugin_id, tool_name, args, timestamp, result_status
- **Timeout:** All tool executions have configurable timeouts (default 30s)

```python
class Sandbox:
    async def execute(self, plugin: LoadedPlugin, tool: BaseTool, **kwargs) -> ToolResult:
        """Execute with permission checks and sandboxing."""
        ...
```

### 4.5 `plugins/adapters/` — External Ecosystem Adapters

Each adapter translates an external protocol into Opia's `BaseTool` interface.

#### 4.5.1 `mcp.py` — MCP Adapter

Full MCP server support:
- **Transport:** `stdio` (spawn subprocess), `http` (connect to server), `sse` (server-sent events)
- **Discovery:** `tools/list`, `resources/list`, `prompts/list`
- **Execution:** `tools/call` with proper JSON-RPC 2.0 framing
- **Skills:** Support MCP skill servers (if present)
- **Streaming:** Handle streaming tool responses
- **Lifecycle:** `initialize`, `initialized`, heartbeat, graceful shutdown

```python
class MCPAdapter(BaseAdapter):
    async def connect(self, transport: str, config: dict) -> Connection: ...
    async def list_tools(self) -> list[ToolInfo]: ...
    async def call_tool(self, name: str, arguments: dict) -> ToolResult: ...
    async def disconnect(self) -> None: ...
```

#### 4.5.2 `codex.py` — Codex CLI Adapter

Compatibility layer for OpenAI Codex CLI plugins:
- Parse Codex plugin manifests
- Map Codex tool definitions to `BaseTool`
- Support Codex file-editing patterns (apply diff, write file)
- Support Codex planning workflows (multi-step task decomposition)
- Execute Codex tools in Opia's sandbox

#### 4.5.3 `claude.py` — Claude Code Adapter

Run Claude Code plugins/skills without modification:
- Parse Claude plugin format
- Map Claude tool use / tool result to `BaseTool.execute()` / `ToolResult`
- Support Claude's file operations (read, write, edit)
- Support Claude's project understanding APIs (if applicable)

#### 4.5.4 `openclaw.py` — OpenClaw Adapter

Support native OpenClaw plugins:
- Parse OpenClaw manifest format
- Map OpenClaw actions to `BaseTool`
- Support OpenClaw agent extensions
- Support OpenClaw workflow plugins (sequential/multi-step)

#### 4.5.5 `native.py` — Native Opia Adapter

The simplest adapter — for plugins written directly for Opia:
- No translation needed
- Direct `BaseTool` import
- Fastest path for Opia-first plugin development

### 4.6 `plugins/builtin/` — Built-in Tools

All built-in tools are just native plugins that ship with Opia. Each conforms to `BaseTool`.

#### 4.6.1 `filesystem.py` — Filesystem Tool

```python
class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Read, write, patch, move, search, and watch files/directories"
    permissions = ["filesystem.read", "filesystem.write"]

    async def read(self, path: str) -> str: ...
    async def write(self, path: str, content: str) -> None: ...
    async def patch(self, path: str, old_string: str, new_string: str) -> None: ...
    async def move(self, source: str, dest: str) -> None: ...
    async def search(self, path: str, pattern: str) -> list[str]: ...
    async def watch(self, path: str) -> AsyncIterator[FileEvent]: ...
```

#### 4.6.2 `terminal.py` — Terminal Tool

```python
class TerminalTool(BaseTool):
    name = "terminal"
    description = "Execute shell commands, stream output, background jobs, env isolation"
    permissions = ["terminal.execute"]

    async def execute(self, command: str, cwd: str | None = None, env: dict | None = None, timeout: int = 30) -> ExecuteResult: ...
    async def execute_streaming(self, command: str, ...) -> AsyncIterator[OutputChunk]: ...
    async def start_background(self, command: str, ...) -> BackgroundJob: ...
    async def stop_background(self, job_id: str) -> bool: ...
```

#### 4.6.3 `search.py` — Search Tool

```python
class SearchTool(BaseTool):
    name = "search"
    description = "Fast code search, semantic search, workspace indexing, symbol lookup"
    permissions = ["search.read"]

    async def grep(self, pattern: str, path: str = ".") -> list[SearchResult]: ...
    async def semantic_search(self, query: str, path: str = ".") -> list[SearchResult]: ...
    async def index_workspace(self, path: str = ".") -> IndexStats: ...
    async def find_symbol(self, name: str, path: str = ".") -> list[SymbolLocation]: ...
```

#### 4.6.4 `git.py` — Git Tool

```python
class GitTool(BaseTool):
    name = "git"
    description = "Git status, diff, commit, branch, merge, rebase, patch generation"
    permissions = ["git.read", "git.write"]

    async def status(self, path: str = ".") -> GitStatus: ...
    async def diff(self, path: str = ".", cached: bool = False) -> str: ...
    async def commit(self, message: str, path: str = ".") -> str: ...
    async def branch(self, name: str | None = None) -> list[str] | str: ...
    async def log(self, path: str = ".", limit: int = 10) -> list[CommitInfo]: ...
    async def generate_patch(self, ref: str) -> str: ...
```

#### 4.6.5 `web.py` — Web Tool

```python
class WebTool(BaseTool):
    name = "web"
    description = "HTTP requests, web search, API exploration, browser automation adapters"
    permissions = ["web.request"]

    async def request(self, url: str, method: str = "GET", headers: dict | None = None, body: str | None = None) -> HTTPResponse: ...
    async def search(self, query: str, engine: str = "duckduckgo") -> list[SearchResult]: ...
    async def fetch_page(self, url: str) -> str: ...
```

#### 4.6.6 `editor.py` — Editor Tool

```python
class EditorTool(BaseTool):
    name = "editor"
    description = "Multi-file refactoring, code formatting, diagnostics, symbol renaming"
    permissions = ["editor.read", "editor.write"]

    async def format_code(self, path: str, language: str | None = None) -> str: ...
    async def lint(self, path: str) -> list[Diagnostic]: ...
    async def rename_symbol(self, path: str, old_name: str, new_name: str) -> list[Edit]: ...
    async def refactor(self, path: str, instruction: str) -> list[Edit]: ...
```

#### 4.6.7 `task_manager.py` — Task Management Tool

```python
class TaskManagerTool(BaseTool):
    name = "task_manager"
    description = "Planning, checkpoints, task graphs, progress tracking"
    permissions = ["task.plan"]

    async def create_plan(self, goal: str, steps: list[str]) -> Plan: ...
    async def checkpoint(self, plan_id: str, status: str, note: str | None = None) -> None: ...
    async def get_progress(self, plan_id: str) -> ProgressReport: ...
    async def list_tasks(self) -> list[Plan]: ...
```

### 4.7 `BaseTool` Interface (You Define This)

```python
class BaseTool(ABC):
    name: str
    description: str
    permissions: list[str] = []
    supports_streaming: bool = False

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...

    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description=self.description,
            permissions=self.permissions,
            supports_streaming=self.supports_streaming,
        )
```

---

## 5. Plugin Manifest Format (`plugin.json`)

Every plugin (built-in or external) must have a `plugin.json`:

```json
{
  "name": "filesystem",
  "version": "1.0.0",
  "description": "Filesystem operations for Opia",
  "author": "Opia Team",
  "type": "native",
  "entrypoint": "main.py",
  "tools": ["filesystem"],
  "permissions": [
    "filesystem.read",
    "filesystem.write"
  ],
  "supports_streaming": false,
  "dependencies": []
}
```

---

## 6. Skills & Tools to Use

| Skill | Why | How to Use |
|-------|-----|------------|
| `swarm-coding` | 7 built-in tools + 5 adapters = massive surface | Use worktrees per adapter, parallelize built-in tools |
| `test-driven-dev` | Tools must be reliable; they touch the real filesystem | Write ONE tool test → ONE tool implementation |
| `test-suite-architect` | Comprehensive QA for all tools and adapters | Use after initial implementation for coverage targets |
| `skill-creator` | Understand how skills work (plugins are similar) | Read to understand manifest patterns, discovery |
| `github` MCP | Push your code to the shared repo | Push files as you complete each adapter/tool |

---

## 7. Implementation Order (Suggested)

1. **Phase 1:** Define `BaseTool` interface + `ToolResult` / `ToolMetadata` schemas
2. **Phase 2:** `PluginManager` + `PluginRegistry` + `PluginLoader` (infrastructure)
3. **Phase 3:** `Sandbox` with permission model + audit logging
4. **Phase 4:** `native.py` adapter (simplest — proves the system works)
5. **Phase 5:** Built-in tools (start with `filesystem` and `terminal` — most critical)
6. **Phase 6:** Remaining built-in tools (`search`, `git`, `web`, `editor`, `task_manager`)
7. **Phase 7:** `mcp.py` adapter (most complex external adapter)
8. **Phase 8:** `codex.py`, `claude.py`, `openclaw.py` adapters
9. **Phase 9:** Integration tests + load tests + security audit

---

## 8. Interface Contract (What Others Expect From You)

### Kimi (CLI Layer) will call:
```python
from opia.plugins.manager import PluginManager
from opia.plugins.registry import PluginRegistry

manager = PluginManager()
await manager.discover(["~/.opia/plugins/"])
await manager.load("filesystem")

registry = PluginRegistry()
tool = registry.get_tool("filesystem")
result = await tool.execute(path="README.md", action="read")
```

### Hermes (Provider Layer) may call:
```python
from opia.plugins.builtin.terminal import TerminalTool
# For provider validation scripts that need shell execution
```

### Your tools will be exposed to the LLM via:
```python
# Kimi will call this to get tool definitions for the LLM
registry.list_tools() → list of tool schemas (OpenAI function format or Anthropic tool format)
```

**DO NOT break these interfaces.** They are the contract.

---

## 9. Success Criteria (Checklist)

- [ ] `BaseTool` interface is complete and well-documented
- [ ] `PluginManager` discovers, installs, loads, and unloads plugins correctly
- [ ] `Sandbox` enforces permissions; unauthorized tool calls are blocked
- [ ] All 7 built-in tools work with real operations (not mocks)
- [ ] `filesystem`: read, write, patch, move, search all work
- [ ] `terminal`: execute, stream, background jobs all work
- [ ] `git`: status, diff, commit, branch, log all work
- [ ] `web`: HTTP requests and web search work
- [ ] MCP adapter connects to stdio, HTTP, and SSE servers
- [ ] Codex adapter parses Codex plugins and maps tools correctly
- [ ] Claude adapter runs Claude plugins without modification
- [ ] OpenClaw adapter supports OpenClaw plugins
- [ ] Native adapter is the fastest path (no translation overhead)
- [ ] `plugin.json` manifest format is validated on load
- [ ] Hot-loading works: new plugins can be loaded without restarting Opia
- [ ] Audit log captures every tool execution with plugin_id, tool, args, result
- [ ] Unit tests cover all tools and adapters
- [ ] Integration test: full flow from plugin discovery → load → execute → result

---

## 10. What NOT to Build

- ❌ Provider/auth system — Hermes owns `opia/providers/` and `opia/auth/`
- ❌ CLI commands (typer/click main entry) — Kimi owns `opia/cli/`
- ❌ `pyproject.toml` / packaging — Kimi owns packaging
- ❌ README / docs — Kimi owns documentation
- ❌ `router/chat.py` — Hermes owns the unified router (but your tools will be CALLED by it)
- ❌ `models/registry.py` — Hermes owns model discovery

---

## 11. Git & Delivery

- Work in a branch: `codex/plugin-ecosystem`
- Push to shared repo (owner will provide repo URL)
- Write a `CODEX_README.md` at root of your branch explaining your architecture decisions
- Tag Kimi when done so integration can begin

---

## 12. Reference Document

Keep the spec PDF at hand:
`C:\Users\donpr\Dropbox\k\OP\Opia_Architecture_Engineering_Spec.pdf`

Pages 3–5 of the spec cover your domain in detail.

---

**Good luck, Codex. Build the engine that makes Opia an agent.**
