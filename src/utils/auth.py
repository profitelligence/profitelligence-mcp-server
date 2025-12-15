"""
Authentication utilities for MCP server.

Handles credential extraction from various sources (context, headers, query params).
Supports API key, OAuth, and Firebase JWT authentication methods.
"""
import logging
from typing import Optional, Tuple
from fastmcp import Context
from .config import get_config

logger = logging.getLogger(__name__)


def _get_http_request():
    """
    Get HTTP request from FastMCP's request context.

    FastMCP provides get_http_request() as a standalone dependency function,
    NOT a method on the Context object.
    """
    try:
        from fastmcp.server.dependencies import get_http_request
        return get_http_request()
    except Exception as e:
        logger.debug(f"Could not get HTTP request: {e}")
        return None


def get_credentials_from_context(ctx: Optional[Context] = None) -> Tuple[str, str]:
    """
    Extract credentials from FastMCP context based on configured auth method.

    Returns appropriate credentials for the configured authentication method:
    - api_key: Returns ('api_key', pk_live_xxx or pk_test_xxx)
    - oauth: Returns ('oauth', bearer_token)
    - both: Auto-detects - Bearer token → oauth, otherwise → api_key
    - firebase_jwt: Returns ('firebase_jwt', firebase_token)

    Args:
        ctx: FastMCP context (optional)

    Returns:
        Tuple of (auth_method, credential)

    Raises:
        ValueError: If no credentials are found
    """
    cfg = get_config()

    # Both mode - auto-detect based on what's provided
    if cfg.auth_method == 'both':
        http_req = _get_http_request()
        if http_req:
            auth_header = getattr(http_req, 'headers', {}).get("authorization")
            # If Bearer token present, use OAuth
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                logger.debug("Auto-detected OAuth Bearer token")
                return ('oauth', token)

        # Otherwise try API key
        try:
            api_key = get_api_key_from_context(ctx)
            logger.debug("Auto-detected API key authentication")
            return ('api_key', api_key)
        except ValueError:
            raise ValueError(
                "No credentials provided. Provide either:\n"
                "- Authorization: Bearer <token> for OAuth\n"
                "- X-API-Key header or apiKey query param for API key"
            )

    # OAuth mode - extract Bearer token
    elif cfg.auth_method == 'oauth':
        http_req = _get_http_request()
        if http_req:
            auth_header = getattr(http_req, 'headers', {}).get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix
                logger.debug("OAuth Bearer token found in Authorization header")
                return ('oauth', token)

        raise ValueError(
            "No OAuth token provided. "
            "OAuth mode requires Authorization: Bearer <token> header."
        )

    # API key mode - extract API key
    elif cfg.auth_method == 'api_key':
        api_key = get_api_key_from_context(ctx)
        return ('api_key', api_key)

    # Firebase JWT mode - extract Firebase token
    else:  # firebase_jwt
        http_req = _get_http_request()
        if http_req:
            auth_header = getattr(http_req, 'headers', {}).get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                logger.debug("Firebase JWT found in Authorization header")
                return ('firebase_jwt', token)

        # Fall back to config
        if cfg.firebase_id_token:
            logger.debug("Firebase JWT found in config")
            return ('firebase_jwt', cfg.firebase_id_token)

        raise ValueError(
            "No Firebase token provided. "
            "Set PROF_FIREBASE_ID_TOKEN or provide Authorization: Bearer <token> header."
        )


def get_api_key_from_context(ctx: Optional[Context] = None) -> str:
    """
    Extract API key from FastMCP context or config.

    Priority order:
    1. HTTP query parameters (apiKey or api_key)
    2. HTTP headers (x-api-key)
    3. HTTP Authorization header (ApiKey or Bearer)
    4. Config file (PROF_API_KEY environment variable)

    Args:
        ctx: FastMCP context (optional)

    Returns:
        API key string

    Raises:
        ValueError: If no API key is found in any source
    """
    # Try to extract from HTTP request context
    http_req = _get_http_request()
    if http_req:
        # 1. Check query parameters
        query_params = getattr(http_req, 'query_params', {})
        if query_params:
            api_key_from_query = (
                query_params.get("apiKey") or
                query_params.get("api_key")
            )
            if api_key_from_query:
                logger.debug("API key found in query parameters")
                return api_key_from_query

        # 2. Check x-api-key header
        headers = getattr(http_req, 'headers', {})
        api_key = headers.get("x-api-key")
        if api_key:
            logger.debug("API key found in x-api-key header")
            return api_key

        # 3. Check Authorization header
        auth_header = headers.get("authorization")
        if auth_header:
            if auth_header.startswith("ApiKey "):
                logger.debug("API key found in Authorization header (ApiKey)")
                return auth_header[7:]
            elif auth_header.startswith("Bearer "):
                logger.debug("API key found in Authorization header (Bearer)")
                return auth_header[7:]
            else:
                logger.debug("API key found in Authorization header (raw)")
                return auth_header

    raise ValueError("No API key provided. Set X-API-Key header or apiKey query parameter.")
