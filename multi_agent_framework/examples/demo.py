#!/usr/bin/env python3
"""
Demo script showing how to use the multi-agent orchestration framework.

This example demonstrates:
1. Loading configuration from YAML
2. Initializing the system
3. Executing a workflow with multiple specialized agents
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_framework.core import SharedContext, EventBus, Coordinator
from multi_agent_framework.core.mcp_client import MCPClient
from multi_agent_framework.core.llm_factory import LLMFactory
from multi_agent_framework.agents import AgentRegistry, SpecializedAgent
from multi_agent_framework.config import load_config


def setup_system(config_path: str):
    """
    Set up the multi-agent system from configuration.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Tuple of (coordinator, agent_registry, context, event_bus)
    """
    print(f"Loading configuration from {config_path}...")
    config = load_config(config_path)
    
    # Initialize core components
    print("Initializing core components...")
    context = SharedContext()
    event_bus = EventBus()
    agent_registry = AgentRegistry()
    
    # Initialize MCP client
    mcp_client = MCPClient(servers=config.mcp_servers)
    
    # Connect to MCP servers
    for server_name, server_config in config.mcp_servers.items():
        print(f"Connecting to MCP server: {server_name}")
        mcp_client.connect(server_name, server_config)
    
    # Initialize LLM providers
    print(f"\nInitializing LLM providers...")
    llm_providers = {}
    try:
        llm_providers = LLMFactory.create_from_config(config)
        for provider_name in llm_providers.keys():
            print(f"  ✓ Created LLM provider: {provider_name}")
    except Exception as e:
        print(f"  ⚠ Warning: LLM provider initialization failed: {e}")
        print(f"  Agents will run without LLM capabilities (mock mode)")
    
    # Get default provider
    default_provider = None
    if config.default_llm_provider and config.default_llm_provider in llm_providers:
        default_provider = llm_providers[config.default_llm_provider]
        print(f"  ✓ Default provider: {config.default_llm_provider}")
    
    # Create and register agents
    print(f"\nRegistering {len(config.agents)} agents...")
    for agent_config in config.agents:
        # Get all allowed tools for this agent
        allowed_tools = agent_config.get_all_tool_names()
        
        # Create specialized agent
        agent = SpecializedAgent(
            agent_id=agent_config.agent_id,
            name=agent_config.name,
            machine_id=agent_config.machine_id,
            function=agent_config.function,
            capabilities=agent_config.capabilities,
            allowed_tools=allowed_tools,
            context=context,
            event_bus=event_bus,
            mcp_client=mcp_client,
            llm_provider=default_provider,  # Pass LLM provider
            model=agent_config.model,
            custom_instructions=agent_config.custom_instructions
        )
        
        agent_registry.register(agent)
        print(f"  ✓ Registered: {agent.name} ({agent.function})")
    
    # Build routing configuration
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
    
    # Create coordinator
    coordinator = Coordinator(
        agent_registry=agent_registry,
        context=context,
        event_bus=event_bus,
        routing_config=routing_config
    )
    
    print(f"\n✓ System initialized successfully!")
    print(f"  - Agents: {len(agent_registry)}")
    print(f"  - Machines: {len(agent_registry.get_all_machines())}")
    print(f"  - Routing examples: {len(routing_config['examples'])}")
    print(f"  - MCP tools available: {len(mcp_client.list_available_tools())}")
    
    return coordinator, agent_registry, context, event_bus


def run_example_queries(coordinator: Coordinator):
    """
    Run example queries through the system.
    
    Args:
        coordinator: Initialized coordinator
    """
    example_queries = [
        "What's the current status of the spar lamination machine?",
        "Has the spar lamination machine had any errors in the last hour?",
        "Show me the performance metrics for the spar lamination machine"
    ]
    
    print("\n" + "="*70)
    print("RUNNING EXAMPLE QUERIES")
    print("="*70)
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n[Query {i}] {query}")
        print("-" * 70)
        
        # Execute workflow
        result = coordinator.execute_workflow(query)
        
        # Display results
        if result["status"] == "success":
            print(f"✓ Status: {result['status']}")
            print(f"✓ Agents used: {len(result['results'])}")
            for step_result in result['results']:
                agent_id = step_result.get('agent_id', 'unknown')
                function = step_result.get('metadata', {}).get('function', 'unknown')
                print(f"  - {agent_id} ({function})")
            print(f"\n📊 Final Output:\n{result['final_output']}")
        else:
            print(f"✗ Status: {result['status']}")
            print(f"✗ Error: {result.get('error', 'Unknown error')}")
        
        print()


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Multi-Agent Orchestration Framework Demo")
    parser.add_argument(
        "--config",
        type=str,
        default="spar_lamination_config.yaml",
        help="Path to configuration YAML file (default: spar_lamination_config.yaml)"
    )
    args = parser.parse_args()
    
    print("="*70)
    print("MULTI-AGENT ORCHESTRATION FRAMEWORK - DEMO")
    print("="*70)
    print()
    
    # Get config path
    config_path = Path(__file__).parent / args.config
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Please ensure the config file exists in the examples directory.")
        print(f"\nAvailable configs:")
        for cfg in Path(__file__).parent.glob("*.yaml"):
            print(f"  - {cfg.name}")
        return 1
    
    try:
        # Set up the system
        coordinator, registry, context, event_bus = setup_system(str(config_path))
        
        # Run example queries
        run_example_queries(coordinator)
        
        # Show event history
        print("\n" + "="*70)
        print("EVENT HISTORY")
        print("="*70)
        history = event_bus.get_history(limit=20)
        for event in history:
            print(f"[{event.timestamp.strftime('%H:%M:%S')}] {event.event_type.value} - {event.agent_id}")
        
        print("\n✓ Demo completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
