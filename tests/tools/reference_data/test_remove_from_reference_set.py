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
Tests for RemoveFromReferenceSetTool
"""

import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.reference_data.remove_from_reference_set import RemoveFromReferenceSetTool


class TestRemoveFromReferenceSetMetadata:
    """Test RemoveFromReferenceSetTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = RemoveFromReferenceSetTool()
        assert tool.name == "remove_from_reference_set"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = RemoveFromReferenceSetTool()
        assert tool.description
        assert "remove" in tool.description.lower()
        assert "entry" in tool.description.lower()
        assert "reference" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = RemoveFromReferenceSetTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test entry_id is required in schema."""
        tool = RemoveFromReferenceSetTool()
        schema = tool.input_schema

        assert "entry_id" in schema["required"]
        assert "entry_id" in schema["properties"]

    def test_input_schema_entry_id_type(self):
        """Test entry_id is integer type with minimum."""
        tool = RemoveFromReferenceSetTool()
        schema = tool.input_schema

        entry_id_prop = schema["properties"]["entry_id"]
        assert entry_id_prop["type"] == "integer"
        assert entry_id_prop["minimum"] == 0


class TestRemoveFromReferenceSetExecution:
    """Test RemoveFromReferenceSetTool execution."""

    @pytest.mark.asyncio
    async def test_execute_successful_removal(self):
        """Test successful entry removal (204 response)."""
        # Setup mock
        mock_response = httpx.Response(204, request=httpx.Request("DELETE", "http://test"))

        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "entry_id": 456
        })

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "removed successfully" in result["content"][0]["text"].lower()
        assert "456" in result["content"][0]["text"]
        assert "isError" not in result

        # Verify API call
        tool.client.delete.assert_called_once_with(
            'reference_data_collections/set_entries/456'
        )

    @pytest.mark.asyncio
    async def test_execute_with_zero_entry_id(self):
        """Test execution with entry_id of 0 (valid minimum)."""
        # Setup mock
        mock_response = httpx.Response(204, request=httpx.Request("DELETE", "http://test"))

        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "entry_id": 0
        })

        # Verify
        assert "isError" not in result
        tool.client.delete.assert_called_once_with(
            'reference_data_collections/set_entries/0'
        )

    @pytest.mark.asyncio
    async def test_execute_with_large_entry_id(self):
        """Test execution with large entry_id."""
        # Setup mock
        mock_response = httpx.Response(204, request=httpx.Request("DELETE", "http://test"))

        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "entry_id": 999999
        })

        # Verify
        assert "isError" not in result
        tool.client.delete.assert_called_once_with(
            'reference_data_collections/set_entries/999999'
        )

    @pytest.mark.asyncio
    async def test_execute_unexpected_status_code(self):
        """Test handling of unexpected status code."""
        # Setup mock
        mock_request = httpx.Request("DELETE", "http://test")
        mock_response = httpx.Response(418, content=b"I'm a teapot", request=mock_request)
        http_error = httpx.HTTPStatusError("418 Client Error: I'm a teapot", request=mock_request, response=mock_response)

        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=http_error)
        result = await tool.execute({
            "entry_id": 456
        })

        # Verify error response
        assert result["isError"] is True
        assert "Error executing remove_from_reference_set: 418 Client Error: I'm a teapot" in result["content"][0]["text"]


class TestRemoveFromReferenceSetValidation:
    """Test RemoveFromReferenceSetTool input validation."""

    @pytest.mark.asyncio
    async def test_missing_entry_id(self):
        """Test error when entry_id is missing."""
        tool = RemoveFromReferenceSetTool()
        result = await tool.execute({})

        assert result["isError"] is True
        assert "entry_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_none_entry_id(self):
        """Test error when entry_id is None."""
        tool = RemoveFromReferenceSetTool()
        result = await tool.execute({
            "entry_id": None
        })

        assert result["isError"] is True
        assert "entry_id is required" in result["content"][0]["text"]


class TestRemoveFromReferenceSetErrorHandling:
    """Test RemoveFromReferenceSetTool error handling."""

    @pytest.mark.asyncio
    async def test_entry_not_found_error(self):
        """Test handling of entry not found error (404)."""
        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=RuntimeError("Entry not found"))
        result = await tool.execute({
            "entry_id": 999
        })

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()
        assert "Entry not found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_permission_denied_error(self):
        """Test handling of permission denied error (403)."""
        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=RuntimeError("Operation not allowed"))
        result = await tool.execute({
            "entry_id": 456
        })

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()
        assert "Operation not allowed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=ValueError("Invalid entry ID format"))
        result = await tool.execute({
            "entry_id": 456
        })

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid entry id format" == result["content"][0]["text"].lower()
        assert "Invalid entry ID format" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self):
        """Test handling of RuntimeError."""
        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=RuntimeError("Server error"))
        result = await tool.execute({
            "entry_id": 456
        })

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()
        assert "Server error" in result["content"][0]["text"]


class TestRemoveFromReferenceSetResponseFormatting:
    """Test RemoveFromReferenceSetTool response formatting."""

    @pytest.mark.asyncio
    async def test_success_message_format(self):
        """Test success message includes entry ID."""
        # Setup mock
        mock_response = httpx.Response(204, request=httpx.Request("DELETE", "http://test"))

        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "entry_id": 123
        })

        # Verify message format
        message = result["content"][0]["text"]
        assert "Entry 123" in message
        assert "removed successfully" in message.lower()

    @pytest.mark.asyncio
    async def test_error_message_includes_entry_id(self):
        """Test error message includes entry ID."""
        # Execute
        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(side_effect=RuntimeError("Test error"))
        result = await tool.execute({
            "entry_id": 789
        })

        # Verify error message
        message = result["content"][0]["text"]
        assert "Tool execution failed: Test error" in message


class TestRemoveFromReferenceSetIntegration:
    """Test RemoveFromReferenceSetTool integration scenarios."""

    @pytest.mark.asyncio
    async def test_remove_multiple_entries_sequentially(self):
        """Test removing multiple entries in sequence."""
        # Setup mock
        mock_response = httpx.Response(204, request=httpx.Request("DELETE", "http://test"))

        tool = RemoveFromReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.delete = AsyncMock(return_value=mock_response)

        # Remove first entry
        result1 = await tool.execute({"entry_id": 100})
        assert "isError" not in result1

        # Remove second entry
        result2 = await tool.execute({"entry_id": 200})
        assert "isError" not in result2

        # Verify both calls were made
        assert tool.client.delete.call_count == 2
        tool.client.delete.assert_any_call('reference_data_collections/set_entries/100')
        tool.client.delete.assert_any_call('reference_data_collections/set_entries/200')
