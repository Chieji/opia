"""Opia providers."""
from opia.providers.base import (
    BaseProvider, Message, ChatResponse, ChatChunk, EmbeddingsResponse,
    ModelInfo, ProviderInfo,
)
from opia.providers.registry import register_provider, get_provider, list_providers, discover_available
from opia.providers import openai, anthropic, groq, mistral, openrouter
from opia.providers import gemini, fireworks, together, deepseek

_PROVIDERS = [
    ("openai", openai.OpenAIProvider),
    ("anthropic", anthropic.AnthropicProvider),
    ("groq", groq.GroqProvider),
    ("mistral", mistral.MistralProvider),
    ("openrouter", openrouter.OpenRouterProvider),
    ("gemini", gemini.GeminiProvider),
    ("fireworks", fireworks.FireworksProvider),
    ("together", together.TogetherProvider),
    ("deepseek", deepseek.DeepSeekProvider),
]

for name, cls in _PROVIDERS:
    register_provider(name, cls)
