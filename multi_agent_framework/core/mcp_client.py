"""Enhanced MCP client wrapper with support for multiple server types."""

from typing import Any, Dict, List, Optional
from .servers import (
    BaseMCPServer,
    HighByteMCPServer,
    SQLServerMCPServer,
    TeradataMCPServer,
    ChromaDBMCPServer
)


class MCPClient:
    """
    Enhanced MCP client supporting multiple server types.
    
    Manages connections to:
    - HighByte (streamable-http with bearer token)
    - SQL Server (local + network)
    - Teradata (pre-defined queries)
    - ChromaDB (RAG/vector search)
    """
    
    # Server type to class mapping
    SERVER_TYPES = {
        "highbyte": HighByteMCPServer,
        "sql": SQLServerMCPServer,
        "teradata": TeradataMCPServer,
        "chromadb": ChromaDBMCPServer,
    }
    
    def __init__(self, servers: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize MCP client.
        
        Args:
            servers: Dictionary of server configurations
                {
                    "highbyte": {
                        "type": "highbyte",
                        "endpoint": "http://localhost:4567/mcp",
                        "auth": {"type": "bearer", "token": "..."}
                    },
                    "sql_local": {
                        "type": "sql",
                        "connection_string": "...",
                        "tools": [...]
                    }
                }
        """
        self.server_configs = servers or {}
        self._servers: Dict[str, BaseMCPServer] = {}
        self._tool_to_server: Dict[str, str] = {}  # tool_name -> server_name
        
    def connect(self, server_name: str, config: Dict[str, Any]) -> None:
        """
        Connect to an MCP server.
        
        Args:
            server_name: Unique identifier for this server instance
            config: Server configuration including "type" field
        """
        server_type = config.get("type")
        if not server_type:
            raise ValueError(f"Server config must include 'type' field: {server_name}")
        
        if server_type not in self.SERVER_TYPES:
            raise ValueError(
                f"Unknown server type '{server_type}'. "
                f"Supported: {list(self.SERVER_TYPES.keys())}"
            )
        
        # Create server instance
        server_class = self.SERVER_TYPES[server_type]
        server = server_class(server_name, config)
        
        # Connect
        server.connect()
        
        # Store server
        self._servers[server_name] = server
        
        # Map tools to this server
        for tool_name in server.list_tools():
            self._tool_to_server[tool_name] = server_name
    
    def disconnect(self, server_name: str) -> None:
        """Disconnect from an MCP server."""
        if server_name in self._servers:
            server = self._servers[server_name]
            
            # Remove tool mappings
            tools_to_remove = [
                tool for tool, srv in self._tool_to_server.items()
                if srv == server_name
            ]
            for tool in tools_to_remove:
                del self._tool_to_server[tool]
            
            # Disconnect and remove server
            server.disconnect()
            del self._servers[server_name]
    
    def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for server_name in list(self._servers.keys()):
            self.disconnect(server_name)
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Invoke an MCP tool.
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool is not found
            RuntimeError: If tool execution fails
        """
        # Find which server has this tool
        server_name = self._tool_to_server.get(tool_name)
        
        if not server_name:
            available = list(self._tool_to_server.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. "
                f"Available tools: {available[:10]}{'...' if len(available) > 10 else ''}"
            )
        
        server = self._servers[server_name]
        return server.call_tool(tool_name, parameters)
    
    def list_available_tools(self, server_name: Optional[str] = None) -> List[str]:
        """
        List available tools.
        
        Args:
            server_name: Optional server to filter by
            
        Returns:
            List of available tool names
        """
        if server_name:
            if server_name in self._servers:
                return self._servers[server_name].list_tools()
            return []
        
        # Return all tools from all servers
        return list(self._tool_to_server.keys())
    
    def list_servers(self) -> List[str]:
        """Get list of connected server names."""
        return list(self._servers.keys())
    
    def get_server(self, server_name: str) -> Optional[BaseMCPServer]:
        """Get a specific server instance (for advanced usage)."""
        return self._servers.get(server_name)
    
    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Get the server name that provides a specific tool."""
        return self._tool_to_server.get(tool_name)
    
    def is_connected(self, server_name: str) -> bool:
        """Check if a specific server is connected."""
        server = self._servers.get(server_name)
        return server.is_connected() if server else False
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool for LLM function calling.
        
        Args:
            tool_name: Tool name
            
        Returns:
            Tool info including description and parameters schema, or None if not found
        """
        server_name = self._tool_to_server.get(tool_name)
        if not server_name:
            return None
        
        server = self._servers.get(server_name)
        if not server:
            return None
        
        # Get tool info from server if available
        if hasattr(server, 'get_tool_info'):
            return server.get_tool_info(tool_name)
        
        # Fallback to basic info
        return {
            "name": tool_name,
            "description": f"Execute {tool_name} on {server_name}",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    
    def __repr__(self) -> str:
        total_tools = len(self._tool_to_server)
        return (
            f"MCPClient(servers={len(self._servers)}, "
            f"tools={total_tools}, "
            f"connected={sum(1 for s in self._servers.values() if s.is_connected())})"
        )
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect_all()

