# Multi-Agent Manufacturing Framework

An intelligent multi-agent system for manufacturing operations, powered by LLMs and designed for non-technical users.

## Overview

This framework enables natural language interaction with manufacturing equipment through a web-based chat interface. Each machine gets its own AI assistant with access to documentation, databases, and real-time data.

## Key Features

- 🤖 **Multi-Agent Architecture** - Specialized agents for data fetching, analysis, and summarization
- 🌐 **Web Interface** - Simple chat UI for non-technical users
- 📚 **RAG Documentation Search** - Agents search machine-specific documentation  
- 🔧 **Flexible Tool Access** - Each machine configured with its own data sources
- 🔐 **Machine Isolation** - Complete separation between machine configurations
- 🚀 **Easy Deployment** - One-command Docker setup

## Quick Start

### 1. Web Interface (Recommended)

The easiest way to use the system:

```bash
# Start backend
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** and start chatting!

### 2. Add Documentation for Your Machine

```bash
# Add your machine's documentation
mkdir -p docs/my_machine
# Add .txt, .md, or .json files to docs/my_machine/

# Ingest into RAG
python tools/setup_rag_collection.py \
  --machine my_machine \
  --docs ./docs/my_machine/
```

### 3. Configure Your Machine

Create `backend/configs/my_machine.yaml`:

```yaml
llm_providers:
  openai_standard:
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4o-mini"

agents:
  - agent_id: "my_machine_assistant"
    name: "My Machine Assistant"
    machine_id: "my_machine"
    function: "data_fetching"
    capabilities:
      - "search_documentation"
    mcp_tools:
      - server: "chromadb"
        tools: ["search_docs"]

mcp_servers:
  chromadb:
    collection_name: "my_machine_docs"
    persist_directory: "./chromadb_data"
```

Reload the web interface - your machine now appears in the dropdown!

## Project Structure

```
Multi-Agent-Framework/
├── backend/              # FastAPI server
│   ├── app/             # API endpoints
│   └── configs/         # Machine configurations
├── frontend/            # React web interface
├── multi_agent_framework/  # Core framework
│   ├── agents/          # Agent implementations
│   ├── core/            # Coordinator, context, LLM providers
│   └── config/          # Configuration schemas
├── tools/               # Utilities
│   └── rag_ingestion/   # Document ingestion for RAG
├── docs/                # Example documentation
└── documentation/       # Setup guides
```

## Documentation

| Guide | Description |
|-------|-------------|
| [LLM Setup Guide](documentation/LLM_SETUP_GUIDE.md) | Configure OpenAI/Gov.cloud LLMs |
| [RAG Ingestion Guide](documentation/RAG_INGESTION_GUIDE.md) | Add documentation to machines |
| [Usage Breakdown](documentation/Usage-Breakdown.md) | How configurations work |
| [Phase 2 Guide](documentation/PHASE2_GUIDE.md) | Advanced features |

## Use Cases

### Equipment Engineer
"What's the current status of the spar lamination machine?"

### Quality Control
"Any errors in the last hour on Robot A?"

### Maintenance
"Show me the troubleshooting procedure for error code E01"

### Production Manager
"What's the efficiency of the conveyor belt today?"

## Architecture

```
User → Web Interface → Backend API → Multi-Agent Framework
                                           ↓
                              ┌────────────┴────────────┐
                              ↓                         ↓
                        LLM Provider              MCP Tools
                         (OpenAI)          (SQL, HighByte, ChromaDB)
```

## Requirements

- Python 3.13+
- Node.js 18+ (for web interface)
- OpenAI API key (or compatible endpoint)
- Optional: SQL Server, HighByte, Teradata for production data

## Installation

```bash
# Clone repository
git clone <repo-url>
cd Multi-Agent-Framework

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install framework
pip install -e .
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

Each machine gets its own YAML configuration defining:
- Which LLM to use
- Which agents are available
- Which tools/data sources each agent can access
- Custom instructions per agent

**Complete isolation** - Machine 1 can't access Machine 2's tools or data.

## Deployment

### Docker (Production)

```bash
docker-compose up --build
```

Visit **http://localhost:3000**

### Manual (Development)

See [Quick Start](#quick-start) above.

## Adding New Machines

1. **Add documentation**: Place files in `docs/machine_name/`
2. **Ingest to RAG**: `python tools/setup_rag_collection.py --machine machine_name --docs ./docs/machine_name/`
3. **Create config**: Add `backend/configs/machine_name.yaml`
4. **Refresh**: Machine appears in web interface automatically!

No code changes needed - just configuration!

## Key Technologies

- **Backend**: FastAPI, Python 3.13
- **Frontend**: React, Vite
- **LLM**: OpenAI API (GPT-4, GPT-4o-mini)
- **RAG**: ChromaDB with semantic chunking
- **MCP**: Model Context Protocol for tool integration

## Development

```bash
# Auto-formatting
black multi_agent_framework/

# Type checking
mypy multi_agent_framework/

# Run tests
pytest
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines]

## Support

For issues or questions, please open a GitHub issue.

---

**Built for manufacturing teams who need intelligent, conversational access to their equipment data.**
