"""
Tests for the API client.
"""
import pytest
import httpx
import respx
from unittest.mock import patch, MagicMock

from src.utils.api_client import APIClient, ProfitelligenceAPIError, create_client


class TestAPIClientInit:
    """Test APIClient initialization."""

    def test_init_with_api_key(self, test_api_key, base_url):
        """Test client initialization with API key."""
        client = APIClient(
            api_key=test_api_key,
            auth_method="api_key",
            base_url=base_url
        )

        assert client.api_key == test_api_key
        assert client.auth_method == "api_key"
        assert client.base_url == base_url
        client.close()

    def test_init_with_live_api_key(self, test_live_api_key, base_url):
        """Test client initialization with live API key."""
        client = APIClient(
            api_key=test_live_api_key,
            auth_method="api_key",
            base_url=base_url
        )

        assert client.api_key == test_live_api_key
        client.close()

    def test_init_with_firebase_token(self, test_firebase_token, base_url):
        """Test client initialization with Firebase token."""
        client = APIClient(
            firebase_token=test_firebase_token,
            auth_method="firebase_jwt",
            base_url=base_url
        )

        assert client.firebase_token == test_firebase_token
        assert client.auth_method == "firebase_jwt"
        client.close()

    def test_init_with_oauth_token(self, test_oauth_token, base_url):
        """Test client initialization with OAuth token."""
        client = APIClient(
            oauth_token=test_oauth_token,
            auth_method="oauth",
            base_url=base_url
        )

        assert client.auth_method == "oauth"
        client.close()

    def test_init_requires_api_key_for_api_key_auth(self, base_url):
        """Test that api_key auth requires an API key."""
        with pytest.raises(ValueError, match="API key is required"):
            APIClient(auth_method="api_key", base_url=base_url)

    def test_init_requires_firebase_token_for_firebase_jwt_auth(self, base_url):
        """Test that firebase_jwt auth requires a token."""
        with pytest.raises(ValueError, match="Firebase token is required"):
            APIClient(auth_method="firebase_jwt", base_url=base_url)

    def test_init_requires_oauth_token_for_oauth_auth(self, base_url):
        """Test that oauth auth requires a token."""
        with pytest.raises(ValueError, match="OAuth token is required"):
            APIClient(auth_method="oauth", base_url=base_url)

    def test_init_rejects_invalid_auth_method(self, test_api_key, base_url):
        """Test that invalid auth method is rejected."""
        with pytest.raises(ValueError, match="auth_method must be"):
            APIClient(
                api_key=test_api_key,
                auth_method="invalid",
                base_url=base_url
            )

    def test_init_validates_api_key_format(self, base_url):
        """Test that API key format is validated."""
        with pytest.raises(ValueError, match="API key must start with"):
            APIClient(
                api_key="invalid_key",
                auth_method="api_key",
                base_url=base_url
            )

    def test_init_strips_trailing_slash_from_base_url(self, test_api_key):
        """Test that trailing slash is removed from base URL."""
        client = APIClient(
            api_key=test_api_key,
            auth_method="api_key",
            base_url="https://api.example.com/"
        )

        assert client.base_url == "https://api.example.com"
        client.close()


class TestAPIClientGet:
    """Test APIClient GET requests."""

    def test_get_success(self, api_client, mock_api, pulse_response):
        """Test successful GET request."""
        mock_api.get("/v1/mcp-pulse").mock(
            return_value=httpx.Response(200, json=pulse_response)
        )

        result = api_client.get("/v1/mcp-pulse")

        assert result == pulse_response
        assert mock_api.calls.called

    def test_get_with_params(self, api_client, mock_api, investigate_response):
        """Test GET request with query parameters."""
        mock_api.get("/v1/mcp-investigate").mock(
            return_value=httpx.Response(200, json=investigate_response)
        )

        result = api_client.get("/v1/mcp-investigate", params={"subject": "AAPL", "days": 30})

        assert result == investigate_response
        assert "subject=AAPL" in str(mock_api.calls.last.request.url)

    def test_get_returns_text_for_csv(self, api_client, mock_api):
        """Test GET returns text for CSV content type."""
        csv_data = "symbol,price\nAAPL,195.50\nTSLA,250.00"
        mock_api.get("/v1/export").mock(
            return_value=httpx.Response(
                200,
                text=csv_data,
                headers={"content-type": "text/csv"}
            )
        )

        result = api_client.get("/v1/export")

        assert result == csv_data

    def test_get_handles_404(self, api_client, mock_api):
        """Test GET handles 404 error."""
        mock_api.get("/v1/not-found").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )

        with pytest.raises(ProfitelligenceAPIError) as exc_info:
            api_client.get("/v1/not-found")

        assert exc_info.value.status_code == 404
        assert "Not found" in exc_info.value.message

    def test_get_handles_401_unauthorized(self, api_client, mock_api):
        """Test GET handles 401 unauthorized error."""
        mock_api.get("/v1/protected").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized", "message": "Invalid API key"})
        )

        with pytest.raises(ProfitelligenceAPIError) as exc_info:
            api_client.get("/v1/protected")

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message

    def test_get_handles_500_server_error(self, api_client, mock_api):
        """Test GET handles 500 server error."""
        mock_api.get("/v1/error").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        with pytest.raises(ProfitelligenceAPIError) as exc_info:
            api_client.get("/v1/error")

        assert exc_info.value.status_code == 500

    def test_get_handles_network_error(self, api_client, mock_api):
        """Test GET handles network errors."""
        mock_api.get("/v1/timeout").mock(side_effect=httpx.ConnectError("Connection refused"))

        with pytest.raises(ProfitelligenceAPIError) as exc_info:
            api_client.get("/v1/timeout")

        assert "HTTP error" in exc_info.value.message


class TestAPIClientPost:
    """Test APIClient POST requests."""

    def test_post_success(self, api_client, mock_api):
        """Test successful POST request."""
        response_data = {"status": "created", "id": "123"}
        mock_api.post("/v1/create").mock(
            return_value=httpx.Response(200, json=response_data)
        )

        result = api_client.post("/v1/create", json={"name": "test"})

        assert result == response_data

    def test_post_handles_400_bad_request(self, api_client, mock_api):
        """Test POST handles 400 bad request."""
        mock_api.post("/v1/create").mock(
            return_value=httpx.Response(400, json={"error": "Bad request", "message": "Invalid parameter"})
        )

        with pytest.raises(ProfitelligenceAPIError) as exc_info:
            api_client.post("/v1/create", json={"invalid": "data"})

        assert exc_info.value.status_code == 400


class TestAPIClientContextManager:
    """Test APIClient context manager protocol."""

    def test_context_manager(self, test_api_key, base_url, mock_api):
        """Test client works as context manager."""
        mock_api.get("/v1/test").mock(return_value=httpx.Response(200, json={}))

        with APIClient(
            api_key=test_api_key,
            auth_method="api_key",
            base_url=base_url
        ) as client:
            result = client.get("/v1/test")
            assert result == {}


class TestCreateClient:
    """Test create_client factory function."""

    def test_create_client_with_api_key(self, test_api_key, base_url):
        """Test creating client with API key."""
        client = create_client(
            api_key=test_api_key,
            auth_method="api_key",
            base_url=base_url
        )

        assert isinstance(client, APIClient)
        assert client.api_key == test_api_key
        client.close()

    def test_create_client_with_firebase_token(self, test_firebase_token, base_url):
        """Test creating client with Firebase token."""
        client = create_client(
            firebase_token=test_firebase_token,
            auth_method="firebase_jwt",
            base_url=base_url
        )

        assert isinstance(client, APIClient)
        assert client.firebase_token == test_firebase_token
        client.close()


class TestProfitelligenceAPIError:
    """Test ProfitelligenceAPIError exception."""

    def test_error_with_all_fields(self):
        """Test error with all fields populated."""
        error = ProfitelligenceAPIError(
            message="Test error",
            status_code=400,
            response_body='{"error": "details"}'
        )

        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.response_body == '{"error": "details"}'
        assert str(error) == "Test error"

    def test_error_with_minimal_fields(self):
        """Test error with only message."""
        error = ProfitelligenceAPIError(message="Minimal error")

        assert error.message == "Minimal error"
        assert error.status_code is None
        assert error.response_body is None
