"""Shared context for efficient information passing between agents."""

from typing import Any, Dict, Optional
from datetime import datetime
import json


class SharedContext:
    """
    Token-efficient shared memory for agent communication.
    
    Stores condensed summaries and structured data rather than full tool outputs
    to minimize token usage when agents need to access previous results.
    """
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._version = 0
        
    def write(self, key: str, value: Any, agent_id: Optional[str] = None, 
              summary: Optional[str] = None) -> None:
        """
        Write data to shared context.
        
        Args:
            key: Structured key (e.g., "robot_a.status", "analysis.error_count")
            value: Data to store (prefer structured data over raw strings)
            agent_id: ID of the agent writing this data
            summary: Optional human-readable summary of the data
        """
        self._data[key] = value
        self._metadata[key] = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "version": self._version
        }
        self._version += 1
        
    def read(self, key: str) -> Optional[Any]:
        """
        Read data from shared context.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Stored value or None if key doesn't exist
        """
        return self._data.get(key)
    
    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific key."""
        return self._metadata.get(key)
    
    def get_all_keys(self) -> list[str]:
        """Get all available keys in context."""
        return list(self._data.keys())
    
    def get_summary(self, key: str) -> Optional[str]:
        """Get human-readable summary for a key if available."""
        meta = self._metadata.get(key, {})
        return meta.get("summary")
    
    def clear(self) -> None:
        """Clear all context data (useful after workflow completion)."""
        self._data.clear()
        self._metadata.clear()
        self._version = 0
        
    def to_dict(self) -> Dict[str, Any]:
        """Export context as dictionary."""
        return {
            "data": self._data.copy(),
            "metadata": self._metadata.copy(),
            "version": self._version
        }
    
    def get_token_optimized_summary(self) -> str:
        """
        Get a token-efficient summary of all context data.
        
        Returns condensed view of context suitable for passing to LLMs.
        """
        summary_parts = []
        for key, value in self._data.items():
            meta = self._metadata.get(key, {})
            if meta.get("summary"):
                summary_parts.append(f"{key}: {meta['summary']}")
            else:
                # Truncate large values
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                summary_parts.append(f"{key}: {value_str}")
        
        return "\n".join(summary_parts)
    
    def __repr__(self) -> str:
        return f"SharedContext(keys={len(self._data)}, version={self._version})"
