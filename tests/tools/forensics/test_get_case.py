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
Unit tests for the GetCaseTool.
"""

import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.forensics.get_case import GetCaseTool


class TestGetCaseToolMetadata:
    """Tests for GetCaseTool metadata properties."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = GetCaseTool()
        assert tool.name == "get_case"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = GetCaseTool()
        assert "Get detailed information about a forensic case" in tool.description
        assert "case" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = GetCaseTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test case_id is required."""
        tool = GetCaseTool()
        schema = tool.input_schema

        # case_id should be required
        assert "required" in schema
        assert "case_id" in schema["required"]

    def test_input_schema_optional_fields(self):
        """Test fields parameter is optional."""
        tool = GetCaseTool()
        schema = tool.input_schema

        # fields should exist but not be required
        assert "fields" in schema["properties"]
        assert "fields" not in schema.get("required", [])

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = GetCaseTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "get_case"
        assert "Get detailed information about a forensic case" in definition["description"]
        assert "inputSchema" in definition


class TestGetCaseToolExecution:
    """Tests for GetCaseTool execute method."""

    @pytest.fixture
    def sample_case(self):
        """Sample forensic case data."""
        return {
            "id": 123,
            "name": "Malware Investigation",
            "status": "OPEN",
            "assignee": "analyst1",
            "created_time": 1234567890000,
            "modified_time": 1234567900000,
            "description": "Investigating suspicious malware activity",
            "priority": "HIGH"
        }

    @pytest.mark.asyncio
    async def test_execute_with_case_id(self, sample_case):
        """Test executing tool with case_id."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_case,
            request=httpx.Request("GET", "http://test")
        )

        tool = GetCaseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"case_id": 123})

        # Verify client was called correctly
        tool.client.get.assert_called_once_with(
            'forensics/case_management/cases/123',
            params={}
        )

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "Malware Investigation" in result["content"][0]["text"]
        assert "OPEN" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_case):
        """Test executing tool with fields parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json={"id": 123, "name": "Malware Investigation"},
            request=httpx.Request("GET", "http://test")
        )

        tool = GetCaseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"case_id": 123, "fields": "id,name"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'forensics/case_management/cases/123',
            params={"fields": "id,name"}
        )

class TestGetCaseToolErrorHandling:
    """Tests for GetCaseTool error handling."""

    @pytest.mark.asyncio
    async def test_forensics_module_not_available(self):
        """Test handling when Forensics module is not available (404)."""
        # Setup mock to raise 404 HTTPStatusError
        mock_response = httpx.Response(
            404,
            request=httpx.Request("GET", "http://test")
        )
        http_error = httpx.HTTPStatusError("404 Not Found", request=mock_response.request, response=mock_response)

        # Execute
        tool = GetCaseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({"case_id": 123})

        # Verify error response
        assert result["isError"] is True
        assert "Error executing get_case: 404 Not Found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_case_not_found(self):
        """Test handling when case is not found (404 with different message)."""
        # Setup mock to raise 404 HTTPStatusError
        mock_response = httpx.Response(
            404,
            text="Case not found",
            request=httpx.Request("GET", "http://test")
        )
        http_error = httpx.HTTPStatusError("404 Not Found", request=mock_response.request, response=mock_response)

        # Execute
        tool = GetCaseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({"case_id": 999})

        # Verify error response
        assert result["isError"] is True
        assert "404" in result["content"][0]["text"] or "not found" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_permission_denied_error(self):
        """Test handling when user lacks permissions (403)."""
        # Setup mock to raise 403 HTTPStatusError
        mock_response = httpx.Response(
            403,
            request=httpx.Request("GET", "http://test")
        )
        http_error = httpx.HTTPStatusError("403 Forbidden", request=mock_response.request, response=mock_response)

        # Execute
        tool = GetCaseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({"case_id": 123})

        # Verify error response mentions permissions or access denied
        assert result["isError"] is True
        error_text = result["content"][0]["text"].lower()
        assert "permission" in error_text or "403" in result["content"][0]["text"] or "access denied" in error_text

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of general API errors."""
        # Setup mock to raise error
        tool = GetCaseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        # Execute
        result = await tool.execute({"case_id": 123})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" == result["content"][0]["text"].lower()
        assert "API connection failed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Setup mock to raise ValueError
        tool = GetCaseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({"case_id": 123})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_missing_case_id(self):
        """Test that missing case_id returns error response."""
        tool = GetCaseTool()

        # Execute without case_id should return error
        result = await tool.execute({})
        assert result["isError"] is True
        assert "case_id" in result["content"][0]["text"].lower() or "required" in result["content"][0]["text"].lower()
