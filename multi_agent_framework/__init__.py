"""
Multi-Agent Orchestration Framework

A framework for orchestrating specialized AI agents with MCP tool integration
for manufacturing and industrial applications.
"""

__version__ = "0.1.0"

from .core import (
    Agent,
    SharedContext,
    EventBus,
    Event,
    EventType,
    Coordinator
)

from .agents import (
    SpecializedAgent,
    AgentRegistry
)

from .config import (
    AgentConfig,
    MCPToolConfig,
    SystemConfig,
    load_config,
    save_config
)

__all__ = [
    "Agent",
    "SharedContext",
    "EventBus",
    "Event",
    "EventType",
    "Coordinator",
    "SpecializedAgent",
    "AgentRegistry",
    "AgentConfig",
    "MCPToolConfig",
    "SystemConfig",
    "load_config",
    "save_config",
]
