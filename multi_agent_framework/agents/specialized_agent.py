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
        llm_provider: Optional[Any] = None,
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
            llm_provider: LLM provider for task execution
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
            llm_provider=llm_provider,
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
        
        Implements a function calling loop:
        1. Call LLM with system prompt, instruction, and context
        2. If LLM requests tool calls, execute them
        3. Add tool results to conversation and continue
        4. Repeat until LLM provides final answer
        
        Args:
            instruction: Task instruction
            parameters: Task parameters
            context_data: Relevant context data
            
        Returns:
            Final LLM response or structured fallback
        """
        # If no LLM provider, return mock response
        if not self.llm_provider:
            return {
                "message": f"Task executed by {self.name} (no LLM provider configured)",
                "instruction": instruction,
                "parameters": parameters,
                "context_available": list(context_data.keys()),
                "tools_available": list(self.allowed_tools)
            }
        
        try:
            from ..core.llm_provider import LLMMessage, ToolDefinition, MessageRole
            
            # Build conversation messages
            messages = []
            
            # System message with specialized prompt
            messages.append(LLMMessage(
                role=MessageRole.SYSTEM,
                content=self.system_prompt
            ))
            
            # Build user message with instruction, parameters, and context
            user_content_parts = [f"Task: {instruction}"]
            
            if parameters:
                user_content_parts.append(f"\nParameters: {parameters}")
            
            if context_data:
                user_content_parts.append(f"\nContext data available: {list(context_data.keys())}")
                # Add summaries of context data
                for key, value in context_data.items():
                    summary = self.context.get_summary(key)
                    if summary:
                        user_content_parts.append(f"  - {key}: {summary}")
            
            messages.append(LLMMessage(
                role=MessageRole.USER,
                content="\n".join(user_content_parts)
            ))
            
            # Get tool definitions for MCP tools
            tools = self._get_tool_definitions()
            
            # Function calling loop with max iterations to prevent infinite loops
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Call LLM
                response = self.llm_provider.complete(
                    messages=messages,
                    model=self.model,
                    tools=tools if tools else None,
                    temperature=0.7
                )
                
                # If no tool calls, we have the final answer
                if not response.tool_calls:
                    return response.content or "Task completed successfully."
                
                # Add assistant message with tool calls
                messages.append(LLMMessage(
                    role=MessageRole.ASSISTANT,
                    content=response.content,
                    tool_calls=response.tool_calls
                ))
                
                # Execute each tool call and add results
                for tool_call in response.tool_calls:
                    try:
                        # Invoke the tool
                        tool_result = self.invoke_tool(tool_call.name, tool_call.arguments)
                        
                        # Add tool result message
                        messages.append(LLMMessage(
                            role=MessageRole.TOOL,
                            content=str(tool_result),
                            tool_call_id=tool_call.id,
                            name=tool_call.name
                        ))
                    except Exception as e:
                        # Add error message as tool result
                        messages.append(LLMMessage(
                            role=MessageRole.TOOL,
                            content=f"Error executing tool: {str(e)}",
                            tool_call_id=tool_call.id,
                            name=tool_call.name
                        ))
            
            # If we hit max iterations, return what we have
            return "Task execution reached maximum iterations. Please review the results."
            
        except Exception as e:
            # If LLM execution fails, return error details
            raise Exception(f"LLM execution failed: {str(e)}") from e
    
    def _get_tool_definitions(self) -> List:
        """
        Get tool definitions for allowed MCP tools.
        
        Returns:
            List of ToolDefinition objects
        """
        from ..core.llm_provider import ToolDefinition
        
        if not self.mcp_client or not self.allowed_tools:
            return []
        
        tool_defs = []
        available_tools = self.mcp_client.list_available_tools()
        
        for tool_name in self.allowed_tools:
            # Get tool info from MCP client
            tool_info = self.mcp_client.get_tool_info(tool_name)
            if tool_info:
                tool_defs.append(ToolDefinition(
                    name=tool_name,
                    description=tool_info.get("description", f"Execute {tool_name}"),
                    parameters=tool_info.get("parameters", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                ))
        
        return tool_defs
    
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
