# Phase 2 Implementation Guide

## Overview

Phase 2 adds production-ready integrations to the multi-agent framework:
- **Real MCP Servers**: HighByte, Teradata, SQL Server
- **RAG Integration**: ChromaDB for document search
- **History Tracking**: SQLite for workflow logging

## MCP Server Integrations

### 1. HighByte (Streamable HTTP)

**Endpoint**: `http://localhost:4567/mcp` (or VM)
**Authentication**: Bearer token in header

```yaml
highbyte:
  type: "highbyte"
  transport: "streamable-http"
  endpoint: "http://localhost:4567/mcp"
  auth:
    type: "bearer"
    token: "your-token"
```

**Tools**: Pre-defined by HighByte MCP server (machine status, process data, metrics)

### 2. Teradata

**Repository**: https://github.com/Teradata/teradata-mcp-server

```yaml
teradata:
  type: "teradata"
  connection_string: "teradata://host/database"
  tools:
    - name: "teradata_spar_lamination_get_stats"
    - name: "teradata_quality_metrics"
```

**Tools**: Pre-defined named queries (read-only)

### 3. SQL Server

**Support**: Local SQL Express + Network SQL Servers

```yaml
sql_local:
  type: "sql"
  connection_string: "mssql://localhost/ManufacturingDB"
  tools:
    - name: "query_spar_lam_logs"
      query: "SELECT TOP 100 * FROM spar_logs WHERE timestamp > @start_time"
```

**Tools**: Pre-defined queries with parameters

## RAG Integration

### Dedicated Research Agent

**Function**: First agent in workflow, searches documentation

**Workflow**: `RAG Agent → Data Fetcher → Analyzer → Summarizer`

### ChromaDB Setup

```yaml
rag_config:
  chromadb:
    persist_directory: "./chroma_data"
    collections:
      - name: "spar_lamination_docs"
      - name: "troubleshooting_guides"
      - name: "user_notes"
```

**Usage**: Users add technical docs, troubleshooting guides, personal notes

## History Tracking

### SQLite Schema

```sql
CREATE TABLE workflow_history (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    user_query TEXT,
    final_result TEXT,
    metadata JSON,
    execution_time_ms INTEGER
);
```

**Storage**:
- Query
- Final result
- Timestamp & metadata
- No per-agent details (those go to debug logs)

**Configuration**:
```yaml
history:
  enabled: true
  database_path: "./workflow_history.db"
  retention_days: 90
```

## Example Configuration

See: [phase2_config.yaml](file:///Users/jg/Documents/github/Multi-Agent-Framework/multi_agent_framework/examples/phase2_config.yaml)

Complete example with:
- 4 agents (RAG + data + analysis + summary)
- All MCP servers configured
- RAG collections defined
- History tracking enabled

## Implementation Steps

See [task.md](file:///Users/jg/.gemini/antigravity/brain/29813c1e-89d6-415a-989b-6cb18b3a5ad5/task.md) for detailed checklist.

**Priority Order**:
1. HighByte integration (streamable-http + bearer auth)
2. SQL Server integration (local + network)
3. RAG agent (ChromaDB)
4. Teradata integration
5. SQLite history tracking

## Testing Strategy

For each integration:
1. Test connection and authentication
2. Verify tool discovery
3. Test tool invocation with real data
4. Validate error handling
5. Integration test with full workflow
