"""Pydantic models for chat functionality."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    machine_id: str = Field(..., description="ID of the machine to query")
    message: str = Field(..., min_length=1, description="User's question or query")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="AI-generated response")
    agent_count: int = Field(..., description="Number of agents involved")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    machine_id: str = Field(..., description="Machine that was queried")
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatError(BaseModel):
    """Error response for chat failures."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    machine_id: Optional[str] = Field(None)
