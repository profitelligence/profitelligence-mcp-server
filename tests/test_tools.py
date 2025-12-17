"""
Tests for MCP tools.
"""
import pytest
import httpx
import respx
from unittest.mock import patch, MagicMock

from src.tools import mcp_tools


class TestPulseTool:
    """Test the pulse() tool."""

    def test_pulse_returns_market_snapshot(self, mock_config, mock_pulse_api, pulse_response):
        """Test pulse returns market data."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = pulse_response
            mock_get_client.return_value = mock_client

            result = mcp_tools.pulse()

            assert result == pulse_response
            mock_client.get.assert_called_once_with("/v1/mcp-pulse")

    def test_pulse_passes_context(self, mock_config):
        """Test pulse passes context to client."""
        mock_ctx = MagicMock()

        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.pulse(ctx=mock_ctx)

            mock_get_client.assert_called_once_with(mock_ctx)


class TestInvestigateTool:
    """Test the investigate() tool."""

    def test_investigate_company(self, mock_config, investigate_response):
        """Test investigating a company by symbol."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = investigate_response
            mock_get_client.return_value = mock_client

            result = mcp_tools.investigate("AAPL")

            assert result == investigate_response
            mock_client.get.assert_called_once_with(
                "/v1/mcp-investigate",
                params={"subject": "AAPL", "days": 30}
            )

    def test_investigate_with_entity_type(self, mock_config):
        """Test investigating with explicit entity type."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.investigate("Technology", entity_type="sector")

            mock_client.get.assert_called_once_with(
                "/v1/mcp-investigate",
                params={"subject": "Technology", "type": "sector", "days": 30}
            )

    def test_investigate_with_custom_days(self, mock_config):
        """Test investigating with custom lookback period."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.investigate("AAPL", days=90)

            mock_client.get.assert_called_once_with(
                "/v1/mcp-investigate",
                params={"subject": "AAPL", "days": 90}
            )

    def test_investigate_insider_by_cik(self, mock_config):
        """Test investigating an insider by CIK."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {"entity_type": "insider"}
            mock_get_client.return_value = mock_client

            result = mcp_tools.investigate("0001067983")

            assert result["entity_type"] == "insider"


class TestScreenTool:
    """Test the screen() tool."""

    def test_screen_default_params(self, mock_config, screen_response):
        """Test screening with default parameters."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = screen_response
            mock_get_client.return_value = mock_client

            result = mcp_tools.screen()

            assert result == screen_response
            mock_client.get.assert_called_once_with(
                "/v1/mcp-screen",
                params={"focus": "all", "days": 7, "limit": 25}
            )

    def test_screen_with_focus(self, mock_config):
        """Test screening with specific focus."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.screen(focus="insider")

            mock_client.get.assert_called_once_with(
                "/v1/mcp-screen",
                params={"focus": "insider", "days": 7, "limit": 25}
            )

    def test_screen_with_sector_filter(self, mock_config):
        """Test screening with sector filter."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.screen(sector="Technology")

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["sector"] == "Technology"

    def test_screen_with_min_score(self, mock_config):
        """Test screening with minimum score."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.screen(min_score=80.0)

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["min_score"] == 80.0


class TestAssessTool:
    """Test the assess() tool."""

    def test_assess_symbol(self, mock_config, assess_response):
        """Test assessing a stock position."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = assess_response
            mock_get_client.return_value = mock_client

            result = mcp_tools.assess("NVDA")

            assert result == assess_response
            mock_client.get.assert_called_once_with(
                "/v1/mcp-assess",
                params={"symbol": "NVDA", "days": 30}
            )

    def test_assess_with_custom_days(self, mock_config):
        """Test assessing with custom lookback period."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.assess("AAPL", days=90)

            mock_client.get.assert_called_once_with(
                "/v1/mcp-assess",
                params={"symbol": "AAPL", "days": 90}
            )


class TestInstitutionalTool:
    """Test the institutional() tool."""

    def test_institutional_manager_query(self, mock_config, institutional_response):
        """Test institutional manager query."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = institutional_response
            mock_get_client.return_value = mock_client

            result = mcp_tools.institutional("manager", identifier="Citadel")

            assert result == institutional_response
            mock_client.get.assert_called_once_with(
                "/v1/mcp-institutional",
                params={"query_type": "manager", "identifier": "Citadel", "limit": 25}
            )

    def test_institutional_security_query(self, mock_config):
        """Test institutional security query."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.institutional("security", identifier="NVDA")

            mock_client.get.assert_called_once_with(
                "/v1/mcp-institutional",
                params={"query_type": "security", "identifier": "NVDA", "limit": 25}
            )

    def test_institutional_signal_query(self, mock_config):
        """Test institutional signal query."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.institutional("signal", signal_type="accumulation")

            mock_client.get.assert_called_once_with(
                "/v1/mcp-institutional",
                params={"query_type": "signal", "signal_type": "accumulation", "limit": 25}
            )

    def test_institutional_with_custom_limit(self, mock_config):
        """Test institutional query with custom limit."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.institutional("manager", identifier="Berkshire", limit=50)

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["limit"] == 50


class TestSearchTool:
    """Test the search() tool."""

    def test_search_basic_query(self, mock_config, search_response):
        """Test basic search query."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = search_response
            mock_get_client.return_value = mock_client

            result = mcp_tools.search("CEO resignation")

            assert result == search_response
            mock_client.get.assert_called_once_with(
                "/v1/search",
                params={"q": "CEO resignation", "limit": 20}
            )

    def test_search_with_entity_type(self, mock_config):
        """Test search with entity type filter."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.search("NVIDIA", entity_type="company")

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["entity_type"] == "company"

    def test_search_with_sector(self, mock_config):
        """Test search with sector filter."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.search("acquisition", sector="Technology")

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["sector"] == "Technology"

    def test_search_with_impact(self, mock_config):
        """Test search with impact filter."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.search("merger", impact="HIGH")

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["impact"] == "HIGH"

    def test_search_with_custom_limit(self, mock_config):
        """Test search with custom limit."""
        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = {}
            mock_get_client.return_value = mock_client

            mcp_tools.search("dividend", limit=50)

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["limit"] == 50


class TestGetClient:
    """Test the _get_client helper."""

    def test_get_client_creates_client_from_config(self, mock_config):
        """Test _get_client creates client using config."""
        with patch('src.tools.mcp_tools.create_client_from_config') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client

            result = mcp_tools._get_client()

            mock_create.assert_called_once()

    def test_get_client_passes_context(self, mock_config):
        """Test _get_client passes context to factory."""
        mock_ctx = MagicMock()

        with patch('src.tools.mcp_tools.create_client_from_config') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client

            mcp_tools._get_client(mock_ctx)

            mock_create.assert_called_once()
            # Context should be passed as second argument
            assert mock_create.call_args[0][1] == mock_ctx
