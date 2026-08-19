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
Unit tests for the ListOffenseTypesTool.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.offense.list_offense_types import ListOffenseTypesTool


class TestListOffenseTypesTool:
    """Tests for ListOffenseTypesTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListOffenseTypesTool()
        assert tool.name == "list_offense_types"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListOffenseTypesTool()
        assert "List all offense type categories" in tool.description
        assert "categorization" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListOffenseTypesTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

        # Check all expected properties exist
        expected_props = ["filter", "sort", "fields"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_input_schema_types(self):
        """Test that input schema has correct types."""
        tool = ListOffenseTypesTool()
        schema = tool.input_schema

        # Check string properties
        assert schema["properties"]["filter"]["type"] == "string"
        assert schema["properties"]["sort"]["type"] == "string"
        assert schema["properties"]["fields"]["type"] == "string"

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListOffenseTypesTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_offense_types"
        assert "List all offense type categories" in definition["description"]
        assert "inputSchema" in definition


class TestListOffenseTypesToolExecution:
    """Tests for ListOffenseTypesTool execute method."""

    @pytest.mark.asyncio
    async def test_execute_with_no_parameters(self):
        """Test executing tool with no parameters."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "name": "Source IP",
                    "database_type": "EVENTS",
                    "custom": False,
                    "property_name": "sourceip"
                },
                {
                    "id": 2,
                    "name": "Destination IP",
                    "database_type": "FLOWS",
                    "custom": False,
                    "property_name": "destinationip"
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify client was called correctly
        tool.client.get.assert_called_once_with(
            'siem/offense_types',
            params={},
            headers={'Range': 'items=0-9'},
        )

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "Source IP" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_filter(self):
        """Test executing tool with filter parameter."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "name": "Source IP",
                    "database_type": "EVENTS",
                    "custom": False
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "database_type='EVENTS'"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/offense_types',
            params={"filter": "database_type='EVENTS'"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_sort(self):
        """Test executing tool with sort parameter."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "name": "A Type"},
                {"id": 2, "name": "B Type"}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"sort": "+name"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/offense_types',
            params={"sort": "+name"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_fields(self):
        """Test executing tool with fields parameter."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "name": "Source IP"}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,name"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/offense_types',
            params={"fields": "id,name"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self):
        """Test executing tool with all parameters."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "name": "Custom Type", "custom": True}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "filter": "custom=true",
            "sort": "-id",
            "fields": "id,name,custom"
        })

        # Verify client was called with all params
        tool.client.get.assert_called_once_with(
            'siem/offense_types',
            params={
                "filter": "custom=true",
                "sort": "-id",
                "fields": "id,name,custom",
            },
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self):
        """Test executing tool with empty result."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "[]" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_filters_custom_types(self):
        """Test executing tool with filter for custom types."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 100, "name": "My Custom Type", "custom": True}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "custom=true"})

        # Verify MCP result
        assert "content" in result
        assert "My Custom Type" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_filters_by_database_type(self):
        """Test executing tool with filter for database type."""
        # Setup mock
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "name": "Event Type", "database_type": "EVENTS"}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "database_type='EVENTS'"})

        # Verify MCP result
        assert "content" in result
        assert "Event Type" in result["content"][0]["text"]
        assert "EVENTS" in result["content"][0]["text"]

class TestListOffenseTypesToolErrorHandling:
    """Tests for error handling in ListOffenseTypesTool."""

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()

        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(
            status_code=403,
            text="Forbidden",
            request=mock_request
        )
        tool.client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "403 Error",
            request=mock_request,
            response=mock_response
        ))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "Error executing list_offense_types: 403 Error" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_value_error(self):
        """Test handling of ValueError."""
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid value"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_runtime_error(self):
        """Test handling of RuntimeError."""
        tool = ListOffenseTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Runtime error occurred"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()
