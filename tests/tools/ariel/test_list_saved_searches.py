"""Tests for list_saved_searches tool."""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.ariel.list_saved_searches import ListSavedSearchesTool


@pytest.fixture
def tool():
    """Create tool instance."""
    return ListSavedSearchesTool()


@pytest.fixture
def mock_saved_searches():
    """Mock saved searches response."""
    return [
        {
            "id": 1,
            "uid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Failed Login Attempts",
            "database": "EVENTS",
            "is_shared": True,
            "owner": "admin",
            "aql": "SELECT sourceip, username, COUNT(*) FROM events WHERE eventname='Failed Login' LAST 24 HOURS GROUP BY sourceip, username",
            "description": "Identifies potential brute force attacks",
            "is_aggregate": True,
            "is_dashboard": False,
            "is_default": False,
            "is_quick_search": True,
            "creation_date": 1640000000000,
            "modified_date": 1640100000000
        },
        {
            "id": 2,
            "uid": "660e8400-e29b-41d4-a716-446655440001",
            "name": "Suspicious Traffic",
            "database": "FLOWS",
            "is_shared": False,
            "owner": "analyst1",
            "aql": "SELECT * FROM flows WHERE destinationport=445 LAST 1 HOURS",
            "description": "SMB traffic analysis",
            "is_aggregate": False,
            "is_dashboard": False,
            "is_default": False,
            "is_quick_search": False,
            "creation_date": 1640000000000,
            "modified_date": 1640100000000
        }
    ]


class TestMetadata:
    """Test tool metadata."""

    def test_tool_name(self, tool):
        """Test tool name is correct."""
        assert tool.name == "list_saved_searches"

    def test_tool_description(self, tool):
        """Test tool description includes key guidance."""
        description = tool.description
        assert "saved searches" in description.lower()
        assert "discover" in description.lower()
        assert "create_ariel_search" in description

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
    async def test_successful_execution(self, tool, mock_saved_searches):
        """Test successful execution without parameters."""
        # Setup mock
        mock_response = httpx.Response(
            status_code=200,
            json=mock_saved_searches,
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({})

        # Verify MCP format
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify content
        content = json.loads(result["content"][0]["text"])
        assert len(content) == 2
        assert content[0]["name"] == "Failed Login Attempts"
        assert content[1]["name"] == "Suspicious Traffic"

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'ariel/saved_searches'

    @pytest.mark.asyncio
    async def test_execution_with_filter(self, tool, mock_saved_searches):
        """Test execution with filter parameter."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=[mock_saved_searches[0]],
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"filter": "is_shared=true"})

        # Verify
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert len(content) == 1

        # Verify filter was passed
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["filter"] == "is_shared=true"

    @pytest.mark.asyncio
    async def test_execution_with_fields(self, tool, mock_saved_searches):
        """Test execution with field selection."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_saved_searches,
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"fields": "id,name,owner"})

        # Verify
        assert "content" in result

        # Verify fields were passed
        call_args = tool.client.get.call_args
        assert "fields" in call_args[1]["params"]
        assert call_args[1]["params"]["fields"] == "id,name,owner"

    @pytest.mark.asyncio
    async def test_execution_with_pagination(self, tool, mock_saved_searches):
        """Test execution with limit and offset."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=[mock_saved_searches[0]],
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"limit": 10, "offset": 5})

        # Verify
        assert "content" in result

        # Verify Range header was set
        call_args = tool.client.get.call_args
        assert "Range" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Range"] == "items=5-14"

    @pytest.mark.asyncio
    async def test_execution_with_all_parameters(self, tool, mock_saved_searches):
        """Test execution with all optional parameters."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_saved_searches,
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            "fields": "id,name",
            "filter": "database='EVENTS'",
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
        # Setup
        mock_response = httpx.Response(
            status_code=500,
            text="Internal Server Error",
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=mock_response.request,
            response=mock_response
        ))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert "Error executing list_saved_searches:" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_value_error_handling(self, tool):
        """Test handling of value errors."""
        # Setup
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Invalid parameter" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self, tool):
        """Test handling of runtime errors."""
        # Setup
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Connection failed"))

        # Execute
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
        # This should work - all parameters are optional
        mock_response = httpx.Response(
            status_code=200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})
        assert "content" in result

    @pytest.mark.asyncio
    async def test_none_fields_parameter(self, tool):
        """Test with None fields parameter."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute with None fields
        result = await tool.execute({"fields": None})

        # Should handle gracefully
        assert "content" in result
