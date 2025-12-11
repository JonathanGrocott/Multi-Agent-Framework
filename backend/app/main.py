"""FastAPI backend for Multi-Agent Manufacturing Framework."""

import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from multi_agent_framework.core import SharedContext, EventBus
from multi_agent_framework.core.mcp_client import MCPClient
from multi_agent_framework.agents import AgentRegistry
from multi_agent_framework.core.coordinator import Coordinator

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Multi-Agent Manufacturing Framework",
    description="Chat interface for manufacturing equipment",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use dependency injection)
context = SharedContext()
event_bus = EventBus()
mcp_client = MCPClient()
registry = AgentRegistry()

# Available machines (would be loaded from configs in production)
MACHINES = {
    "spar_lamination": {
        "id": "spar_lamination",
        "name": "Spar Lamination Machine",
        "description": "Composite spar lamination equipment"
    },
    "robot_a": {
        "id": "robot_a", 
        "name": "Robot A",
        "description": "Assembly robot station A"
    },
    "conveyor_belt": {
        "id": "conveyor_belt",
        "name": "Conveyor Belt",
        "description": "Main production line conveyor"
    }
}


class ChatRequest(BaseModel):
    message: str
    machine_id: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    machine_id: str
    session_id: str


class Machine(BaseModel):
    id: str
    name: str
    description: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Multi-Agent Manufacturing Framework"}


@app.get("/api/machines", response_model=list[Machine])
async def list_machines():
    """List available machines."""
    return [Machine(**m) for m in MACHINES.values()]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with a machine's AI assistant.
    
    This is a simplified demo that returns mock responses.
    In production, this would use the full multi-agent framework.
    """
    if request.machine_id not in MACHINES:
        raise HTTPException(status_code=404, detail=f"Machine '{request.machine_id}' not found")
    
    machine = MACHINES[request.machine_id]
    
    # Generate session ID if not provided
    session_id = request.session_id or f"session_{request.machine_id}_{id(request)}"
    
    # Demo responses based on query keywords
    query_lower = request.message.lower()
    
    if "status" in query_lower or "state" in query_lower:
        response = f"""**{machine['name']} Status Report**

🟢 **Overall Status**: Operational

**Current Metrics:**
- Cycle Time: 45.2 seconds
- Efficiency: 94.3%
- Parts Produced: 1,247
- Temperature: 72°F

**Recent Events:**
- Last maintenance: 2 days ago
- No active alarms
- Quality rate: 99.1%

The machine is running within normal parameters."""

    elif "error" in query_lower or "problem" in query_lower or "issue" in query_lower:
        response = f"""**{machine['name']} Error Analysis**

📋 **Recent Errors (Last 24 Hours):**

| Time | Error Code | Description | Status |
|------|------------|-------------|--------|
| 14:32 | E-101 | Temperature warning | Resolved |
| 09:15 | E-042 | Sensor calibration needed | Pending |

**Recommendations:**
1. Schedule sensor calibration during next break
2. Monitor temperature sensor readings

No critical errors detected."""

    elif "maintenance" in query_lower or "troubleshoot" in query_lower:
        response = f"""**{machine['name']} Maintenance Guide**

🔧 **Recommended Actions:**

1. **Daily Checks:**
   - Verify sensor readings
   - Check lubrication levels
   - Inspect safety guards

2. **Weekly Maintenance:**
   - Clean filters
   - Calibrate sensors
   - Test emergency stops

3. **Troubleshooting Tips:**
   - For E-101: Check cooling system
   - For E-042: Run sensor diagnostic

📅 Next scheduled maintenance: December 15, 2025"""

    else:
        response = f"""I'm the AI assistant for **{machine['name']}**.

I can help you with:
- 📊 **Status queries**: "What's the current status?"
- ⚠️ **Error analysis**: "Any errors in the last hour?"
- 🔧 **Maintenance**: "Show troubleshooting guide"
- 📈 **Performance**: "What's the efficiency today?"

What would you like to know?"""
    
    return ChatResponse(
        response=response,
        machine_id=request.machine_id,
        session_id=session_id
    )


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "api": "ok",
            "mcp_client": "ok",
            "agents": len(registry.list_agents())
        }
    }
