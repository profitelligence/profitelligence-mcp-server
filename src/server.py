"""
Profitelligence MCP Server.

FastMCP server providing access to Profitelligence financial data APIs.
"""
import logging
from typing import Optional
from fastmcp import FastMCP, Context

from .capabilities import service_info
from .tools import mcp_tools
from .utils.config import get_config
from .utils.oauth import get_oauth_metadata, should_use_oauth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Profitelligence")


# ============================================================================
# V3 TOOLS - Clean, LLM-friendly (maps to /mcp-* endpoints)
# ============================================================================

@mcp.tool()
def pulse(ctx: Context) -> str:
    """
    Market snapshot - what's happening right now.

    Returns market movers, recent filings, insider trades, economic indicators.
    No parameters needed.

    Example: pulse()
    """
    logger.info("Tool invoked: pulse()")
    import json
    return json.dumps(mcp_tools.pulse(ctx))


@mcp.tool()
def investigate(
    subject: str,
    ctx: Context,
    entity_type: str = None,
    days: int = 30
) -> str:
    """
    Research any entity - company, insider, or sector.

    Auto-detects type from subject:
    - Stock symbols (AAPL) → company
    - CIK numbers (0001067983) → insider
    - Sector names (Technology) → sector

    Args:
        subject: Symbol, CIK, or sector name
        entity_type: Optional override - "company", "insider", or "sector"
        days: Lookback period (default 30)

    Examples:
        investigate("AAPL")
        investigate("0001067983")
        investigate("Technology", entity_type="sector")
    """
    logger.info(f"Tool invoked: investigate(subject={subject}, days={days})")
    import json
    return json.dumps(mcp_tools.investigate(subject, entity_type, days, ctx))


@mcp.tool()
def screen(
    ctx: Context,
    focus: str = "all",
    sector: str = None,
    min_score: float = None,
    days: int = 7,
    limit: int = 25
) -> str:
    """
    Scan market for opportunities.

    Args:
        focus: "all", "multi_signal", "insider", or "events"
        sector: Filter by sector (e.g., "Technology")
        min_score: Minimum score 0-100
        days: Lookback period (default 7)
        limit: Max results (default 25)

    Examples:
        screen()
        screen(focus="insider", sector="Technology")
    """
    logger.info(f"Tool invoked: screen(focus={focus}, sector={sector})")
    import json
    return json.dumps(mcp_tools.screen(focus, sector, min_score, days, limit, ctx))


@mcp.tool()
def assess(
    symbol: str,
    ctx: Context,
    days: int = 30
) -> str:
    """
    Position health check for a stock.

    Returns material events, insider sentiment, institutional sentiment, technical signals, risk factors.

    Args:
        symbol: Stock symbol to assess
        days: Lookback period (default 30)

    Examples:
        assess("NVDA")
        assess("AAPL", days=90)
    """
    logger.info(f"Tool invoked: assess(symbol={symbol}, days={days})")
    import json
    return json.dumps(mcp_tools.assess(symbol, days, ctx))


@mcp.tool()
def institutional(
    query_type: str,
    ctx: Context,
    identifier: str = None,
    signal_type: str = None,
    limit: int = 25
) -> str:
    """
    Institutional investor intelligence from 13F filings.

    Query types:
    - "manager": Profile an institutional investor (by name or CIK)
    - "security": Institutional ownership landscape for a stock
    - "signal": Find stocks with institutional flow patterns

    Args:
        query_type: Type of query ("manager", "security", "signal")
        identifier: Symbol or manager name/CIK (required for manager/security)
        signal_type: For signal queries - "accumulation", "distribution", "conviction", "new"
        limit: Max results (default 25)

    Examples:
        institutional("manager", identifier="Citadel")
        institutional("security", identifier="NVDA")
        institutional("signal", signal_type="accumulation")
        institutional("signal")  # Overview of all signals
    """
    logger.info(f"Tool invoked: institutional(query_type={query_type}, identifier={identifier}, signal_type={signal_type})")
    import json
    return json.dumps(mcp_tools.institutional(query_type, identifier, signal_type, limit, ctx))


@mcp.tool()
def search(
    q: str,
    ctx: Context,
    entity_type: str = None,
    sector: str = None,
    impact: str = None,
    limit: int = 20
) -> str:
    """
    Semantic search across filings, companies, insiders, and managers.

    Powerful cross-platform search using PostgreSQL full-text search.
    Perfect for finding specific events, people, or companies.

    Args:
        q: Search query (min 2 chars). Natural language supported.
        entity_type: Filter by type - "filing", "company", "insider", "manager"
        sector: Filter by sector (e.g., "Technology")
        impact: Filter filings by impact - "HIGH", "MEDIUM", "LOW"
        limit: Max results (default 20, max 100)

    Examples:
        search("CEO resignation")  # Find CEO departure filings
        search("NVIDIA", entity_type="company")  # Find NVIDIA
        search("Buffett", entity_type="insider")  # Find Warren Buffett
        search("activist", entity_type="manager")  # Find activist funds
        search("acquisition", sector="Technology", impact="HIGH")  # High-impact M&A
    """
    logger.info(f"Tool invoked: search(q={q}, entity_type={entity_type}, sector={sector}, impact={impact})")
    import json
    return json.dumps(mcp_tools.search(q, entity_type, sector, impact, limit, ctx))


@mcp.tool()
def service_info(
    info_type: str = "overview",
    ctx: Context = None
) -> str:
    """
    Info about Profitelligence service and your account.

    Args:
        info_type: What info to retrieve
            - "overview": Service description and capabilities
            - "profile": Your subscription tier, features, and account status
            - "pricing": Subscription tiers and pricing
            - "capabilities": Available tools and data sources
            - "status": Server configuration and health

    Examples:
        service_info()  # Overview
        service_info("profile")  # Your account
        service_info("pricing")  # Pricing info
    """
    logger.info(f"Tool invoked: service_info(info_type={info_type})")
    from .capabilities import service_info as svc_info
    return svc_info.get_service_info(info_type, ctx)



# ============================================================================
# MCP PROMPTS - Professional Intelligence Reports
# ============================================================================
# Each prompt follows structured metadata for:
# - Auto-generating prompt catalogs
# - External agent integration
# - Future usage metering
# - Explicit failure modes


@mcp.prompt()
def morning_briefing() -> str:
    """
    Daily pre-market intelligence briefing.

    Job: Get the user up to speed before market open.
    Tools: pulse (1 call), investigate (0-3 calls for HIGH impact events)
    Failure behavior: Return pulse data only if investigate fails.
    Tier requirement: Free
    Frequency: Daily
    """
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    return f"""You are a senior market intelligence analyst preparing the daily pre-market briefing.

Generate a concise, actionable morning briefing for {today}.

## TOOL CALLS
1. Call `pulse()` to get the current market snapshot
2. For any HIGH impact filings in the pulse data, call `investigate(symbol)` for context (max 3)

## OUTPUT STRUCTURE

# Market Briefing - {today}
Data via Profitelligence

## Data Confidence
- Filing coverage: Last 24 hours
- Insider data lag: ~2 business days from SEC
- Price data: Pre-market as of [time from data]

## Market Pulse
[From pulse() data]
- Pre-market direction and key movers
- Economic data released overnight

## Material Events Overnight
[Table format: Symbol | Event | Impact | 1-Line Summary]

Focus on HIGH impact 8-Ks. For each:
- What happened
- Why it matters

**Why This Matters Now**: [1-2 sentences on the most important event and its timing significance]

## Notable Insider Activity
[Table: Symbol | Insider | Role | Action | Value]

Prioritize:
- Large transactions (>$1M)
- Cluster buying (multiple insiders, same company)
- C-suite activity (CEO/CFO)

## What to Watch Today
- Earnings after close
- Fed speakers scheduled
- Economic releases

## Bottom Line
[2 sentences maximum: The single most important thing to focus on today, framed conditionally]

Example: "The data currently supports a risk-on posture unless the Fed minutes at 2pm signal a more hawkish stance than expected."

---
IMPORTANT:
- Keep this to a 2-minute read
- Lead with insight, not data
- No fluff, no filler
- Format in clean markdown with tables"""


@mcp.prompt()
def company_intelligence_report(symbol: str) -> str:
    """
    Generate a comprehensive intelligence report for a single company.

    Job: Provide sell-side grade analysis of a public company.
    Tools: investigate (1 call), institutional (1 call), search (1 call)
    Estimated tokens: ~2500 output
    Failure behavior: Return partial report with data gaps noted.
    Tier requirement: Free (basic), Pro (opportunity analysis, full 13F history)

    Args:
        symbol: Stock ticker (e.g., "AAPL", "NVDA")
    """
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    return f"""You are a senior equity research analyst preparing an institutional-grade intelligence report.

Generate a comprehensive intelligence report for {symbol}.

## TOOL CALLS (in order)
1. `investigate("{symbol}", days=90)` - Full company data
2. `institutional("security", identifier="{symbol}")` - Who owns it
3. `search("{symbol}", entity_type="filing", limit=10)` - Recent filing history

## SIGNAL STRENGTH SCALE
Use consistently throughout:
- **Strong**: ≥3 independent signals aligned (e.g., insider buying + institutional accumulation + positive 8-K)
- **Medium**: 2 signals aligned
- **Emerging**: 1 strong signal or early anomaly worth monitoring

## OUTPUT STRUCTURE

# {symbol} Intelligence Report
Generated: {today} | Data via Profitelligence

## Data Confidence
- Filing coverage: Complete (last 90 days)
- Insider data lag: ~2 business days from SEC Form 4
- Institutional data: As of [quarter from data] (13F filings are 45 days delayed)
- Price data: EOD [date from data]

## Executive Summary
[2-3 sentences: The single most important thing to know about this stock right now]

**Why This Matters Now**: [Specific timing context - earnings approaching, pattern break, macro sensitivity, etc.]

## Company Profile
- **Sector/Industry**: [from profile]
- **Market Cap**: [value]
- **CEO**: [name]
- **Business**: [1 paragraph description]

## Price Performance
| Metric | Value |
|--------|-------|
| Current Price | $ |
| 30-Day Change | % |
| 90-Day Change | % |
| 52-Week Range | $ - $ |

[Brief commentary on notable moves and what drove them]

## Material Events (8-K Analysis)
**Signal Strength**: [Strong/Medium/Emerging based on event count and impact]

[For each HIGH/MEDIUM impact filing]
| Date | Event Type | Impact | Summary |
|------|------------|--------|---------|

[Commentary: What do these events tell us about company trajectory?]

## Insider Intelligence
**Signal Strength**: [Strong/Medium/Emerging]
**Net Position**: [$ value] ([Bullish/Bearish/Neutral])

| Date | Insider | Role | Action | Shares | Value |
|------|---------|------|--------|--------|-------|

**Pattern Analysis**:
- [Is this typical or unusual?]
- [Any cluster activity?]
- [C-suite vs other insiders?]

## Institutional Ownership
**Holder Count**: [X] ([+/- Y] vs prior quarter)
**Crowded Signal**: [from data - Accumulation/Distribution/Stable]

**Top Holders**:
| Manager | Shares | Value | % of Their Portfolio |
|---------|--------|-------|---------------------|

**Notable Changes This Quarter**:
| Manager | Action | Change Size |
|---------|--------|-------------|

**High Conviction Holders** (>5% of their portfolio):
[List with brief context on why this matters]

## Financial Snapshot
| Metric | Latest | Prior Quarter | YoY Change |
|--------|--------|---------------|------------|
| Revenue | | | |
| EPS | | | |
| Gross Margin | | | |
| Free Cash Flow | | | |

## Technical Signals
| Indicator | Signal | Triggered |
|-----------|--------|-----------|

[Note convergence or divergence]

## Key Risks
[Bullet list of specific risks derived from the data - not generic boilerplate]

## Bottom Line
The data currently supports a [bullish/bearish/neutral] thesis unless [specific trigger] occurs.

**Key tensions to monitor**:
- [Tension 1: e.g., strong fundamentals but heavy insider selling]
- [Tension 2: e.g., institutional accumulation despite price weakness]

**This view would change if**: [specific, measurable condition]

---
DISCLAIMER: This is informational analysis only, not investment advice."""


@mcp.prompt()
def position_risk_check(symbol: str) -> str:
    """
    Quick risk/signal check for an existing position.

    Job: Answer "Should I be worried about this holding?"
    Tools: assess (1 call), investigate (0-1 call if red flags)
    Estimated tokens: ~1000 output
    Failure behavior: Return assess data with note about missing context.
    Tier requirement: Free
    Frequency: Weekly or ad-hoc

    Args:
        symbol: Stock ticker to check (e.g., "TSLA", "GOOGL")
    """
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    return f"""You are a portfolio risk analyst conducting a position health check.

Generate a concise risk assessment for {symbol}.

## TOOL CALLS
1. `assess("{symbol}", days=30)` - Position health check
2. If any 🔴 signals appear, call `investigate("{symbol}")` for deeper context

## OUTPUT STRUCTURE

# Position Check: {symbol}
As of: {today}

## Data Confidence
- Filing coverage: Last 30 days
- Insider data lag: ~2 business days from SEC
- Institutional data: As of [quarter from data]

## Risk Dashboard
**Overall Signal Strength**: [Strong/Medium/Emerging/Weak]

| Dimension | Status | Detail |
|-----------|--------|--------|
| Insider Sentiment | 🟢/🟡/🔴 | Net $X [buying/selling] |
| Institutional Flow | 🟢/🟡/🔴 | [+/-X] holders QoQ |
| Material Events | 🟢/🟡/🔴 | [X] HIGH impact filings |
| Technical Picture | 🟢/🟡/🔴 | [X of Y] indicators bullish |

**Legend**: 🟢 Favorable | 🟡 Monitor | 🔴 Attention Required

## Why This Matters Now
[1-2 sentences on the most pressing timing issue for this position]

## Recent Material Events
[Any 8-Ks in the period - brief summary with impact]

## Insider Activity Summary
- **Net**: $[value] [buying/selling]
- **Notable**: [Any significant transactions]

## Institutional Sentiment
- **Holder Change**: [+/-X] this quarter
- **Signal**: [Accumulation/Distribution/Stable]

## Action Items
[Specific things to watch or do - be concrete]
- [ ] [e.g., "Monitor Q4 earnings on Jan 25 - guidance is key"]
- [ ] [e.g., "CFO sold $2M - first sale in 3 years, investigate further"]
- [ ] [e.g., "Set alert for break below $150 support"]

## Hold/Trim/Exit Framework

**Reasons to Hold**:
- [Bullet from data]

**Reasons to Trim**:
- [Bullet from data]

**Would Exit If**:
- [Specific, measurable trigger]

## Bottom Line
The position is currently [low/moderate/elevated] risk.

**Key trigger to watch**: [The single most important thing that would change this assessment]

---
This is a risk monitoring tool, not investment advice."""


@mcp.prompt()
def smart_money_report() -> str:
    """
    Map institutional positioning and flow patterns.

    Job: Answer "What are the big institutions doing?"
    Tools: institutional (4 calls - accumulation, distribution, conviction, new), investigate (2-3 calls for top signals)
    Estimated tokens: ~2000 output
    Failure behavior: Return available signals, note which queries failed.
    Tier requirement: Pro (full history), Elite (conviction signals)
    Frequency: Quarterly or after 13F deadline
    """
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    return f"""You are an institutional flow analyst tracking smart money positioning.

Generate a comprehensive institutional flow report.

## TOOL CALLS (in order)
1. `institutional("signal", signal_type="accumulation", limit=15)` - What's being bought
2. `institutional("signal", signal_type="distribution", limit=15)` - What's being sold
3. `institutional("signal", signal_type="conviction", limit=10)` - High conviction bets
4. `institutional("signal", signal_type="new", limit=10)` - New positions
5. For top 2-3 most interesting signals, call `investigate(symbol)` for context

## OUTPUT STRUCTURE

# Institutional Flow Report
Generated: {today} | Data via Profitelligence

## Data Confidence
- 13F filing period: [Quarter from data]
- Coverage: ~5,000 institutional managers with >$100M AUM
- Data lag: 13F filings are 45 days delayed from quarter-end
- Note: This shows where institutions WERE positioned, not necessarily where they ARE now

## Executive Summary
[2-3 sentences: Key theme - are institutions risk-on or risk-off? Any sector rotations?]

**Why This Matters Now**: [Timing context - e.g., first full quarter post-election, post-Fed pivot, etc.]

## Accumulation Signals
**Signal Strength**: [Strong/Medium/Emerging]

Stocks seeing net institutional buying:
| Symbol | Net Buyers | Notable Names | Signal Strength |
|--------|------------|---------------|-----------------|

**Spotlight**: [Deep dive on the most interesting accumulation]
- Who's buying: [Names and their styles]
- Why it matters: [Context from investigate call]
- Cross-reference: [Any supporting signals - insider buying, positive events?]

## Distribution Signals
Stocks seeing net institutional selling:
| Symbol | Net Sellers | Notable Names | Signal Strength |
|--------|-------------|---------------|-----------------|

**Warning**: [Any concerning exits - major funds reducing positions]

## High Conviction Positions
Managers with concentrated bets (>5% of their portfolio):
| Manager | Symbol | % of Portfolio | Position Size |
|---------|--------|----------------|---------------|

[Commentary: These are the bets where managers have real skin in the game]

## New Position Initiations
Fresh positions started this quarter:
| Symbol | Manager | Position Size | Manager Style |
|--------|---------|---------------|---------------|

[Note any patterns - are value managers piling into growth? vice versa?]

## Sector Rotation Analysis
[Which sectors seeing inflows/outflows - what does it suggest about institutional positioning?]

| Sector | Flow Direction | Notable Moves |
|--------|----------------|---------------|

## Actionable Ideas
Top 3-5 stocks with institutional tailwinds worth researching:

### 1. [SYMBOL]
**Signal Strength**: [Strong/Medium/Emerging]
- Institutional signal: [What the 13F data shows]
- Supporting factors: [Other signals]
- Contradicting factors: [Any concerns]
- Thesis invalidated if: [Specific trigger]

[Repeat for each idea]

## Bottom Line
Institutional positioning currently suggests [thesis].

This view would change if: [Specific trigger - e.g., "next quarter shows reversal of accumulation pattern"]

---
DISCLAIMER: 13F data is delayed and shows historical positioning. This is informational analysis, not investment advice."""


@mcp.prompt()
def sector_scan(sector: str) -> str:
    """
    Surface best opportunities within a specific sector.

    Job: Answer "Find me the best opportunities in [sector]"
    Tools: screen (2 calls - all signals, insider focus), investigate (3-5 calls for top hits)
    Estimated tokens: ~1800 output
    Failure behavior: Return screen results, note if investigate calls fail.
    Tier requirement: Free (top 500), Pro (6,000+ securities)

    Args:
        sector: Sector to scan (e.g., "Technology", "Healthcare", "Energy")
    """
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    valid_sectors = [
        "Technology", "Healthcare", "Financial Services", "Consumer Cyclical",
        "Consumer Defensive", "Industrials", "Energy", "Basic Materials",
        "Real Estate", "Utilities", "Communication Services"
    ]

    return f"""You are a sector specialist identifying investment opportunities.

Generate an opportunity scan for the **{sector}** sector.

Valid sectors: {', '.join(valid_sectors)}

## TOOL CALLS (in order)
1. `screen(focus="all", sector="{sector}", days=14, limit=25)` - All signals in sector
2. `screen(focus="insider", sector="{sector}", days=14, limit=15)` - Insider activity
3. For top 3-5 opportunities, call `investigate(symbol)` for depth

## SIGNAL STRENGTH SCALE
- **Strong**: ≥3 independent signals aligned
- **Medium**: 2 signals aligned
- **Emerging**: 1 strong signal or early anomaly

## OUTPUT STRUCTURE

# {sector} Sector Opportunity Scan
Period: Last 14 Days | Generated: {today}

## Data Confidence
- Securities screened: [X] in {sector}
- Filing coverage: Last 14 days
- Insider data lag: ~2 business days from SEC
- Institutional data: As of [quarter]

## Sector Snapshot
- **Stocks Screened**: [count]
- **Insider Sentiment**: [Net buyers vs sellers across sector]
- **Material Events**: [Count of HIGH impact 8-Ks]

**Why This Matters Now**: [Sector-specific timing - earnings season, regulatory change, macro shift, etc.]

## Top Opportunities Identified

### 1. [SYMBOL] - [Company Name]
**Signal Strength**: [Strong/Medium/Emerging]
**Signals Aligned**: [X of 4 possible]

**Why it's flagged**:
- [Specific signal with numbers, e.g., "3 executives bought $5M combined in past 10 days"]
- [Another signal]

**Quick Fundamentals**:
| Metric | Value |
|--------|-------|
| Market Cap | |
| P/E | |
| Revenue Growth | |

**What to watch**: [Specific near-term catalyst]

**Thesis invalidated if**: [Specific condition]

### 2. [SYMBOL] - [Company Name]
[Repeat structure]

### 3. [SYMBOL] - [Company Name]
[Repeat structure]

## Insider Activity Heat Map
| Symbol | Buyers | Sellers | Net $ | Notable Names |
|--------|--------|---------|-------|---------------|

**Cluster Buying** (3+ insiders, same company - rare and strong signal):
[List any with brief context]

## Material Events in Sector
Recent HIGH impact 8-Ks:
| Symbol | Date | Event | Impact |
|--------|------|-------|--------|

## Pass/Monitor List
Stocks that appeared in screens but don't make the cut:
- [SYMBOL] - [1-line reason, e.g., "Single insider sale, no pattern"]
- [SYMBOL] - [1-line reason]

## Sector Thesis
The data currently supports [thesis about sector] unless [specific trigger].

**Key tensions**:
- [Tension 1]
- [Tension 2]

---
This is a screening tool, not investment advice. Always conduct thorough due diligence."""


@mcp.prompt()
def insider_deep_dive(identifier: str) -> str:
    """
    Profile a specific insider's trading activity and patterns.

    Job: Answer "What is this executive/insider doing across their holdings?"
    Tools: search (1 call), investigate (1 call for insider), investigate (1-3 calls for company context)
    Estimated tokens: ~1500 output
    Failure behavior: Return insider data, note if company context unavailable.
    Tier requirement: Free

    Args:
        identifier: Insider name or CIK (e.g., "Warren Buffett", "0001067983")
    """
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    return f"""You are an insider trading analyst profiling a specific market participant.

Generate a comprehensive insider profile for: {identifier}

## TOOL CALLS (in order)
1. If name provided: `search("{identifier}", entity_type="insider", limit=5)` to find CIK
2. `investigate(cik, entity_type="insider", days=180)` - Full insider profile
3. For top 2-3 companies they trade, call `investigate(symbol)` for company context

## OUTPUT STRUCTURE

# Insider Profile: [Full Name]
CIK: [number] | Generated: {today}

## Data Confidence
- Transaction history: Last 180 days
- Insider data lag: ~2 business days from SEC Form 4 filing
- Company context: As of [date]

## Profile Summary
- **Companies**: [List where they're an insider]
- **Typical Role**: [CEO, Director, 10% Owner, etc.]
- **Trading Style**: [Frequent trader, rare transactions, seasonal patterns, etc.]

## Trading Statistics
| Metric | Value |
|--------|-------|
| Total Transactions (180d) | |
| Net Position | $ [buying/selling] |
| Avg Transaction Size | $ |

**Signal Strength**: [Strong/Medium/Emerging]
(Based on consistency, size, and pattern unusualness)

## Recent Activity (180 Days)
| Date | Company | Action | Shares | Value | Price |
|------|---------|--------|--------|-------|-------|

## Pattern Analysis
[Analysis of their trading behavior]
- **Trend**: Are they buying or selling lately?
- **Clustering**: Any cluster activity across multiple holdings?
- **Timing**: Before earnings? After announcements? 10b5-1 plan?

**Why This Matters Now**: [Timing context - e.g., "First buy after 2 years of only selling"]

## By Company Breakdown

### [Company 1] (SYMBOL)
- **Their Role**: [CEO, CFO, Director, etc.]
- **Recent Transactions**: [Summary]
- **Company Context**: [Brief from investigate - what's happening at the company?]
- **Thesis supported if**: [Condition]
- **Thesis invalidated if**: [Condition]

### [Company 2] (SYMBOL)
[Repeat structure]

## Notable Observations
[Bullets: Anything unusual or worth highlighting]
- [e.g., "First purchase in 2 years - broke a consistent selling pattern"]
- [e.g., "Buying into 30% price decline - contrarian bet"]
- [e.g., "Transaction size 5x their typical - high conviction"]

## Following This Insider
The data currently suggests this insider is [bullish/bearish/neutral] on their holdings.

**Key pattern to watch**: [Specific behavior that would signal change]

**This interpretation would change if**: [Specific trigger]

---
DISCLAIMER: Insider trading data is one signal among many. Insiders sell for many reasons beyond bearish outlook. This is informational analysis, not investment advice."""


# OAuth Middleware - Starlette middleware for 401 responses
class OAuthMiddleware:
    """
    Starlette middleware that returns 401 Unauthorized for unauthenticated requests.

    This triggers MCP clients (like Claude Desktop) to discover OAuth endpoints.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        from starlette.requests import Request
        from starlette.responses import Response

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        cfg = get_config()

        # Skip auth for health check, OAuth metadata, and OAuth authorization endpoints
        oauth_public_paths = [
            "/", "/health",
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
            "/.well-known/oauth-authorization-server",
            "/register",
            "/authorize",
            "/oauth/token",
            "/oauth/callback"
        ]
        if request.url.path in oauth_public_paths:
            await self.app(scope, receive, send)
            return

        # Handle CORS preflight for /mcp endpoint
        if request.method == "OPTIONS" and request.url.path == "/mcp":
            response = Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Max-Age": "86400",
                }
            )
            await response(scope, receive, send)
            return

        # If OAuth mode is enabled, check for Bearer token
        if should_use_oauth(cfg):
            auth_header = request.headers.get("authorization", "")

            if not auth_header.startswith("Bearer "):
                # Return 401 with WWW-Authenticate header pointing to MCP-specific metadata endpoint
                # Use https for production (ALB terminates SSL), http for localhost
                scheme = "http" if "localhost" in request.url.netloc or "127.0.0.1" in request.url.netloc else "https"
                base_url = f"{scheme}://{request.url.netloc}"
                metadata_url = f"{base_url}/.well-known/oauth-protected-resource/mcp"

                response = Response(
                    status_code=401,
                    content='{"error": "unauthorized", "message": "Bearer token required"}',
                    headers={
                        "WWW-Authenticate": f'Bearer realm="mcp-server", resource_metadata="{metadata_url}"',
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    }
                )
                await response(scope, receive, send)
                return

        # Continue with request
        await self.app(scope, receive, send)


# Add health check endpoint for ALB/ECS at root
@mcp.custom_route("/", methods=["GET"])
async def root_health_check(request):
    """Root health check endpoint for load balancer."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "service": "profitelligence-mcp", "version": "1.0"})


# Add health check endpoint at /health as well
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for load balancer."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "service": "profitelligence-mcp"})


# OAuth 2.1 Authorization Server Metadata Endpoint
# MCP Inspector looks for this endpoint (RFC 8414)
@mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET", "OPTIONS"])
async def oauth_authorization_server_metadata(request):
    """
    OAuth 2.0 Authorization Server Metadata endpoint (RFC 8414).

    MCP Inspector checks this endpoint for full OAuth discovery.
    Returns the authorization server configuration.
    """
    from starlette.responses import JSONResponse

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    cfg = get_config()

    if not should_use_oauth(cfg):
        return JSONResponse({"error": "OAuth not enabled"}, status_code=404)

    # Derive base URL from mcp_server_url
    # Use removesuffix to properly remove the /mcp path (not individual characters)
    base_url = cfg.mcp_server_url.removesuffix('/mcp').rstrip('/')

    metadata = {
        "issuer": base_url,  # We are the authorization server, not Google
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "registration_endpoint": f"{base_url}/register",
        "jwks_uri": cfg.oauth_jwks_uri,
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": ["openid", "email", "profile"],
        "response_modes_supported": ["query"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
    }

    logger.info("OAuth authorization server metadata requested")
    return JSONResponse(
        metadata,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )


# OAuth 2.1 Dynamic Client Registration Endpoint (RFC 7591)
# Required by Claude Desktop for OAuth configuration
@mcp.custom_route("/register", methods=["POST", "OPTIONS"])
async def oauth_register(request):
    """
    OAuth 2.1 Dynamic Client Registration endpoint (RFC 7591).

    Claude Desktop uses this to register as an OAuth client. We return
    the configured client_id since we're using Google OAuth (pre-registered).
    """
    from starlette.responses import JSONResponse
    import json

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    cfg = get_config()

    if not should_use_oauth(cfg):
        return JSONResponse({"error": "OAuth not enabled"}, status_code=404)

    # Parse request body
    try:
        body = await request.body()
        client_metadata = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return JSONResponse(
            {
                "error": "invalid_client_metadata",
                "error_description": "Invalid JSON in request body"
            },
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    # Validate redirect URIs if provided
    redirect_uris = client_metadata.get("redirect_uris", [])
    if redirect_uris:
        for uri in redirect_uris:
            # RFC 7591: HTTPS required except for localhost
            if not uri.startswith("https://") and not uri.startswith("http://localhost") and not uri.startswith("http://127.0.0.1"):
                return JSONResponse(
                    {
                        "error": "invalid_redirect_uri",
                        "error_description": f"Redirect URI must use HTTPS or localhost: {uri}"
                    },
                    status_code=400,
                    headers={"Access-Control-Allow-Origin": "*"}
                )

    # Return client registration response with our pre-configured Google OAuth client_id
    # We don't generate new client_ids since we're using Google OAuth (pre-registered app)
    response_data = {
        "client_id": cfg.oauth_client_id,
        "client_id_issued_at": 1704067200,  # Static timestamp (we use Google's pre-registered client)
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",  # PKCE public client
    }

    # Include redirect URIs if provided
    if redirect_uris:
        response_data["redirect_uris"] = redirect_uris

    # Include client name if provided
    client_name = client_metadata.get("client_name")
    if client_name:
        response_data["client_name"] = client_name

    client_id_display = cfg.oauth_client_id[:20] + "..." if cfg.oauth_client_id else "None"
    logger.info(f"Dynamic client registration request - returning client_id: {client_id_display}")

    return JSONResponse(
        response_data,
        status_code=201,  # RFC 7591 requires 201 Created
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store",
            "Pragma": "no-cache"
        }
    )


# OAuth 2.1 Authorization Proxy Endpoint
# Claude Desktop expects the MCP server to handle OAuth directly
# This endpoint proxies to Google OAuth
@mcp.custom_route("/authorize", methods=["GET", "OPTIONS"])
async def oauth_authorize(request):
    """
    OAuth authorization endpoint that proxies to Google OAuth with PKCE support.

    ChatGPT hits this endpoint. We redirect to Google with OUR callback URL,
    then later redirect back to ChatGPT's redirect_uri with a temp code.
    """
    from starlette.responses import RedirectResponse, JSONResponse
    from urllib.parse import urlencode
    from .utils.pkce import generate_pkce_pair, store_pkce_state
    import secrets

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    cfg = get_config()

    # Get query parameters from ChatGPT
    client_redirect_uri = request.query_params.get("redirect_uri")
    client_state = request.query_params.get("state", "")
    client_id = request.query_params.get("client_id", cfg.oauth_client_id)
    scope = request.query_params.get("scope", "openid email profile")
    response_type = request.query_params.get("response_type", "code")

    if not client_redirect_uri:
        return JSONResponse(
            {"error": "invalid_request", "error_description": "Missing redirect_uri parameter"},
            status_code=400
        )

    # Generate PKCE code_verifier and code_challenge for Google OAuth
    code_verifier, code_challenge = generate_pkce_pair()

    # Generate our own state parameter for the Google OAuth request
    google_state = secrets.token_urlsafe(32)

    # Store PKCE state with client info for callback
    store_pkce_state(google_state, code_verifier, client_id, client_redirect_uri, client_state)

    # Build redirect URL to Google OAuth with OUR callback URL
    base_url = cfg.mcp_server_url.removesuffix('/mcp').rstrip('/')
    our_callback_url = f"{base_url}/oauth/callback"

    google_params = {
        "client_id": cfg.oauth_client_id,
        "redirect_uri": our_callback_url,
        "response_type": "code",
        "scope": scope,
        "state": google_state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",  # Request refresh token
        "prompt": "consent"  # Force consent screen to get refresh token
    }

    google_auth_url = f"{cfg.oauth_auth_url}?{urlencode(google_params)}"

    logger.info(f"OAuth authorize request - redirecting to Google")
    logger.info(f"  Client redirect URI: {client_redirect_uri}")
    logger.info(f"  Our callback URL: {our_callback_url}")

    return RedirectResponse(url=google_auth_url, status_code=302)


@mcp.custom_route("/oauth/token", methods=["POST", "OPTIONS"])
async def oauth_token(request):
    """
    OAuth 2.1 Token endpoint - exchanges authorization code for access token.

    ChatGPT calls this endpoint to exchange the authorization code for a Firebase token.
    We look up the stored code_verifier and exchange with Google.
    """
    from starlette.responses import JSONResponse
    from .utils.pkce import get_pkce_state, delete_pkce_state
    from .utils.token_exchange import exchange_google_token_for_firebase_token
    import httpx

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    cfg = get_config()

    # Parse form data
    form = await request.form()
    grant_type = form.get("grant_type")
    code = form.get("code")
    redirect_uri = form.get("redirect_uri")
    client_id = form.get("client_id")

    logger.info(f"Token request: grant_type={grant_type}, redirect_uri={redirect_uri}")

    # Validate grant_type
    if grant_type != "authorization_code":
        return JSONResponse(
            {
                "error": "unsupported_grant_type",
                "error_description": f"Grant type '{grant_type}' not supported"
            },
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    if not code:
        return JSONResponse(
            {
                "error": "invalid_request",
                "error_description": "Missing authorization code"
            },
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    # Look up the stored authorization code to get the PKCE verifier
    # We stored it by code in the authorize endpoint
    from .utils.pkce import get_auth_code_data, delete_auth_code_data

    auth_data = get_auth_code_data(code)
    if not auth_data:
        logger.error(f"Invalid or expired authorization code: {code[:10]}...")
        return JSONResponse(
            {
                "error": "invalid_grant",
                "error_description": "Invalid or expired authorization code"
            },
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    code_verifier = auth_data["code_verifier"]
    google_code = auth_data["google_code"]
    google_redirect_uri = auth_data.get("google_redirect_uri")

    # CRITICAL FIX: Use the EXACT redirect_uri we stored during authorization
    # Do NOT reconstruct it - Google requires byte-for-byte match
    if not google_redirect_uri:
        logger.error("Missing google_redirect_uri in stored auth data")
        delete_auth_code_data(code)
        return JSONResponse(
            {
                "error": "invalid_grant",
                "error_description": "Invalid authorization code data"
            },
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )

    try:
        # Exchange authorization code with Google for tokens
        logger.info("Exchanging authorization code with Google...")
        logger.info(f"  Using redirect_uri: {google_redirect_uri}")

        token_request_data = {
            "code": google_code,
            "client_id": cfg.oauth_client_id,
            "redirect_uri": google_redirect_uri,
            "grant_type": "authorization_code",
            "client_secret": cfg.oauth_client_secret,
            "code_verifier": code_verifier
        }

        logger.info("  Using client_secret + code_verifier")

        async with httpx.AsyncClient() as client:
            logger.info(f"  POST {cfg.oauth_token_url}")
            token_response = await client.post(
                cfg.oauth_token_url,
                data=token_request_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        logger.info(f"  Google token response: {token_response.status_code}")

        if token_response.status_code != 200:
            logger.error(f"Google token exchange failed: {token_response.status_code}")
            logger.error(f"  Response body: {token_response.text}")
            delete_auth_code_data(code)
            return JSONResponse(
                {
                    "error": "invalid_grant",
                    "error_description": f"Token exchange failed: {token_response.status_code}, {token_response.text}"
                },
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        token_data = token_response.json()
        logger.info("  ✓ Successfully received tokens from Google")
        id_token = token_data.get("id_token")

        if not id_token:
            logger.error("No ID token returned from Google")
            delete_auth_code_data(code)
            return JSONResponse(
                {
                    "error": "invalid_grant",
                    "error_description": "No ID token returned from token endpoint"
                },
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Exchange Google ID token for Firebase ID token using Firebase Auth REST API
        logger.info("Exchanging Google ID token for Firebase ID token...")

        # Firebase Web API Key from config
        if not cfg.firebase_web_api_key:
            logger.error("Firebase Web API Key not configured")
            delete_auth_code_data(code)
            return JSONResponse(
                {"error": "server_configuration_error", "error_description": "Firebase Web API Key not configured"},
                status_code=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        FIREBASE_WEB_API_KEY = cfg.firebase_web_api_key

        async with httpx.AsyncClient() as client:
            firebase_auth_response = await client.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_WEB_API_KEY}",
                json={
                    "postBody": f"id_token={id_token}&providerId=google.com",
                    "requestUri": "http://localhost",
                    "returnSecureToken": True
                }
            )

        if firebase_auth_response.status_code != 200:
            logger.error(f"Firebase Auth exchange failed: {firebase_auth_response.status_code}")
            logger.error(f"Response: {firebase_auth_response.text}")
            delete_auth_code_data(code)
            return JSONResponse(
                {
                    "error": "invalid_grant",
                    "error_description": f"Firebase Auth exchange failed: {firebase_auth_response.text}"
                },
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        firebase_data = firebase_auth_response.json()
        firebase_id_token = firebase_data.get("idToken")

        if not firebase_id_token:
            logger.error("No Firebase ID token in response")
            delete_auth_code_data(code)
            return JSONResponse(
                {
                    "error": "invalid_grant",
                    "error_description": "No Firebase ID token returned"
                },
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Delete authorization code (one-time use)
        delete_auth_code_data(code)

        logger.info("Successfully exchanged for Firebase ID token")

        # Return Firebase ID token to ChatGPT
        return JSONResponse(
            {
                "access_token": firebase_id_token,
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-store",
                "Pragma": "no-cache"
            }
        )

    except ValueError as e:
        logger.error(f"Token exchange failed: {str(e)}")
        delete_auth_code_data(code)
        return JSONResponse(
            {
                "error": "invalid_grant",
                "error_description": str(e)
            },
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Unexpected error in token exchange: {str(e)}", exc_info=True)
        delete_auth_code_data(code)
        return JSONResponse(
            {
                "error": "server_error",
                "error_description": "An unexpected error occurred during token exchange"
            },
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )


@mcp.custom_route("/oauth/callback", methods=["GET", "OPTIONS"])
async def oauth_callback(request):
    """
    OAuth callback endpoint - receives authorization code from Google and redirects to client.

    This endpoint receives the callback from Google after user authentication:
    1. Receives authorization code from Google
    2. Generates a temporary authorization code for the client
    3. Stores the mapping (temp_code → google_code + code_verifier)
    4. Redirects to client's original redirect_uri with temp_code
    """
    from starlette.responses import JSONResponse, RedirectResponse
    from .utils.pkce import get_pkce_state, delete_pkce_state, store_auth_code_data
    import secrets

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    cfg = get_config()

    # Get callback parameters from Google
    google_code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    # Check for authorization errors
    if error:
        error_description = request.query_params.get("error_description", "Unknown error")
        logger.error(f"OAuth authorization error from Google: {error} - {error_description}")

        # Get original redirect_uri from state to redirect back with error
        pkce_state = get_pkce_state(state) if state else None
        if pkce_state and pkce_state.get("redirect_uri"):
            from urllib.parse import urlencode
            error_params = urlencode({
                "error": error,
                "error_description": error_description,
                "state": pkce_state.get("client_state", "")
            })
            return RedirectResponse(url=f"{pkce_state['redirect_uri']}?{error_params}")

        return JSONResponse(
            {
                "error": error,
                "error_description": error_description
            },
            status_code=400
        )

    if not google_code or not state:
        logger.error("OAuth callback missing code or state parameter")
        return JSONResponse(
            {
                "error": "invalid_request",
                "error_description": "Missing code or state parameter"
            },
            status_code=400
        )

    # Verify state and retrieve PKCE state
    pkce_state = get_pkce_state(state)
    if not pkce_state:
        logger.error(f"Invalid or expired state parameter: {state[:10]}...")
        return JSONResponse(
            {
                "error": "invalid_grant",
                "error_description": "Invalid or expired state parameter"
            },
            status_code=400
        )

    code_verifier = pkce_state["code_verifier"]
    client_redirect_uri = pkce_state["redirect_uri"]
    client_state = pkce_state.get("client_state", "")

    # Generate a temporary authorization code for the client
    temp_code = secrets.token_urlsafe(32)

    # Store the mapping: temp_code → (google_code, code_verifier, redirect_uri)
    # CRITICAL: Store the exact redirect_uri we used with Google for token exchange
    base_url = cfg.mcp_server_url.removesuffix('/mcp').rstrip('/')
    our_callback_url = f"{base_url}/oauth/callback"

    store_auth_code_data(temp_code, {
        "google_code": google_code,
        "code_verifier": code_verifier,
        "google_redirect_uri": our_callback_url  # Must match exactly in token exchange
    })

    # Delete the PKCE state (no longer needed)
    delete_pkce_state(state)

    logger.info(f"Generated temp code for client redirect: {temp_code[:10]}...")

    # Redirect to client's original redirect_uri with temp code and state
    from urllib.parse import urlencode
    params = {"code": temp_code}
    if client_state:
        params["state"] = client_state

    redirect_url = f"{client_redirect_uri}?{urlencode(params)}"
    logger.info(f"Redirecting to client: {client_redirect_uri}")

    return RedirectResponse(url=redirect_url, status_code=302)


# OAuth 2.1 Protected Resource Metadata endpoints (RFC 9728)
# MCP clients probe these endpoints to discover OAuth support

# Primary MCP-specific endpoint (checked first by MCP clients)
@mcp.custom_route("/.well-known/oauth-protected-resource/mcp", methods=["GET", "OPTIONS"])
async def oauth_metadata_mcp(request):
    """
    MCP-specific OAuth 2.0 Protected Resource Metadata endpoint.

    This is the PRIMARY endpoint that MCP clients check first.
    Returns metadata about this protected resource and its authorization servers.
    """
    from starlette.responses import JSONResponse

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    cfg = get_config()

    # Only serve metadata if OAuth is enabled
    if not should_use_oauth(cfg):
        return JSONResponse(
            {"error": "OAuth not enabled"},
            status_code=404
        )

    # Return Protected Resource Metadata with CORS headers
    metadata = get_oauth_metadata(cfg)
    logger.info("OAuth metadata requested (MCP endpoint) - returning Protected Resource Metadata")

    return JSONResponse(
        metadata,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )


# Fallback generic endpoint (checked if MCP-specific endpoint not found)
@mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET", "OPTIONS"])
async def oauth_metadata(request):
    """
    Generic OAuth 2.0 Protected Resource Metadata endpoint (RFC 9728).

    This is the FALLBACK endpoint if the MCP-specific one isn't found.
    Returns metadata about this protected resource and its authorization servers.
    """
    from starlette.responses import JSONResponse

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return JSONResponse(
            {},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    cfg = get_config()

    # Only serve metadata if OAuth is enabled
    if not should_use_oauth(cfg):
        return JSONResponse(
            {"error": "OAuth not enabled"},
            status_code=404
        )

    # Return Protected Resource Metadata with CORS headers
    metadata = get_oauth_metadata(cfg)
    logger.info("OAuth metadata requested (generic endpoint) - returning Protected Resource Metadata")

    return JSONResponse(
        metadata,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )


def main():
    """Run the MCP server."""
    try:
        # Load and validate configuration
        cfg = get_config()
        logger.info(f"Starting Profitelligence MCP Server")
        logger.info(f"Mode: {cfg.mcp_mode}")
        logger.info(f"API Base URL: {cfg.api_base_url}")

        # Download OAuth credentials from S3 if in OAuth mode
        import os
        if cfg.auth_method == 'oauth':
            env = os.environ.get('ENVIRONMENT', 'dev')

            # Skip S3 downloads for local Docker testing (files are already mounted)
            if env == 'local':
                logger.info("Running in local environment - skipping S3 downloads (files are mounted)")
                logger.info("  Firebase service account: Mounted from volume")
                logger.info("  OAuth client config: Mounted from volume")
            else:
                try:
                    import boto3
                    s3 = boto3.client('s3')

                    # Download Firebase service account key
                    if cfg.firebase_service_account_key_path:
                        s3_key = f"mcp/{env}/firebase-service-account.json"
                        local_path = cfg.firebase_service_account_key_path

                        logger.info(f"Downloading Firebase service account key from S3...")
                        logger.info(f"  S3: s3://profitelligence-cicd/{s3_key}")
                        logger.info(f"  Local: {local_path}")

                        s3.download_file('profitelligence-cicd', s3_key, local_path)
                        logger.info("  ✓ Firebase service account key downloaded successfully")

                    # Download OAuth client config (contains client_id and client_secret)
                    if cfg.oauth_client_config_path:
                        s3_key = f"mcp/{env}/client-config.json"
                        local_path = cfg.oauth_client_config_path

                        logger.info(f"Downloading OAuth client config from S3...")
                        logger.info(f"  S3: s3://profitelligence-cicd/{s3_key}")
                        logger.info(f"  Local: {local_path}")

                        s3.download_file('profitelligence-cicd', s3_key, local_path)
                        logger.info("  ✓ OAuth client config downloaded successfully")

                        # Re-load config to trigger the model_validator that reads from the JSON file
                        logger.info("Re-loading config to parse OAuth credentials from file...")
                        from .utils.config import load_config
                        global config
                        config = None  # Clear cached config
                        cfg = get_config()  # Reload with file now present
                        logger.info(f"  ✓ OAuth client_id loaded: {cfg.oauth_client_id[:40] if cfg.oauth_client_id else 'NOT LOADED'}...")
                        logger.info(f"  ✓ OAuth client_secret loaded: {'YES' if cfg.oauth_client_secret else 'NO'}")

                except Exception as e:
                    logger.error(f"✗ Failed to download OAuth credentials from S3: {e}")
                    raise ValueError(f"Failed to download OAuth credentials from S3: {e}")

        # Log authentication method
        logger.info(f"Authentication Method: {cfg.auth_method}")

        if cfg.auth_method == 'both':
            logger.info("   Supports BOTH authentication methods:")
            logger.info("   1️⃣  API Key Authentication:")
            if cfg.api_key:
                logger.info(f"      - Default API Key: {cfg.api_key[:15]}... (masked)")
            else:
                logger.info("      - API Key: Not set (users provide per-request)")
            logger.info("      - Via: X-API-Key header, apiKey query param, or Authorization: ApiKey")

            logger.info("   2️⃣  OAuth 2.1 Authentication: ENABLED ✅")
            logger.info(f"      - Client ID: {cfg.oauth_client_id}")
            logger.info(f"      - Authorization Server: {cfg.oauth_issuer}")
            logger.info(f"      - Metadata: /.well-known/oauth-protected-resource")
            logger.info("      - Via: Authorization: Bearer <token>")
            logger.info("   → Server auto-detects which method client is using")

        elif cfg.auth_method == 'api_key':
            if cfg.api_key:
                logger.info(f"   API Key: {cfg.api_key[:15]}... (masked)")
            else:
                logger.info("   API Key: Not set (users provide keys in requests)")

        elif cfg.auth_method == 'oauth':
            logger.info("   OAuth 2.1: ENABLED ✅")
            logger.info(f"   Client ID: {cfg.oauth_client_id}")
            logger.info(f"   Authorization Server: {cfg.oauth_issuer}")
            logger.info(f"   Protected Resource: {cfg.api_base_url}")
            logger.info(f"   Metadata Endpoint: /.well-known/oauth-protected-resource")
            logger.info("   → Claude Desktop will auto-discover client ID from metadata")

        elif cfg.auth_method == 'firebase_jwt':
            # Legacy Phase 1 support
            if cfg.firebase_id_token:
                logger.info(f"   Firebase ID Token: {cfg.firebase_id_token[:20]}... (masked, expires ~1hr)")
            elif cfg.firebase_refresh_token:
                logger.info(f"   Firebase Refresh Token: {cfg.firebase_refresh_token[:20]}... (masked)")
            else:
                logger.info("   Firebase Token: Not set (legacy mode)")

        logger.info(f"Web Search: {'enabled' if cfg.enable_web_search else 'disabled'}")

        # Run FastMCP server
        if cfg.mcp_mode == "stdio":
            logger.info("Running in stdio mode (for Claude Desktop)")
            mcp.run()
        else:
            logger.info(f"Running in HTTP mode on {cfg.mcp_host}:{cfg.mcp_port}")

            # Apply OAuth middleware for HTTP mode
            if should_use_oauth(cfg):
                logger.info("   → Applying OAuth middleware (401 responses for authentication)")

                # Create HTTP app with OAuth middleware
                import uvicorn
                from starlette.middleware import Middleware

                # Get base http app from FastMCP
                http_app = mcp.http_app()

                # Wrap with OAuth middleware
                app = OAuthMiddleware(http_app)

                # Run with uvicorn
                uvicorn.run(app, host=cfg.mcp_host, port=cfg.mcp_port)
            else:
                # No OAuth, run normally
                mcp.run(transport="streamable-http", host=cfg.mcp_host, port=cfg.mcp_port)

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        print(f"ERROR: {str(e)}")
        print("\nAuthentication:")
        print("  PROF_AUTH_METHOD - Authentication method: 'api_key', 'oauth', or 'firebase_jwt' (default: api_key)")
        print("\nOption 1 - API Key (for MCP multitenancy):")
        print("  PROF_API_KEY - OPTIONAL - Your Profitelligence API key (pk_live_... or pk_test_...)")
        print("  Note: Users typically provide API keys per-request via headers/query params")
        print("\nOption 2 - OAuth 2.1 (for Claude Desktop):")
        print("  PROF_AUTH_METHOD=oauth - Enable OAuth 2.1 authentication")
        print("  Claude Desktop will auto-discover and handle OAuth flow")
        print("\nOption 3 - Firebase JWT (legacy):")
        print("  PROF_FIREBASE_ID_TOKEN - Firebase ID token (get from firebase.auth().currentUser.getIdToken())")
        print("  PROF_FIREBASE_REFRESH_TOKEN - Firebase refresh token (optional, for future auto-refresh)")
        print("\nOptional environment variables:")
        print("  PROF_API_BASE_URL - API base URL (default: https://apollo.profitelligence.com)")
        print("  PROF_MCP_MODE - Transport mode: stdio or http (default: stdio)")
        print("  PROF_MCP_PORT - HTTP port when using http mode (default: 3000)")
        print("  PROF_ENABLE_WEB_SEARCH - Enable web search tool (default: true)")
        exit(1)

    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        print(f"ERROR: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
