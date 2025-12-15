"""
Service information capability.

Provides information about Profitelligence platform, pricing, capabilities, user profile, and links.
"""
import logging
import json
from typing import Optional
from fastmcp import Context
from ..utils.config import get_config
from ..utils.api_client import create_client_from_config

logger = logging.getLogger(__name__)


def get_service_info(
    info_type: str = "overview",
    ctx: Optional[Context] = None
) -> str:
    """
    Profitelligence service information and help.

    Get information about subscriptions, pricing, capabilities, user profile, and links.

    Args:
        info_type: Type of information requested
            - "overview": General service info and capabilities
            - "pricing": Subscription tiers and pricing
            - "capabilities": Available tools and features
            - "profile": Your user profile (tier, features, account)
            - "status": Service status and configuration
        ctx: FastMCP context (optional)

    Returns:
        JSON with requested service information
    """
    try:
        cfg = get_config()

        if info_type == "pricing":
            result = _get_pricing_info()
        elif info_type == "capabilities":
            result = _get_capabilities_info()
        elif info_type == "profile":
            result = _get_profile_info(cfg, ctx)
        elif info_type == "status":
            result = _get_status_info(cfg)
        else:  # overview
            result = _get_overview_info(cfg)

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Failed to get service info: {e}")
        return json.dumps({
            "info_type": info_type,
            "error": str(e),
            "message": "Failed to retrieve service information"
        }, indent=2)


def _get_overview_info(cfg) -> dict:
    """Get overview information about Profitelligence."""
    return {
        "service": "Profitelligence MCP Server",
        "version": "2.0.0",
        "description": "Model Context Protocol server for SEC filing intelligence, insider trades, and institutional holdings",
        "api_endpoint": cfg.api_base_url,
        "mode": cfg.mcp_mode,
        "tools": {
            "pulse": "Market snapshot - movers, recent filings, insider trades, economic indicators",
            "investigate": "Deep research on company (symbol), insider (CIK), or sector",
            "screen": "Scan market for opportunities - multi-signal, insider buying, material events",
            "assess": "Position health check - events, insider/institutional sentiment, technicals",
            "institutional": "13F institutional holdings - manager profiles, security ownership, flow signals",
            "search": "Semantic search across filings, companies, insiders, and managers"
        },
        "documentation": "https://profitelligence.com/docs",
        "support": "support@profitelligence.com",
        "website": "https://profitelligence.com"
    }


def _get_pricing_info() -> dict:
    """Get pricing and subscription information."""
    return {
        "pricing": {
            "tiers": {
                "foundation": {
                    "price": "Free",
                    "description": "Core intelligence for getting started",
                    "features": [
                        "Top 500 securities by volume",
                        "LLM-powered 8-K summaries (top 500)",
                        "Insider transactions (top 500)",
                        "3 watchlists",
                        "REST API: 100 calls/day (promo)"
                    ]
                },
                "pro": {
                    "price": "$10/month",
                    "early_price": "$4.99/month until Dec 2026",
                    "description": "Full-stack event intelligence",
                    "features": [
                        "6,000+ securities",
                        "Unlimited LLM summaries & insider data",
                        "10Q/10K fundamentals",
                        "10 watchlists",
                        "Alert Manager (10 alerts, email)",
                        "Opportunities Engine (top 500)",
                        "Event Dynamics Engine (top 500)",
                        "13F institutional flow (1 year history)",
                        "REST API: 1,000 calls/day (promo)"
                    ],
                    "recommended": True
                },
                "elite": {
                    "price": "$29/month",
                    "early_price": "$9.99/month until Dec 2026",
                    "description": "Unlimited access & priority features",
                    "features": [
                        "Everything in Pro",
                        "Unlimited securities (all 6,000+)",
                        "Unlimited alerts + SMS delivery",
                        "Unlimited watchlists",
                        "10Q/10K historical downloads",
                        "13F full history (13 years)",
                        "Crowded trades & conviction signals",
                        "Early beta access + priority support",
                        "REST API: 10,000 calls/day (promo)"
                    ]
                }
            },
            "early_user_offer": {
                "active": True,
                "description": "Sign up by April 1, 2026 for discounted pricing until December 31, 2026",
                "pro_price": "$4.99/month",
                "elite_price": "$9.99/month"
            }
        },
        "links": {
            "pricing_page": "https://profitelligence.com/pricing",
            "signup": "https://profitelligence.com/signup"
        },
        "note": "Early user pricing available for first 1,000 users. Visit pricing page for details."
    }


def _get_capabilities_info() -> dict:
    """Get detailed capabilities and tools information."""
    return {
        "tools": {
            "pulse": {
                "description": "Market snapshot - what's happening right now",
                "returns": "Market movers, recent material filings, notable insider trades, economic indicators",
                "parameters": "None required",
                "example": "pulse()"
            },
            "investigate": {
                "description": "Deep research on any entity - company, insider, or sector",
                "returns": "Profile, price history, 8-K filings, insider activity, 13F holdings, financials, technicals",
                "parameters": {
                    "subject": "Symbol (AAPL), CIK (0001067983), or sector name (Technology)",
                    "entity_type": "Optional: 'company', 'insider', or 'sector' (auto-detected)",
                    "days": "Lookback period, default 30"
                },
                "examples": [
                    "investigate('AAPL')",
                    "investigate('0001067983')  # Warren Buffett by CIK",
                    "investigate('Technology', entity_type='sector')"
                ]
            },
            "screen": {
                "description": "Scan market for opportunities across all stocks",
                "returns": "Ranked opportunities by signal type",
                "parameters": {
                    "focus": "'all', 'multi_signal', 'insider', or 'events'",
                    "sector": "Optional sector filter (e.g., 'Technology')",
                    "min_score": "Optional minimum score 0-100",
                    "days": "Lookback period, default 7",
                    "limit": "Max results, default 25"
                },
                "examples": [
                    "screen()",
                    "screen(focus='insider', sector='Technology')",
                    "screen(focus='events', days=14)"
                ]
            },
            "assess": {
                "description": "Position health check - evaluate an existing holding",
                "returns": "Material events, insider sentiment, institutional sentiment, financials, technicals",
                "parameters": {
                    "symbol": "Stock symbol to assess",
                    "days": "Lookback period, default 30"
                },
                "examples": [
                    "assess('NVDA')",
                    "assess('AAPL', days=90)"
                ]
            },
            "institutional": {
                "description": "13F institutional investor intelligence",
                "returns": "Manager profiles, security ownership, flow signals",
                "parameters": {
                    "query_type": "'manager', 'security', or 'signal'",
                    "identifier": "Manager name/CIK or symbol (for manager/security queries)",
                    "signal_type": "'accumulation', 'distribution', 'conviction', 'new' (for signal queries)",
                    "limit": "Max results, default 25"
                },
                "examples": [
                    "institutional('manager', identifier='Citadel')",
                    "institutional('security', identifier='NVDA')",
                    "institutional('signal', signal_type='accumulation')"
                ]
            },
            "search": {
                "description": "Semantic search across the entire platform",
                "returns": "Filings, companies, insiders, institutional managers matching query",
                "parameters": {
                    "q": "Search query (min 2 chars)",
                    "entity_type": "Optional: 'filing', 'company', 'insider', 'manager'",
                    "sector": "Optional sector filter",
                    "impact": "Optional: 'HIGH', 'MEDIUM', 'LOW' (filings only)",
                    "limit": "Max results, default 20"
                },
                "examples": [
                    "search('CEO resignation')",
                    "search('Buffett', entity_type='insider')",
                    "search('acquisition', sector='Technology', impact='HIGH')"
                ]
            }
        },
        "data_sources": {
            "8k_filings": "AI-summarized SEC 8-K material events with impact scoring",
            "form4_insider": "Form 4 insider transactions with cluster detection",
            "13f_institutional": "Quarterly 13F holdings from institutional managers",
            "10k_10q_fundamentals": "Income statement, balance sheet, cash flow from 10-K/10-Q",
            "price_data": "Historical OHLC with volume",
            "company_profiles": "Sector, industry, executives, market cap",
            "fred_economic": "Federal Reserve economic indicators"
        }
    }


def _get_status_info(cfg) -> dict:
    """Get service status and configuration."""
    return {
        "status": "operational",
        "configuration": {
            "api_base_url": cfg.api_base_url,
            "mode": cfg.mcp_mode,
            "port": cfg.mcp_port if cfg.mcp_mode == "http" else None,
            "web_search_enabled": cfg.enable_web_search,
            "log_level": cfg.log_level,
        },
        "api_key": {
            "configured": bool(cfg.api_key),
            "masked": f"{cfg.api_key[:15]}..." if cfg.api_key else None,
            "note": "User-provided API key required for most operations"
        },
        "health": {
            "server": "healthy",
            "api_connectivity": "operational"
        }
    }


def _get_profile_info(cfg, ctx) -> dict:
    """
    Get user profile from the Profitelligence API.

    Calls /user-status endpoint to retrieve:
    - subscription_tier (free/pro/elite)
    - available_features (what features this user can access)
    - feature_version (main/beta)
    - account_status
    """
    try:
        client = create_client_from_config(cfg, ctx)

        # Call the user-status endpoint
        response = client.get("/v1/user-status")

        # Parse response - it may come as JSON or dict
        if isinstance(response, str):
            user_data = json.loads(response)
        else:
            user_data = response

        # Build a clean, LLM-friendly profile response
        tier = user_data.get("subscription_tier", "free")
        features = user_data.get("available_features", [])

        # Tier descriptions
        tier_info = {
            "free": {
                "name": "Free",
                "description": "Basic access to company data and insider trading",
                "symbol_access": "Top 500 by volume"
            },
            "pro": {
                "name": "Pro",
                "description": "Full access including AI opportunity scores",
                "symbol_access": "Top 6,000 by volume"
            },
            "elite": {
                "name": "Elite",
                "description": "Unlimited access with custom integrations",
                "symbol_access": "All symbols"
            }
        }

        return {
            "profile": {
                "email": user_data.get("email"),
                "account_status": user_data.get("account_status", "active"),
                "member_since": user_data.get("signup_date"),
                "last_active": user_data.get("last_login_at")
            },
            "subscription": {
                "tier": tier,
                "tier_details": tier_info.get(tier, tier_info["free"]),
                "feature_version": user_data.get("feature_version", "main"),
                "available_features": features,
                "feature_count": len(features) if features else 0
            },
            "access": {
                "verified_account": user_data.get("verified_legal_documents", False),
                "feature_flags": user_data.get("feature_flags", {})
            },
            "upgrade": {
                "current_tier": tier,
                "can_upgrade": tier != "elite",
                "upgrade_url": "https://profitelligence.com/pricing",
                "benefits": _get_upgrade_benefits(tier)
            }
        }

    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        return {
            "error": "Unable to retrieve profile",
            "message": str(e),
            "note": "Profile requires authentication. Make sure you're authenticated with a valid API key or OAuth token.",
            "help": {
                "api_keys": "https://profitelligence.com/account/api-keys",
                "documentation": "https://profitelligence.com/docs"
            }
        }


def _get_upgrade_benefits(current_tier: str) -> list:
    """Get benefits of upgrading from current tier."""
    if current_tier == "elite":
        return ["You have full access!"]
    elif current_tier == "pro":
        return [
            "Custom data integrations",
            "Dedicated support",
            "SLA guarantees",
            "Team collaboration",
            "Bulk data access"
        ]
    else:  # free
        return [
            "AI opportunity scores with explainability",
            "Multi-signal opportunity scanner",
            "Advanced pattern detection",
            "Access to 6,000+ symbols (vs 500)",
            "Unlimited API calls",
            "Priority support"
        ]
