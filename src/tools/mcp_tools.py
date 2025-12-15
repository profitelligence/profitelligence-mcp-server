"""
MCP Tools - Clean, LLM-friendly tool definitions.

These map 1:1 to the /mcp-* backend endpoints.
Designed for minimal context bloat and clear parameter constraints.
"""

import logging
from typing import Literal, Optional
from ..utils.api_client import create_client_from_config
from ..utils.config import get_config

logger = logging.getLogger(__name__)


def _get_client(ctx=None):
    """Get configured API client."""
    config = get_config()
    return create_client_from_config(config, ctx)


def pulse(ctx=None) -> dict:
    """
    Market snapshot - what's happening right now.

    Returns market movers, recent material filings, notable insider trades,
    and key economic indicators. No parameters needed.

    Example: pulse()
    """
    client = _get_client(ctx)
    return client.get("/v1/mcp-pulse")


def investigate(
    subject: str,
    entity_type: Optional[Literal["company", "insider", "sector"]] = None,
    days: int = 30,
    ctx=None
) -> dict:
    """
    Deep research on any entity - company, insider, or sector.

    Auto-detects entity type from subject:
    - Stock symbols (AAPL, TSLA) → company research
    - CIK numbers (0001067983) → insider research
    - Sector names (Technology) → sector analysis

    For companies, returns:
    - Profile, price history, material events (8-K)
    - Insider intelligence (Form 4 summary + transactions)
    - Financials (10-K/10-Q): income statement, balance sheet, cash flow
    - Opportunity analysis, technical signals

    Args:
        subject: What to research (symbol, CIK, or sector name)
        entity_type: Force type if auto-detection fails ("company", "insider", "sector")
        days: Lookback period (default 30)

    Examples:
        investigate("AAPL")
        investigate("0001067983")  # Warren Buffett
        investigate("Technology", entity_type="sector")
    """
    client = _get_client(ctx)
    params = {"subject": subject, "days": days}
    if entity_type:
        params["type"] = entity_type
    return client.get("/v1/mcp-investigate", params=params)


def screen(
    focus: Literal["all", "multi_signal", "insider", "events"] = "all",
    sector: Optional[str] = None,
    min_score: Optional[float] = None,
    days: int = 7,
    limit: int = 25,
    ctx=None
) -> dict:
    """
    Scan market for opportunities across all stocks.

    Args:
        focus: What to scan for
            - "all": All opportunity types (default)
            - "multi_signal": Stocks with multiple confirming signals
            - "insider": Insider buying clusters and large transactions
            - "events": High-impact material events (8-K filings)
        sector: Filter by sector (e.g., "Technology", "Healthcare")
        min_score: Minimum opportunity score 0-100
        days: Lookback period (default 7)
        limit: Max results per category (default 25)

    Examples:
        screen()  # Everything
        screen(focus="insider", sector="Technology")
        screen(focus="events", days=14)
    """
    client = _get_client(ctx)
    params = {"focus": focus, "days": days, "limit": limit}
    if sector:
        params["sector"] = sector
    if min_score is not None:
        params["min_score"] = min_score
    return client.get("/v1/mcp-screen", params=params)


def assess(
    symbol: str,
    days: int = 30,
    ctx=None
) -> dict:
    """
    Position health check - evaluate an existing holding.

    Returns:
    - Company snapshot, price action
    - Material events (8-K filings)
    - Insider sentiment (Form 4 summary + recent trades)
    - Institutional sentiment (13F accumulation/distribution)
    - Financials (10-K/10-Q): income statement, balance sheet, cash flow
    - Technical indicators, opportunity signals

    Args:
        symbol: Stock symbol to assess
        days: Lookback period (default 30)

    Examples:
        assess("NVDA")
        assess("AAPL", days=90)
    """
    client = _get_client(ctx)
    params = {"symbol": symbol, "days": days}
    return client.get("/v1/mcp-assess", params=params)


def institutional(
    query_type: Literal["manager", "security", "signal"],
    identifier: Optional[str] = None,
    signal_type: Optional[Literal["accumulation", "distribution", "conviction", "new"]] = None,
    limit: int = 25,
    ctx=None
) -> dict:
    """
    Institutional investor intelligence from 13F filings.

    Query types:
    - "manager": Profile an institutional investor (by name or CIK)
    - "security": Institutional ownership landscape for a stock
    - "signal": Find stocks with institutional flow patterns

    For manager queries, uses trigram fuzzy search (e.g., "Citadel" finds
    "CITADEL ADVISORS LLC").

    Args:
        query_type: Type of query ("manager", "security", "signal")
        identifier: Symbol or manager name/CIK (required for manager/security)
        signal_type: For signal queries - what pattern to find
            - "accumulation": Stocks institutions are buying
            - "distribution": Stocks institutions are selling
            - "conviction": Stocks with high conviction positions (5%+)
            - "new": Stocks with multiple new institutional positions
        limit: Max results (default 25)

    Examples:
        institutional("manager", "Citadel")  # What does Citadel own?
        institutional("manager", "0001067983")  # Berkshire by CIK
        institutional("security", "NVDA")  # Who owns NVIDIA?
        institutional("signal", signal_type="accumulation")  # Smart money buying
        institutional("signal", signal_type="conviction")  # High conviction bets
        institutional("signal")  # Overview of all signals
    """
    client = _get_client(ctx)
    params = {"query_type": query_type, "limit": limit}
    if identifier:
        params["identifier"] = identifier
    if signal_type:
        params["signal_type"] = signal_type
    return client.get("/v1/mcp-institutional", params=params)


def search(
    q: str,
    entity_type: Optional[Literal["filing", "company", "insider", "manager"]] = None,
    sector: Optional[str] = None,
    impact: Optional[Literal["HIGH", "MEDIUM", "LOW"]] = None,
    limit: int = 20,
    ctx=None
) -> dict:
    """
    Semantic search across the entire Profitelligence platform.

    Searches SEC filings, companies, insiders, and institutional managers
    using PostgreSQL full-text search with prefix matching.

    Args:
        q: Search query (minimum 2 characters). Supports natural language queries.
        entity_type: Filter results by type
            - "filing": SEC 8-K filings with LLM-extracted insights
            - "company": Public companies by name or symbol
            - "insider": Corporate insiders (executives, directors)
            - "manager": Institutional investors (13F filers)
        sector: Filter by sector (e.g., "Technology", "Healthcare")
        impact: Filter filings by impact level ("HIGH", "MEDIUM", "LOW")
        limit: Max results (default 20, max 100)

    Returns:
        {
            "results": [
                {
                    "entity_type": "filing|company|insider|manager",
                    "entity_id": "unique identifier",
                    "symbol": "stock symbol if applicable",
                    "title": "display title",
                    "rank": relevance score,
                    "metadata": {...additional context...},
                    "created_at": "ISO8601 timestamp"
                }
            ],
            "query": "original query",
            "total": result count
        }

    Examples:
        search("CEO resignation")  # Find all CEO departure filings
        search("NVIDIA", entity_type="company")  # Find NVIDIA company
        search("Buffett", entity_type="insider")  # Find Warren Buffett
        search("activist", entity_type="manager")  # Find activist investors
        search("acquisition", sector="Technology", impact="HIGH")  # High-impact tech M&A
    """
    client = _get_client(ctx)
    params = {"q": q, "limit": limit}
    if entity_type:
        params["entity_type"] = entity_type
    if sector:
        params["sector"] = sector
    if impact:
        params["impact"] = impact
    return client.get("/v1/search", params=params)
