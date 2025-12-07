"""API endpoints for machine management."""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models.machine import MachineInfo, MachineListResponse
from ..core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/machines", tags=["machines"])

# Global config manager instance (initialized in main.py)
config_manager: ConfigManager = None


def init_config_manager(manager: ConfigManager):
    """Initialize the global config manager."""
    global config_manager
    config_manager = manager


@router.get("", response_model=MachineListResponse)
async def list_machines():
    """
    Get list of all available machines.
    
    Returns:
        List of configured machines with their metadata
    """
    try:
        machine_ids = config_manager.list_machines()
        machines = []
        
        for machine_id in machine_ids:
            info = config_manager.get_machine_info(machine_id)
            if info:
                machines.append(MachineInfo(**info))
        
        logger.info(f"Returning {len(machines)} machines")
        return MachineListResponse(
            machines=machines,
            total=len(machines)
        )
    except Exception as e:
        logger.error(f"Error listing machines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{machine_id}", response_model=MachineInfo)
async def get_machine(machine_id: str):
    """
    Get detailed information about a specific machine.
    
    Args:
        machine_id: Machine identifier
        
    Returns:
        Machine information
    """
    try:
        info = config_manager.get_machine_info(machine_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")
        
        return MachineInfo(**info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting machine {machine_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_configs():
    """
    Reload all machine configurations from disk.
    
    Useful for admins to reload configs without restarting server.
    """
    try:
        config_manager.reload()
        machine_count = len(config_manager)
        logger.info(f"Reloaded {machine_count} configurations")
        return {"message": f"Reloaded {machine_count} machine configurations"}
    except Exception as e:
        logger.error(f"Error reloading configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
