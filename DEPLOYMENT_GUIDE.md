# Deployment Guide for Non-Technical Users

## Overview

This guide outlines different deployment strategies to make the Multi-Agent Framework accessible to non-technical users across your company. The goal is to let users simply select a machine and ask questions without needing to understand YAML configs or command-line tools.

## Recommended Approach: Web-Based Chat Interface

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│  (Web Browser - Simple Chat + Machine Selector)     │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend Server                  │
│  - Manages configurations for all machines          │
│  - Handles chat requests                             │
│  - Routes to appropriate agent deployment            │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│         Multi-Agent Framework (Core)                 │
│  - Loads config based on machine selection          │
│  - Executes workflow                                 │
│  - Returns results                                   │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              MCP Servers + LLM                       │
│  - HighByte, SQL, Teradata, ChromaDB               │
│  - OpenAI / Gov.Cloud LLM                           │
└─────────────────────────────────────────────────────┘
```

### User Experience

```
┌──────────────────────────────────────────────┐
│     Manufacturing AI Assistant                │
├──────────────────────────────────────────────┤
│                                               │
│  Select Machine:  [Spar Lamination ▼]       │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │ You: What's the current status?         │ │
│  │                                          │ │
│  │ AI: The Spar Lamination machine is      │ │
│  │     running at 95% efficiency...        │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  [Type your question...]          [Send →]   │
└──────────────────────────────────────────────┘
```

## Implementation Options

### Option 1: Simple Web Interface (Recommended)

**Best for**: Company-wide deployment, non-technical users

**Components**:
1. **Frontend**: React/Vue simple chat interface
2. **Backend**: FastAPI server
3. **Config Management**: Pre-built configs for all machines
4. **Authentication**: SSO integration (Active Directory/Okta)

**User Flow**:
1. User logs in (SSO)
2. Dropdown shows machines they have access to
3. User selects machine
4. User types question in chat
5. AI responds with answer

**Pros**:
- ✅ Most user-friendly
- ✅ Works on any device with browser
- ✅ Can add permissions/access control
- ✅ Chat history stored
- ✅ No installation needed for users

**Cons**:
- ⚠️ Requires web hosting
- ⚠️ More initial setup work

---

### Option 2: Interactive CLI Tool

**Best for**: Power users, IT staff, testing

**User Flow**:
```bash
$ manufacturing-ai

Welcome to Manufacturing AI Assistant!

Select a machine site:
  1. Spar Lamination Machine
  2. Robot A
  3. Conveyor Belt System
  4. Quality Control Station

Enter number (1-4): 1

✓ Connected to: Spar Lamination Machine

Ask a question (or 'quit' to exit):
> What's the current status?

AI: The Spar Lamination machine is currently running...

Ask a question (or 'quit' to exit):
> _
```

**Pros**:
- ✅ Quick to implement
- ✅ No web hosting needed
- ✅ Good for power users

**Cons**:
- ⚠️ Still requires command line access
- ⚠️ Less accessible to non-technical users

---

### Option 3: Slack/Teams Bot

**Best for**: Companies already using Slack/Teams

**User Flow**:
```
User: @ManufacturingAI /machine spar-lamination
Bot: ✓ Now talking about Spar Lamination Machine

User: What's the current status?
Bot: The Spar Lamination machine is running at 95%...

User: Any errors in the last hour?
Bot: No critical errors detected...
```

**Pros**:
- ✅ Users already familiar with interface
- ✅ Natural conversation flow
- ✅ Easy notifications/alerts
- ✅ Mobile-friendly

**Cons**:
- ⚠️ Requires Slack/Teams app development
- ⚠️ Company must use Slack/Teams

---

### Option 4: Configuration Generator Tool

**Best for**: Semi-technical users who manage their own machines

**User Flow**:
```bash
$ create-machine-config

Machine Configuration Generator
================================

1. What is the machine name?
   > Spar Lamination Machine

2. What data sources does it use?
   [ ] HighByte
   [x] SQL Server
   [ ] Teradata
   > Select sources (space to toggle, enter to continue)

3. What is the SQL connection string?
   > mssql://localhost/SparLamDB

4. Select capabilities:
   [x] Fetch current status
   [x] Analyze performance
   [x] Generate reports
   > Select capabilities

✓ Configuration saved: spar_lamination_config.yaml
✓ Ready to use!

Run with: python demo.py --config spar_lamination_config.yaml
```

**Pros**:
- ✅ Self-service for technical users
- ✅ Reduces admin burden
- ✅ Standardized configs

**Cons**:
- ⚠️ Still requires some technical knowledge
- ⚠️ Not suitable for all users

---

## Detailed Implementation: Web Interface (Recommended)

### Step 1: Backend API (FastAPI)

Create a REST API that manages configurations and chat:

```python
# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import yaml
from pathlib import Path

app = FastAPI()

class ChatRequest(BaseModel):
    machine_id: str
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    agent_count: int
    execution_time: float

# Load all machine configurations on startup
MACHINE_CONFIGS = {}

@app.on_event("startup")
def load_configs():
    config_dir = Path("configs")
    for config_file in config_dir.glob("*.yaml"):
        machine_id = config_file.stem
        MACHINE_CONFIGS[machine_id] = config_file

@app.get("/api/machines")
def list_machines(user_id: str):
    """Get list of machines user has access to"""
    # TODO: Add permission checking based on user_id
    return {
        "machines": [
            {"id": "spar_lamination", "name": "Spar Lamination Machine"},
            {"id": "robot_a", "name": "Robot A"},
            {"id": "conveyor", "name": "Conveyor Belt System"}
        ]
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Handle chat request for specific machine"""
    
    # Get config for machine
    if request.machine_id not in MACHINE_CONFIGS:
        raise HTTPException(404, "Machine not found")
    
    config_path = MACHINE_CONFIGS[request.machine_id]
    
    # Load framework and execute
    from multi_agent_framework.core import SharedContext, EventBus, Coordinator
    from multi_agent_framework.config import load_config
    # ... (initialization code)
    
    # Execute workflow
    result = coordinator.execute_workflow(request.message)
    
    return ChatResponse(
        response=result["final_output"],
        agent_count=len(result["results"]),
        execution_time=result.get("execution_time", 0)
    )
```

### Step 2: Frontend (React)

Simple chat interface:

```typescript
// frontend/src/App.tsx
import React, { useState } from 'react';

function App() {
  const [selectedMachine, setSelectedMachine] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  
  const machines = [
    { id: 'spar_lamination', name: 'Spar Lamination Machine' },
    { id: 'robot_a', name: 'Robot A' },
    { id: 'conveyor', name: 'Conveyor Belt System' }
  ];
  
  const sendMessage = async () => {
    // Add user message
    setMessages([...messages, { role: 'user', content: input }]);
    
    // Call API
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        machine_id: selectedMachine,
        message: input,
        user_id: 'current_user'
      })
    });
    
    const data = await response.json();
    
    // Add AI response
    setMessages([...messages, 
      { role: 'user', content: input },
      { role: 'assistant', content: data.response }
    ]);
    
    setInput('');
  };
  
  return (
    <div className="chat-container">
      <h1>Manufacturing AI Assistant</h1>
      
      <select 
        value={selectedMachine}
        onChange={(e) => setSelectedMachine(e.target.value)}
      >
        <option value="">Select Machine...</option>
        {machines.map(m => (
          <option key={m.id} value={m.id}>{m.name}</option>
        ))}
      </select>
      
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            {msg.content}
          </div>
        ))}
      </div>
      
      <input 
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        placeholder="Ask a question..."
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}
```

### Step 3: Configuration Management

**Central config directory structure**:

```
configs/
├── spar_lamination.yaml
├── robot_a.yaml
├── conveyor.yaml
├── quality_station.yaml
└── permissions.yaml        # Who can access what
```

**Permissions file**:

```yaml
# configs/permissions.yaml
user_groups:
  equipment_engineers:
    users:
      - john.doe@company.com
      - jane.smith@company.com
    machines:
      - spar_lamination
      - robot_a
      - conveyor
  
  quality_engineers:
    users:
      - bob.quality@company.com
    machines:
      - quality_station
      - spar_lamination  # View-only for quality metrics
  
  managers:
    users:
      - manager@company.com
    machines:
      - "*"  # Access to all
```

### Step 4: Deployment

**Docker Compose** for easy deployment:

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOVCLOUD_API_KEY=${GOVCLOUD_API_KEY}
    volumes:
      - ./configs:/app/configs
    depends_on:
      - redis
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

**One-command deployment**:

```bash
# On server
docker-compose up -d

# Users just visit: https://manufacturing-ai.company.com
```

## Setup Process for Admins

### Initial Setup (One-time)

1. **Clone repository** on deployment server
2. **Set up environment variables** (API keys, database connections)
3. **Create machine configurations** (one YAML per machine)
4. **Configure permissions** (who can access what)
5. **Deploy with Docker Compose**
6. **Set up SSL certificate** (https)
7. **Configure SSO** (Active Directory/Okta)

### Adding New Machine (Per Machine)

1. Create new YAML config: `configs/new_machine.yaml`
2. Define tools and data sources
3. Add to permissions file
4. Restart service: `docker-compose restart backend`

**That's it!** No code changes needed.

## User Training (5 minutes)

For end users:

1. **Go to website**: manufacturing-ai.company.com
2. **Login** with company credentials
3. **Select machine** from dropdown
4. **Type question** in chat box
5. **Get answer** from AI

**Training materials needed**:
- 1-page quick start guide
- 2-minute demo video
- Example questions for each machine

## Cost Considerations

### Monthly Operating Costs

| Component | Estimated Cost |
|-----------|----------------|
| Server hosting (AWS/Azure) | $50-200/month |
| LLM API calls (OpenAI) | $100-500/month |
| Database hosting | $50-100/month |
| **Total** | **$200-800/month** |

**Cost scales with usage** - more queries = higher LLM costs.

## Security & Access Control

1. **Authentication**: SSO integration (Active Directory, Okta)
2. **Authorization**: Permission-based machine access
3. **Audit Logging**: Track all queries and who asked them
4. **Rate Limiting**: Prevent abuse
5. **Data Encryption**: HTTPS, encrypted API keys

## Monitoring & Maintenance

### What to Monitor

1. **API response times** - Should be < 5 seconds
2. **Error rates** - Track failed queries
3. **LLM costs** - Monitor token usage
4. **User activity** - Which machines are used most
5. **MCP server health** - Are data sources available?

### Maintenance Schedule

- **Daily**: Check error logs
- **Weekly**: Review usage metrics
- **Monthly**: Update configurations based on feedback
- **Quarterly**: Review and optimize costs

## Migration Path

### Phase 1: Pilot (Week 1-2)
- Deploy for 1-2 machines
- Limited user group (5-10 people)
- Gather feedback

### Phase 2: Department Rollout (Week 3-4)
- Add 5-10 more machines
- Expand to one department
- Refine based on usage patterns

### Phase 3: Company-wide (Week 5+)
- All machines configured
- All users have access
- Full documentation and training

## Comparison Matrix

| Approach | Ease of Use | Setup Effort | Maintenance | Best For |
|----------|-------------|--------------|-------------|----------|
| **Web Interface** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Non-technical users |
| **Interactive CLI** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Power users |
| **Slack/Teams Bot** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Slack/Teams shops |
| **Config Generator** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Semi-technical admins |

## Recommendation

**For company-wide deployment to non-technical users**: 

👉 **Option 1: Web Interface** is the clear winner.

**Why**:
1. ✅ Lowest barrier to entry for users
2. ✅ Familiar interface (just like ChatGPT)
3. ✅ Works on all devices (desktop, tablet, mobile)
4. ✅ Easy to add features (chat history, favorites, etc.)
5. ✅ Best access control and auditing
6. ✅ Professional appearance

**Quick Start Path**:
1. Start with simple FastAPI backend + React frontend
2. Pre-configure 2-3 machines
3. Pilot with small user group
4. Iterate based on feedback
5. Scale to more machines and users

The key is: **Users never see YAML files or command lines**. They just select a machine and ask questions.
