"""RAG (Retrieval Augmented Generation) Agent for document search."""

from typing import Any, Dict, List, Optional
from ..core.agent import Agent
from ..core.context import SharedContext
from ..core.events import EventBus, EventType


class RAGAgent(Agent):
    """
    RAG Research Agent for searching technical documentation.
    
    This agent queries ChromaDB to find relevant context from user documents
    and provides that context to subsequent agents in the workflow.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        context: SharedContext,
        event_bus: EventBus,
        mcp_client: Optional[Any] = None,
        model: str = "gpt-4",
        collections: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize RAG Agent.
        
        Args:
            agent_id: Unique identifier
            name: Human-readable name
            context: Shared context
            event_bus: Event bus
            mcp_client: MCP client (should have ChromaDB server)
            model: LLM model
            collections: List of ChromaDB collections to search
            top_k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
        """
        self.collections = collections or []
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        
        system_prompt = self._build_system_prompt()
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            context=context,
            event_bus=event_bus,
            mcp_client=mcp_client,
            model=model,
            system_prompt=system_prompt
        )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for RAG agent."""
        return (
            f"You are {self.name if hasattr(self, 'name') else 'a RAG Research Agent'}, "
            "an AI agent specialized in searching technical documentation and knowledge bases. "
            "Your role is to find relevant context from documents that will help answer the user's query. "
            "Focus on extracting the most relevant information and summarizing key points concisely."
        )
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute RAG search task.
        
        Args:
            task: Task with 'instruction' (user query)
            
        Returns:
            Search results with relevant documents
        """
        self.emit_event(EventType.TASK_STARTED, {"task": task})
        
        try:
            query = task.get("instruction", "")
            parameters = task.get("parameters", {})
            
            # Search documents using ChromaDB
            search_results = self._search_documents(query, parameters)
            
            # Format results
            formatted_results = self._format_search_results(search_results)
            
            # Emit task completed
            self.emit_event(EventType.TASK_COMPLETED, {
                "task": task,
                "result": formatted_results
            })
            
            return {
                "status": "success",
                "agent_id": self.agent_id,
                "output": formatted_results,
                "metadata": {
                    "collections_searched": len(search_results.get("results", [])),
                    "total_documents": sum(
                        len(r.get("documents", []))
                        for r in search_results.get("results", [])
                    )
                }
            }
            
        except Exception as e:
            self.emit_event(EventType.TASK_FAILED, {
                "task": task,
                "error": str(e)
            })
            
            return {
                "status": "failed",
                "agent_id": self.agent_id,
                "error": str(e)
            }
    
    def _search_documents(self, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search documents in ChromaDB.
        
        Args:
            query: Search query
            parameters: Additional search parameters
            
        Returns:
            Search results from ChromaDB
        """
        if not self.mcp_client:
            return {"results": [], "message": "No MCP client configured"}
        
        try:
            # Call ChromaDB query tool
            result = self.invoke_tool("query_documents", {
                "query": query,
                "collection_name": parameters.get("collection"),
                "top_k": parameters.get("top_k", self.top_k)
            })
            
            return result.get("result", {})
            
        except Exception as e:
            print(f"RAG search error: {e}")
            return {"results": [], "error": str(e)}
    
    def _format_search_results(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format search results for consumption by other agents.
        
        Args:
            search_results: Raw search results from ChromaDB
            
       Returns:
            Formatted results with relevant context
        """
        results = search_results.get("results", [])
        
        if not results:
            return {
                "message": "No relevant documents found",
                "context": "",
                "documents": []
            }
        
        # Extract relevant documents
        relevant_docs = []
        context_parts = []
        
        for collection_result in results:
            collection_name = collection_result.get("collection", "unknown")
            documents = collection_result.get("documents", [])
            metadatas = collection_result.get("metadatas", [])
            distances = collection_result.get("distances", [])
            
            for idx, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                # Filter by similarity threshold (lower distance = more similar)
                if distance < (1 - self.similarity_threshold):
                    relevant_docs.append({
                        "collection": collection_name,
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - distance
                    })
                    
                    # Add to context summary
                    context_parts.append(f"[{collection_name}] {doc[:200]}...")
        
        # Create consolidated context
        context_summary = "\n\n".join(context_parts[:5])  # Limit to top 5
        
        return {
            "message": f"Found {len(relevant_docs)} relevant documents",
            "context": context_summary,
            "documents": relevant_docs,
            "query": search_results.get("query", "")
        }
    
    def __repr__(self) -> str:
        return f"RAGAgent(id={self.agent_id}, collections={len(self.collections)})"
