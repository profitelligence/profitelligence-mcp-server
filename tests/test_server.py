"""
Integration tests for the MCP server.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock


class TestServerInitialization:
    """Test server initialization and configuration."""

    def test_server_imports(self):
        """Test that server module can be imported."""
        from src import server
        assert hasattr(server, 'mcp')

    def test_mcp_instance_created(self):
        """Test that FastMCP instance is created."""
        from src.server import mcp
        assert mcp is not None
        assert mcp.name == "Profitelligence"


class TestToolRegistration:
    """Test that all tools are registered correctly."""

    def test_pulse_tool_registered(self):
        """Test pulse tool is registered."""
        from src.server import mcp

        # Get registered tools
        tools = mcp._tool_manager._tools
        assert "pulse" in tools

    def test_investigate_tool_registered(self):
        """Test investigate tool is registered."""
        from src.server import mcp

        tools = mcp._tool_manager._tools
        assert "investigate" in tools

    def test_screen_tool_registered(self):
        """Test screen tool is registered."""
        from src.server import mcp

        tools = mcp._tool_manager._tools
        assert "screen" in tools

    def test_assess_tool_registered(self):
        """Test assess tool is registered."""
        from src.server import mcp

        tools = mcp._tool_manager._tools
        assert "assess" in tools

    def test_institutional_tool_registered(self):
        """Test institutional tool is registered."""
        from src.server import mcp

        tools = mcp._tool_manager._tools
        assert "institutional" in tools

    def test_search_tool_registered(self):
        """Test search tool is registered."""
        from src.server import mcp

        tools = mcp._tool_manager._tools
        assert "search" in tools

    def test_service_info_tool_registered(self):
        """Test service_info tool is registered."""
        from src.server import mcp

        tools = mcp._tool_manager._tools
        assert "service_info" in tools

    def test_all_seven_tools_registered(self):
        """Test that exactly 7 main MCP tools are registered."""
        from src.server import mcp

        expected_tools = {
            "pulse", "investigate", "screen", "assess",
            "institutional", "search", "service_info"
        }

        tools = mcp._tool_manager._tools
        registered = set(tools.keys())

        # Check our expected tools are present
        assert expected_tools.issubset(registered), \
            f"Missing tools: {expected_tools - registered}"


class TestPromptRegistration:
    """Test that MCP prompts are registered."""

    def test_morning_briefing_prompt_registered(self):
        """Test morning_briefing prompt is registered."""
        from src.server import mcp

        prompts = mcp._prompt_manager._prompts
        assert "morning_briefing" in prompts

    def test_company_intelligence_report_prompt_registered(self):
        """Test company_intelligence_report prompt is registered."""
        from src.server import mcp

        prompts = mcp._prompt_manager._prompts
        assert "company_intelligence_report" in prompts

    def test_position_risk_check_prompt_registered(self):
        """Test position_risk_check prompt is registered."""
        from src.server import mcp

        prompts = mcp._prompt_manager._prompts
        assert "position_risk_check" in prompts

    def test_smart_money_report_prompt_registered(self):
        """Test smart_money_report prompt is registered."""
        from src.server import mcp

        prompts = mcp._prompt_manager._prompts
        assert "smart_money_report" in prompts

    def test_sector_scan_prompt_registered(self):
        """Test sector_scan prompt is registered."""
        from src.server import mcp

        prompts = mcp._prompt_manager._prompts
        assert "sector_scan" in prompts

    def test_insider_deep_dive_prompt_registered(self):
        """Test insider_deep_dive prompt is registered."""
        from src.server import mcp

        prompts = mcp._prompt_manager._prompts
        assert "insider_deep_dive" in prompts


class TestToolExecution:
    """Test tool execution through the MCP server."""

    def test_pulse_tool_returns_json(self, mock_config, pulse_response):
        """Test pulse tool returns JSON-serialized response."""
        from src.server import mcp
        from src.tools import mcp_tools

        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = pulse_response
            mock_get_client.return_value = mock_client

            # Get the tool function
            tool_func = mcp._tool_manager._tools["pulse"].fn

            # Call with mock context
            mock_ctx = MagicMock()
            result = tool_func(mock_ctx)

            # Result should be JSON string
            assert isinstance(result, str)
            parsed = json.loads(result)
            assert parsed == pulse_response

    def test_investigate_tool_returns_json(self, mock_config, investigate_response):
        """Test investigate tool returns JSON-serialized response."""
        from src.server import mcp
        from src.tools import mcp_tools

        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = investigate_response
            mock_get_client.return_value = mock_client

            tool_func = mcp._tool_manager._tools["investigate"].fn

            mock_ctx = MagicMock()
            result = tool_func("AAPL", None, 30, mock_ctx)

            assert isinstance(result, str)
            parsed = json.loads(result)
            assert parsed == investigate_response

    def test_screen_tool_returns_json(self, mock_config, screen_response):
        """Test screen tool returns JSON-serialized response."""
        from src.server import mcp
        from src.tools import mcp_tools

        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = screen_response
            mock_get_client.return_value = mock_client

            tool_func = mcp._tool_manager._tools["screen"].fn

            mock_ctx = MagicMock()
            result = tool_func("all", None, None, 7, 25, mock_ctx)

            assert isinstance(result, str)
            parsed = json.loads(result)
            assert parsed == screen_response


class TestToolDescriptions:
    """Test that tool descriptions are properly set for LLMs."""

    def test_pulse_has_description(self):
        """Test pulse tool has a description."""
        from src.server import mcp

        tool = mcp._tool_manager._tools["pulse"]
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_investigate_has_description(self):
        """Test investigate tool has a description."""
        from src.server import mcp

        tool = mcp._tool_manager._tools["investigate"]
        assert tool.description is not None
        assert "research" in tool.description.lower() or "entity" in tool.description.lower()

    def test_screen_has_description(self):
        """Test screen tool has a description."""
        from src.server import mcp

        tool = mcp._tool_manager._tools["screen"]
        assert tool.description is not None
        assert "scan" in tool.description.lower() or "screen" in tool.description.lower()


class TestErrorHandling:
    """Test error handling in tool execution."""

    def test_tool_handles_api_error(self, mock_config):
        """Test that tools properly propagate API errors."""
        from src.server import mcp
        from src.tools import mcp_tools
        from src.utils.api_client import ProfitelligenceAPIError

        with patch.object(mcp_tools, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.side_effect = ProfitelligenceAPIError(
                message="API Error",
                status_code=500
            )
            mock_get_client.return_value = mock_client

            tool_func = mcp._tool_manager._tools["pulse"].fn
            mock_ctx = MagicMock()

            with pytest.raises(ProfitelligenceAPIError):
                tool_func(mock_ctx)
