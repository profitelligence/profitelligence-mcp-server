"""
OAuth 2.1 authentication support for Profitelligence MCP Server.

Implements MCP authorization specification using Firebase Auth as the
authorization server, following RFC 9728 (Protected Resource Metadata).

Note: This is a simplified implementation that provides OAuth discovery
via the metadata endpoint. Token validation is handled by the backend API.
"""
import logging
from typing import Dict, Any
from .config import Config

logger = logging.getLogger(__name__)


def get_oauth_metadata(config: Config) -> Dict[str, Any]:
    """
    Get OAuth 2.0 Protected Resource Metadata (RFC 9728).

    This metadata tells OAuth clients (like Claude Desktop) where to
    get access tokens and what scopes are supported.

    Implements MCP OAuth 2.1 specification requirements:
    - RFC 9728 Protected Resource Metadata format
    - RFC 8414 Authorization Server Metadata format
    - PKCE support indication (OAuth 2.1 requirement)
    - Client credentials configuration

    Args:
        config: Server configuration with OAuth settings

    Returns:
        Dictionary containing RFC 9728 Protected Resource Metadata
    """
    # Build RFC 8414 compliant authorization server metadata
    # MCP spec requires complete authorization server metadata, not just URLs
    # NOTE: Claude Desktop expects the MCP server to BE the authorization server,
    # so we use the MCP server URL + /authorize endpoint (which proxies to Google)

    # Derive base URL from mcp_server_url (remove /mcp suffix if present)
    # Use proper URL parsing to avoid bugs with rstrip
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(config.mcp_server_url)
    path = parsed.path.rstrip('/')
    if path.endswith('/mcp'):
        path = path[:-4]  # Remove '/mcp' suffix
    base_url = urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))

    auth_server = {
        "issuer": base_url,  # WE are the authorization server (proxying to Google)
        "authorization_endpoint": f"{base_url}/authorize",  # MCP server proxies to Google
        "token_endpoint": f"{base_url}/oauth/token",  # MCP server exchanges with Google internally
        "jwks_uri": config.oauth_jwks_uri,  # Google's JWKS for token validation

        # Required OAuth 2.1 fields
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],  # PKCE required
        "token_endpoint_auth_methods_supported": ["none"],  # Public client (no client secret)

        # Supported scopes
        "scopes_supported": ["openid", "email", "profile"],

        # Additional OAuth metadata
        "response_modes_supported": ["query"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
    }

    # Build protected resource metadata (RFC 9728)
    metadata = {
        "resource": config.mcp_server_url,  # The MCP server URL (configurable via PROF_MCP_SERVER_URL)
        "authorization_servers": [auth_server],
        "scopes_supported": ["openid", "email", "profile"],
        "bearer_methods_supported": ["header"],
        "resource_documentation": "https://profitelligence.com/docs/api/authentication"
    }

    # Add client_id at TOP LEVEL (per MCP spec, not nested in auth_server)
    # When client_id is provided, Claude Desktop uses it directly (no DCR needed)
    if config.oauth_client_id:
        metadata["client_id"] = config.oauth_client_id
        logger.debug(f"Including pre-registered client_id in metadata: {config.oauth_client_id}")

    return metadata


def should_use_oauth(config: Config) -> bool:
    """
    Determine if OAuth should be enabled based on configuration.

    Args:
        config: Server configuration

    Returns:
        True if OAuth is enabled (oauth or both mode), False otherwise
    """
    return config.oauth_enabled and config.auth_method in ('oauth', 'both')
