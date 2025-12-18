"""
Configuration management for Profitelligence MCP Server.

Loads settings from environment variables with validation.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator, ValidationInfo


class Config(BaseSettings):
    """MCP Server configuration."""

    # Authentication Configuration
    auth_method: str = Field(
        default="api_key",
        description="Authentication method: 'api_key', 'oauth', 'both' (supports both), or 'firebase_jwt' (legacy)"
    )

    # API Key Authentication (traditional method)
    api_key: Optional[str] = Field(
        default=None,
        description="Profitelligence API key (pk_live_... or pk_test_...) - for api_key auth"
    )

    # OAuth 2.1 Configuration
    oauth_enabled: bool = Field(
        default=False,
        description="Enable OAuth 2.1 support (auto-enabled when auth_method is 'oauth')"
    )

    oauth_client_id: Optional[str] = Field(
        default=None,
        description="OAuth client ID for MCP client authentication"
    )

    oauth_client_secret: Optional[str] = Field(
        default=None,
        description="OAuth client secret (optional for public clients with PKCE)"
    )

    oauth_client_config_path: Optional[str] = Field(
        default=None,
        description="Path to OAuth client config JSON file (contains client_id and client_secret)"
    )

    oauth_issuer: str = Field(
        default="https://accounts.google.com",
        description="OAuth authorization server issuer URL (used for metadata discovery)"
    )

    oauth_audience: str = Field(
        default="profitelligence",
        description="OAuth token audience (typically project ID)"
    )

    oauth_jwks_uri: str = Field(
        default="https://www.googleapis.com/oauth2/v3/certs",
        description="JWKS URI for OAuth token validation (Google OAuth keys)"
    )

    oauth_auth_url: str = Field(
        default="https://accounts.google.com/o/oauth2/v2/auth",
        description="OAuth authorization endpoint URL (Google OAuth for Firebase)"
    )

    oauth_token_url: str = Field(
        default="https://oauth2.googleapis.com/token",
        description="OAuth token endpoint URL (Google OAuth token exchange)"
    )

    # Firebase Admin SDK Configuration (for token exchange)
    firebase_service_account_key_path: Optional[str] = Field(
        default=None,
        description="Path to Firebase service account key JSON file"
    )

    firebase_service_account_json: Optional[str] = Field(
        default=None,
        description="Firebase service account key as inline JSON string"
    )

    # Firebase Web API Key (for client-side auth operations)
    # Accepts PROF_FIREBASE_WEB_API_KEY or FIREBASE_WEB_API_KEY (for backward compatibility)
    firebase_web_api_key: Optional[str] = Field(
        default_factory=lambda: os.environ.get('PROF_FIREBASE_WEB_API_KEY') or os.environ.get('FIREBASE_WEB_API_KEY'),
        description="Firebase Web API key for signInWithIdp endpoint"
    )

    # Legacy Firebase JWT support (for backward compatibility)
    firebase_id_token: Optional[str] = Field(
        default=None,
        description="Firebase ID token - legacy manual token auth (Phase 1)"
    )

    firebase_refresh_token: Optional[str] = Field(
        default=None,
        description="Firebase refresh token - legacy manual token auth (Phase 1)"
    )

    # API Configuration
    api_base_url: str = Field(
        default="https://apollo.profitelligence.com",
        description="Base URL for Profitelligence API"
    )

    # MCP Server URL (for OAuth resource field)
    # Should be the full URL to the MCP endpoint (including /mcp path)
    mcp_server_url: str = Field(
        default="https://mcp-dev.profitelligence.com/mcp",
        description="Public URL of this MCP server (used in OAuth metadata)"
    )

    # MCP Configuration
    mcp_mode: str = Field(
        default="stdio",
        description="Transport mode: stdio or http"
    )

    mcp_port: int = Field(
        default=3000,
        description="HTTP port when using http mode"
    )

    mcp_host: str = Field(
        default="0.0.0.0",
        description="HTTP host binding (0.0.0.0 for Docker, 127.0.0.1 for local)"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    # Feature Flags
    enable_web_search: bool = Field(
        default=True,
        description="Enable web search tool (Brave Search API or DuckDuckGo)"
    )

    @model_validator(mode='after')
    def load_oauth_credentials_from_file(self):
        """Load OAuth credentials from JSON file if oauth_client_config_path is provided."""
        import json
        import logging

        logger = logging.getLogger(__name__)

        # Only proceed if config path is provided and client_secret not already set
        if not self.oauth_client_config_path:
            return self

        if self.oauth_client_secret and self.oauth_client_id:
            logger.debug("OAuth credentials already provided via env vars, skipping file load")
            return self

        # Load credentials from JSON file
        if os.path.exists(self.oauth_client_config_path):
            try:
                with open(self.oauth_client_config_path, 'r') as f:
                    config_data = json.load(f)

                    # Support Google OAuth client config format
                    if 'web' in config_data:
                        web_config = config_data['web']

                        # Load client_secret if not already set
                        if not self.oauth_client_secret and 'client_secret' in web_config:
                            self.oauth_client_secret = web_config['client_secret']
                            logger.info(f"✓ Loaded oauth_client_secret from {self.oauth_client_config_path}")

                        # Load client_id if not already set
                        if not self.oauth_client_id and 'client_id' in web_config:
                            self.oauth_client_id = web_config['client_id']
                            logger.info(f"✓ Loaded oauth_client_id from {self.oauth_client_config_path}")

                    # Also support flat format
                    elif 'client_secret' in config_data or 'client_id' in config_data:
                        if not self.oauth_client_secret and 'client_secret' in config_data:
                            self.oauth_client_secret = config_data['client_secret']
                            logger.info(f"✓ Loaded oauth_client_secret from {self.oauth_client_config_path}")

                        if not self.oauth_client_id and 'client_id' in config_data:
                            self.oauth_client_id = config_data['client_id']
                            logger.info(f"✓ Loaded oauth_client_id from {self.oauth_client_config_path}")

            except Exception as e:
                raise ValueError(f"Failed to load OAuth client config from {self.oauth_client_config_path}: {e}")
        else:
            logger.warning(f"OAuth client config file not found: {self.oauth_client_config_path}")

        return self

    @field_validator('auth_method')
    @classmethod
    def validate_auth_method(cls, v: str) -> str:
        """Ensure auth method is valid."""
        if v not in ('api_key', 'oauth', 'both', 'firebase_jwt'):
            raise ValueError("auth_method must be 'api_key', 'oauth', 'both', or 'firebase_jwt'")
        return v

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Ensure API key has correct format if provided."""
        # API key is OPTIONAL in config for multitenancy
        # Users can provide API keys per-request via headers/query params
        # Only validate format if provided
        if v and not (v.startswith('pk_live_') or v.startswith('pk_test_')):
            raise ValueError("API key must start with 'pk_live_' or 'pk_test_'")

        return v

    @field_validator('api_base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Ensure base URL is valid."""
        if not v.startswith('http://') and not v.startswith('https://'):
            raise ValueError("Base URL must start with http:// or https://")

        # Remove trailing slash
        return v.rstrip('/')

    @field_validator('mcp_mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Ensure mode is valid."""
        if v not in ('stdio', 'http'):
            raise ValueError("Mode must be 'stdio' or 'http'")
        return v

    @model_validator(mode='after')
    def set_oauth_enabled_and_validate_firebase(self):
        """Auto-enable OAuth based on auth_method and validate Firebase token."""
        # Enable OAuth for 'oauth' mode or 'both' mode
        if self.auth_method in ('oauth', 'both'):
            self.oauth_enabled = True

        # Validate Firebase token for legacy firebase_jwt auth
        if self.auth_method == 'firebase_jwt':
            if not self.firebase_id_token and not self.firebase_refresh_token:
                raise ValueError(
                    "Either firebase_id_token or firebase_refresh_token is required "
                    "when auth_method is 'firebase_jwt'"
                )

        return self

    model_config = SettingsConfigDict(
        env_prefix="PROF_",
        case_sensitive=False,
    )


def load_config() -> Config:
    """
    Load configuration from environment variables.

    Environment variables:
    Authentication:
    - PROF_AUTH_METHOD: Authentication method ('api_key', 'oauth', or 'firebase_jwt', default: 'api_key')
    - PROF_API_KEY: Your Profitelligence API key (OPTIONAL - users can provide per-request)
    - PROF_FIREBASE_ID_TOKEN: Firebase ID token (required if auth_method='firebase_jwt')
    - PROF_FIREBASE_REFRESH_TOKEN: Firebase refresh token (optional, for future auto-refresh)

    Other configuration:
    - PROF_API_BASE_URL: API base URL (optional, default: https://apollo.profitelligence.com)
    - PROF_MCP_MODE: Transport mode (optional, default: stdio)
    - PROF_MCP_PORT: HTTP port (optional, default: 3000)
    - PROF_LOG_LEVEL: Logging level (optional, default: INFO)
    - PROF_ENABLE_WEB_SEARCH: Enable web search tool (optional, default: true)

    Note:
        For MCP multitenancy, users typically provide API keys per-request via:
        - HTTP query parameter: ?apiKey=pk_live_xxx
        - HTTP header: X-API-Key: pk_live_xxx
        - HTTP header: Authorization: ApiKey pk_live_xxx

    Returns:
        Config: Validated configuration object

    Raises:
        ValueError: If required config is missing or invalid
    """
    try:
        return Config()
    except Exception as e:
        raise ValueError(f"Configuration error: {str(e)}")


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get or initialize global config instance."""
    global config
    if config is None:
        config = load_config()
    return config
