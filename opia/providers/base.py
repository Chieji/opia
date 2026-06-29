"""Base provider contract for Opia."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)
    finish_reason: Optional[str] = None


@dataclass
class ChatChunk:
    content: str
    done: bool


@dataclass
class EmbeddingsResponse:
    embeddings: list[list[float]]
    model: str
    provider: str


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    context_length: int = 4096
    supports_streaming: bool = True
    supports_vision: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class ProviderInfo:
    name: str
    display_name: str
    base_url: str
    default_model: str
    has_credentials: bool
    supports_oauth: bool


class BaseProvider(ABC):
    name: str
    base_url: str
    supports_streaming: bool = True
    supports_oauth: bool = False

    @abstractmethod
    async def authenticate(self, credential: str) -> bool:
        """Test a credential against the provider and store it if valid."""
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return list of available models from the provider."""
        ...

    @abstractmethod
    async def chat(
        self, messages: list[Message], model: str, **kwargs
    ) -> ChatResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def embeddings(
        self, input: str | list[str], model: str, **kwargs
    ) -> EmbeddingsResponse:
        """Send an embeddings request."""
        ...

    @abstractmethod
    async def validate_credentials(self, credential: str) -> bool:
        """Validate a credential without persisting it."""
        ...

    async def refresh_token(self) -> str | None:
        """Optional: Override for OAuth providers."""
        return None
