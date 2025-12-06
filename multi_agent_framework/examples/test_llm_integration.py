#!/usr/bin/env python3
"""
Simple test script to verify LLM provider integration.

This script tests:
1. Loading environment variables
2. Creating LLM providers
3. Basic completion without tools
4. Completion with function calling
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_framework.core.llm_provider import LLMMessage, ToolDefinition, MessageRole
from multi_agent_framework.core.llm_factory import LLMFactory


def test_env_loading():
    """Test environment variable loading."""
    print("=" * 70)
    print("TEST 1: Environment Variable Loading")
    print("=" * 70)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    govcloud_key = os.getenv("GOVCLOUD_API_KEY")
    govcloud_url = os.getenv("GOVCLOUD_BASE_URL")
    
    print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not set'}")
    print(f"GOVCLOUD_API_KEY: {'✓ Set' if govcloud_key else '✗ Not set'}")
    print(f"GOVCLOUD_BASE_URL: {'✓ Set' if govcloud_url else '✗ Not set'}")
    print()


def test_provider_creation():
    """Test creating LLM providers."""
    print("=" * 70)
    print("TEST 2: LLM Provider Creation")
    print("=" * 70)
    
    # Test OpenAI provider
    try:
        provider_config = {
            "type": "openai",
            "api_key": "${OPENAI_API_KEY}",
            "default_model": "gpt-4o-mini"
        }
        
        provider = LLMFactory.create_provider(provider_config, "test_openai")
        print(f"✓ Created OpenAI provider: {provider}")
        return provider
    except Exception as e:
        print(f"✗ Failed to create provider: {e}")
        return None


def test_basic_completion(provider):
    """Test basic LLM completion."""
    if not provider:
        print("\n⚠ Skipping basic completion test (no provider)")
        return
    
    print("\n" + "=" * 70)
    print("TEST 3: Basic Completion (No Tools)")
    print("=" * 70)
    
    try:
        messages = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant."
            ),
            LLMMessage(
                role=MessageRole.USER,
                content="What is 2+2? Answer with just the number."
            )
        ]
        
        response = provider.complete(messages, temperature=0.3)
        
        print(f"✓ Response: {response.content}")
        print(f"✓ Finish reason: {response.finish_reason}")
        if response.usage:
            print(f"✓ Tokens used: {response.usage.total_tokens}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_function_calling(provider):
    """Test LLM function calling."""
    if not provider:
        print("\n⚠ Skipping function calling test (no provider)")
        return
    
    print("\n" + "=" * 70)
    print("TEST 4: Function Calling")
    print("=" * 70)
    
    try:
        # Define a simple tool
        tools = [
            ToolDefinition(
                name="get_current_temperature",
                description="Get the current temperature for a location",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            )
        ]
        
        messages = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant with access to weather tools."
            ),
            LLMMessage(
                role=MessageRole.USER,
                content="What's the temperature in Seattle?"
            )
        ]
        
        response = provider.complete(messages, tools=tools, temperature=0.3)
        
        if response.tool_calls:
            print(f"✓ LLM requested {len(response.tool_calls)} tool call(s):")
            for tc in response.tool_calls:
                print(f"  - Tool: {tc.name}")
                print(f"    Arguments: {tc.arguments}")
        else:
            print(f"✗ No tool calls requested")
            print(f"  Response: {response.content}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    print("=" * 70)
    print("LLM PROVIDER INTEGRATION TEST")
    print("=" * 70)
    print()
    
    # Test 1: Environment variables
    test_env_loading()
    
    # Test 2: Provider creation
    provider = test_provider_creation()
    
    # Test 3 & 4: Only if provider was created successfully
    if provider:
        test_basic_completion(provider)
        test_function_calling(provider)
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print("✓ LLM provider integration is working!")
        print("✓ Ready to use in multi-agent framework")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Run the main demo: python demo.py --config llm_config_openai.yaml")
        return 0
    else:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print("✗ LLM provider test incomplete")
        print("\nPlease:")
        print("1. Copy .env.example to .env")
        print("2. Add your OPENAI_API_KEY to .env")
        print("3. Run this test again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
