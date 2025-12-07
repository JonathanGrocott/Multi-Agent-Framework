"""Configuration manager for loading and caching machine configs."""

import yaml
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages loading and caching of machine configurations."""
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing machine config YAML files
        """
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, dict] = {}
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """Load all configuration files from the config directory."""
        if not self.config_dir.exists():
            logger.warning(f"Config directory not found: {self.config_dir}")
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                machine_id = config_file.stem
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                self._configs[machine_id] = config
                logger.info(f"Loaded config for machine: {machine_id}")
            except Exception as e:
                logger.error(f"Failed to load config {config_file}: {e}")
    
    def get_config(self, machine_id: str) -> Optional[dict]:
        """
        Get configuration for a specific machine.
        
        Args:
            machine_id: Machine identifier
            
        Returns:
            Configuration dictionary or None if not found
        """
        return self._configs.get(machine_id)
    
    def list_machines(self) -> List[str]:
        """
        Get list of all configured machine IDs.
        
        Returns:
            List of machine IDs
        """
        return list(self._configs.keys())
    
    def get_machine_info(self, machine_id: str) -> Optional[dict]:
        """
        Get information about a machine from its config.
        
        Args:
            machine_id: Machine identifier
            
        Returns:
            Dictionary with machine info or None
        """
        config = self.get_config(machine_id)
        if not config:
            return None
        
        agents = config.get('agents', [])
        
        # Extract capabilities from all agents
        all_capabilities = set()
        for agent in agents:
            all_capabilities.update(agent.get('capabilities', []))
        
        # Get machine name from first agent's machine_id or use the config id
        machine_name = machine_id.replace('_', ' ').title()
        if agents and 'machine_id' in agents[0]:
            machine_name = agents[0]['machine_id'].replace('_', ' ').title()
        
        return {
            'id': machine_id,
            'name': machine_name,
            'description': f"Multi-agent assistant for {machine_name}",
            'capabilities': sorted(list(all_capabilities)),
            'agent_count': len(agents)
        }
    
    def reload(self) -> None:
        """Reload all configurations from disk."""
        logger.info("Reloading configurations...")
        self._configs.clear()
        self._load_all_configs()
    
    def __len__(self) -> int:
        """Return number of loaded configurations."""
        return len(self._configs)
