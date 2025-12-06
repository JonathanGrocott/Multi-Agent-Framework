"""Base LLM provider abstraction for flexible model integration."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """Represents a tool call request from the LLM."""
    id: str = Field(..., description="Unique identifier for this tool call")
    name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class LLMMessage(BaseModel):
    """Standardized message format for LLM conversations."""
    role: MessageRole = Field(..., description="Role of the message sender")
    content: Optional[str] = Field(None, description="Text content of the message")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls requested by assistant")
    tool_call_id: Optional[str] = Field(None, description="ID of the tool call this message responds to")
    name: Optional[str] = Field(None, description="Name of the tool that produced this result")


class ToolDefinition(BaseModel):
    """Definition of a tool that can be called by the LLM."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="What the tool does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema of parameters")


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(0, description="Tokens in the prompt")
    completion_tokens: int = Field(0, description="Tokens in the completion")
    total_tokens: int = Field(0, description="Total tokens used")


class LLMResponse(BaseModel):
    """Standardized response from LLM provider."""
    content: Optional[str] = Field(None, description="Response text from the LLM")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls requested by the LLM")
    finish_reason: str = Field(..., description="Why the generation stopped: 'stop', 'tool_calls', 'length', etc.")
    usage: Optional[UsageInfo] = Field(None, description="Token usage information")
    raw_response: Optional[Any] = Field(None, description="Raw response from provider (for debugging)")


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    This allows the framework to work with different LLM providers
    (OpenAI, Azure OpenAI, custom endpoints, etc.) through a unified interface.
    """
    
    def __init__(self, provider_name: str, default_model: str):
        """
        Initialize the provider.
        
        Args:
            provider_name: Name of this provider instance
            default_model: Default model to use if not specified
        """
        self.provider_name = provider_name
        self.default_model = default_model
    
    @abstractmethod
    def complete(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: Conversation history
            model: Model to use (uses default if None)
            tools: Available tools for function calling
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Standardized LLM response
            
        Raises:
            Exception: If the LLM call fails
        """
        pass
    
    def _convert_tools_to_provider_format(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """
        Convert standardized tool definitions to provider-specific format.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            Provider-specific tool format
        """
        # Default implementation for OpenAI-compatible format
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in tools
        ]
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.provider_name}, model={self.default_model})"
