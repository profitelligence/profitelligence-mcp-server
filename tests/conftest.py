"""
Pytest configuration and fixtures for Profitelligence MCP Server tests.

Fixtures are organized into categories:
- Environment setup (autouse)
- Authentication credentials (test_api_key, test_firebase_token, etc.)
- API client instances
- MCP context mocks
- Sample API responses
- HTTP mocking helpers
"""
import pytest
import httpx
import respx
from unittest.mock import MagicMock


# Set test environment variables before importing config
@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set up test environment variables."""
    # Clear any existing config
    import src.utils.config as config_module
    config_module.config = None

    # Set minimal required environment
    monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
    monkeypatch.setenv("PROF_API_KEY", "pk_test_abc123")
    monkeypatch.setenv("PROF_API_BASE_URL", "https://test-api.profitelligence.com")
    monkeypatch.setenv("PROF_MCP_MODE", "stdio")
    monkeypatch.setenv("PROF_LOG_LEVEL", "DEBUG")


@pytest.fixture
def test_api_key():
    """Return a valid test API key."""
    return "pk_test_abc123"


@pytest.fixture
def test_live_api_key():
    """Return a valid live API key."""
    return "pk_live_xyz789"


@pytest.fixture
def test_firebase_token():
    """Return a mock Firebase JWT token."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIifQ.signature"


@pytest.fixture
def test_oauth_token():
    """Return a mock OAuth Bearer token."""
    return "ya29.test-oauth-token-abc123"


@pytest.fixture
def base_url():
    """Return the test API base URL."""
    return "https://test-api.profitelligence.com"


@pytest.fixture
def api_client(test_api_key, base_url):
    """Create a configured API client for testing."""
    from src.utils.api_client import APIClient

    client = APIClient(
        api_key=test_api_key,
        auth_method="api_key",
        base_url=base_url
    )
    yield client
    client.close()


@pytest.fixture
def mock_config(test_api_key, base_url, monkeypatch):
    """Create a mock Config object."""
    from src.utils.config import Config, get_config
    import src.utils.config as config_module

    # Reset the global config
    config_module.config = None

    # Set environment
    monkeypatch.setenv("PROF_API_KEY", test_api_key)
    monkeypatch.setenv("PROF_API_BASE_URL", base_url)

    config = get_config()
    return config


# MCP Context fixtures - useful for testing tool execution with context
@pytest.fixture
def mock_mcp_context():
    """Create a mock FastMCP context for tool testing.

    Use this when testing tools that need a context object but don't
    need specific credentials in the context.
    """
    ctx = MagicMock()
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = {}
    return ctx


@pytest.fixture
def mock_mcp_context_with_api_key(test_api_key):
    """Create a mock FastMCP context with API key in headers.

    Use this when testing the full auth flow through MCP context.
    The API key is placed in the x-api-key header.
    """
    ctx = MagicMock()
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = {}

    # Mock the request headers
    request = MagicMock()
    request.headers = {"x-api-key": test_api_key}
    request.query_params = {}
    ctx.request_context.request = request

    return ctx


# Sample API response fixtures
@pytest.fixture
def pulse_response():
    """Sample response from /v1/mcp-pulse endpoint."""
    return {
        "market_status": "open",
        "movers": [
            {"symbol": "AAPL", "change_percent": 2.5, "volume": 100000000},
            {"symbol": "TSLA", "change_percent": -1.8, "volume": 80000000}
        ],
        "filings": [
            {"symbol": "NVDA", "form_type": "8-K", "summary": "Material event disclosure"}
        ],
        "insider_trades": [
            {"symbol": "META", "insider_name": "John Doe", "transaction_type": "Buy", "value": 500000}
        ],
        "indicators": {
            "sp500": 5200.0,
            "vix": 15.5
        }
    }


@pytest.fixture
def investigate_response():
    """Sample response from /v1/mcp-investigate endpoint."""
    return {
        "subject": "AAPL",
        "entity_type": "company",
        "profile": {
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 3000000000000
        },
        "price_history": [
            {"date": "2024-01-15", "close": 195.50}
        ],
        "filings": [
            {"form_type": "10-K", "filed_date": "2024-01-10"}
        ],
        "insider_summary": {
            "net_shares": 10000,
            "insider_sentiment": "bullish"
        }
    }


@pytest.fixture
def screen_response():
    """Sample response from /v1/mcp-screen endpoint."""
    return {
        "focus": "all",
        "results": [
            {
                "symbol": "NVDA",
                "score": 95.0,
                "signals": ["insider_buying", "multi_signal"]
            },
            {
                "symbol": "AMD",
                "score": 85.0,
                "signals": ["events"]
            }
        ],
        "total": 2
    }


@pytest.fixture
def assess_response():
    """Sample response from /v1/mcp-assess endpoint."""
    return {
        "symbol": "NVDA",
        "assessment": {
            "overall_score": 90,
            "risk_level": "medium",
            "recommendation": "hold"
        },
        "price_action": {
            "current": 950.0,
            "change_30d": 15.5
        },
        "insider_sentiment": "bullish",
        "institutional_sentiment": "accumulation"
    }


@pytest.fixture
def institutional_response():
    """Sample response from /v1/mcp-institutional endpoint."""
    return {
        "query_type": "manager",
        "identifier": "Citadel",
        "results": [
            {
                "name": "CITADEL ADVISORS LLC",
                "cik": "0001423053",
                "total_value": 500000000000,
                "top_holdings": [
                    {"symbol": "AAPL", "value": 10000000000},
                    {"symbol": "NVDA", "value": 8000000000}
                ]
            }
        ]
    }


@pytest.fixture
def search_response():
    """Sample response from /v1/search endpoint."""
    return {
        "query": "CEO resignation",
        "results": [
            {
                "entity_type": "filing",
                "entity_id": "12345",
                "symbol": "XYZ",
                "title": "XYZ Corp CEO Resignation",
                "rank": 0.95,
                "metadata": {"form_type": "8-K", "impact": "HIGH"}
            }
        ],
        "total": 1
    }


@pytest.fixture
def service_info_response():
    """Sample response from service info endpoint."""
    return {
        "service": "profitelligence",
        "version": "1.0.0",
        "user": {
            "email": "test@example.com",
            "plan": "pro"
        },
        "limits": {
            "requests_per_day": 10000,
            "requests_remaining": 9500
        }
    }


# HTTP mocking helper
@pytest.fixture
def mock_api(base_url):
    """Create a respx mock router for API calls."""
    with respx.mock(base_url=base_url, assert_all_called=False) as respx_mock:
        yield respx_mock


@pytest.fixture
def mock_pulse_api(mock_api, pulse_response):
    """Mock the pulse endpoint."""
    mock_api.get("/v1/mcp-pulse").mock(return_value=httpx.Response(200, json=pulse_response))
    return mock_api


@pytest.fixture
def mock_investigate_api(mock_api, investigate_response):
    """Mock the investigate endpoint."""
    mock_api.get("/v1/mcp-investigate").mock(return_value=httpx.Response(200, json=investigate_response))
    return mock_api


@pytest.fixture
def mock_screen_api(mock_api, screen_response):
    """Mock the screen endpoint."""
    mock_api.get("/v1/mcp-screen").mock(return_value=httpx.Response(200, json=screen_response))
    return mock_api


@pytest.fixture
def mock_assess_api(mock_api, assess_response):
    """Mock the assess endpoint."""
    mock_api.get("/v1/mcp-assess").mock(return_value=httpx.Response(200, json=assess_response))
    return mock_api


@pytest.fixture
def mock_institutional_api(mock_api, institutional_response):
    """Mock the institutional endpoint."""
    mock_api.get("/v1/mcp-institutional").mock(return_value=httpx.Response(200, json=institutional_response))
    return mock_api


@pytest.fixture
def mock_search_api(mock_api, search_response):
    """Mock the search endpoint."""
    mock_api.get("/v1/search").mock(return_value=httpx.Response(200, json=search_response))
    return mock_api
