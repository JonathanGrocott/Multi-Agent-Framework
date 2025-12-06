"""Configuration loader for YAML-based agent setup."""

import yaml
from pathlib import Path
from typing import Dict, Any
from .agent_config import SystemConfig, AgentConfig, RoutingExample


def load_config(config_path: str) -> SystemConfig:
    """
    Load system configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Validated SystemConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # Validate and parse using Pydantic
    return SystemConfig(**config_dict)


def save_config(config: SystemConfig, config_path: str) -> None:
    """
    Save system configuration to YAML file.
    
    Args:
        config: SystemConfig object
        config_path: Path to save configuration
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.safe_dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)


def validate_config(config_path: str) -> bool:
    """
    Validate a configuration file without loading it fully.
    
    Args:
        config_path: Path to config file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        load_config(config_path)
        return True
    except Exception as e:
        print(f"Config validation failed: {e}")
        return False
