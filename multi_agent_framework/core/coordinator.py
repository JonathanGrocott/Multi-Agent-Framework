"""Coordinator for orchestrating multi-agent workflows."""

from typing import Any, Dict, List, Optional, Tuple
from .context import SharedContext
from .events import Event, EventBus, EventType
from ..agents.registry import AgentRegistry
from ..agents.specialized_agent import SpecializedAgent


class Coordinator:
    """
    Coordinator for task routing and agent orchestration.
    
    Uses a routing configuration (local database/file) to determine which
    agents should handle specific tasks based on user input.
    
    Implements sequential execution in Phase 1, with async support in Phase 2.
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        context: SharedContext,
        event_bus: EventBus,
        routing_config: Optional[Dict[str, Any]] = None,
        llm_client: Optional[Any] = None
    ):
        """
        Initialize coordinator.
        
        Args:
            agent_registry: Registry of available agents
            context: Shared context for agents
            event_bus: Event bus for coordination
            routing_config: Routing configuration (examples, patterns, etc.)
            llm_client: Optional LLM client for intelligent routing
        """
        self.agent_registry = agent_registry
        self.context = context
        self.event_bus = event_bus
        self.routing_config = routing_config or {}
        self.llm_client = llm_client
        
        # Track workflow state
        self.current_workflow: Optional[Dict[str, Any]] = None
        
    def execute_workflow(self, user_query: str) -> Dict[str, Any]:
        """
        Execute a complete workflow for a user query.
        
        Args:
            user_query: User's request/question
            
        Returns:
            Workflow results with final output and metadata
        """
        # Emit workflow started event
        self.event_bus.publish(Event(
            event_type=EventType.WORKFLOW_STARTED,
            agent_id="coordinator",
            data={"query": user_query}
        ))
        
        try:
            # 1. Route the query to determine which agents to use
            workflow_plan = self.route_query(user_query)
            
            # 2. Execute agents sequentially
            results = []
            for step in workflow_plan["steps"]:
                agent_id = step["agent_id"]
                task = step["task"]
                
                agent = self.agent_registry.get_agent(agent_id)
                if not agent:
                    raise ValueError(f"Agent {agent_id} not found in registry")
                
                # Execute the task
                result = agent.execute(task)
                results.append(result)
                
                # Store result in context for next agents
                if result.get("status") == "success":
                    context_key = step.get("context_key", f"{agent_id}.result")
                    self.context.write(
                        context_key,
                        result["output"],
                        agent_id="coordinator",
                        summary=step.get("summary", "Task result")
                    )
            
            # 3. Aggregate final results
            final_output = self._aggregate_results(results)
            
            # Emit workflow completed event
            self.event_bus.publish(Event(
                event_type=EventType.WORKFLOW_COMPLETED,
                agent_id="coordinator",
                data={"results": final_output}
            ))
            
            return {
                "status": "success",
                "query": user_query,
                "workflow_plan": workflow_plan,
                "results": results,
                "final_output": final_output
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "query": user_query,
                "error": str(e)
            }
        finally:
            # Clear context after workflow
            # self.context.clear()  # Optional: uncomment if you want to clear after each workflow
            pass
    
    def route_query(self, user_query: str) -> Dict[str, Any]:
        """
        Route a user query to determine which agents should handle it.
        
        Uses either:
        1. Keyword matching against routing config examples
        2. LLM-based intent extraction (if llm_client is available)
        
        Args:
            user_query: User's question/request
            
        Returns:
            Workflow plan with agents and tasks
        """
        # Try LLM-based routing first if available
        if self.llm_client:
            return self._route_with_llm(user_query)
        
        # Fall back to keyword-based routing
        return self._route_with_keywords(user_query)
    
    def _route_with_keywords(self, user_query: str) -> Dict[str, Any]:
        """
        Route query using keyword matching.
        
        Looks for machine names and function keywords in the routing config.
        """
        query_lower = user_query.lower()
        
        # Extract machine ID from query
        machine_id = None
        for example in self.routing_config.get("examples", []):
            keywords = example.get("keywords", [])
            if any(keyword.lower() in query_lower for keyword in keywords):
                machine_id = example.get("machine_id")
                break
        
        if not machine_id:
            # Default to first available machine
            machines = self.agent_registry.get_all_machines()
            if machines:
                machine_id = machines[0]
            else:
                raise ValueError("No agents available in registry")
        
        # Determine workflow steps based on query type
        steps = self._create_workflow_steps(machine_id, user_query)
        
        return {
            "method": "keyword_matching",
            "machine_id": machine_id,
            "steps": steps
        }
    
    def _route_with_llm(self, user_query: str) -> Dict[str, Any]:
        """
        Route query using LLM-based intent extraction.
        
        Calls LLM with routing examples to determine best agent(s) to use.
        """
        # TODO: Implement LLM-based routing
        # For now, fall back to keyword routing
        return self._route_with_keywords(user_query)
    
    def _create_workflow_steps(self, machine_id: str, user_query: str) -> List[Dict[str, Any]]:
        """
        Create workflow steps for a given machine and query.
        
        Default workflow:
        1. Data fetching agent
        2. Analysis agent  
        3. Summary agent
        """
        steps = []
        
        # Step 1: Data fetching
        data_agent = self.agent_registry.find_agent(machine_id, "data_fetching")
        if data_agent:
            steps.append({
                "agent_id": data_agent.agent_id,
                "task": {
                    "instruction": f"Fetch relevant data for: {user_query}",
                    "parameters": {"query": user_query}
                },
                "context_key": f"{machine_id}.data",
                "summary": "Fetched machine data"
            })
        
        # Step 2: Analysis
        analysis_agent = self.agent_registry.find_agent(machine_id, "analysis")
        if analysis_agent:
            steps.append({
                "agent_id": analysis_agent.agent_id,
                "task": {
                    "instruction": f"Analyze the data to answer: {user_query}",
                    "parameters": {"query": user_query},
                    "context_keys": [f"{machine_id}.data"]
                },
                "context_key": f"{machine_id}.analysis",
                "summary": "Analysis results"
            })
        
        # Step 3: Summary
        summary_agent = self.agent_registry.find_agent(machine_id, "summary")
        if summary_agent:
            steps.append({
                "agent_id": summary_agent.agent_id,
                "task": {
                    "instruction": f"Create a summary answering: {user_query}",
                    "parameters": {"query": user_query},
                    "context_keys": [f"{machine_id}.data", f"{machine_id}.analysis"]
                },
                "context_key": f"{machine_id}.final_summary",
                "summary": "Final summary"
            })
        
        return steps
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Aggregate results from all agents into final output.
        
        Args:
            results: List of agent results
            
        Returns:
            Final aggregated output
        """
        # Find the last successful result (usually from summary agent)
        for result in reversed(results):
            if result.get("status") == "success":
                output = result.get("output", {})
                if isinstance(output, dict):
                    return output.get("message", str(output))
                return str(output)
        
        return "No results available"
    
    def add_routing_example(self, keywords: List[str], machine_id: str, 
                          description: str = "") -> None:
        """
        Add a routing example to help with keyword-based routing.
        
        Args:
            keywords: Keywords to match in user queries
            machine_id: Machine to route to when these keywords are found
            description: Optional description
        """
        if "examples" not in self.routing_config:
            self.routing_config["examples"] = []
        
        self.routing_config["examples"].append({
            "keywords": keywords,
            "machine_id": machine_id,
            "description": description
        })
    
    def __repr__(self) -> str:
        return (
            f"Coordinator(agents={len(self.agent_registry)}, "
            f"routing_examples={len(self.routing_config.get('examples', []))})"
        )
