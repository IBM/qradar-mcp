"""Tests for list_custom_actions tool."""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.analytics.list_custom_actions import ListCustomActionsTool


@pytest.fixture
def tool():
    """Create tool instance."""
    return ListCustomActionsTool()


@pytest.fixture
def mock_custom_actions():
    """Mock custom actions response."""
    return [
        {
            "id": 1,
            "name": "Block IP at Firewall",
            "description": "Automatically blocks source IP at perimeter firewall",
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
                }
            ]
        },
        {
            "id": 2,
            "name": "Email Security Team",
            "description": "Sends email notification to security team",
            "interpreter": 2,
            "script": 10,
            "parameters": [
                {
                    "name": "offense_id",
                    "parameter_type": "dynamic",
                    "encrypted": False,
                    "value": "offense_id"
                },
                {
                    "name": "smtp_password",
                    "parameter_type": "fixed",
                    "encrypted": True,
                    "value": "********"
                }
            ]
        }
    ]


class TestMetadata:
    """Test tool metadata."""

    def test_tool_name(self, tool):
        """Test tool name is correct."""
        assert tool.name == "list_custom_actions"

    def test_tool_description(self, tool):
        """Test tool description includes use cases."""
        description = tool.description
        assert "custom actions" in description.lower()
        assert "use cases" in description.lower()
        assert "automated" in description.lower()

    def test_input_schema(self, tool):
        """Test input schema has correct parameters."""
        schema = tool.input_schema
        assert "properties" in schema
        assert "fields" in schema["properties"]
        assert "filter" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "offset" in schema["properties"]

        # Verify limit constraints
        assert schema["properties"]["limit"]["minimum"] == 1
        assert schema["properties"]["limit"]["maximum"] == 100

        # Verify offset constraints
        assert schema["properties"]["offset"]["minimum"] == 0


class TestExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_execution(self, tool, mock_custom_actions):
        """Test successful execution without parameters."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_actions,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify MCP format
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify content
        content = json.loads(result["content"][0]["text"])
        assert len(content) == 2
        assert content[0]["name"] == "Block IP at Firewall"
        assert content[1]["name"] == "Email Security Team"

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'analytics/custom_actions/actions'

    @pytest.mark.asyncio
    async def test_execution_with_filter(self, tool, mock_custom_actions):
        """Test execution with filter parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=[mock_custom_actions[0]],
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "name LIKE '%Block%'"})

        # Verify
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert len(content) == 1

        # Verify filter was passed
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["filter"] == "name LIKE '%Block%'"

    @pytest.mark.asyncio
    async def test_execution_with_fields(self, tool, mock_custom_actions):
        """Test execution with field selection."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_actions,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,name,description"})

        # Verify
        assert "content" in result

        # Verify fields were passed
        call_args = tool.client.get.call_args
        assert "fields" in call_args[1]["params"]
        assert call_args[1]["params"]["fields"] == "id,name,description"

    @pytest.mark.asyncio
    async def test_execution_with_pagination(self, tool, mock_custom_actions):
        """Test execution with limit and offset."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=[mock_custom_actions[0]],
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"limit": 10, "offset": 5})

        # Verify
        assert "content" in result

        # Verify Range header was set
        call_args = tool.client.get.call_args
        assert "Range" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Range"] == "items=5-14"

    @pytest.mark.asyncio
    async def test_execution_with_all_parameters(self, tool, mock_custom_actions):
        """Test execution with all optional parameters."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=mock_custom_actions,
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "fields": "id,name,parameters",
            "filter": "interpreter=1",
            "limit": 50,
            "offset": 0
        })

        # Verify
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert len(content) == 2

        # Verify all parameters were passed
        call_args = tool.client.get.call_args
        assert "fields" in call_args[1]["params"]
        assert "filter" in call_args[1]["params"]
        assert "Range" in call_args[1]["headers"]


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_http_error_handling(self, tool):
        """Test handling of HTTP errors."""
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

        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert "Error executing list_custom_actions:" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_value_error_handling(self, tool):
        """Test handling of value errors."""
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Invalid parameter" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self, tool):
        """Test handling of runtime errors."""
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Connection failed"))

        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Connection failed" in result["content"][0]["text"]
        assert result["isError"] is True


class TestValidation:
    """Test parameter validation."""

    @pytest.mark.asyncio
    async def test_empty_arguments(self, tool):
        """Test execution with empty arguments."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=[],
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})
        assert "content" in result

    @pytest.mark.asyncio
    async def test_none_fields_parameter(self, tool):
        """Test with None fields parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=[],
            request=mock_request
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": None})

        # Should handle gracefully
        assert "content" in result
