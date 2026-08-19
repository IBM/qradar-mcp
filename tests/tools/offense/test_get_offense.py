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
Unit tests for the GetOffenseTool.
"""

from unittest.mock import AsyncMock
import httpx
import pytest
from qradar_mcp.tools.offense.get_offense import GetOffenseTool


class TestGetOffenseTool:
    """Tests for GetOffenseTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = GetOffenseTool()
        assert tool.name == "get_offense"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = GetOffenseTool()
        assert tool.description == "Get offense data by ID from QRadar SIEM"

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = GetOffenseTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "offense_id" in schema["properties"]
        assert schema["properties"]["offense_id"]["type"] == "integer"
        assert "required" in schema
        assert "offense_id" in schema["required"]

    def test_input_schema_constraints(self):
        """Test that input schema has correct constraints."""
        tool = GetOffenseTool()
        schema = tool.input_schema

        offense_id_schema = schema["properties"]["offense_id"]
        assert offense_id_schema["minimum"] == 0
        assert "description" in offense_id_schema

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = GetOffenseTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "get_offense"
        assert definition["description"] == "Get offense data by ID from QRadar SIEM"
        assert "inputSchema" in definition

    @pytest.mark.asyncio
    async def test_execute_with_valid_offense_id(self):
        """Test executing tool with valid offense ID."""
        # Setup mock
        tool = GetOffenseTool()
        mock_response = httpx.Response(
            status_code=200,
            json={
                "id": 123,
                "description": "Test offense",
                "severity": 5
            },
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"offense_id": 123})

        # Verify client was called correctly
        tool.client.get.assert_called_once_with('siem/offenses/123')

        # Verify result
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "123" in result["content"][0]["text"]
        assert "isError" not in result

    @pytest.mark.asyncio
    async def test_execute_without_offense_id(self):
        """Test executing tool without offense_id parameter."""
        tool = GetOffenseTool()
        result = await tool.execute({})

        assert "content" in result
        assert result["content"][0]["text"] == "Error: offense_id is required"
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_execute_with_none_offense_id(self):
        """Test executing tool with None offense_id."""
        tool = GetOffenseTool()
        result = await tool.execute({"offense_id": None})

        assert "content" in result
        assert result["content"][0]["text"] == "Error: offense_id is required"
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_execute_with_http_error(self):
        """Test executing tool when HTTPError is raised."""
        tool = GetOffenseTool()
        mock_response = httpx.Response(
            status_code=404,
            json={"message": "Offense not found"},
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=mock_response.request,
            response=mock_response
        ))

        result = await tool.execute({"offense_id": 999})

        assert "content" in result
        assert "Error" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_execute_with_runtime_error(self):
        """Test executing tool when RuntimeError is raised."""
        tool = GetOffenseTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        result = await tool.execute({"offense_id": 456})

        assert "content" in result
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "API connection failed" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_execute_with_zero_offense_id(self):
        """Test executing tool with offense_id of 0."""
        tool = GetOffenseTool()
        mock_response = httpx.Response(
            status_code=200,
            json={"id": 0, "description": "Test"},
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"offense_id": 0})

        tool.client.get.assert_called_once_with('siem/offenses/0')
        assert "isError" not in result

    @pytest.mark.asyncio
    async def test_execute_with_large_offense_id(self):
        """Test executing tool with large offense_id."""
        large_id = 999999999
        tool = GetOffenseTool()
        mock_response = httpx.Response(
            status_code=200,
            json={"id": large_id, "description": "Test"},
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"offense_id": large_id})

        tool.client.get.assert_called_once_with(f'siem/offenses/{large_id}')
        assert "isError" not in result

    @pytest.mark.asyncio
    async def test_execute_response_format(self):
        """Test that execute returns properly formatted JSON response."""
        tool = GetOffenseTool()
        mock_response = httpx.Response(
            status_code=200,
            json={
                "id": 123,
                "description": "Test offense",
                "severity": 5,
                "magnitude": 3
            },
            request=httpx.Request("GET", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"offense_id": 123})

        # Verify the response contains formatted JSON
        response_text = result["content"][0]["text"]
        assert "id" in response_text
        assert "description" in response_text
        assert "severity" in response_text
