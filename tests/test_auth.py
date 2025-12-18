"""
Tests for authentication utilities.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.utils.auth import get_credentials_from_context, get_api_key_from_context


class TestGetApiKeyFromContext:
    """Test API key extraction from various sources."""

    def test_extracts_api_key_from_query_params_apiKey(self, mock_http_request):
        """Test extraction from ?apiKey=xxx query param."""
        mock_request = mock_http_request(query_params={"apiKey": "pk_test_from_query"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            result = get_api_key_from_context(None)

        assert result == "pk_test_from_query"

    def test_extracts_api_key_from_query_params_api_key(self, mock_http_request):
        """Test extraction from ?api_key=xxx query param (snake_case)."""
        mock_request = mock_http_request(query_params={"api_key": "pk_test_snake_case"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            result = get_api_key_from_context(None)

        assert result == "pk_test_snake_case"

    def test_extracts_api_key_from_x_api_key_header(self, mock_http_request):
        """Test extraction from X-API-Key header."""
        mock_request = mock_http_request(headers={"x-api-key": "pk_live_from_header"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            result = get_api_key_from_context(None)

        assert result == "pk_live_from_header"

    def test_extracts_api_key_from_authorization_apikey(self, mock_http_request):
        """Test extraction from Authorization: ApiKey xxx header."""
        mock_request = mock_http_request(headers={"authorization": "ApiKey pk_test_auth_header"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            result = get_api_key_from_context(None)

        assert result == "pk_test_auth_header"

    def test_extracts_api_key_from_authorization_bearer(self, mock_http_request):
        """Test extraction from Authorization: Bearer xxx header."""
        mock_request = mock_http_request(headers={"authorization": "Bearer pk_test_bearer"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            result = get_api_key_from_context(None)

        assert result == "pk_test_bearer"

    def test_query_params_take_priority_over_headers(self, mock_http_request):
        """Test that query params are checked before headers."""
        mock_request = mock_http_request(
            query_params={"apiKey": "pk_test_query_wins"},
            headers={"x-api-key": "pk_test_header_loses"}
        )

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            result = get_api_key_from_context(None)

        assert result == "pk_test_query_wins"

    def test_raises_when_no_api_key_found(self, mock_http_request):
        """Test ValueError when no API key in any source."""
        mock_request = mock_http_request()

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            with pytest.raises(ValueError, match="No API key provided"):
                get_api_key_from_context(None)

    def test_raises_when_no_http_request(self):
        """Test ValueError when HTTP request context unavailable."""
        with patch('src.utils.auth._get_http_request', return_value=None):
            with pytest.raises(ValueError, match="No API key provided"):
                get_api_key_from_context(None)


class TestGetCredentialsFromContext:
    """Test credential extraction based on auth method."""

    def test_api_key_mode_returns_api_key(self, reset_config, monkeypatch, mock_http_request):
        """Test api_key auth method returns API key credentials."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "api_key")
        monkeypatch.setenv("PROF_API_KEY", "pk_test_unused")

        mock_request = mock_http_request(headers={"x-api-key": "pk_test_extracted"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            auth_method, credential = get_credentials_from_context(None)

        assert auth_method == "api_key"
        assert credential == "pk_test_extracted"

    def test_oauth_mode_extracts_bearer_token(self, reset_config, monkeypatch, mock_http_request):
        """Test oauth auth method extracts Bearer token."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "oauth")
        monkeypatch.setenv("PROF_OAUTH_CLIENT_ID", "test-client")

        mock_request = mock_http_request(headers={"authorization": "Bearer oauth_token_abc123"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            auth_method, credential = get_credentials_from_context(None)

        assert auth_method == "oauth"
        assert credential == "oauth_token_abc123"

    def test_oauth_mode_raises_without_bearer_token(self, reset_config, monkeypatch, mock_http_request):
        """Test oauth mode raises when no Bearer token present."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "oauth")
        monkeypatch.setenv("PROF_OAUTH_CLIENT_ID", "test-client")

        mock_request = mock_http_request()

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            with pytest.raises(ValueError, match="No OAuth token provided"):
                get_credentials_from_context(None)

    def test_firebase_jwt_mode_extracts_bearer_token(self, reset_config, monkeypatch, mock_http_request):
        """Test firebase_jwt mode extracts Bearer token from header."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "firebase_jwt")
        monkeypatch.setenv("PROF_FIREBASE_ID_TOKEN", "config_token")

        mock_request = mock_http_request(headers={"authorization": "Bearer header_firebase_token"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            auth_method, credential = get_credentials_from_context(None)

        assert auth_method == "firebase_jwt"
        assert credential == "header_firebase_token"

    def test_firebase_jwt_mode_falls_back_to_config(self, reset_config, monkeypatch, mock_http_request):
        """Test firebase_jwt mode uses config token when header absent."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "firebase_jwt")
        monkeypatch.setenv("PROF_FIREBASE_ID_TOKEN", "config_firebase_token")

        mock_request = mock_http_request()

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            auth_method, credential = get_credentials_from_context(None)

        assert auth_method == "firebase_jwt"
        assert credential == "config_firebase_token"

    def test_firebase_jwt_mode_raises_without_token(self, reset_config, monkeypatch, mock_http_request):
        """Test firebase_jwt mode raises when no token available."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "firebase_jwt")
        monkeypatch.delenv("PROF_FIREBASE_ID_TOKEN", raising=False)
        # Need a refresh token to pass config validation
        monkeypatch.setenv("PROF_FIREBASE_REFRESH_TOKEN", "temp")

        # Force config reload and clear the token
        cfg = reset_config.get_config()
        cfg.firebase_id_token = None

        mock_request = mock_http_request()

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            with pytest.raises(ValueError, match="No Firebase token provided"):
                get_credentials_from_context(None)

    def test_both_mode_prefers_bearer_token(self, reset_config, monkeypatch, mock_http_request):
        """Test 'both' mode uses OAuth when Bearer token present."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "both")

        mock_request = mock_http_request(
            query_params={"apiKey": "pk_test_api_key"},
            headers={"authorization": "Bearer oauth_wins"}
        )

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            auth_method, credential = get_credentials_from_context(None)

        assert auth_method == "oauth"
        assert credential == "oauth_wins"

    def test_both_mode_falls_back_to_api_key(self, reset_config, monkeypatch, mock_http_request):
        """Test 'both' mode uses API key when no Bearer token."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "both")

        mock_request = mock_http_request(query_params={"apiKey": "pk_test_fallback"})

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            auth_method, credential = get_credentials_from_context(None)

        assert auth_method == "api_key"
        assert credential == "pk_test_fallback"

    def test_both_mode_raises_when_no_credentials(self, reset_config, monkeypatch, mock_http_request):
        """Test 'both' mode raises when neither credential type present."""
        monkeypatch.setenv("PROF_AUTH_METHOD", "both")

        mock_request = mock_http_request()

        with patch('src.utils.auth._get_http_request', return_value=mock_request):
            with pytest.raises(ValueError, match="No credentials provided"):
                get_credentials_from_context(None)


class TestGetHttpRequest:
    """Test HTTP request extraction from FastMCP context."""

    def test_returns_none_when_get_http_request_raises(self):
        """Test graceful handling when get_http_request raises."""
        from src.utils.auth import _get_http_request

        # Mock the fastmcp import to raise an exception
        with patch.dict('sys.modules', {'fastmcp.server.dependencies': MagicMock()}):
            with patch('fastmcp.server.dependencies.get_http_request', side_effect=Exception("Not in request context")):
                result = _get_http_request()
                # The function catches exceptions and returns None
                assert result is None
