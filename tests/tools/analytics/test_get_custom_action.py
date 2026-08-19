"""Tests for get_custom_action tool."""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.analytics.get_custom_action import GetCustomActionTool


@pytest.fixture
def tool():
    """Create tool instance."""
    return GetCustomActionTool()


@pytest.fixture
def mock_custom_action():
    """Mock custom action response."""
    return {
        "id": 1,
        "name": "Block IP at Firewall",
        "description": "Automatically blocks source IP at perimeter firewall for specified duration",
        "interpreter": 1,
        "script": 5,
        "parameters": [
            {
                "name": "sourceip",
                "parameter_type": "dynamic",
                "encrypted": False,
                "value": "sourceip"
            },
            {
                "name": "duration",
                "parameter_type": "fixed",
                "encrypted": False,
                "value": "3600"
            },
            {
                "name": "api_key",
                "parameter_type": "fixed",
                "encrypted": True,
                "value": "********"
            }
        ]
    }


class TestMetadata:
    """Test tool metadata."""

    def test_tool_name(self, tool):
        """Test tool name is correct."""
        assert tool.name == "get_custom_action"

    def test_tool_description(self, tool):
        """Test tool description includes use cases."""
        description = tool.description
        assert "custom action" in description.lower()
        assert "use cases" in description.lower()
        assert "parameter" in description.lower()

    def test_input_schema(self, tool):
        """Test input schema has correct parameters."""
        schema = tool.input_schema
        assert "properties" in schema
        assert "action_id" in schema["properties"]
        assert "fields" in schema["properties"]

        # Verify action_id is required
        assert "required" in schema
        assert "action_id" in schema["required"]

        # Verify action_id constraints
        assert schema["properties"]["action_id"]["minimum"] == 1


class TestExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_execution(self, tool, mock_custom_action):
        """Test successful execution."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_action,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"action_id": 1})

        # Verify MCP format
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify content
        content = json.loads(result["content"][0]["text"])
        assert content["id"] == 1
        assert content["name"] == "Block IP at Firewall"
        assert len(content["parameters"]) == 3

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'analytics/custom_actions/actions/1'

    @pytest.mark.asyncio
    async def test_execution_with_fields(self, tool, mock_custom_action):
        """Test execution with field selection."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_action,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"action_id": 1, "fields": "id,name,parameters"})

        # Verify
        assert "content" in result

        # Verify fields were passed
        call_args = tool.client.get.call_args
        assert "fields" in call_args[1]["params"]
        assert call_args[1]["params"]["fields"] == "id,name,parameters"

    @pytest.mark.asyncio
    async def test_execution_with_string_action_id(self, tool, mock_custom_action):
        """Test execution converts string action_id to int."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_action,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"action_id": "1"})

        # Verify
        assert "content" in result

        # Verify int conversion in API call
        call_args = tool.client.get.call_args
        assert 'analytics/custom_actions/actions/1' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_encrypted_parameters_masked(self, tool, mock_custom_action):
        """Test that encrypted parameters are masked in response."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_action,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"action_id": 1})

        # Verify
        assert "content" in result
        content = json.loads(result["content"][0]["text"])

        # Find encrypted parameter
        encrypted_param = next(p for p in content["parameters"] if p["encrypted"])
        assert encrypted_param["value"] == "********"


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_missing_action_id(self, tool):
        """Test error when action_id is missing."""
        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert "action_id is required" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_none_action_id(self, tool):
        """Test error when action_id is None."""
        result = await tool.execute({"action_id": None})

        # Verify error response
        assert "content" in result
        assert "action_id is required" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_http_404_error(self, tool):
        """Test handling of 404 Not Found."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            404,
            text="Custom action not found",
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Custom action not found",
                request=mock_request,
                response=mock_response
            )
        )

        result = await tool.execute({"action_id": 999})

        # Verify error response
        assert "content" in result
        assert "Error executing get_custom_action:" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_http_500_error(self, tool):
        """Test handling of 500 Internal Server Error."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Internal Server Error",
                request=mock_request,
                response=mock_response
            )
        )

        result = await tool.execute({"action_id": 1})

        # Verify error response
        assert "content" in result
        assert "Error executing get_custom_action:" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_value_error_handling(self, tool):
        """Test handling of value errors."""
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid action ID"))

        result = await tool.execute({"action_id": 1})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Invalid action ID" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self, tool):
        """Test handling of runtime errors."""
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Connection failed"))

        result = await tool.execute({"action_id": 1})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Connection failed" in result["content"][0]["text"]
        assert result["isError"] is True


class TestValidation:
    """Test parameter validation."""

    @pytest.mark.asyncio
    async def test_none_fields_parameter(self, tool, mock_custom_action):
        """Test with None fields parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_action,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"action_id": 1, "fields": None})

        # Should handle gracefully
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert content["id"] == 1
