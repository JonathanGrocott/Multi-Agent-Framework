"""API endpoints for chat functionality."""

from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime

from ..models.chat import ChatRequest, ChatResponse, ChatError
from ..core.config_manager import ConfigManager
from ..core.framework_executor import FrameworkExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Global instances (initialized in main.py)
config_manager: ConfigManager = None
executor: FrameworkExecutor = None


def init_chat_dependencies(manager: ConfigManager, exec: FrameworkExecutor):
    """Initialize global dependencies."""
    global config_manager, executor
    config_manager = manager
    executor = exec


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Execute a chat query for a specific machine.
    
    Args:
        request: Chat request with machine_id and message
        
    Returns:
        AI-generated response with metadata
    """
    logger.info(f"Chat request for {request.machine_id}: {request.message[:50]}...")
    
    try:
        # Get machine configuration
        config = config_manager.get_config(request.machine_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Machine '{request.machine_id}' not found"
            )
        
        # Execute query using framework
        result = executor.execute_query(
            machine_id=request.machine_id,
            query=request.message,
            config_dict=config
        )
        
        if result['success']:
            return ChatResponse(
                response=result['response'],
                agent_count=result['agent_count'],
                execution_time_ms=result['execution_time_ms'],
                machine_id=request.machine_id,
                timestamp=datetime.now()
            )
        else:
            # Framework execution failed
            logger.error(f"Framework error: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Unknown error during execution')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/clear-cache")
async def clear_cache(machine_id: str = None):
    """
    Clear cached coordinators for machines.
    
    Args:
        machine_id: Optional specific machine to clear, or clear all if None
        
    Returns:
        Success message
    """
    try:
        executor.clear_cache(machine_id)
        if machine_id:
            message = f"Cleared cache for machine: {machine_id}"
        else:
            message = "Cleared cache for all machines"
        
        logger.info(message)
        return {"message": message}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
