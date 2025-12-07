#!/usr/bin/env python3
"""
Simple demo with NO MCP servers - just LLM reasoning.

This demonstrates the LLM integration without needing any MCP servers running.
Perfect for testing the LLM integration in isolation.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_framework.core import SharedContext, EventBus, Coordinator
from multi_agent_framework.core.llm_factory import LLMFactory
from multi_agent_framework.agents import AgentRegistry, SpecializedAgent
from multi_agent_framework.config import load_config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simple LLM-only demo")
    parser.add_argument(
        "--config",
        type=str,
        default="test_config_simple.yaml",
        help="Config file (default: test_config_simple.yaml)"
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("MULTI-AGENT FRAMEWORK - SIMPLE LLM DEMO")
    print("(No MCP servers required)")
    print("=" * 70)
    print()
    
    config_path = Path(__file__).parent / args.config
    
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        return 1
    
    try:
        print(f"Loading config: {config_path.name}")
        config = load_config(str(config_path))
        
        # Initialize components
        context = SharedContext()
        event_bus = EventBus()
        agent_registry = AgentRegistry()
        
        # Initialize LLM providers
        print("\nInitializing LLM providers...")
        llm_providers = LLMFactory.create_from_config(config)
        default_provider = None
        if config.default_llm_provider and config.default_llm_provider in llm_providers:
            default_provider = llm_providers[config.default_llm_provider]
            print(f"✓ Using provider: {config.default_llm_provider}")
        
        # Create agents
        print(f"\nRegistering {len(config.agents)} agents...")
        for agent_config in config.agents:
            agent = SpecializedAgent(
                agent_id=agent_config.agent_id,
                name=agent_config.name,
                machine_id=agent_config.machine_id,
                function=agent_config.function,
                capabilities=agent_config.capabilities,
                allowed_tools=[],  # No tools
                context=context,
                event_bus=event_bus,
                mcp_client=None,  # No MCP client needed
                llm_provider=default_provider,
                model=agent_config.model,
                custom_instructions=agent_config.custom_instructions
            )
            agent_registry.register(agent)
            print(f"  ✓ {agent.name} ({agent.function})")
        
        # Create coordinator
        routing_config = {
            "examples": [
                {
                    "keywords": example.keywords,
                    "machine_id": example.machine_id,
                    "description": example.description
                }
                for example in config.routing_examples
            ]
        }
        
        coordinator = Coordinator(
            agent_registry=agent_registry,
            context=context,
            event_bus=event_bus,
            routing_config=routing_config
        )
        
        print("\n✓ System initialized!\n")
        
        # Run example queries
        queries = [
            "What is the current status of the test machine?",
            "Analyze the performance of the test machine over the last hour.",
            "Give me a summary of the test machine's operation."
        ]
        
        print("=" * 70)
        print("RUNNING EXAMPLE QUERIES")
        print("=" * 70)
        
        for i, query in enumerate(queries, 1):
            print(f"\n[Query {i}] {query}")
            print("-" * 70)
            
            result = coordinator.execute_workflow(query)
            
            if result["status"] == "success":
                print(f"✓ Status: {result['status']}")
                print(f"✓ Agents: {len(result['results'])}")
                print(f"\n📊 Final Output:\n{result['final_output']}\n")
            else:
                print(f"✗ Error: {result.get('error', 'Unknown')}\n")
        
        print("=" * 70)
        print("✓ Demo completed successfully!")
        print("=" * 70)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
