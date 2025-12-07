"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

from .api import machines, chat
from .core.config_manager import ConfigManager
from .core.framework_executor import FrameworkExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Manufacturing API",
    description="API for interacting with multi-agent manufacturing assistants",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config_manager = None
executor = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global config_manager, executor
    
    logger.info("Starting Multi-Agent Manufacturing API...")
    
    # Initialize config manager
    config_dir = Path(__file__).parent.parent / "configs"
    config_manager = ConfigManager(str(config_dir))
    logger.info(f"Loaded {len(config_manager)} machine configurations")
    
    # Initialize framework executor
    executor = FrameworkExecutor()
    logger.info("Framework executor initialized")
    
    # Initialize API route dependencies
    machines.init_config_manager(config_manager)
    chat.init_chat_dependencies(config_manager, executor)
    
    logger.info("API ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API...")
    if executor:
        executor.clear_cache()


# Include routers
app.include_router(machines.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint showing API status."""
    return {
        "name": "Multi-Agent Manufacturing API",
        "version": "1.0.0",
        "status": "running",
        "machines_loaded": len(config_manager) if config_manager else 0
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "config_manager": "ok" if config_manager else "not initialized",
        "executor": "ok" if executor else "not initialized"
    }
