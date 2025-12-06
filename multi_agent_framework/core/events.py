"""Event system for agent coordination and workflow orchestration."""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


class EventType(Enum):
    """Types of events in the agent system."""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_READY = "agent_ready"
    TOOL_INVOKED = "tool_invoked"
    TOOL_COMPLETED = "tool_completed"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"


@dataclass
class Event:
    """
    Event object for agent communication.
    
    Attributes:
        event_type: Type of event
        agent_id: ID of the agent that emitted this event
        data: Event payload (task results, tool outputs, etc.)
        timestamp: When the event was created
        metadata: Additional event metadata
    """
    event_type: EventType
    agent_id: str
    data: Any = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class EventBus:
    """
    Synchronous event bus for agent coordination.
    
    Implements publish/subscribe pattern for event-driven workflows.
    Phase 1: Synchronous handlers (sequential execution)
    Phase 2: Can be extended to async handlers
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self._event_history: List[Event] = []
        self._max_history = 100  # Limit history size
        
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to listen for
            handler: Callback function that takes an Event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Call handlers synchronously
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't stop other handlers
                print(f"Error in event handler for {event.event_type}: {e}")
                
    def get_history(self, 
                   event_type: Optional[EventType] = None,
                   agent_id: Optional[str] = None,
                   limit: int = 10) -> List[Event]:
        """
        Get event history with optional filtering.
        
        Args:
            event_type: Filter by event type
            agent_id: Filter by agent ID
            limit: Maximum number of events to return
            
        Returns:
            List of events (most recent first)
        """
        filtered = self._event_history
        
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if agent_id:
            filtered = [e for e in filtered if e.agent_id == agent_id]
            
        return list(reversed(filtered[-limit:]))
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        
    def __repr__(self) -> str:
        total_handlers = sum(len(handlers) for handlers in self._handlers.values())
        return f"EventBus(handlers={total_handlers}, history={len(self._event_history)})"
