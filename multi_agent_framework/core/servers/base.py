"""Base class for MCP server implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseMCPServer(ABC):
    """
    Base class for MCP server implementations.
    
    Each server type (HighByte, SQL, Teradata, etc.) implements this interface
    to provide a consistent way to connect and invoke tools.
    """
    
    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        Initialize MCP server.
        
        Args:
            server_name: Unique name for this server instance
            config: Server configuration dictionary
        """
        self.server_name = server_name
        self.config = config
        self._connected = False
        
    @abstractmethod
    def connect(self) -> None:
        """
        Connect to the MCP server.
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        pass
    
    @abstractmethod
    def list_tools(self) -> List[str]:
        """
        List available tools from this server.
        
        Returns:
            List of tool names
        """
        pass
    
    @abstractmethod
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Invoke a tool on this server.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool doesn't exist
            RuntimeError: If tool execution fails
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if server is connected."""
        return self._connected
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.server_name}, connected={self._connected})"
