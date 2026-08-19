"""Tests for delete_saved_search tool."""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.ariel.delete_saved_search import DeleteSavedSearchTool


@pytest.fixture
def tool():
    """Create tool instance."""
    return DeleteSavedSearchTool()


@pytest.fixture
def mock_delete_task():
    """Mock delete task response."""
    return {
        "id": 123,
        "message": "Checking dependencies for saved search deletion",
        "status": "PROCESSING",
        "name": "Delete Saved Search Task",
        "created_by": "admin",
        "created": 1640000000000,
        "started": 1640000001000,
        "modified": 1640000002000,
        "completed": None
    }


class TestMetadata:
    """Test tool metadata."""

    def test_tool_name(self, tool):
        """Test tool name is correct."""
        assert tool.name == "delete_saved_search"

    def test_tool_description(self, tool):
        """Test tool description includes key guidance."""
        description = tool.description
        assert "delete" in description.lower()
        assert "saved search" in description.lower()
        assert "dependency" in description.lower()
        assert "conflict" in description.lower()

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
    async def test_successful_execution(self, tool, mock_delete_task):
        """Test successful execution."""
        # Setup mock
        mock_response = httpx.Response(
            status_code=200,
            json=mock_delete_task,
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify MCP format
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify content
        content = json.loads(result["content"][0]["text"])
        assert content["id"] == 123
        assert content["status"] == "PROCESSING"
        assert "Delete" in content["name"]

        # Verify API call
        tool.client.delete.assert_called_once()
        call_args = tool.client.delete.call_args
        assert call_args[0][0] == 'ariel/saved_searches/42'

    @pytest.mark.asyncio
    async def test_execution_with_fields(self, tool, mock_delete_task):
        """Test execution with field selection."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_delete_task,
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"search_id": 42, "fields": "id,status,message"})

        # Verify
        assert "content" in result

        # Verify fields were passed
        call_args = tool.client.delete.call_args
        assert "fields" in call_args[1]["params"]
        assert call_args[1]["params"]["fields"] == "id,status,message"

    @pytest.mark.asyncio
    async def test_execution_with_string_search_id(self, tool, mock_delete_task):
        """Test execution converts string search_id to int."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_delete_task,
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)

        # Execute with string
        result = await tool.execute({"search_id": "42"})

        # Verify
        assert "content" in result

        # Verify int conversion in API call
        call_args = tool.client.delete.call_args
        assert 'ariel/saved_searches/42' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_async_task_response(self, tool):
        """Test async task response format."""
        # Setup - task in QUEUED state
        mock_response = httpx.Response(
            status_code=200,
            json={
                "id": 456,
                "status": "QUEUED",
                "message": "Task queued for processing",
                "name": "Delete Saved Search Task"
            },
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert content["status"] == "QUEUED"


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
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=mock_response.request,
            response=mock_response
        ))

        # Execute
        result = await tool.execute({"search_id": 999})

        # Verify error response
        assert "content" in result
        assert "Error executing delete_saved_search: 404 Not Found" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_http_403_error(self, tool):
        """Test handling of 403 Forbidden (insufficient permissions)."""
        # Setup
        mock_response = httpx.Response(
            status_code=403,
            text="You do not have the required capabilities",
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=httpx.HTTPStatusError(
            "403 Forbidden",
            request=mock_response.request,
            response=mock_response
        ))

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify error response
        assert "content" in result
        assert "Error executing delete_saved_search: 403 Forbidden" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_http_500_error(self, tool):
        """Test handling of 500 Internal Server Error."""
        # Setup
        mock_response = httpx.Response(
            status_code=500,
            text="Internal Server Error",
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=mock_response.request,
            response=mock_response
        ))

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify error response
        assert "content" in result
        assert "Error executing delete_saved_search: 500 Internal Server Error" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_value_error_handling(self, tool):
        """Test handling of value errors."""
        # Setup
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=ValueError("Invalid search ID"))

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed: Invalid search ID" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self, tool):
        """Test handling of runtime errors."""
        # Setup
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=RuntimeError("Connection failed"))

        # Execute
        result = await tool.execute({"search_id": 42})

        # Verify error response
        assert "content" in result
        assert "Tool execution failed: Connection failed" in result["content"][0]["text"]
        assert "Connection failed" in result["content"][0]["text"]
        assert result["isError"] is True


class TestValidation:
    """Test parameter validation."""

    @pytest.mark.asyncio
    async def test_none_fields_parameter(self, tool, mock_delete_task):
        """Test with None fields parameter."""
        # Setup
        mock_response = httpx.Response(
            status_code=200,
            json=mock_delete_task,
            request=httpx.Request("DELETE", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)

        # Execute with None fields
        result = await tool.execute({"search_id": 42, "fields": None})

        # Should handle gracefully
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert content["id"] == 123