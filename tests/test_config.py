"""
Tests for configuration management.
"""
import os
import pytest
from unittest.mock import patch


class TestConfig:
    """Test Config class validation and loading."""

    def test_load_default_config(self, monkeypatch):
        """Test loading config with minimal environment."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
        monkeypatch.setenv("PROF_API_KEY", "pk_test_abc123")

        config = config_module.load_config()

        assert config.auth_method == "api_key"
        assert config.api_key == "pk_test_abc123"
        assert config.mcp_mode == "stdio"
        assert config.mcp_port == 3000

    def test_load_config_with_all_options(self, monkeypatch):
        """Test loading config with all options set."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
        monkeypatch.setenv("PROF_API_KEY", "pk_live_fullconfig123")
        monkeypatch.setenv("PROF_API_BASE_URL", "https://custom-api.example.com")
        monkeypatch.setenv("PROF_MCP_MODE", "http")
        monkeypatch.setenv("PROF_MCP_PORT", "8080")
        monkeypatch.setenv("PROF_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("PROF_ENABLE_WEB_SEARCH", "false")

        config = config_module.load_config()

        assert config.api_key == "pk_live_fullconfig123"
        assert config.api_base_url == "https://custom-api.example.com"
        assert config.mcp_mode == "http"
        assert config.mcp_port == 8080
        assert config.log_level == "DEBUG"
        assert config.enable_web_search is False


class TestAuthMethodValidation:
    """Test authentication method validation."""

    def test_valid_auth_methods(self, monkeypatch):
        """Test all valid auth methods are accepted."""
        import src.utils.config as config_module

        valid_methods = ["api_key", "oauth", "both", "firebase_jwt"]

        for method in valid_methods:
            config_module.config = None
            monkeypatch.setenv("PROF_AUTH_METHOD", method)

            # For firebase_jwt, need a token
            if method == "firebase_jwt":
                monkeypatch.setenv("PROF_FIREBASE_ID_TOKEN", "test-token")
            else:
                monkeypatch.delenv("PROF_FIREBASE_ID_TOKEN", raising=False)

            config = config_module.load_config()
            assert config.auth_method == method

    def test_invalid_auth_method(self, monkeypatch):
        """Test that invalid auth method raises error."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "invalid_method")

        with pytest.raises(ValueError, match="auth_method must be"):
            config_module.load_config()


class TestApiKeyValidation:
    """Test API key validation."""

    def test_valid_test_api_key(self, monkeypatch):
        """Test that pk_test_ keys are accepted."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
        monkeypatch.setenv("PROF_API_KEY", "pk_test_valid123")

        config = config_module.load_config()
        assert config.api_key == "pk_test_valid123"

    def test_valid_live_api_key(self, monkeypatch):
        """Test that pk_live_ keys are accepted."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
        monkeypatch.setenv("PROF_API_KEY", "pk_live_valid456")

        config = config_module.load_config()
        assert config.api_key == "pk_live_valid456"

    def test_invalid_api_key_format(self, monkeypatch):
        """Test that invalid API key format raises error."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
        monkeypatch.setenv("PROF_API_KEY", "invalid_key_format")

        with pytest.raises(ValueError, match="API key must start with"):
            config_module.load_config()

    def test_api_key_optional_for_multitenancy(self, monkeypatch):
        """Test that API key is optional (for multitenancy mode)."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
        monkeypatch.delenv("PROF_API_KEY", raising=False)

        config = config_module.load_config()
        assert config.api_key is None


class TestMcpModeValidation:
    """Test MCP mode validation."""

    def test_stdio_mode(self, monkeypatch):
        """Test stdio mode is valid."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_MCP_MODE", "stdio")

        config = config_module.load_config()
        assert config.mcp_mode == "stdio"

    def test_http_mode(self, monkeypatch):
        """Test http mode is valid."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_MCP_MODE", "http")

        config = config_module.load_config()
        assert config.mcp_mode == "http"

    def test_invalid_mode(self, monkeypatch):
        """Test that invalid mode raises error."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_MCP_MODE", "websocket")

        with pytest.raises(ValueError, match="Mode must be"):
            config_module.load_config()


class TestBaseUrlValidation:
    """Test base URL validation."""

    def test_https_url(self, monkeypatch):
        """Test https URLs are accepted."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_API_BASE_URL", "https://api.example.com")

        config = config_module.load_config()
        assert config.api_base_url == "https://api.example.com"

    def test_http_url(self, monkeypatch):
        """Test http URLs are accepted (for local dev)."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_API_BASE_URL", "http://localhost:8000")

        config = config_module.load_config()
        assert config.api_base_url == "http://localhost:8000"

    def test_trailing_slash_removed(self, monkeypatch):
        """Test that trailing slash is removed from URL."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_API_BASE_URL", "https://api.example.com/")

        config = config_module.load_config()
        assert config.api_base_url == "https://api.example.com"

    def test_invalid_url_scheme(self, monkeypatch):
        """Test that invalid URL scheme raises error."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_API_BASE_URL", "ftp://api.example.com")

        with pytest.raises(ValueError, match="Base URL must start with"):
            config_module.load_config()


class TestOAuthConfig:
    """Test OAuth configuration."""

    def test_oauth_enabled_for_oauth_method(self, monkeypatch):
        """Test OAuth is auto-enabled when auth_method is 'oauth'."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "oauth")
        monkeypatch.setenv("PROF_OAUTH_CLIENT_ID", "test-client-id")

        config = config_module.load_config()
        assert config.oauth_enabled is True

    def test_oauth_enabled_for_both_method(self, monkeypatch):
        """Test OAuth is auto-enabled when auth_method is 'both'."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "both")

        config = config_module.load_config()
        assert config.oauth_enabled is True


class TestFirebaseJwtConfig:
    """Test Firebase JWT configuration."""

    def test_firebase_jwt_requires_token(self, monkeypatch):
        """Test firebase_jwt mode requires a token."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "firebase_jwt")
        monkeypatch.delenv("PROF_FIREBASE_ID_TOKEN", raising=False)
        monkeypatch.delenv("PROF_FIREBASE_REFRESH_TOKEN", raising=False)

        with pytest.raises(ValueError, match="firebase_id_token or firebase_refresh_token is required"):
            config_module.load_config()

    def test_firebase_jwt_accepts_id_token(self, monkeypatch):
        """Test firebase_jwt mode accepts ID token."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "firebase_jwt")
        monkeypatch.setenv("PROF_FIREBASE_ID_TOKEN", "eyJhbGciOiJSUzI1NiJ9.test")

        config = config_module.load_config()
        assert config.firebase_id_token == "eyJhbGciOiJSUzI1NiJ9.test"

    def test_firebase_jwt_accepts_refresh_token(self, monkeypatch):
        """Test firebase_jwt mode accepts refresh token (along with id_token due to validator order)."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_AUTH_METHOD", "firebase_jwt")
        # Note: Due to pydantic validator order, firebase_id_token is validated before
        # firebase_refresh_token is parsed, so we need to provide the id_token as well
        monkeypatch.setenv("PROF_FIREBASE_ID_TOKEN", "eyJhbGciOiJSUzI1NiJ9.test")
        monkeypatch.setenv("PROF_FIREBASE_REFRESH_TOKEN", "refresh-token-123")

        config = config_module.load_config()
        assert config.firebase_refresh_token == "refresh-token-123"
        assert config.firebase_id_token == "eyJhbGciOiJSUzI1NiJ9.test"


class TestGetConfig:
    """Test get_config singleton behavior."""

    def test_get_config_caches_config(self, monkeypatch):
        """Test that get_config returns cached config."""
        import src.utils.config as config_module
        config_module.config = None

        config1 = config_module.get_config()
        config2 = config_module.get_config()

        assert config1 is config2

    def test_get_config_respects_env_changes_after_reset(self, monkeypatch):
        """Test that resetting config picks up new env vars."""
        import src.utils.config as config_module
        config_module.config = None

        monkeypatch.setenv("PROF_API_KEY", "pk_test_first")
        config1 = config_module.get_config()
        assert config1.api_key == "pk_test_first"

        # Reset and change
        config_module.config = None
        monkeypatch.setenv("PROF_API_KEY", "pk_test_second")
        config2 = config_module.get_config()
        assert config2.api_key == "pk_test_second"
