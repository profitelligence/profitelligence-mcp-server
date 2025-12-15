<p align="center">
  <img src="assets/logo.png" alt="Profitelligence" width="200" />
</p>

<h1 align="center">Profitelligence MCP Server</h1>

<p align="center">

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Docker](https://img.shields.io/badge/docker-profitelligence%2Fmcp--server-blue.svg)](https://hub.docker.com/r/profitelligence/mcp-server)

**Financial intelligence for AI agents.** Give Claude access to insider trading data, SEC filings, economic indicators, and multi-signal analysis — all through a single MCP server.

[Get Started Free](https://profitelligence.com) · [View Pricing](https://profitelligence.com/pricing)

---

## Why Profitelligence?

Traditional financial APIs return mountains of raw data. Your AI agent burns through tokens parsing CSVs, making repeated calls, and piecing together context. **Profitelligence is different.**

We provide **semantically dense, LLM-optimized responses** designed for AI agents:

| Traditional MCP Servers | Profitelligence MCP |
|------------------------|---------------------|
| Many narrow tools (10-20+) | **5 powerful tools** with rich filtering |
| Raw data dumps | **Pre-contextualized intelligence** |
| Multiple calls to answer one question | **One call, complete answer** |
| Token-heavy responses | **Optimized for token efficiency** |
| Complex tool orchestration | **Agent has full control** |

### What You Get

- **Insider Trading Intelligence** — Form 4 filings with entity search ("find Warren Buffett's trades")
- **SEC Filing Analysis** — AI-summarized 8-K events with impact scoring
- **Market Data** — Company profiles, OHLC prices, sector/industry context
- **Economic Indicators** — Federal Reserve (FRED) data for macro context
- **Multi-Signal Analysis** — Opportunity scoring that combines insider activity + SEC events + price action (PRO)

### Safe by Design

This MCP server is a **thin, stateless layer** over Profitelligence's REST APIs:

- ✅ **Read-only** — No ability to modify your account or execute trades
- ✅ **No data storage** — Responses flow through, nothing is cached locally
- ✅ **Open source** — Audit the code yourself, it's ~2000 lines of Python
- ✅ **Your API key** — You control access; revoke anytime from your dashboard

---

## Quick Start

### 1. Create a Free Account

Sign up at **[profitelligence.com](https://profitelligence.com)** — no credit card required.

The free tier includes:
- Access to top 500 stocks by volume
- Insider trading data (Form 4)
- SEC 8-K filing summaries
- Economic indicators (FRED)
- 250 API calls/day

### 2. Get Your API Key

Generate an API key from your [account dashboard](https://profitelligence.com/account/api-keys).

### 3. Add to Claude

**Claude Code (one-liner):**
```bash
claude mcp add profitelligence --transport http \
  https://mcp.profitelligence.com/mcp \
  --header "X-API-Key: YOUR_API_KEY"
```

**Claude Desktop** (add to `~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "profitelligence": {
      "url": "https://mcp.profitelligence.com/mcp",
      "transport": "streamable-http",
      "headers": {
        "X-API-Key": "YOUR_API_KEY"
      }
    }
  }
}
```

That's it! Ask Claude: *"What insider buying happened in tech stocks this week?"*

---

## Pricing & Tiers

| Feature | Free | PRO ($4.99/mo) | Elite ($9.99/mo) |
|---------|------|----------------|------------------|
| Stock coverage | Top 500 | Top 6,000 | All stocks |
| API calls | 250/day | 1,000/day | 10,000/day |
| Insider trading (Form 4) | ✅ | ✅ | ✅ |
| SEC 8-K summaries | ✅ | ✅ | ✅ |
| Economic indicators | ✅ | ✅ | ✅ |
| Opportunity scoring | — | ✅ | ✅ |
| Multi-signal analysis | — | ✅ | ✅ |
| Alert subscriptions | — | 10 alerts | Unlimited |
| Priority support | — | — | ✅ |

**Early adopter pricing** — $4.99/mo PRO and $9.99/mo Elite rates are locked in for the first 1,000 users (regular: $10/mo and $29/mo). [Upgrade anytime](https://profitelligence.com/pricing).

---

## Available Tools

7 tools designed for maximum token efficiency. Each answers complete questions with rich, contextual responses:

| Tool | Purpose | Example Query |
|------|---------|---------------|
| `pulse()` | Market snapshot | "What's happening in the market right now?" |
| `investigate(subject)` | Deep research | "Tell me about NVDA's insider activity" |
| `screen(focus)` | Opportunity scanning | "Find tech stocks with insider buying" |
| `assess(symbol)` | Position health check | "How is my AAPL position doing?" |
| `institutional(query_type)` | 13F intelligence | "What is Berkshire buying?" |
| `search(q)` | Semantic search | "Find CEO resignation filings" |
| `service_info()` | Account & service info | "What's my subscription tier?" |

---

## Tool Reference

Understanding **when** to use each tool is key to getting the best results. Here's the mental model:

### `pulse()` — What's happening right now?

**Use when:** User wants a market overview without a specific company in mind.

**Returns:** Market movers, recent high-impact 8-K filings, notable insider trades, key economic indicators.

**No parameters.** Just call it.

```
pulse()
```

**Best for:** Starting a session, getting oriented, "what should I look at today?"

---

### `investigate(subject)` — Deep dive on a specific entity

**Use when:** User names a specific company, insider, or sector they want to research.

**Auto-detects entity type:**
- Stock symbols (`AAPL`, `NVDA`) → Company research
- CIK numbers (`0001067983`) → Insider research
- Sector names (`Technology`) → Sector analysis

**Returns for companies:**
- Profile, price history, material events (8-K filings)
- Insider intelligence (Form 4 summary + recent transactions)
- Financials (income statement, balance sheet, cash flow from 10-K/10-Q)
- Opportunity signals, technical indicators

```
investigate("AAPL")                           # Company
investigate("0001067983")                     # Warren Buffett by CIK
investigate("Technology", entity_type="sector")  # Sector
```

**Best for:** "Tell me about X", "What's going on with X?", research before a decision.

---

### `screen(focus)` — Find opportunities across the market

**Use when:** User wants to discover stocks matching certain criteria, not research a specific one.

**Parameters:**
- `focus`: What signal to screen for
  - `"all"` — Everything (default)
  - `"multi_signal"` — Stocks with multiple confirming signals
  - `"insider"` — Insider buying clusters
  - `"events"` — High-impact 8-K filings
- `sector`: Filter to a sector (e.g., `"Technology"`)
- `min_score`: Minimum opportunity score (0-100)
- `days`: Lookback period (default 7)
- `limit`: Max results (default 25)

```
screen()                                    # Everything
screen(focus="insider", sector="Technology") # Tech insider buying
screen(focus="events", days=14)             # Recent material events
```

**Best for:** "What opportunities are out there?", "Find me stocks where insiders are buying."

---

### `assess(symbol)` — Health check for a position you own

**Use when:** User owns a stock and wants to evaluate whether to hold, add, or sell.

**Returns:**
- Current price action and technical signals
- Recent material events (8-K filings)
- Insider sentiment (are insiders buying or selling?)
- Institutional sentiment (13F accumulation/distribution)
- Financials snapshot
- Risk factors

```
assess("NVDA")
assess("AAPL", days=90)  # Longer lookback
```

**Best for:** Portfolio review, "How's my position in X?", "Should I be worried about X?"

---

### `institutional(query_type)` — 13F institutional investor intelligence

**Use when:** User wants to know what big money is doing.

**Query types:**
- `"manager"` — Profile a specific fund (by name or CIK)
- `"security"` — Who owns a specific stock?
- `"signal"` — Find stocks with institutional flow patterns

**Signal types** (for `query_type="signal"`):
- `"accumulation"` — Stocks institutions are buying
- `"distribution"` — Stocks institutions are selling
- `"conviction"` — High conviction positions (5%+ of portfolio)
- `"new"` — Fresh institutional positions

```
institutional("manager", identifier="Citadel")     # What does Citadel own?
institutional("security", identifier="NVDA")       # Who owns NVIDIA?
institutional("signal", signal_type="accumulation") # Smart money buying
```

**Best for:** "What is Berkshire buying?", "Who owns NVDA?", "Follow the smart money."

---

### `search(q)` — Find anything across the platform

**Use when:** User is looking for something specific but doesn't know where it is.

**Searches across:**
- SEC 8-K filings (with LLM-extracted insights)
- Companies (by name or symbol)
- Insiders (executives, directors)
- Institutional managers (13F filers)

**Parameters:**
- `q`: Search query (min 2 chars)
- `entity_type`: Filter results — `"filing"`, `"company"`, `"insider"`, `"manager"`
- `sector`: Filter by sector
- `impact`: Filter filings by impact level — `"HIGH"`, `"MEDIUM"`, `"LOW"`
- `limit`: Max results (default 20, max 100)

```
search("CEO resignation")                           # Find CEO departure filings
search("NVIDIA", entity_type="company")             # Find NVIDIA
search("Buffett", entity_type="insider")            # Find Warren Buffett
search("activist", entity_type="manager")           # Find activist funds
search("acquisition", sector="Technology", impact="HIGH")  # High-impact tech M&A
```

**Best for:** "Find filings about X", "Search for Y", discovery when you're not sure where to look.

---

### `service_info(info_type)` — Account and service information

**Use when:** User asks about their subscription, features, or the service itself.

**Info types:**
- `"overview"` — Service description and capabilities (default)
- `"profile"` — User's subscription tier, features, account status
- `"pricing"` — Subscription tiers and pricing
- `"capabilities"` — Available tools and data sources
- `"status"` — Server health and configuration

```
service_info()            # Overview
service_info("profile")   # Your account
service_info("pricing")   # Pricing info
```

**Best for:** "What can you do?", "What's my tier?", "How much does PRO cost?"

---

## Tool Selection Guide

| User Intent | Tool |
|-------------|------|
| "What's happening?" / "Market overview" | `pulse()` |
| "Tell me about [company/insider/sector]" | `investigate()` |
| "Find stocks where..." / "What opportunities..." | `screen()` |
| "How's my [position]?" / "Should I worry about..." | `assess()` |
| "What is [fund] buying?" / "Who owns [stock]?" | `institutional()` |
| "Search for..." / "Find filings about..." | `search()` |
| "What's my tier?" / "What can you do?" | `service_info()` |

---

### MCP Prompts

Pre-built research workflows that produce complete reports:

- `insider_activity_report` — Insider trading analysis for a symbol
- `sec_filing_intelligence_report` — 8-K filing analysis
- `macro_market_conditions_report` — Economic backdrop
- `influential_investor_research` — Smart money deep dive
- `sector_opportunity_scan` — Multi-signal sector analysis
- `quarterly_stock_checkup` — Portfolio position review

---

## Self-Hosting (Optional)

> **Most users don't need this.** The hosted version at `mcp.profitelligence.com` is free, fast, and requires zero setup. Just add your API key and go (see [Quick Start](#quick-start) above).

This repo exists so you can:
- **Audit the code** — See exactly what runs when you use our MCP server
- **Self-host for privacy** — Run your own instance if you prefer
- **Customize** — Fork and add your own tools

### When to Self-Host

| Use Case | Recommendation |
|----------|----------------|
| Just want financial intelligence in Claude | **Use hosted** — it's free |
| Want to audit what code is running | Read this repo, use hosted |
| Need custom web search privacy | Self-host with your own Brave API key |
| Building on top of our tools | Fork and extend |

### Docker Hub

We publish multi-arch images (amd64 + arm64) to Docker Hub:

```bash
docker pull profitelligence/mcp-server:latest
```

**Run in stdio mode** (for Claude Desktop):
```bash
docker run -i --rm \
  -e PROF_API_KEY=pk_live_xxx \
  profitelligence/mcp-server:latest
```

**Run in HTTP mode** (for development/testing):
```bash
docker run -d -p 3000:3000 \
  -e PROF_API_KEY=pk_live_xxx \
  -e PROF_MCP_MODE=http \
  profitelligence/mcp-server:latest
```

### From Source

```bash
git clone https://github.com/profitelligence/profitelligence-mcp-server.git
cd profitelligence-mcp-server
pip install -e .
PROF_API_KEY=pk_live_xxx python -m src.server
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PROF_API_KEY` | Yes | Your API key from [profitelligence.com](https://profitelligence.com/account/api-keys) |
| `PROF_MCP_MODE` | No | `stdio` (default) or `http` |
| `PROF_MCP_PORT` | No | HTTP port (default: 3000) |
| `BRAVE_API_KEY` | No | Your Brave Search key for web search privacy |

### Web Search Privacy

The hosted version uses our shared infrastructure. When self-hosting, you can provide your own [Brave Search API key](https://brave.com/search/api/) (2,000 free queries/month):

- ✅ Your search queries go directly to Brave
- ✅ We never see what you're searching for
- ✅ Falls back to DuckDuckGo if no key provided

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

---

## Support

- Issues: [GitHub Issues](https://github.com/profitelligence/profitelligence-mcp-server/issues)
- Contact: [profitelligence.com/contact](https://profitelligence.com/contact)
- Email: support@profitelligence.com

## License

MIT License - See [LICENSE](LICENSE) for details.
