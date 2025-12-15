# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Profitelligence MCP Server is a FastMCP-based server that provides AI agents access to financial intelligence: insider trading data, SEC filings, economic indicators, and multi-signal analysis. It acts as a thin, stateless layer over Profitelligence's REST APIs.

## Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run the server (stdio mode for Claude Desktop)
PROF_API_KEY=pk_live_xxx python -m src.server

# Run in HTTP mode (for development/testing)
PROF_API_KEY=pk_live_xxx PROF_MCP_MODE=http python -m src.server

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Run a single test file
pytest tests/test_tools.py -v

# Linting and formatting
ruff check src/
ruff format --check src/
```

## Architecture

### Entry Point
- `src/server.py` - FastMCP server initialization, tool registration, OAuth middleware, and all HTTP endpoints

### Core Components

**Tools Layer** (`src/tools/mcp_tools.py`):
- 7 MCP tools that map 1:1 to `/v1/mcp-*` backend endpoints
- `pulse()`, `investigate()`, `screen()`, `assess()`, `institutional()`, `search()`, `service_info()`
- Each tool returns JSON-serialized dicts; tools are registered via `@mcp.tool()` decorator in server.py

**Utilities** (`src/utils/`):
- `config.py` - Pydantic-based configuration from environment variables (PROF_* prefix)
- `api_client.py` - HTTP client with support for three auth methods: api_key, oauth, firebase_jwt
- `auth.py` - Credential extraction from MCP context (headers, query params)
- `oauth.py`, `pkce.py`, `token_exchange.py` - OAuth 2.1 flow with Google → Firebase token exchange

### Authentication Flow

The server supports three authentication methods configured via `PROF_AUTH_METHOD`:

1. **api_key** (default) - Users provide `pk_live_*` or `pk_test_*` keys via X-API-Key header or apiKey query param
2. **oauth** - Full OAuth 2.1 flow: Google OAuth → Firebase ID token exchange → Backend API
3. **firebase_jwt** - Legacy direct Firebase token authentication

When `auth_method=oauth`:
- Server acts as OAuth authorization server (endpoints: `/authorize`, `/oauth/token`, `/oauth/callback`)
- Proxies to Google OAuth with PKCE
- Exchanges Google tokens for Firebase ID tokens
- Returns Firebase tokens as Bearer tokens to clients
- Backend API receives Firebase tokens for user identification

### Key Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PROF_API_KEY` | No* | API key (optional for multitenancy) |
| `PROF_AUTH_METHOD` | No | `api_key`, `oauth`, `both`, or `firebase_jwt` |
| `PROF_MCP_MODE` | No | `stdio` (default) or `http` |
| `PROF_MCP_PORT` | No | HTTP port (default: 3000) |
| `PROF_API_BASE_URL` | No | Backend API URL |

*Users typically provide API keys per-request in multitenancy mode

### MCP Prompts

Pre-built research workflows defined in `src/server.py`:
- `morning_briefing()` - Daily pre-market intelligence
- `company_intelligence_report(symbol)` - Deep company analysis
- `position_risk_check(symbol)` - Portfolio position health check
- `smart_money_report()` - Institutional flow analysis
- `sector_scan(sector)` - Sector opportunity screening
- `insider_deep_dive(identifier)` - Insider trading profile

## Code Patterns

### Adding a New Tool

1. Define implementation in `src/tools/mcp_tools.py`:
```python
def my_tool(param: str, ctx=None) -> dict:
    client = _get_client(ctx)
    return client.get("/v1/mcp-my-endpoint", params={"param": param})
```

2. Register with FastMCP decorator in `src/server.py`:
```python
@mcp.tool()
def my_tool(param: str, ctx: Context) -> str:
    """Docstring becomes the tool description for LLMs."""
    import json
    return json.dumps(mcp_tools.my_tool(param, ctx))
```

### API Client Pattern

Tools use `_get_client(ctx)` to get an authenticated httpx client. The client is created per-request based on credentials extracted from the MCP context.
