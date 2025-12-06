"""Configuration schema for agents using Pydantic."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MCPToolConfig(BaseModel):
    """Configuration for MCP tool access."""
    server: str = Field(..., description="MCP server name (e.g., 'highbyte', 'sql', 'teradata')")
    connection: Dict[str, Any] = Field(default_factory=dict, description="Connection parameters")
    tools: List[str] = Field(default_factory=list, description="List of allowed tool names")


class AgentConfig(BaseModel):
    """Configuration for a specialized agent."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    machine_id: str = Field(..., description="Machine this agent is expert on")
    function: str = Field(..., description="Primary function (data_fetching, analysis, summary)")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities")
    mcp_tools: List[MCPToolConfig] = Field(default_factory=list, description="MCP tool configurations")
    model: str = Field(default="gpt-4", description="LLM model to use")
    custom_instructions: Optional[str] = Field(None, description="Additional agent instructions")
    
    def get_all_tool_names(self) -> List[str]:
        """Get flat list of all allowed tool names across all servers."""
        all_tools = []
        for mcp_config in self.mcp_tools:
            all_tools.extend(mcp_config.tools)
        return all_tools


class RoutingExample(BaseModel):
    """Routing configuration example for keyword matching."""
    keywords: List[str] = Field(..., description="Keywords to match in user queries")
    machine_id: str = Field(..., description="Machine to route to")
    description: str = Field(default="", description="Description of this routing rule")


class SystemConfig(BaseModel):
    """Overall system configuration."""
    agents: List[AgentConfig] = Field(default_factory=list, description="Agent configurations")
    routing_examples: List[RoutingExample] = Field(default_factory=list, description="Routing examples")
    mcp_servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="MCP server connections")
    model: str = Field(default="gpt-4", description="Default LLM model")
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
