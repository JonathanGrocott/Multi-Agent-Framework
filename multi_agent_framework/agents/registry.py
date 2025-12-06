"""Agent registry for managing specialized agents."""

from typing import Dict, List, Optional
from .specialized_agent import SpecializedAgent


class AgentRegistry:
    """
    Registry for managing and discovering specialized agents.
    
    Provides methods to register agents and query them by machine ID,
    function type, or capabilities.
    """
    
    def __init__(self):
        self._agents: Dict[str, SpecializedAgent] = {}
        self._by_machine: Dict[str, List[str]] = {}  # machine_id -> [agent_ids]
        self._by_function: Dict[str, List[str]] = {}  # function -> [agent_ids]
        
    def register(self, agent: SpecializedAgent) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent: Specialized agent to register
        """
        self._agents[agent.agent_id] = agent
        
        # Index by machine
        if agent.machine_id not in self._by_machine:
            self._by_machine[agent.machine_id] = []
        self._by_machine[agent.machine_id].append(agent.agent_id)
        
        # Index by function
        if agent.function not in self._by_function:
            self._by_function[agent.function] = []
        self._by_function[agent.function].append(agent.agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[SpecializedAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def get_agents_for_machine(self, machine_id: str) -> List[SpecializedAgent]:
        """
        Get all agents specialized for a specific machine.
        
        Args:
            machine_id: Machine identifier
            
        Returns:
            List of specialized agents for this machine
        """
        agent_ids = self._by_machine.get(machine_id, [])
        return [self._agents[aid] for aid in agent_ids]
    
    def get_agents_by_function(self, function: str) -> List[SpecializedAgent]:
        """
        Get all agents with a specific function type.
        
        Args:
            function: Function type (e.g., "data_fetching", "analysis")
            
        Returns:
            List of agents with this function
        """
        agent_ids = self._by_function.get(function, [])
        return [self._agents[aid] for aid in agent_ids]
    
    def find_agent(self, machine_id: str, function: str) -> Optional[SpecializedAgent]:
        """
        Find agent for specific machine and function combination.
        
        Args:
            machine_id: Machine identifier
            function: Function type
            
        Returns:
            Matching agent or None
        """
        for agent in self._agents.values():
            if agent.can_handle_task(machine_id, function):
                return agent
        return None
    
    def get_all_agents(self) -> List[SpecializedAgent]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def get_all_machines(self) -> List[str]:
        """Get list of all machine IDs that have agents."""
        return list(self._by_machine.keys())
    
    def get_all_functions(self) -> List[str]:
        """Get list of all function types available."""
        return list(self._by_function.keys())
    
    def __len__(self) -> int:
        return len(self._agents)
    
    def __repr__(self) -> str:
        return (
            f"AgentRegistry(agents={len(self._agents)}, "
            f"machines={len(self._by_machine)}, "
            f"functions={len(self._by_function)})"
        )
