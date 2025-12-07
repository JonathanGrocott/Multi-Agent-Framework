# Quick Start Guide: LLM Setup

## Overview

The Multi-Agent Framework now supports flexible LLM integration with OpenAI-compatible providers, including standard OpenAI API and custom gov.cloud endpoints.

## Quick Setup

### 1. Install Dependencies

```bash
cd /Users/jg/Documents/github/Multi-Agent-Framework
pip install -r requirements.txt
```

This will install:
- `openai>=1.0.0` - OpenAI SDK (works with custom endpoints)
- `python-dotenv>=1.0.0` - Environment variable management
- `tiktoken>=0.5.0` - Token counting

### 2. Configure Environment Variables

Copy the example file and add your API keys:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

**For Standard OpenAI:**
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**For Gov.Cloud Custom Endpoint:**
```bash
GOVCLOUD_API_KEY=your-govcloud-token
GOVCLOUD_BASE_URL=https://your-govcloud-endpoint.gov/v1
```

### 3. Choose Configuration

Use one of the example configurations:

**Standard OpenAI:**
```bash
cd multi_agent_framework/examples
python demo.py --config llm_config_openai.yaml
```

**Gov.Cloud Custom Endpoint:**
```bash
python demo.py --config llm_config_govcloud.yaml
```

## Configuration Examples

### Standard OpenAI

```yaml
llm_providers:
  openai_standard:
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4o-mini"
    timeout: 60
    max_retries: 3

default_llm_provider: "openai_standard"

agents:
  - agent_id: "data_fetcher"
    # ... agent config ...
    model: "gpt-4o-mini"  # Uses default provider
```

### Gov.Cloud Custom Endpoint

```yaml
llm_providers:
  govcloud_openai:
    type: "openai"
    api_key: "${GOVCLOUD_API_KEY}"
    base_url: "${GOVCLOUD_BASE_URL}"
    default_model: "4o-mini"
    timeout: 90
    max_retries: 2

default_llm_provider: "govcloud_openai"

agents:
  - agent_id: "data_fetcher"
    # ... agent config ...
    model: "4o-mini"  # Gov.cloud model name
    
  - agent_id: "analyzer"
    # ... agent config ...
    model: "5o-mini"  # Different gov.cloud model
```

### Multiple Providers

You can configure multiple providers and switch between them:

```yaml
llm_providers:
  openai_standard:
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4o-mini"
  
  govcloud_openai:
    type: "openai"
    api_key: "${GOVCLOUD_API_KEY}"
    base_url: "${GOVCLOUD_BASE_URL}"
    default_model: "4o-mini"

default_llm_provider: "openai_standard"

# Agents can specify which provider to use via model syntax
agents:
  - agent_id: "agent1"
    model: "gpt-4o-mini"  # Uses default provider (openai_standard)
  
  - agent_id: "agent2"
    model: "4o-mini"  # Uses govcloud if model name matches
```

## Model Support

### OpenAI Standard Models
- `gpt-4` - Most capable, higher cost
- `gpt-4o-mini` - Balanced performance and cost
- `o1-mini` - Fast, efficient
- `gpt-3.5-turbo` - Fastest, lowest cost

### Gov.Cloud Models
- `4o-mini` - Equivalent to gpt-4o-mini
- `5o-mini` - Enhanced model
- Custom model names as provided by your endpoint

## Troubleshooting

### API Key Not Found

**Error:** `Environment variable 'OPENAI_API_KEY' not found`

**Solution:** 
1. Ensure `.env` file exists in project root
2. Verify the variable name matches exactly
3. No quotes needed in `.env` file: `OPENAI_API_KEY=sk-...`

### Custom Endpoint Connection Failed

**Error:** `OpenAI API call failed`

**Solution:**
1. Verify `GOVCLOUD_BASE_URL` is correct and ends with `/v1`
2. Check bearer token has proper permissions
3. Test endpoint directly with curl first
4. Verify gov.cloud endpoint follows OpenAI API format

### No LLM Provider Configured

**Warning:** `Agents will run without LLM capabilities (mock mode)`

This is expected if:
- `.env` file is missing
- LLM provider configuration is empty
- API keys are invalid

Agents will still run but return mock responses instead of real LLM outputs.

## Testing Your Setup

### Test with OpenAI

```bash
# Set your API key
export OPENAI_API_KEY="sk-your-key"

# Run demo
cd multi_agent_framework/examples
python demo.py --config llm_config_openai.yaml
```

### Test with Gov.Cloud

```bash
# Set your credentials
export GOVCLOUD_API_KEY="your-token"
export GOVCLOUD_BASE_URL="https://your-endpoint.gov/v1"

# Run demo
python demo.py --config llm_config_govcloud.yaml
```

## Advanced Configuration

### Custom Timeout and Retries

```yaml
llm_providers:
  my_provider:
    type: "openai"
    api_key: "${API_KEY}"
    timeout: 120  # Longer timeout for complex queries
    max_retries: 5  # More retries for unstable connections
```

### Organization ID

```yaml
llm_providers:
  openai_org:
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    organization: "${OPENAI_ORG_ID}"  # Optional org ID
```

## Next Steps

1. **Add Your Data Sources**: Configure MCP servers (HighByte, SQL, Teradata, ChromaDB)
2. **Customize Agents**: Modify agent configurations for your specific machines
3. **Add RAG**: Set up ChromaDB with your technical documentation
4. **Production Deployment**: Review security best practices for API key management
