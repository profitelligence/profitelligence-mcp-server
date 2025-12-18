"""
Tests for service_info capability.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

from src.capabilities.service_info import (
    get_service_info,
    _get_overview_info,
    _get_pricing_info,
    _get_capabilities_info,
    _get_status_info,
    _get_profile_info,
    _get_upgrade_benefits
)


class TestGetServiceInfo:
    """Test the main get_service_info function."""

    def test_returns_overview_by_default(self, mock_config):
        """Test that overview is returned by default."""
        result = get_service_info()

        parsed = json.loads(result)
        assert "service" in parsed
        assert parsed["service"] == "Profitelligence MCP Server"
        assert "tools" in parsed

    def test_returns_pricing_info(self, mock_config):
        """Test pricing info type."""
        result = get_service_info(info_type="pricing")

        parsed = json.loads(result)
        assert "pricing" in parsed
        assert "tiers" in parsed["pricing"]
        assert "foundation" in parsed["pricing"]["tiers"]
        assert "pro" in parsed["pricing"]["tiers"]
        assert "elite" in parsed["pricing"]["tiers"]

    def test_returns_capabilities_info(self, mock_config):
        """Test capabilities info type."""
        result = get_service_info(info_type="capabilities")

        parsed = json.loads(result)
        assert "tools" in parsed
        assert "pulse" in parsed["tools"]
        assert "investigate" in parsed["tools"]
        assert "data_sources" in parsed

    def test_returns_status_info(self, mock_config):
        """Test status info type."""
        result = get_service_info(info_type="status")

        parsed = json.loads(result)
        assert "status" in parsed
        assert parsed["status"] == "operational"
        assert "configuration" in parsed
        assert "health" in parsed

    def test_returns_profile_info(self, mock_config):
        """Test profile info type calls API."""
        mock_response = {
            "email": "test@example.com",
            "subscription_tier": "pro",
            "available_features": ["feature1", "feature2"],
            "feature_version": "main",
            "account_status": "active"
        }

        with patch('src.capabilities.service_info.create_client_from_config') as mock_create:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_create.return_value = mock_client

            result = get_service_info(info_type="profile")

        parsed = json.loads(result)
        assert "profile" in parsed
        assert "subscription" in parsed
        assert parsed["subscription"]["tier"] == "pro"

    def test_handles_profile_api_error(self, mock_config):
        """Test profile returns error info on API failure."""
        with patch('src.capabilities.service_info.create_client_from_config') as mock_create:
            mock_create.side_effect = Exception("API connection failed")

            result = get_service_info(info_type="profile")

        parsed = json.loads(result)
        assert "error" in parsed
        assert "Unable to retrieve profile" in parsed["error"]

    def test_handles_unknown_info_type(self, mock_config):
        """Test unknown info_type falls back to overview."""
        result = get_service_info(info_type="unknown_type")

        parsed = json.loads(result)
        # Should fall back to overview (else branch)
        assert "service" in parsed


class TestOverviewInfo:
    """Test _get_overview_info helper."""

    def test_contains_required_fields(self, mock_config):
        """Test overview has all required fields."""
        from src.utils.config import get_config
        cfg = get_config()

        result = _get_overview_info(cfg)

        assert result["service"] == "Profitelligence MCP Server"
        assert "version" in result
        assert "description" in result
        assert "tools" in result
        assert "documentation" in result
        assert "support" in result

    def test_lists_all_tools(self, mock_config):
        """Test overview lists all MCP tools."""
        from src.utils.config import get_config
        cfg = get_config()

        result = _get_overview_info(cfg)

        expected_tools = {"pulse", "investigate", "screen", "assess", "institutional", "search"}
        assert expected_tools == set(result["tools"].keys())


class TestPricingInfo:
    """Test _get_pricing_info helper."""

    def test_contains_all_tiers(self):
        """Test pricing info has all subscription tiers."""
        result = _get_pricing_info()

        tiers = result["pricing"]["tiers"]
        assert "foundation" in tiers
        assert "pro" in tiers
        assert "elite" in tiers

    def test_foundation_tier_is_free(self):
        """Test foundation tier is free."""
        result = _get_pricing_info()

        foundation = result["pricing"]["tiers"]["foundation"]
        assert foundation["price"] == "Free"

    def test_pro_tier_has_early_price(self):
        """Test pro tier has early bird pricing."""
        result = _get_pricing_info()

        pro = result["pricing"]["tiers"]["pro"]
        assert "early_price" in pro
        assert pro["recommended"] is True

    def test_contains_early_user_offer(self):
        """Test pricing includes early user offer details."""
        result = _get_pricing_info()

        assert "early_user_offer" in result["pricing"]
        assert result["pricing"]["early_user_offer"]["active"] is True


class TestCapabilitiesInfo:
    """Test _get_capabilities_info helper."""

    def test_lists_all_tools_with_details(self):
        """Test capabilities info has details for all tools."""
        result = _get_capabilities_info()

        tools = result["tools"]
        for tool_name in ["pulse", "investigate", "screen", "assess", "institutional", "search"]:
            assert tool_name in tools
            assert "description" in tools[tool_name]
            assert "returns" in tools[tool_name]

    def test_tools_have_examples(self):
        """Test tools include usage examples."""
        result = _get_capabilities_info()

        # Most tools should have examples
        assert "example" in result["tools"]["pulse"] or "examples" in result["tools"]["pulse"]
        assert "examples" in result["tools"]["investigate"]

    def test_lists_data_sources(self):
        """Test capabilities info lists data sources."""
        result = _get_capabilities_info()

        assert "data_sources" in result
        assert "8k_filings" in result["data_sources"]
        assert "form4_insider" in result["data_sources"]
        assert "13f_institutional" in result["data_sources"]


class TestStatusInfo:
    """Test _get_status_info helper."""

    def test_shows_operational_status(self, mock_config):
        """Test status shows operational by default."""
        from src.utils.config import get_config
        cfg = get_config()

        result = _get_status_info(cfg)

        assert result["status"] == "operational"

    def test_shows_configuration(self, mock_config):
        """Test status includes configuration details."""
        from src.utils.config import get_config
        cfg = get_config()

        result = _get_status_info(cfg)

        assert "configuration" in result
        assert "api_base_url" in result["configuration"]
        assert "mode" in result["configuration"]

    def test_shows_api_key_masked(self, mock_config):
        """Test API key is masked in status."""
        from src.utils.config import get_config
        cfg = get_config()

        result = _get_status_info(cfg)

        assert "api_key" in result
        if result["api_key"]["configured"]:
            assert "..." in result["api_key"]["masked"]

    def test_shows_health_status(self, mock_config):
        """Test status includes health info."""
        from src.utils.config import get_config
        cfg = get_config()

        result = _get_status_info(cfg)

        assert "health" in result
        assert result["health"]["server"] == "healthy"


class TestProfileInfo:
    """Test _get_profile_info helper."""

    def test_parses_api_response_correctly(self, mock_config):
        """Test profile correctly parses API response."""
        from src.utils.config import get_config
        cfg = get_config()

        mock_response = {
            "email": "user@example.com",
            "subscription_tier": "elite",
            "available_features": ["feature1", "feature2", "feature3"],
            "feature_version": "beta",
            "account_status": "active",
            "signup_date": "2024-01-15",
            "last_login_at": "2024-06-01",
            "verified_legal_documents": True
        }

        with patch('src.capabilities.service_info.create_client_from_config') as mock_create:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_create.return_value = mock_client

            result = _get_profile_info(cfg, ctx=None)

        assert result["profile"]["email"] == "user@example.com"
        assert result["subscription"]["tier"] == "elite"
        assert result["subscription"]["feature_count"] == 3
        assert result["access"]["verified_account"] is True

    def test_handles_free_tier(self, mock_config):
        """Test profile handles free tier correctly."""
        from src.utils.config import get_config
        cfg = get_config()

        mock_response = {
            "subscription_tier": "free",
            "available_features": []
        }

        with patch('src.capabilities.service_info.create_client_from_config') as mock_create:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_create.return_value = mock_client

            result = _get_profile_info(cfg, ctx=None)

        assert result["subscription"]["tier"] == "free"
        assert result["upgrade"]["can_upgrade"] is True

    def test_elite_cannot_upgrade(self, mock_config):
        """Test elite tier shows cannot upgrade."""
        from src.utils.config import get_config
        cfg = get_config()

        mock_response = {
            "subscription_tier": "elite",
            "available_features": []
        }

        with patch('src.capabilities.service_info.create_client_from_config') as mock_create:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_create.return_value = mock_client

            result = _get_profile_info(cfg, ctx=None)

        assert result["upgrade"]["can_upgrade"] is False


class TestUpgradeBenefits:
    """Test _get_upgrade_benefits helper."""

    def test_free_tier_benefits(self):
        """Test upgrade benefits for free tier."""
        benefits = _get_upgrade_benefits("free")

        assert len(benefits) > 0
        assert any("AI opportunity" in b for b in benefits)
        assert any("6,000" in b for b in benefits)

    def test_pro_tier_benefits(self):
        """Test upgrade benefits for pro tier."""
        benefits = _get_upgrade_benefits("pro")

        assert len(benefits) > 0
        assert any("Custom" in b or "Dedicated" in b for b in benefits)

    def test_elite_tier_message(self):
        """Test elite tier has full access message."""
        benefits = _get_upgrade_benefits("elite")

        assert "full access" in benefits[0].lower()
