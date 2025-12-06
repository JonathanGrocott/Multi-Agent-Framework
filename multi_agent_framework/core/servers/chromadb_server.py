"""ChromaDB MCP Server for RAG functionality."""

from typing import Any, Dict, List, Optional
from .base import BaseMCPServer

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class ChromaDBMCPServer(BaseMCPServer):
    """
    ChromaDB MCP Server for document search and RAG.
    
    Provides vector search capabilities over user documents.
    """
    
    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        Initialize ChromaDB MCP server.
        
        Expected config:
        {
            "persist_directory": "./chroma_data",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "tools": [
                {"name": "query_documents", "description": "Search documents"}
            ]
        }
        """
        super().__init__(server_name, config)
        
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB not installed. Install with: pip install chromadb"
            )
        
        self.persist_directory = config.get("persist_directory", "./chroma_data")
        self.embedding_model = config.get("embedding_model", "all-MiniLM-L6-v2")
        self.tool_definitions = config.get("tools", [])
        self._client: Optional[chromadb.Client] = None
        self._tools: List[str] = []
        
    def connect(self) -> None:
        """Connect to ChromaDB."""
        try:
            # Initialize ChromaDB client
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Register tools
            for tool_def in self.tool_definitions:
                self._tools.append(tool_def.get("name"))
            
            # Get collection count
            collections = self._client.list_collections()
            
            self._connected = True
            print(f"✓ Connected to ChromaDB: {len(collections)} collections")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ChromaDB: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from ChromaDB."""
        # ChromaDB client doesn't need explicit disconnection
        self._client = None
        self._connected = False
    
    def list_tools(self) -> List[str]:
        """List available ChromaDB tools."""
        return self._tools.copy()
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute ChromaDB query tool.
        
        Args:
            tool_name: Name of tool (e.g., "query_documents")
            parameters: Must include "query" and optional "collection_name", "top_k"
            
        Returns:
            Search results with documents and metadata
        """
        if not self._connected or not self._client:
            raise RuntimeError("Not connected to ChromaDB")
        
        if tool_name not in self._tools:
            raise ValueError(
                f"Tool '{tool_name}' not found. Available: {self._tools}"
            )
        
        try:
            if tool_name == "query_documents":
                return self._query_documents(parameters)
            else:
                raise ValueError(f"Unknown ChromaDB tool: {tool_name}")
                
        except Exception as e:
            raise RuntimeError(f"ChromaDB query failed: {e}")
    
    def _query_documents(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query documents in ChromaDB collections.
        
        Args:
            parameters: 
                - query: Search query string
                - collection_name: Optional specific collection (searches all if not specified)
                - top_k: Number of results (default 5)
                
        Returns:
            Search results
        """
        query = parameters.get("query")
        if not query:
            raise ValueError("Parameter 'query' is required")
        
        collection_name = parameters.get("collection_name")
        top_k = parameters.get("top_k", 5)
        
        results = []
        
        if collection_name:
            # Query specific collection
            collection = self._client.get_collection(collection_name)
            query_result = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            results.append({
                "collection": collection_name,
                "documents": query_result.get("documents", [[]])[0],
                "metadatas": query_result.get("metadatas", [[]])[0],
                "distances": query_result.get("distances", [[]])[0]
            })
        else:
            # Query all collections
            collections = self._client.list_collections()
            for collection in collections:
                query_result = collection.query(
                    query_texts=[query],
                    n_results=top_k
                )
                if query_result.get("documents") and query_result["documents"][0]:
                    results.append({
                        "collection": collection.name,
                        "documents": query_result["documents"][0],
                        "metadatas": query_result["metadatas"][0] if query_result.get("metadatas") else [],
                        "distances": query_result["distances"][0] if query_result.get("distances") else []
                    })
        
        return {
            "tool": tool_name,
            "parameters": parameters,
            "result": {
                "query": query,
                "results": results,
                "total_collections_searched": len(results)
            }
        }
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None) -> None:
        """
        Add documents to a ChromaDB collection.
        
        Args:
            collection_name: Name of collection
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents
        """
        if not self._connected or not self._client:
            raise RuntimeError("Not connected to ChromaDB")
        
        collection = self._client.get_or_create_collection(collection_name)
        
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()
