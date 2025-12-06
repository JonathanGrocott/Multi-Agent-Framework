"""OpenAI provider implementation supporting both standard and custom endpoints."""

import os
import json
from typing import Any, Dict, List, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from .llm_provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    ToolDefinition,
    ToolCall,
    UsageInfo,
    MessageRole
)


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider supporting both standard OpenAI API and custom endpoints.
    
    This provider works with:
    - Standard OpenAI API (api.openai.com)
    - Custom OpenAI-compatible endpoints (e.g., gov.cloud)
    - Azure OpenAI (with appropriate base_url)
    """
    
    def __init__(
        self,
        provider_name: str,
        api_key: str,
        default_model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            provider_name: Name of this provider instance
            api_key: OpenAI API key or bearer token for custom endpoints
            default_model: Default model to use
            base_url: Optional base URL for custom endpoints (e.g., gov.cloud)
            organization: Optional OpenAI organization ID
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(provider_name, default_model)
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries
        )
        self.base_url = base_url or "https://api.openai.com/v1"
    
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
        Generate a completion using OpenAI API.
        
        Args:
            messages: Conversation history
            model: Model to use (uses default if None)
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI-specific parameters
            
        Returns:
            Standardized LLM response
            
        Raises:
            Exception: If the API call fails
        """
        model_to_use = model or self.default_model
        
        # Convert our standardized messages to OpenAI format
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Prepare the API call parameters
        api_params = {
            "model": model_to_use,
            "messages": openai_messages,
            "temperature": temperature,
        }
        
        if max_tokens is not None:
            api_params["max_tokens"] = max_tokens
        
        # Add tools if provided
        if tools:
            api_params["tools"] = self._convert_tools_to_provider_format(tools)
            api_params["tool_choice"] = "auto"
        
        # Add any additional parameters
        api_params.update(kwargs)
        
        # Make the API call
        try:
            response: ChatCompletion = self.client.chat.completions.create(**api_params)
            return self._convert_openai_response_to_standard(response)
        
        except Exception as e:
            # Re-raise with context
            raise Exception(f"OpenAI API call failed for provider '{self.provider_name}': {str(e)}") from e
    
    def _convert_messages_to_openai_format(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert standardized messages to OpenAI format."""
        openai_messages = []
        
        for msg in messages:
            openai_msg: Dict[str, Any] = {"role": msg.role.value}
            
            if msg.content:
                openai_msg["content"] = msg.content
            
            # Handle tool calls (from assistant)
            if msg.tool_calls:
                openai_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)
                        }
                    }
                    for tc in msg.tool_calls
                ]
            
            # Handle tool responses
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            
            if msg.name:
                openai_msg["name"] = msg.name
            
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def _convert_openai_response_to_standard(self, response: ChatCompletion) -> LLMResponse:
        """Convert OpenAI response to standardized format."""
        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason or "stop"
        
        # Extract content
        content = message.content if message.content else None
        
        # Extract tool calls if present
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments) if tc.function.arguments else {}
                )
                for tc in message.tool_calls
            ]
        
        # Extract usage information
        usage = None
        if response.usage:
            usage = UsageInfo(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
        )
    
    def __repr__(self) -> str:
        return f"OpenAIProvider(name={self.provider_name}, model={self.default_model}, base_url={self.base_url})"
