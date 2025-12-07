# Web Interface Guide

## Overview

This web interface provides a simple chat-based UI for non-technical users to interact with multi-agent manufacturing assistants.

## Architecture

```
┌─────────────┐                  ┌──────────────┐
│  Frontend   │  HTTP/JSON      │   Backend    │
│  (React)    │ ───────────────▶│  (FastAPI)   │
│  Port 3000  │                  │  Port 8000   │
└─────────────┘                  └──────┬───────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  Multi-Agent     │
                              │  Framework       │
                              └──────────────────┘
```

## Quick Start

### Option 1: Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cd ..
pip install -e .  # Install framework
cd backend
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

### Option 2: Docker (Easiest)

```bash
# From project root
docker-compose up --build
```

Visit: http://localhost:3000

## Adding New Machines

1. Create a YAML config file in `backend/configs/`:

```bash
# Example: backend/configs/my_machine.yaml
llm_providers:
  openai_standard:
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4o-mini"

default_llm_provider: "openai_standard"

agents:
  - agent_id: "my_machine_fetcher"
    name: "My Machine Data Fetcher"
    machine_id: "my_machine"
    function: "data_fetching"
    capabilities:
      - "fetch_status"
    mcp_tools: []
    model: "gpt-4o-mini"
```

2. Reload configs (if server is running):
```bash
curl -X POST http://localhost:8000/api/machines/reload
```

3. Machine immediately appears in dropdown!

## User Experience

### For End Users

1. Open browser to web interface URL
2. Select machine from dropdown
3. Type question in plain English
4. Get AI-powered response
5. Continue conversation

### For Administrators

**Adding Machines:**
- Create YAML file in `configs/`
- No code changes needed
- Hot-reload supported

**Monitoring:**
- Check logs: `docker-compose logs -f backend`
- API docs: http://localhost:8000/docs

**Updating:**
```bash
git pull
docker-compose down
docker-compose up --build
```

## API Endpoints

### GET /api/machines
List all configured machines

**Response:**
```json
{
  "machines": [
    {
      "id": "test_machine",
      "name": "Test Machine",
      "description": "Multi-agent assistant for Test Machine",
      "capabilities": ["fetch_current_status", "retrieve_sensor_data"],
      "agent_count": 3
    }
  ],
  "total": 1
}
```

### POST /api/chat
Send a message to a machine

**Request:**
```json
{
  "machine_id": "test_machine",
  "message": "What is the current status?",
  "user_id": "web-user"
}
```

**Response:**
```json
{
  "response": "The test machine is currently running at 95% efficiency...",
  "agent_count": 3,
  "execution_time_ms": 2453.2,
  "machine_id": "test_machine",
  "timestamp": "2025-12-06T16:00:00Z"
}
```

## Deployment for Production

### Security Checklist

Before production deployment:

- [ ] Add authentication (SSO/OAuth)
- [ ] Update CORS settings to specific origins
- [ ] Use HTTPS (SSL certificate)
- [ ] Set up rate limiting
- [ ] Configure logging and monitoring
- [ ] Set up backup for conversation history
- [ ] Review and restrict API keys

### Recommended Stack

**Hosting:**
- AWS/Azure/GCP cloud hosting
- Docker containers
- Load balancer for scaling

**Security:**
- Azure AD or Okta for SSO
- API Gateway for rate limiting
- CloudFlare for DDoS protection

**Monitoring:**
- Prometheus + Grafana for metrics
- ELK stack for log aggregation
- Sentry for error tracking

## Troubleshooting

### Backend won't start

Check that:
- Python 3.13 is installed
- All deps installed: `pip install -r requirements.txt`
- Framework installed: `pip install -e .`
- `.env` file exists with API keys

### Frontend can't connect

Check that:
- Backend is running on port 8000
- CORS is enabled in backend
- API_BASE in `frontend/src/api.js` is correct

### No machines showing up

Check that:
- Config files exist in `backend/configs/`
- YAML files are valid
- Reload endpoint called if configs added while running

### LLM errors

Check that:
- API keys are set in `.env`
- API keys are valid and have credit
- Internet connection is working

## Future Enhancements

**Planned Features:**
- [ ] SSO/OAuth authentication
- [ ] User permissions per machine
- [ ] Conversation history storage
- [ ] Export conversations
- [ ] Admin dashboard
- [ ] Usage analytics
- [ ] Multi-language support
- [ ] Voice input option
