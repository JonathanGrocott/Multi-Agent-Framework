"""Specialized agent that combines machine and function expertise."""

from typing import Any, Dict, List, Optional
from ..core.agent import Agent
from ..core.context import SharedContext
from ..core.events import EventBus


class SpecializedAgent(Agent):
    """
    Specialized agent with combined machine and function expertise.
    
    Each agent is specialized for:
    - A specific machine (e.g., "Spar_Lamination_Machine", "Robot_A")
    - A specific function (e.g., "data_fetching", "analysis", "summary")
    
    This ensures clear ownership and eliminates confusion about which tools to use.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        machine_id: str,
        function: str,
        capabilities: List[str],
        allowed_tools: List[str],
        context: SharedContext,
        event_bus: EventBus,
        mcp_client: Optional[Any] = None,
        model: str = "gpt-4",
        custom_instructions: Optional[str] = None
    ):
        """
        Initialize specialized agent.
        
        Args:
            agent_id: Unique identifier (e.g., "spar_lam_data_fetcher")
            name: Human-readable name (e.g., "Spar Lamination Data Fetcher")
            machine_id: Machine this agent is expert on (e.g., "spar_lamination_machine")
            function: Primary function (e.g., "data_fetching", "analysis", "summary")
            capabilities: List of specific capabilities this agent has
            allowed_tools: List of MCP tool names this agent can use
            context: Shared context
            event_bus: Event bus
            mcp_client: MCP client
            model: LLM model
            custom_instructions: Additional instructions for the agent
        """
        self.machine_id = machine_id
        self.function = function
        self.capabilities = capabilities
        self.allowed_tools = set(allowed_tools)
        self.custom_instructions = custom_instructions
        
        # Store name temporarily for system prompt building
        self._temp_name = name
        
        # Build specialized system prompt
        system_prompt = self._build_system_prompt()
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            context=context,
            event_bus=event_bus,
            mcp_client=mcp_client,
            model=model,
            system_prompt=system_prompt
        )
    
    def _build_system_prompt(self) -> str:
        """Build specialized system prompt based on machine and function."""
        prompt_parts = [
            f"You are {self._temp_name}, an AI agent specialized in {self.function} for the {self.machine_id}.",
            f"\nYour capabilities: {', '.join(self.capabilities)}",
            f"\nYou have access to these MCP tools: {', '.join(self.allowed_tools)}",
            "\nYour role is to use these tools to complete your assigned tasks efficiently.",
        ]
        
        if self.custom_instructions:
            prompt_parts.append(f"\nAdditional instructions: {self.custom_instructions}")
        
        prompt_parts.append("\nAlways provide clear, concise results and store relevant data in the shared context for other agents.")
        
        return "\n".join(prompt_parts)
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task assigned to this specialized agent.
        
        Args:
            task: Task specification with:
                - instruction: What to do
                - parameters: Optional task parameters
                - context_keys: Optional keys to read from context
                
        Returns:
            Results with status, output, and context updates
        """
        from ..core.events import EventType
        
        # Emit task started event
        self.emit_event(EventType.TASK_STARTED, {"task": task})
        
        try:
            instruction = task.get("instruction", "")
            parameters = task.get("parameters", {})
            context_keys = task.get("context_keys", [])
            
            # Read relevant context if specified
            context_data = {}
            for key in context_keys:
                value = self.read_context(key)
                if value is not None:
                    context_data[key] = value
            
            # Execute the task using LLM and MCP tools
            result = self._execute_with_llm(instruction, parameters, context_data)
            
            # Emit task completed event
            self.emit_event(EventType.TASK_COMPLETED, {
                "task": task,
                "result": result
            })
            
            return {
                "status": "success",
                "agent_id": self.agent_id,
                "output": result,
                "metadata": {
                    "machine_id": self.machine_id,
                    "function": self.function
                }
            }
            
        except Exception as e:
            # Emit task failed event
            self.emit_event(EventType.TASK_FAILED, {
                "task": task,
                "error": str(e)
            })
            
            return {
                "status": "failed",
                "agent_id": self.agent_id,
                "error": str(e),
                "metadata": {
                    "machine_id": self.machine_id,
                    "function": self.function
                }
            }
    
    def _execute_with_llm(self, instruction: str, parameters: Dict[str, Any], 
                          context_data: Dict[str, Any]) -> Any:
        """
        Execute task using LLM with access to MCP tools.
        
        This is a placeholder for LLM integration. In Phase 2, this will:
        1. Call LLM with system prompt and instruction
        2. Allow LLM to invoke MCP tools through function calling
        3. Process results and return output
        
        For now, returns a simple mock response.
        """
        # TODO: Implement actual LLM integration with tool calling
        # For now, return structured response
        return {
            "message": f"Task executed by {self.name}",
            "instruction": instruction,
            "parameters": parameters,
            "context_available": list(context_data.keys()),
            "tools_available": list(self.allowed_tools)
        }
    
    def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Invoke an MCP tool (only if in allowed tools list).
        
        Args:
            tool_name: Name of tool to invoke
            parameters: Tool parameters
            
        Returns:
            Tool result
            
        Raises:
            PermissionError: If tool is not in allowed_tools
        """
        if tool_name not in self.allowed_tools:
            raise PermissionError(
                f"Agent {self.agent_id} is not allowed to use tool '{tool_name}'. "
                f"Allowed tools: {self.allowed_tools}"
            )
        
        return super().invoke_tool(tool_name, parameters)
    
    def can_handle_task(self, machine_id: str, required_function: str) -> bool:
        """
        Check if this agent can handle a task for a specific machine/function.
        
        Args:
            machine_id: Machine ID required for the task
            required_function: Function type required
            
        Returns:
            True if this agent can handle the task
        """
        return (
            self.machine_id == machine_id and 
            self.function == required_function
        )
    
    def __repr__(self) -> str:
        return (
            f"SpecializedAgent(id={self.agent_id}, machine={self.machine_id}, "
            f"function={self.function}, tools={len(self.allowed_tools)})"
        )
