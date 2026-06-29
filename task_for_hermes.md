# Task Assignment: Hermes Agent — Opia Authentication & Provider System

> **Project:** Opia — OpenCode-Compatible AI CLI Agent  
> **Your Domain:** Part 1 — Authentication & Provider System (The Foundation)  
> **Source Spec:** `C:\Users\donpr\Dropbox\k\OP\Opia_Architecture_Engineering_Spec.pdf`

---

## 1. Your Mission

Build the **core infrastructure** of Opia. This is the foundation everything else rests on. You own the authentication layer, credential security, multi-provider LLM framework, model discovery, and unified request routing. **Codex** will build on top of your provider system; **Kimi** will build the CLI that consumes it.

---

## 2. Directory Ownership

You own and must create everything under:

```
opia/
├── providers/           # ALL provider implementations
│   ├── base.py          # BaseProvider abstract class
│   ├── openai.py
│   ├── anthropic.py
│   ├── groq.py
│   ├── openrouter.py
│   ├── mistral.py
│   ├── gemini.py
│   ├── fireworks.py
│   ├── together.py
│   ├── deepseek.py
│   └── registry.py      # ProviderRegistry
│
├── auth/                # Authentication & security layer
│   ├── manager.py       # AuthManager (login/logout/validate)
│   ├── credentials.py   # Credential model & resolution logic
│   ├── storage.py       # Keychain + encrypted file + env fallback
│   └── session.py       # Active session tracking (provider, model, status)
│
├── models/              # Model discovery & metadata
│   ├── registry.py      # ModelRegistry (caches available models)
│   └── discovery.py     # Dynamic model fetching per provider
│
├── config/
│   └── providers.yaml     # Provider metadata (endpoints, auth types, etc.)
│
└── router/
    └── chat.py          # UnifiedChatRouter — THE single entry point
```

---

## 3. Technical Stack

- **Language:** Python 3.11+
- **Async:** `asyncio` / `async` / `await` throughout
- **HTTP:** `httpx` (async-capable, modern)
- **CLI framework (for your tests):** `typer` or `click` (Kimi owns the CLI, but you need basic CLI commands for testing login/logout)
- **Encryption:** `cryptography` (AES-256-GCM for fallback storage)
- **Keychain:** `keyring` (cross-platform: macOS Keychain, Linux Secret Service, Windows Credential Manager)
- **Config:** `pydantic` + `pydantic-settings` for type-safe config
- **YAML:** `pyyaml`

---

## 4. Detailed Specifications

### 4.1 `providers/base.py` — BaseProvider Interface

Every provider MUST inherit from this. This is the contract Codex and Kimi will depend on.

```python
class BaseProvider(ABC):
    name: str                    # e.g., "groq", "openai"
    base_url: str                # Provider API base URL
    supports_streaming: bool = True
    supports_oauth: bool = False

    @abstractmethod
    async def authenticate(self, credential: str) -> bool: ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]: ...

    @abstractmethod
    async def chat(self, messages: list[Message], model: str, **kwargs) -> ChatResponse: ...

    @abstractmethod
    async def embeddings(self, input: str | list[str], model: str, **kwargs) -> EmbeddingsResponse: ...

    @abstractmethod
    async def validate_credentials(self, credential: str) -> bool: ...

    async def refresh_token(self) -> str | None:
        """Optional: Override for OAuth providers."""
        return None
```

### 4.2 `providers/registry.py` — ProviderRegistry

- Register all provider classes
- `get_provider(name: str) -> BaseProvider`
- `list_providers() -> list[str]`
- `discover_available() -> list[ProviderInfo]` (checks which providers have credentials configured)

### 4.3 `auth/storage.py` — Secure Credential Storage

Resolution order (highest to lowest priority):
1. **System Keychain** via `keyring` (`opia/<provider_name>`)
2. **Encrypted Local File** (`~/.opia/credentials.enc` — AES-256-GCM)
3. **Environment Variables** (`OPENAI_API_KEY`, `GROQ_API_KEY`, etc.)

**Requirements:**
- Never store plaintext
- `set_credential(provider, key)` → encrypt → store in keyring (fallback to encrypted file)
- `get_credential(provider)` → resolve from keyring → encrypted file → env var
- `delete_credential(provider)` → remove from all stores
- `validate_on_store`: When storing, immediately test against provider's `/models` endpoint
- Invalid credentials are **never** persisted

### 4.4 `auth/manager.py` — AuthManager

- `login(provider, key=None)` → Prompt for key if not provided → validate → store → set active
- `logout(provider=None)` → Remove credentials (all if no provider specified)
- `whoami()` → Show active provider, model, auth status
- `validate(provider)` → Test credentials against provider

### 4.5 `auth/session.py` — Session Tracking

- `ActiveSession` dataclass: provider, model, auth_status, last_used, created_at
- Persist to `~/.opia/session.json` (non-sensitive metadata only — NO KEYS)
- `set_active(provider, model)` → update session
- `get_active()` → return current session
- `clear()` → reset session

### 4.6 `models/registry.py` + `models/discovery.py`

- `ModelInfo` dataclass: id, name, provider, context_length, supports_streaming, supports_vision, metadata
- `ModelRegistry`: cache models to `~/.opia/models_cache.json` (TTL: 1 hour)
- `discover_models(provider)` → fetch from provider API → cache → return
- `list_models()` → return all cached models across all configured providers
- `get_model(id)` → lookup by model ID

### 4.7 `router/chat.py` — UnifiedChatRouter

**THE central gateway.** No one talks to providers directly except this router.

```python
class UnifiedChatRouter:
    async def chat(
        self,
        messages: list[Message],
        provider: str | None = None,   # None → use active session
        model: str | None = None,        # None → use provider default
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs
    ) -> ChatResponse | AsyncIterator[ChatChunk]:
        ...
```

- Resolve provider (from arg → session → error)
- Load credentials via `auth`
- Select model (from arg → session → provider default)
- Normalize request format per provider
- Handle retries (3 attempts with exponential backoff)
- Normalize response format (return unified `ChatResponse` regardless of provider)
- Handle streaming consistently

### 4.8 `config/providers.yaml`

Metadata for each provider:

```yaml
providers:
  openai:
    name: OpenAI
    base_url: https://api.openai.com/v1
    auth_type: api_key
    env_var: OPENAI_API_KEY
    keyring_service: opia/openai
    default_model: gpt-4o
  
  anthropic:
    name: Anthropic
    base_url: https://api.anthropic.com/v1
    auth_type: api_key
    env_var: ANTHROPIC_API_KEY
    keyring_service: opia/anthropic
    default_model: claude-3-opus-20240229
  
  groq:
    name: Groq
    base_url: https://api.groq.com/openai/v1
    auth_type: api_key
    env_var: GROQ_API_KEY
    keyring_service: opia/groq
    default_model: llama-3.3-70b-versatile
  
  # ... (repeat for all 9 providers)
  # mistral, openrouter, gemini, fireworks, together, deepseek
```

---

## 5. Skills & Tools to Use

| Skill | Why | How to Use |
|-------|-----|------------|
| `test-driven-dev` | Auth & routing must be rock-solid | Write ONE test → ONE implementation. Start with `BaseProvider` interface tests. |
| `secure-code-review` | Credential storage is security-critical | Run after implementing `auth/storage.py` |
| `code-vuln-audit` | Scan for secret leaks, hardcoded keys | Run before submitting your work |
| `swarm-coding` | If you need parallel workers for multiple providers | Use worktrees per provider family |
| `github` MCP | Push your code to the shared repo | Use `github__push_files` or `github__create_or_update_file` |

---

## 6. Implementation Order (Suggested)

1. **Phase 1:** `config/providers.yaml` + `providers/base.py` (establish contract)
2. **Phase 2:** `auth/storage.py` + `auth/credentials.py` (security layer)
3. **Phase 3:** `auth/manager.py` + `auth/session.py` (auth flow)
4. **Phase 4:** `providers/registry.py` + one provider (e.g., `groq.py`) as proof-of-concept
5. **Phase 5:** Remaining 8 providers (can parallelize with swarm-coding if needed)
6. **Phase 6:** `models/discovery.py` + `models/registry.py`
7. **Phase 7:** `router/chat.py` (the integration piece)
8. **Phase 8:** Security audit + tests

---

## 7. Interface Contract (What Others Expect From You)

### Kimi (CLI Layer) will call:
```python
from opia.auth.manager import AuthManager
from opia.router.chat import UnifiedChatRouter
from opia.models.registry import ModelRegistry

auth = AuthManager()
await auth.login("groq", api_key)
await auth.logout("groq")

router = UnifiedChatRouter()
response = await router.chat(messages=[...], provider="groq", model="llama-4")

models = ModelRegistry()
await models.discover_models("groq")
```

### Codex (Plugin Layer) will call:
```python
from opia.providers.base import BaseProvider
from opia.providers.registry import ProviderRegistry

registry = ProviderRegistry()
provider = registry.get_provider("groq")
models = await provider.list_models()
```

**DO NOT break these interfaces.** They are the contract.

---

## 8. Success Criteria (Checklist)

- [ ] `BaseProvider` abstract class is complete and well-documented
- [ ] All 9 provider implementations exist and pass basic connectivity tests
- [ ] Credentials are encrypted; plaintext storage is impossible
- [ ] `auth.login()` validates before persisting
- [ ] `auth.logout()` removes from all stores (keychain + file + env-awareness)
- [ ] `UnifiedChatRouter.chat()` works end-to-end with at least 3 providers
- [ ] `ModelRegistry` caches and TTL-expires correctly
- [ ] `Session` tracks active provider/model without storing keys
- [ ] All async code uses `async`/`await` consistently (no sync blocking)
- [ ] `providers.yaml` configures all 9 providers with correct metadata
- [ ] Unit tests cover auth, storage, and router logic
- [ ] Security audit passes (no hardcoded keys, no plaintext secrets)

---

## 9. What NOT to Build

- ❌ CLI commands (typer/click main entry) — Kimi owns `opia/cli/`
- ❌ Plugin system — Codex owns `opia/plugins/`
- ❌ Tool adapters — Codex owns `opia/plugins/adapters/`
- ❌ Built-in tools (filesystem, terminal, etc.) — Codex owns these
- ❌ `pyproject.toml` / packaging — Kimi owns packaging
- ❌ README / docs — Kimi owns documentation

---

## 10. Git & Delivery

- Work in a branch: `hermes/provider-system`
- Push to shared repo (owner will provide repo URL)
- Write a `HERMES_README.md` at root of your branch explaining your architecture decisions
- Tag Kimi when done so integration can begin

---

## 11. Reference Document

Keep the spec PDF at hand:
`C:\Users\donpr\Dropbox\k\OP\Opia_Architecture_Engineering_Spec.pdf`

Pages 1–3 of the spec cover your domain in detail.

---

**Good luck, Hermes. Build the foundation strong. Everything else stands on it.**
