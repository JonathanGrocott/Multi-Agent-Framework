# Backend README

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt

# Also install the core framework in development mode
cd ..
pip install -e .
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Add Machine Configurations

Place machine config YAML files in `configs/`:

```bash
configs/
├── test_machine.yaml      # Included - simple test config
├── spar_lamination.yaml   # Add your real configs here
└── robot_a.yaml
```

### 4. Run Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Or use the run script
python -m uvicorn app.main:app --reload
```

### 5. Test API

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

#### Test Endpoints:

```bash
# Get list of machines
curl http://localhost:8000/api/machines

# Send a chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "test_machine",
    "message": "What is the current status?"
  }'
```

## API Endpoints

### Machines

- `GET /api/machines` - List all configured machines
- `GET /api/machines/{id}` - Get specific machine info
- `POST /api/machines/reload` - Reload configurations from disk

### Chat

- `POST /api/chat` - Send a question to a machine
- `POST /api/chat/clear-cache` - Clear cached coordinators

### System

- `GET /` - API status and version
- `GET /health` - Health check

## Adding New Machines

1. Create a YAML config file in `configs/`
2. Name it with the machine ID (e.g., `my_machine.yaml`)
3. Reload configs: `POST /api/machines/reload`
4. Machine is immediately available!

No code changes or server restart needed.

## Directory Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/                 # API endpoints
│   │   ├── machines.py
│   │   └── chat.py
│   ├── core/                # Business logic
│   │
   ├── config_manager.py
│   │   └── framework_executor.py
│   └── models/              # Pydantic models
│       ├── chat.py
│       └── machine.py
├── configs/                 # Machine YAML configs
│   └── test_machine.yaml
├── requirements.txt
└── .env.example
```

## Development

### Enable Debug Logging

In `.env`:
```
LOG_LEVEL=DEBUG
```

### Hot Reload Configs

Call the reload endpoint:
```bash
curl -X POST http://localhost:8000/api/machines/reload
```

### Clear Coordinator Cache

When testing config changes:
```bash
curl -X POST http://localhost:8000/api/chat/clear-cache
```

## Troubleshooting

### "Module not found" errors

Make sure you installed the core framework:
```bash
cd ..  # Go to Multi-Agent-Framework root
pip install -e .
```

### No machines showing up

Check that configs exist in `backend/configs/` and are valid YAML.

### LLM errors

Verify your API keys are set in `.env` file.
