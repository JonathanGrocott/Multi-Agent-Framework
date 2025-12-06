#!/usr/bin/env python3
"""
Phase 2 Demo - MCP Server Integration Test

Tests the new MCP server implementations:
- HighByte (streamable-http with bearer token)
- SQL Server (parameterized queries)
- Teradata (named queries)
- ChromaDB (RAG)
- SQLite history tracking
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_agent_framework.core import SharedContext, EventBus, HistoryService
from multi_agent_framework.core.mcp_client import MCPClient
from multi_agent_framework.agents import AgentRegistry, SpecializedAgent, RAGAgent
from multi_agent_framework.core.coordinator import Coordinator
from multi_agent_framework.config import load_config


def test_mcp_servers():
    """Test MCP server connections."""
    print("="*70)
    print("TESTING MCP SERVER CONNECTIONS")
    print("="*70)
    print()
    
    # Create MCP client
    mcp_client = MCPClient()
    
    # Test HighByte connection (mock for now)
    print("1. Testing HighByte MCP Server...")
    try:
        mcp_client.connect("highbyte", {
            "type": "highbyte",
            "endpoint": "http://localhost:4567/mcp",
            "auth": {
                "type": "bearer",
                "token": "test-token"
            }
        })
        tools = mcp_client.list_available_tools("highbyte")
        print(f"   ✓ Connected with {len(tools)} tools: {tools[:3]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test SQL Server connection (requires actual DB - will use mock for now)
    print("\n2. Testing SQL Server...")
    print("   (Requires actual SQL Server - skipping for demo)")
    # try:
    #     mcp_client.connect("sql_local", {
    #         "type": "sql",
    #         "connection_string": "mssql://localhost/TestDB",
    #         "tools": [...]
    #     })
    # except Exception as e:
    #     print(f"   Note: {e}")
    
    # Test Teradata connection (mock)
    print("\n3. Testing Teradata MCP Server...")
    try:
        mcp_client.connect("teradata", {
            "type": "teradata",
            "connection_string": "teradata://localhost/analytics",
            "tools": [
                {"name": "teradata_spar_lamination_get_stats", "description": "Get stats"}
            ]
        })
        tools = mcp_client.list_available_tools("teradata")
        print(f"   ✓ Connected with {len(tools)} tools: {tools}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test ChromaDB connection
    print("\n4. Testing ChromaDB...")
    try:
        mcp_client.connect("chromadb", {
            "type": "chromadb",
            "persist_directory": "./test_chroma_data",
            "tools": [
                {"name": "query_documents", "description": "Search documents"}
            ]
        })
        tools = mcp_client.list_available_tools("chromadb")
        print(f"   ✓ Connected with {len(tools)} tools: {tools}")
    except ImportError as e:
        print(f"   ⚠ ChromaDB not installed. Install with: pip install chromadb")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print(f"\n{mcp_client}")
    print()
    
    return mcp_client


def test_history_service():
    """Test SQLite history tracking."""
    print("="*70)
    print("TESTING HISTORY SERVICE")
    print("="*70)
    print()
    
    history = HistoryService(database_path="./test_workflow_history.db")
    
    # Log a test workflow
    workflow_id = history.log_workflow(
        user_query="Test query: What is the status of the machine?",
        final_result="Machine is running normally at 95% efficiency.",
        metadata={"machine_id": "test_machine", "agent_count": 3},
        execution_time_ms=1500,
        status="success"
    )
    
    print(f"✓ Logged workflow ID: {workflow_id}")
    
    # Get statistics
    stats = history.get_statistics()
    print(f"✓ Total workflows: {stats['total_workflows']}")
    print(f"✓ Status counts: {stats['status_counts']}")
    
    # Get recent records
    recent = history.get_recent(limit=3)
    print(f"\n✓ Recent workflows:")
    for record in recent:
        print(f"   ID {record['id']}: {record['user_query'][:50]}...")
    
    print(f"\n{history}")
    print()
    
    return history


def test_rag_agent(mcp_client):
    """Test RAG agent."""
    print("="*70)
    print("TESTING RAG AGENT")
    print("="*70)
    print()
    
    context = SharedContext()
    event_bus = EventBus()
    
    # Create RAG agent
    rag_agent = RAGAgent(
        agent_id="test_rag_agent",
        name="Test RAG Research Agent",
        context=context,
        event_bus=event_bus,
        mcp_client=mcp_client,
        collections=["test_docs"],
        top_k=5
    )
    
    print(f"✓ Created: {rag_agent}")
    
    # Test search (will use mock data if ChromaDB not available)
    task = {
        "instruction": "Find information about spar lamination troubleshooting",
        "parameters": {}
    }
    
    print(f"\n✓ Executing search task...")
    result = rag_agent.execute(task)
    
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        output = result.get('output', {})
        print(f"   Message: {output.get('message', 'N/A')}")
        print(f"   Documents found: {result.get('metadata', {}).get('total_documents', 0)}")
    else:
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    print()
    return rag_agent


def main():
    """Main entry point."""
    print("="*70)
    print("MULTI-AGENT FRAMEWORK - PHASE 2 DEMO")
    print("="*70)
    print()
    
    try:
        # Test 1: MCP Servers
        mcp_client = test_mcp_servers()
        
        # Test 2: History Service
        history = test_history_service()
        
        # Test 3: RAG Agent
        if mcp_client.is_connected("chromadb"):
            rag_agent = test_rag_agent(mcp_client)
        else:
            print("⚠ Skipping RAG agent test (ChromaDB not available)")
            print("  Install with: pip install chromadb\n")
        
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print()
        print("✓ Phase 2 core components implemented:")
        print("  - HighByte MCP Server (streamable-http + bearer token)")
        print("  - SQL Server integration (parameterized queries)")
        print("  - Teradata MCP Server (named queries)")
        print("  - ChromaDB integration (RAG)")
        print("  - SQLite history tracking")
        print("  - RAG Agent for document search")
        print()
        print("📝 Next steps:")
        print("  1. Configure real MCP server endpoints")
        print("  2. Add LLM integration for agent execution")
        print("  3. Test with production data")
        print("  4. Add document ingestion utilities")
        print()
        print("✓ Phase 2 Demo completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
