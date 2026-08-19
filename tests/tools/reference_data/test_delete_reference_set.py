# Copyright 2026 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Tests for Delete Reference Set Tool
"""

from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.reference_data.delete_reference_set import DeleteReferenceSetTool


@pytest.fixture
def delete_reference_set_tool():
    """Fixture providing DeleteReferenceSetTool instance."""
    return DeleteReferenceSetTool()


class TestDeleteReferenceSetToolProperties:
    """Test DeleteReferenceSetTool properties."""

    def test_name(self, delete_reference_set_tool):
        """Test tool name property."""
        assert delete_reference_set_tool.name == "delete_reference_set"

    def test_description(self, delete_reference_set_tool):
        """Test tool description property."""
        description = delete_reference_set_tool.description
        assert "Delete a reference data set" in description
        assert "WARNING" in description
        assert "permanent" in description

    def test_input_schema(self, delete_reference_set_tool):
        """Test input schema structure."""
        schema = delete_reference_set_tool.input_schema
        assert schema["type"] == "object"
        assert "set_id" in schema["properties"]
        assert schema["required"] == ["set_id"]
        assert schema["properties"]["set_id"]["type"] == "integer"
        assert schema["properties"]["set_id"]["minimum"] == 0


class TestDeleteReferenceSetToolExecution:
    """Test DeleteReferenceSetTool execution."""

    @pytest.mark.asyncio
    async def test_successful_deletion(self, delete_reference_set_tool):
        """Test successful reference set deletion."""
        mock_response = httpx.Response(
            204,
            request=httpx.Request("DELETE", "http://test")
        )

        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(return_value=mock_response)
        result = await delete_reference_set_tool.execute({"set_id": 123})

        assert result["content"][0]["type"] == "text"
        assert "deleted successfully" in result["content"][0]["text"]
        assert "123" in result["content"][0]["text"]
        delete_reference_set_tool.client.delete.assert_called_once_with('reference_data_collections/sets/123')

    @pytest.mark.asyncio
    async def test_delete_with_zero_id(self, delete_reference_set_tool):
        """Test deletion with set_id of 0."""
        mock_response = httpx.Response(
            204,
            request=httpx.Request("DELETE", "http://test")
        )

        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(return_value=mock_response)
        result = await delete_reference_set_tool.execute({"set_id": 0})

        assert result["content"][0]["type"] == "text"
        assert "deleted successfully" in result["content"][0]["text"]
        delete_reference_set_tool.client.delete.assert_called_once_with('reference_data_collections/sets/0')

    @pytest.mark.asyncio
    async def test_delete_with_large_id(self, delete_reference_set_tool):
        """Test deletion with large set_id."""
        mock_response = httpx.Response(
            204,
            request=httpx.Request("DELETE", "http://test")
        )

        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(return_value=mock_response)
        result = await delete_reference_set_tool.execute({"set_id": 999999})

        assert result["content"][0]["type"] == "text"
        assert "deleted successfully" in result["content"][0]["text"]
        delete_reference_set_tool.client.delete.assert_called_once_with('reference_data_collections/sets/999999')


class TestDeleteReferenceSetToolValidation:
    """Test DeleteReferenceSetTool validation."""

    @pytest.mark.asyncio
    async def test_missing_set_id(self, delete_reference_set_tool):
        """Test error when set_id is missing."""
        result = await delete_reference_set_tool.execute({})

        assert result["isError"] is True
        assert "set_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_none_set_id(self, delete_reference_set_tool):
        """Test error when set_id is None."""
        result = await delete_reference_set_tool.execute({"set_id": None})

        assert result["isError"] is True
        assert "set_id is required" in result["content"][0]["text"]


class TestDeleteReferenceSetToolErrorHandling:
    """Test DeleteReferenceSetTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_404(self, delete_reference_set_tool):
        """Test handling of 404 Not Found error."""
        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(side_effect=RuntimeError("API Error: 404 Not Found"))
        result = await delete_reference_set_tool.execute({"set_id": 999})

        assert result["isError"] is True
        assert "Tool execution failed: API Error:" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_api_error_409_conflict(self, delete_reference_set_tool):
        """Test handling of 409 Conflict error (set in use)."""
        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(
            side_effect=RuntimeError("API Error: 409 Conflict - Reference set is in use by active rules")
        )
        result = await delete_reference_set_tool.execute({"set_id": 123})

        assert result["isError"] is True
        assert "Tool execution failed: API Error:" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_value_error(self, delete_reference_set_tool):
        """Test handling of value errors."""
        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(side_effect=ValueError("Invalid set ID"))
        result = await delete_reference_set_tool.execute({"set_id": 123})

        assert result["isError"] is True
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Invalid set ID" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_unexpected_status_code(self, delete_reference_set_tool):
        """Test handling of unexpected status codes."""
        mock_response = httpx.Response(
            418,  # I'm a teapot - truly unexpected
            text="I'm a teapot",
            request=httpx.Request("DELETE", "http://test")
        )

        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(
            side_effect=httpx.HTTPStatusError("418 Client Error: I'm a teapot", request=mock_response.request, response=mock_response)
        )
        result = await delete_reference_set_tool.execute({"set_id": 123})

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_network_error(self, delete_reference_set_tool):
        """Test handling of network errors."""
        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(side_effect=RuntimeError("Connection timeout"))
        result = await delete_reference_set_tool.execute({"set_id": 123})

        assert result["isError"] is True
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "Connection timeout" in result["content"][0]["text"]


class TestDeleteReferenceSetToolResponseHandling:
    """Test DeleteReferenceSetTool response handling."""

    @pytest.mark.asyncio
    async def test_response_format(self, delete_reference_set_tool):
        """Test that successful response has correct format."""
        mock_response = httpx.Response(
            204,
            request=httpx.Request("DELETE", "http://test")
        )

        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(return_value=mock_response)
        result = await delete_reference_set_tool.execute({"set_id": 123})

        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert isinstance(result["content"][0]["text"], str)
        assert "isError" not in result or result["isError"] is False

    @pytest.mark.asyncio
    async def test_error_response_format(self, delete_reference_set_tool):
        """Test that error response has correct format."""
        delete_reference_set_tool.client = AsyncMock()
        delete_reference_set_tool.client.delete = AsyncMock(side_effect=RuntimeError("Test error"))
        result = await delete_reference_set_tool.execute({"set_id": 123})

        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert isinstance(result["content"][0]["text"], str)
        assert result["isError"] is True
