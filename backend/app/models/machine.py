"""Pydantic models for machine information."""

from pydantic import BaseModel, Field
from typing import List, Optional


class MachineInfo(BaseModel):
    """Information about a configured machine."""
    id: str = Field(..., description="Unique machine identifier")
    name: str = Field(..., description="Human-readable machine name")
    description: Optional[str] = Field(None, description="Machine description")
    capabilities: List[str] = Field(default_factory=list, description="Machine capabilities")
    agent_count: int = Field(..., description="Number of agents configured")


class MachineListResponse(BaseModel):
    """Response containing list of available machines."""
    machines: List[MachineInfo] = Field(..., description="List of configured machines")
    total: int = Field(..., description="Total number of machines")
