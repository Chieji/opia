"""OpiaOrchestrator — the central conductor that wires Auth → Router → Plugins → Tools."""
from __future__ import annotations

from typing import Optional, List, Any
from dataclasses import dataclass, field

from opia.auth.manager import AuthManager
from opia.router.chat import UnifiedChatRouter
from opia.models.registry import ModelRegistry
from opia.providers.base import Message, ChatResponse, ChatChunk, ModelInfo


@dataclass
class ToolInfo:
    """Lightweight tool descriptor for CLI display."""
    name: str
    description: str
    permissions: list[str] = field(default_factory=list)
    plugin_name: Optional[str] = None
    loaded: bool = True


@dataclass
class PluginInfo:
    """Lightweight plugin descriptor for CLI display."""
    name: str
    version: str
    type: str
    loaded: bool
    tools: list[str] = field(default_factory=list)


class OpiaOrchestrator:
    """The central conductor. Connects Auth → Router → Plugins → Tools."""

    def __init__(self):
        self.auth = AuthManager()
        self.router = UnifiedChatRouter()
        self.models = ModelRegistry()
        self._plugins_initialized = False
        self._plugin_manager = None
        self._plugin_registry = None

    # ───────────────────────────────────────────
    # Auth convenience
    # ───────────────────────────────────────────

    async def discover_providers(self) -> list[Any]:
        """Discover all providers with their credential status."""
        from opia.providers.registry import discover_available
        return await discover_available()

    # ───────────────────────────────────────────
    # Chat
    # ───────────────────────────────────────────

    async def chat(
        self,
        messages: list[Message],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> ChatResponse:
        """Send a chat request through the unified router."""
        return await self.router.chat(
            messages=messages,
            provider=provider,
            model=model,
            **kwargs,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ):
        """Stream a chat response."""
        return self.router.chat(
            messages=messages,
            provider=provider,
            model=model,
            stream=True,
            **kwargs,
        )

    # ───────────────────────────────────────────
    # Models
    # ───────────────────────────────────────────

    async def list_models(self, provider: Optional[str] = None) -> list[ModelInfo]:
        """List all available models (optionally filtered by provider)."""
        if provider:
            return await self.models.discover_models(provider)

        # Discover all providers that have credentials
        providers = await self.discover_providers()
        all_models: list[ModelInfo] = []
        for p in providers:
            if p.has_credentials:
                try:
                    models = await self.models.discover_models(p.name)
                    all_models.extend(models)
                except Exception:
                    pass
        return all_models

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get a specific model by ID."""
        return self.models.get_model(model_id)

    # ───────────────────────────────────────────
    # Plugins & Tools (stub-aware)
    # ───────────────────────────────────────────

    def _ensure_plugins(self) -> None:
        """Lazy-load plugin system if available."""
        if self._plugins_initialized:
            return
        self._plugins_initialized = True
        try:
            from opia.plugins.manager import PluginManager
            from opia.plugins.registry import PluginRegistry
            self._plugin_manager = PluginManager()
            self._plugin_registry = PluginRegistry()
        except ImportError:
            # Codex hasn't built the plugin system yet — that's fine
            self._plugin_manager = None
            self._plugin_registry = None

    def list_tools(self) -> list[ToolInfo]:
        """Return all available tools (built-in + plugin)."""
        self._ensure_plugins()
        tools: list[ToolInfo] = []

        if self._plugin_registry:
            try:
                raw_tools = self._plugin_registry.list_tools()
                for t in raw_tools:
                    tools.append(ToolInfo(
                        name=t.name,
                        description=t.description,
                        permissions=getattr(t, "permissions", []),
                        plugin_name=getattr(t, "plugin_name", None),
                        loaded=True,
                    ))
            except Exception:
                pass

        return tools

    def list_plugins(self) -> list[PluginInfo]:
        """Return all installed plugins."""
        self._ensure_plugins()
        plugins: list[PluginInfo] = []

        if self._plugin_manager:
            try:
                raw_plugins = self._plugin_manager.discovered_plugins()
                for p in raw_plugins:
                    plugins.append(PluginInfo(
                        name=p.name,
                        version=p.version,
                        type=p.type,
                        loaded=p.loaded,
                        tools=p.tools,
                    ))
            except Exception:
                pass

        return plugins

    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name through the plugin system."""
        self._ensure_plugins()

        if not self._plugin_registry:
            raise RuntimeError(
                "Plugin system not available yet. "
                "The Codex agent is building the tooling ecosystem."
            )

        try:
            tool = self._plugin_registry.get_tool(tool_name)
            return await tool.execute(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Tool execution failed: {e}")
