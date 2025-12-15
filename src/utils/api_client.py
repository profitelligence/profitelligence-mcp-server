"""
HTTP client for Profitelligence API.

Handles authentication, retries, and error handling.
"""
import httpx
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ProfitelligenceAPIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class APIClient:
    """HTTP client for Profitelligence API."""

    def __init__(
        self,
        api_key: str = None,
        firebase_token: str = None,
        oauth_token: str = None,
        auth_method: str = 'api_key',
        base_url: str = "https://apollo.profitelligence.com"
    ):
        """
        Initialize API client with credentials.

        Args:
            api_key: Profitelligence API key (pk_live_... or pk_test_...)
            firebase_token: Firebase ID token (for firebase_jwt auth)
            oauth_token: OAuth Bearer token (for oauth auth)
            auth_method: Authentication method ('api_key', 'oauth', or 'firebase_jwt')
            base_url: Base URL for API (default: apollo.profitelligence.com)
        """
        # Validate authentication method
        if auth_method not in ('api_key', 'oauth', 'firebase_jwt'):
            raise ValueError("auth_method must be 'api_key', 'oauth', or 'firebase_jwt'")

        # Set up authorization header based on method
        if auth_method == 'api_key':
            if not api_key:
                raise ValueError("API key is required for api_key authentication")
            if not (api_key.startswith('pk_live_') or api_key.startswith('pk_test_')):
                raise ValueError("API key must start with 'pk_live_' or 'pk_test_'")
            auth_header = f"ApiKey {api_key}"
            self.api_key = api_key
            logger.debug(f"Using API key authentication: {api_key[:15]}...")

        elif auth_method == 'oauth':
            if not oauth_token:
                raise ValueError("OAuth token is required for oauth authentication")
            auth_header = f"Bearer {oauth_token}"
            self.api_key = None
            logger.debug("Using OAuth 2.1 Bearer token authentication")

        else:  # firebase_jwt
            if not firebase_token:
                raise ValueError("Firebase token is required for firebase_jwt authentication")
            auth_header = f"Bearer {firebase_token}"
            self.api_key = None
            logger.debug("Using Firebase JWT authentication")

        self.base_url = base_url.rstrip('/')
        self.auth_method = auth_method
        self.firebase_token = firebase_token

        # Create httpx client with sensible defaults
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            follow_redirects=True,
            headers={
                "Authorization": auth_header,
                "User-Agent": "Profitelligence-MCP/0.1.0",
            }
        )

        logger.debug(f"API client initialized for {self.base_url} using {auth_method}")

    def _parse_response(self, response: httpx.Response) -> Any:
        """
        Parse API response and handle errors.

        Args:
            response: httpx Response object

        Returns:
            Parsed response data (dict, list, or str)

        Raises:
            ProfitelligenceAPIError: If response indicates an error
        """
        # Check for HTTP errors
        if response.status_code >= 400:
            error_msg = f"API request failed with status {response.status_code}"

            # Try to parse error body
            try:
                error_body = response.json()
                if isinstance(error_body, dict):
                    # Extract error message if available
                    if 'error' in error_body:
                        error_msg = f"{error_msg}: {error_body.get('error')}"
                    if 'message' in error_body:
                        error_msg = f"{error_msg} - {error_body.get('message')}"
            except Exception:
                error_body = response.text

            logger.error(f"{error_msg}\nBody: {error_body}")
            raise ProfitelligenceAPIError(
                message=error_msg,
                status_code=response.status_code,
                response_body=str(error_body)
            )

        # Parse successful response
        content_type = response.headers.get('content-type', '')

        if 'application/json' in content_type:
            return response.json()
        elif 'text/csv' in content_type:
            return response.text
        else:
            return response.text

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make GET request to API.

        Args:
            path: API endpoint path (e.g., "/v1/company-profile")
            params: Query parameters (optional)

        Returns:
            Parsed response data

        Raises:
            ProfitelligenceAPIError: If request fails
        """
        try:
            logger.debug(f"GET {path} with params: {params}")
            response = self.client.get(path, params=params)
            return self._parse_response(response)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during GET {path}: {str(e)}")
            raise ProfitelligenceAPIError(f"HTTP error: {str(e)}")

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make POST request to API.

        Args:
            path: API endpoint path
            json: JSON request body (optional)

        Returns:
            Parsed response data

        Raises:
            ProfitelligenceAPIError: If request fails
        """
        try:
            logger.debug(f"POST {path} with body: {json}")
            response = self.client.post(path, json=json)
            return self._parse_response(response)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during POST {path}: {str(e)}")
            raise ProfitelligenceAPIError(f"HTTP error: {str(e)}")

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_client(
    api_key: str = None,
    firebase_token: str = None,
    oauth_token: str = None,
    auth_method: str = 'api_key',
    base_url: str = "https://apollo.profitelligence.com"
) -> APIClient:
    """
    Create a new API client instance for a specific user.

    Args:
        api_key: User's Profitelligence API key (for api_key auth)
        firebase_token: Firebase ID token (for firebase_jwt auth)
        oauth_token: OAuth Bearer token (for oauth auth)
        auth_method: Authentication method ('api_key', 'oauth', or 'firebase_jwt')
        base_url: API base URL (default: apollo.profitelligence.com)

    Returns:
        Configured APIClient instance

    Raises:
        ValueError: If authentication credentials are invalid
    """
    return APIClient(
        api_key=api_key,
        firebase_token=firebase_token,
        oauth_token=oauth_token,
        auth_method=auth_method,
        base_url=base_url
    )


def create_client_from_config(config, ctx=None) -> APIClient:
    """
    Create API client using configuration and optional context.

    This is a convenience function that handles all authentication methods
    automatically based on the config.

    Args:
        config: Config object with auth settings
        ctx: Optional FastMCP context (for per-request auth)

    Returns:
        Configured APIClient instance

    Example:
        cfg = get_config()
        client = create_client_from_config(cfg)
    """
    if config.auth_method == 'api_key':
        # API key authentication - extract from context (query params, headers, etc.)
        from .auth import get_api_key_from_context
        api_key = get_api_key_from_context(ctx)

        return create_client(
            api_key=api_key,
            auth_method='api_key',
            base_url=config.api_base_url
        )

    elif config.auth_method == 'oauth':
        # OAuth 2.1 authentication - extract Bearer token from context
        # The token is actually a Firebase ID token (from our OAuth → Firebase exchange)
        from .auth import get_credentials_from_context

        auth_method, oauth_token = get_credentials_from_context(ctx)

        if auth_method != 'oauth':
            raise ValueError("OAuth mode configured but no OAuth token found in context")

        # The OAuth token is actually a Firebase ID token from our token exchange
        # So we need to use firebase_jwt auth method for the backend API
        return create_client(
            firebase_token=oauth_token,
            auth_method='firebase_jwt',
            base_url=config.api_base_url
        )

    else:  # firebase_jwt
        # Firebase JWT authentication
        firebase_token = config.firebase_id_token
        if ctx and hasattr(ctx, 'firebase_token') and ctx.firebase_token:
            # Override with context-provided token (for multi-user scenarios)
            firebase_token = ctx.firebase_token

        if not firebase_token:
            raise ValueError(
                "Firebase ID token not configured. "
                "Set PROF_FIREBASE_ID_TOKEN environment variable."
            )

        return create_client(
            firebase_token=firebase_token,
            auth_method='firebase_jwt',
            base_url=config.api_base_url
        )
