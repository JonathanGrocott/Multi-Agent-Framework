"""Factory for creating LLM providers from configuration."""

import os
from typing import Dict, Optional
from dotenv import load_dotenv
from .llm_provider import LLMProvider
from .openai_provider import OpenAIProvider


class LLMFactory:
    """Factory for creating LLM provider instances from configuration."""
    
    @staticmethod
    def create_provider(provider_config: Dict, provider_name: str) -> LLMProvider:
        """
        Create an LLM provider from configuration.
        
        Args:
            provider_config: Configuration dictionary for the provider
            provider_name: Name to assign to this provider instance
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider type is unsupported or config is invalid
        """
        provider_type = provider_config.get("type", "").lower()
        
        if provider_type == "openai":
            return LLMFactory._create_openai_provider(provider_config, provider_name)
        else:
            raise ValueError(f"Unsupported LLM provider type: {provider_type}")
    
    @staticmethod
    def _create_openai_provider(config: Dict, provider_name: str) -> OpenAIProvider:
        """Create an OpenAI provider from configuration."""
        # Load environment variables
        load_dotenv()
        
        # Get API key from config or environment
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError(f"No api_key provided for provider '{provider_name}'")
        
        # Resolve environment variable if specified (format: ${VAR_NAME})
        api_key = LLMFactory._resolve_env_var(api_key)
        
        # Get optional parameters
        base_url = config.get("base_url")
        if base_url:
            base_url = LLMFactory._resolve_env_var(base_url)
        
        organization = config.get("organization")
        if organization:
            organization = LLMFactory._resolve_env_var(organization)
        
        default_model = config.get("default_model", "gpt-4o-mini")
        timeout = config.get("timeout", 60)
        max_retries = config.get("max_retries", 3)
        
        return OpenAIProvider(
            provider_name=provider_name,
            api_key=api_key,
            default_model=default_model,
            base_url=base_url,
            organization=organization,
            timeout=timeout,
            max_retries=max_retries
        )
    
    @staticmethod
    def _resolve_env_var(value: str) -> str:
        """
        Resolve environment variable references in config values.
        
        Supports format: ${VAR_NAME}
        
        Args:
            value: Config value that may contain env var reference
            
        Returns:
            Resolved value
        """
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var_name = value[2:-1]
            resolved = os.getenv(env_var_name)
            if resolved is None:
                raise ValueError(
                    f"Environment variable '{env_var_name}' not found. "
                    f"Please set it in your .env file or environment."
                )
            return resolved
        return value
    
    @staticmethod
    def create_from_config(system_config) -> Dict[str, LLMProvider]:
        """
        Create all LLM providers from system configuration.
        
        Args:
            system_config: SystemConfig object with llm_providers field
            
        Returns:
            Dictionary mapping provider names to provider instances
        """
        providers = {}
        
        if not hasattr(system_config, 'llm_providers') or not system_config.llm_providers:
            return providers
        
        for provider_name, provider_config in system_config.llm_providers.items():
            try:
                # Convert Pydantic model to dict if needed
                config_dict = provider_config.model_dump() if hasattr(provider_config, 'model_dump') else provider_config
                provider = LLMFactory.create_provider(config_dict, provider_name)
                providers[provider_name] = provider
            except Exception as e:
                raise Exception(f"Failed to create LLM provider '{provider_name}': {str(e)}") from e
        
        return providers
