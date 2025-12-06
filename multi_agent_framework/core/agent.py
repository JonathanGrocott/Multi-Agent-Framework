"""Base agent class for the multi-agent framework."""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from .context import SharedContext
from .events import Event, EventBus, EventType


class Agent(ABC):
    """
    Base agent class with MCP tool integration and event handling.
    
    All specialized agents should inherit from this class and implement
    the execute() method for their specific functionality.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        context: SharedContext,
        event_bus: EventBus,
        mcp_client: Optional[Any] = None,
        llm_provider: Optional[Any] = None,
        model: str = "gpt-4",
        system_prompt: Optional[str] = None
    ):
        """
        Initialize agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            context: Shared context for inter-agent communication
            event_bus: Event bus for publishing/subscribing to events
            mcp_client: MCP client for tool invocation
            llm_provider: LLM provider for executing tasks
            model: LLM model to use
            system_prompt: Custom system prompt for this agent
        """
        self.agent_id = agent_id
        self.name = name
        self.context = context
        self.event_bus = event_bus
        self.mcp_client = mcp_client
        self.llm_provider = llm_provider
        self.model = model
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Subscribe to events
        self._setup_event_handlers()
        
    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return f"You are {self.name}, an AI agent specialized in specific tasks."
    
    def _setup_event_handlers(self) -> None:
        """
        Set up event handlers for this agent.
        Subclasses can override to add custom event handling.
        """
        pass
    
    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: Task specification with 'instruction' and optional parameters
            
        Returns:
            Task results including status, output, and any metadata
        """
        pass
    
    def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Invoke an MCP tool.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If MCP client is not configured
        """
        if not self.mcp_client:
            raise ValueError(f"Agent {self.agent_id} has no MCP client configured")
        
        # Emit tool invocation event
        self.emit_event(EventType.TOOL_INVOKED, {
            "tool_name": tool_name,
            "parameters": parameters
        })
        
        # Invoke tool through MCP client
        result = self.mcp_client.call_tool(tool_name, parameters)
        
        # Emit tool completion event
        self.emit_event(EventType.TOOL_COMPLETED, {
            "tool_name": tool_name,
            "result": result
        })
        
        return result
    
    def emit_event(self, event_type: EventType, data: Any = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit an event to the event bus.
        
        Args:
            event_type: Type of event
            data: Event data payload
            metadata: Additional event metadata
        """
        event = Event(
            event_type=event_type,
            agent_id=self.agent_id,
            data=data,
            metadata=metadata or {}
        )
        self.event_bus.publish(event)
    
    def read_context(self, key: str) -> Any:
        """
        Read from shared context.
        
        Args:
            key: Context key to read
            
        Returns:
            Context value or None
        """
        return self.context.read(key)
    
    def write_context(self, key: str, value: Any, summary: Optional[str] = None) -> None:
        """
        Write to shared context.
        
        Args:
            key: Context key
            value: Value to store
            summary: Optional summary for token optimization
        """
        self.context.write(key, value, agent_id=self.agent_id, summary=summary)
    
    def get_context_summary(self) -> str:
        """Get token-optimized summary of all context data."""
        return self.context.get_token_optimized_summary()
    
    def __repr__(self) -> str:
        return f"Agent(id={self.agent_id}, name={self.name})"
