"""Tests for get_saved_search tool."""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.ariel.get_saved_search import GetSavedSearchTool


@pytest.fixture
def tool():
    """Create tool instance."""
    return GetSavedSearchTool()


@pytest.fixture
def mock_saved_search():
    """Mock saved search response."""
    return {
        "id": 42,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Failed Login Attempts - Last 24h",
        "database": "EVENTS",
        "is_shared": True,
        "owner": "admin",
        "aql": "SELECT sourceip, username, COUNT(*) FROM events WHERE eventname='Failed Login' LAST 24 HOURS GROUP BY sourceip, username",
        "description": "Identifies potential brute force attacks by counting failed login attempts",
        "is_aggregate": True,
        "is_dashboard": False,
        "is_default": False,
        "is_quick_search": True,
        "creation_date": 1640000000000,
        "modified_date": 1640100000000
    }


class TestMetadata:
    """Test tool metadata."""

    def test_tool_name(self, tool):
        """Test tool name is correct."""
        assert tool.name == "get_saved_search"

    def test_tool_description(self, tool):
        """Test tool description includes key guidance."""
        description = tool.description
        assert "saved search" in description.lower()
        assert "aql" in description.lower()
        assert "create_ariel_search" in description

    def test_input_schema(self, tool):
        """Test input schema has correct parameters."""
        schema = tool.input_schema
        assert "properties" in schema
        assert "search_id" in schema["properties"]
        assert "fields" in schema["properties"]

        # Verify search_id is required
        assert "required" in schema
        assert "search_id" in schema["required"]

        # Verify search_id constraints
        assert schema["properties"]["search_id"]["minimum"] == 1


class TestExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_execution(self, tool, mock_saved_search):
        """Test successful execution."""
        # Setup mock
        mock_response = httpx.Response(
            status_code=200,
            json=mock_saved_search,
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify MCP format
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify content
        content = json.loads(result["content"][0]["text"])
        assert content["id"] == 42
        assert content["name"] == "Failed Login Attempts - Last 24h"
        assert "SELECT" in content["aql"]

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'ariel/saved_searches/42'

    @pytest.mark.asyncio
    async def test_execution_with_fields(self, tool, mock_saved_search):
        """Test execution with field selection."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_saved_search,
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"search_id": 42, "fields": "id,name,aql"})

        # Verify
        assert "content" in result

        # Verify fields were passed
        call_args = tool.client.get.call_args
        assert "fields" in call_args[1]["params"]
        assert call_args[1]["params"]["fields"] == "id,name,aql"

    @pytest.mark.asyncio
    async def test_execution_with_string_search_id(self, tool, mock_saved_search):
        """Test execution converts string search_id to int."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_saved_search,
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute with string
        result = await tool.execute({"search_id": "42"})

        # Verify
        assert "content" in result

        # Verify int conversion in API call
        call_args = tool.client.get.call_args
        assert 'ariel/saved_searches/42' in call_args[0][0]


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_missing_search_id(self, tool):
        """Test error when search_id is missing."""
        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert "search_id is required" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_none_search_id(self, tool):
        """Test error when search_id is None."""
        result = await tool.execute({"search_id": None})

        # Verify error response
        assert "content" in result
        assert "search_id is required" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_http_404_error(self, tool):
        """Test handling of 404 Not Found."""
        # Setup
        mock_response = httpx.Response(
            status_code=404,
            text="Saved search not found",
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=mock_response.request,
            response=mock_response
        ))

        # Execute
        result = await tool.execute({"search_id": 999})

        # Verify error response
        assert "content" in result
        assert "Error executing get_saved_search:" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_http_500_error(self, tool):
        """Test handling of 500 Internal Server Error."""
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
        result = await tool.execute({"search_id": 42})

        # Verify error response
        assert "content" in result
        assert "Error executing get_saved_search:" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_value_error_handling(self, tool):
        """Test handling of value errors."""
        # Setup
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid search ID"))

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Invalid search ID" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self, tool):
        """Test handling of runtime errors."""
        # Setup
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Connection failed"))

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Connection failed" in result["content"][0]["text"]
        assert result["isError"] is True


class TestValidation:
    """Test parameter validation."""

    @pytest.mark.asyncio
    async def test_none_fields_parameter(self, tool, mock_saved_search):
        """Test with None fields parameter."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_saved_search,
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        # Execute with None fields
        result = await tool.execute({"search_id": 42, "fields": None})

        # Should handle gracefully
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert content["id"] == 42
