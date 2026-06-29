#!/usr/bin/env python3

"""
Base Tool Interface and Core Schemas for Opia Plugin Ecosystem

This module defines the foundational interfaces that all Opia plugins must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Literal, TypeVar, Generic

from pydantic import BaseModel, Field



class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    UNRESTRICTED = "unrestricted"
    RESTRICTED = "restricted"
    NETWORK = "network"


@dataclass
class ToolResult:
    status: ToolResultStatus
    data: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def success(cls, data: Any = None, execution_time_ms: float = 0.0, metadata: dict[str, Any] | None = None):
        return cls(
            status=ToolResultStatus.SUCCESS,
            data=data,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
        )

    @classmethod
    def error(cls, error: str, data: Any = None, execution_time_ms: float = 0.0):
        return cls(
            status=ToolResultStatus.ERROR,
            data=data,
            error=error,
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def permission_denied(cls, permission: str, execution_time_ms: float = 0.0):
        return cls(
            status=ToolResultStatus.PERMISSION_DENIED,
            error=f"Permission denied: {permission}",
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def timeout(cls, timeout_seconds: float, execution_time_ms: float = 0.0):
        return cls(
            status=ToolResultStatus.TIMEOUT,
            error=f"Execution timed out after {timeout_seconds}s",
            execution_time_ms=execution_time_ms,
        )


@dataclass
class ToolMetadata:
    name: str
    description: str
    permissions: list[str] = field(default_factory=list)
    supports_streaming: bool = False
    parameters: dict[str, Any] = field(default_factory=dict)
    returns: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "supports_streaming": self.supports_streaming,
            "parameters": self.parameters,
            "returns": self.returns,
        }

    def to_openai_function(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_anthropic_tool(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


class OutputChunk:
    type: Literal["stdout", "stderr", "result"] = "stdout"
    content: str = ""
    is_final: bool = False

T = TypeVar('T')


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    permissions: list[str] = []
    supports_streaming: bool = False
    execution_mode: ExecutionMode = ExecutionMode.RESTRICTED

    def __init__(self):
        if not self.name:
            raise ValueError(f"Tool {self.__class__.__name__} must define a name")
        if not self.description:
            raise ValueError(f"Tool {self.name} must define a description")


    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError

    async def execute_streaming(self, *kwargs) -> AsyncIterator[OutputChunk]:
        if not self.supports_streaming:
            raise NotImplementedError(f"Tool {self.name} does not support streaming")
        result = await self.execute(**kwargs)
        yield OutputChunk(type="result", content=str(result.to_dict()), is_final=True)


    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description=self.description,
            permissions=self.permissions,
            supports_streaming=self.supports_streaming,
            parameters=self._get_parameters_schema(),
            returns=self._get_returns_schema(),
        )

    def _get_parameters_schema(self):
        import inspect
        sig = inspect.signature(self.execute)
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            param_schema = self._type_to_json_schema(param.annotation)
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
            else:
                param_schema["default"] = param.default
            properties[param_name] = param_schema
        return {"type": "object", "properties": properties, "required": required}

    def _get_returns_schema(self):
        return {"type": "object", "description": "Tool execution result"}

    def _type_to_json_schema(self, annotation: Any) -> dict[str, Any]:
        import typing
        if annotation is inspect.Parameter.empty:
            return {"type": "string"}
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)
        if annotation is str or annotation == 'str':
            return {"type": "string"}
        elif annotation is int or annotation == 'int':
            return {"type": "integer"}
        elif annotation is bool or annotation == 'bool':
            return {"type": "boolean"}
        elif origin is list:
            if args:
                return {"type": "array", "items": self._type_to_json_schema(args[0])}
            return {"type": "array"}
        elif origin is dict:
            return {"type": "object"}
        elif origin is typing.Union:
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                return self._type_to_json_schema(non_none_args[0])
            schemas = [self._type_to_json_schema(a) for a in non_none_args]
            return {"anyOf": schemas}
        else:
            return {"type": "string"}


class BaseAdapter(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    async def connect(self, config: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_tools(self) -> list[ToolMetadata]:
        raise NotImplementedError

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        raise NotImplementedError


__all__ = [
    "BaseTool",
    "BaseAdapter",
    "ToolResult",
    "ToolMetadata",
    "OutputChunk",
    "ToolResultStatus",
    "ExecutionMode",
]
