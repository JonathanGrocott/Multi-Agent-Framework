"""Framework executor that integrates with the multi-agent framework."""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to import framework
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from multi_agent_framework.core import SharedContext, EventBus, Coordinator
from multi_agent_framework.core.mcp_client import MCPClient
from multi_agent_framework.core.llm_factory import LLMFactory
from multi_agent_framework.agents import AgentRegistry, SpecializedAgent
from multi_agent_framework.config import load_config

logger = logging.getLogger(__name__)


class FrameworkExecutor:
    """Executes queries using the multi-agent framework."""
    
    def __init__(self):
        """Initialize the executor."""
        self._coordinators: Dict[str, Coordinator] = {}
        self._contexts: Dict[str, SharedContext] = {}
    
    def execute_query(self, machine_id: str, query: str, config_dict: dict) -> Dict[str, Any]:
        """
        Execute a query for a specific machine.
        
        Args:
            machine_id: Machine identifier
            query: User query
            config_dict: Machine configuration
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Get or create coordinator for this machine
            coordinator = self._get_or_create_coordinator(machine_id, config_dict)
            
            # Execute workflow
            logger.info(f"Executing query for {machine_id}: {query[:50]}...")
            result = coordinator.execute_workflow(query)
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if result['status'] == 'success':
                return {
                    'success': True,
                    'response': result['final_output'],
                    'agent_count': len(result.get('results', [])),
                    'execution_time_ms': execution_time
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'execution_time_ms': execution_time
                }
                
        except Exception as e:
            logger.error(f"Error executing query for {machine_id}: {e}")
            execution_time = (time.time() - start_time) * 1000
            return {
                'success': False,
                'error': str(e),
                'execution_time_ms': execution_time
            }
    
    def _get_or_create_coordinator(self, machine_id: str, config_dict: dict) -> Coordinator:
        """
        Get existing coordinator or create new one for machine.
        
        Args:
            machine_id: Machine identifier
            config_dict: Configuration dictionary
            
        Returns:
            Coordinator instance
        """
        # Return cached coordinator if exists
        if machine_id in self._coordinators:
            return self._coordinators[machine_id]
        
        logger.info(f"Initializing coordinator for {machine_id}")
        
        # Parse config using framework's config model
        from multi_agent_framework.config.agent_config import SystemConfig
        config = SystemConfig(**config_dict)
        
        # Initialize core components
        context = SharedContext()
        event_bus = EventBus()
        agent_registry = AgentRegistry()
        
        # Initialize MCP client if servers configured
        mcp_client = None
        if config.mcp_servers:
            mcp_client = MCPClient()
            for server_name, server_config in config.mcp_servers.items():
                try:
                    mcp_client.connect(server_name, server_config)
                    logger.info(f"Connected to MCP server: {server_name}")
                except Exception as e:
                    logger.warning(f"Failed to connect to {server_name}: {e}")
        
        # Initialize LLM providers
        llm_providers = {}
        default_provider = None
        try:
            llm_providers = LLMFactory.create_from_config(config)
            if config.default_llm_provider and config.default_llm_provider in llm_providers:
                default_provider = llm_providers[config.default_llm_provider]
                logger.info(f"Using LLM provider: {config.default_llm_provider}")
        except Exception as e:
            logger.warning(f"LLM provider initialization failed: {e}")
        
        # Create and register agents
        for agent_config in config.agents:
            allowed_tools = agent_config.get_all_tool_names()
            
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
                llm_provider=default_provider,
                model=agent_config.model,
                custom_instructions=agent_config.custom_instructions
            )
            agent_registry.register(agent)
            logger.info(f"Registered agent: {agent.name}")
        
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
        
        # Cache for reuse
        self._coordinators[machine_id] = coordinator
        self._contexts[machine_id] = context
        
        logger.info(f"Coordinator initialized for {machine_id}")
        return coordinator
    
    def clear_cache(self, machine_id: Optional[str] = None) -> None:
        """
        Clear cached coordinators.
        
        Args:
            machine_id: Specific machine to clear, or None to clear all
        """
        if machine_id:
            self._coordinators.pop(machine_id, None)
            self._contexts.pop(machine_id, None)
            logger.info(f"Cleared cache for {machine_id}")
        else:
            self._coordinators.clear()
            self._contexts.clear()
            logger.info("Cleared all coordinator caches")
