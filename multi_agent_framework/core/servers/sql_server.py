"""SQL Server MCP implementation with pre-defined query tools."""

import sqlalchemy
from sqlalchemy import create_engine, text
from typing import Any, Dict, List, Optional
from .base import BaseMCPServer


class SQLServerMCPServer(BaseMCPServer):
    """
    SQL Server MCP implementation.
    
    Supports both local SQL Express and network SQL Servers with
    pre-defined query tools.
    """
    
    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        Initialize SQL Server MCP.
        
        Expected config:
        {
            "connection_string": "mssql://localhost/DatabaseName",
            "driver": "pyodbc",
            "tools": [
                {
                    "name": "query_logs",
                    "query": "SELECT TOP 100 * FROM logs WHERE timestamp > @start_time",
                    "description": "Get recent logs"
                }
            ]
        }
        """
        super().__init__(server_name, config)
        self.connection_string = config.get("connection_string")
        self.driver = config.get("driver", "pyodbc")
        self.tool_definitions = config.get("tools", [])
        self._engine: Optional[sqlalchemy.Engine] = None
        self._tools: Dict[str, Dict[str, Any]] = {}
        
    def connect(self) -> None:
        """Connect to SQL Server."""
        try:
            # Create SQLAlchemy engine
            # For pyodbc, need to append driver info
            conn_str = self.connection_string
            if self.driver == "pyodbc" and "?" not in conn_str:
                conn_str += "?driver=ODBC+Driver+17+for+SQL+Server"
            
            self._engine = create_engine(conn_str, echo=False)
            
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Register tools
            for tool_def in self.tool_definitions:
                tool_name = tool_def.get("name")
                self._tools[tool_name] = {
                    "query": tool_def.get("query"),
                    "description": tool_def.get("description", "")
                }
            
            self._connected = True
            print(f"✓ Connected to SQL Server: {self.server_name} ({len(self._tools)} tools)")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SQL Server: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from SQL Server."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        self._connected = False
    
    def list_tools(self) -> List[str]:
        """List available SQL query tools."""
        return list(self._tools.keys())
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a pre-defined SQL query tool.
        
        Args:
            tool_name: Name of the query tool
            parameters: Query parameters (e.g., {"start_time": "2025-12-06"})
            
        Returns:
            Query results as list of dicts
        """
        if not self._connected or not self._engine:
            raise RuntimeError(f"Not connected to SQL Server: {self.server_name}")
        
        if tool_name not in self._tools:
            raise ValueError(
                f"Tool '{tool_name}' not found. Available: {list(self._tools.keys())}"
            )
        
        try:
            tool_def = self._tools[tool_name]
            query_template = tool_def["query"]
            
            # Execute query with parameters
            with self._engine.connect() as conn:
                result = conn.execute(text(query_template), parameters)
                
                # Convert to list of dicts
                rows = []
                for row in result:
                    rows.append(dict(row._mapping))
                
                return {
                    "tool": tool_name,
                    "parameters": parameters,
                    "result": {
                        "rows": rows,
                        "row_count": len(rows),
                        "server": self.server_name
                    }
                }
                
        except Exception as e:
            raise RuntimeError(f"SQL query failed: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()
