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
Unit tests for the ListLogSourceTypesTool.
"""

import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.log_source.list_log_source_types import ListLogSourceTypesTool


class TestListLogSourceTypesToolMetadata:
    """Tests for ListLogSourceTypesTool metadata properties."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListLogSourceTypesTool()
        assert tool.name == "list_log_source_types"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListLogSourceTypesTool()
        assert "List available log source types in QRadar" in tool.description
        assert "log source types" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListLogSourceTypesTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListLogSourceTypesTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # Check expected properties exist
        expected_props = ["filter", "fields", "limit", "offset"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListLogSourceTypesTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_log_source_types"
        assert "List available log source types" in definition["description"]
        assert "inputSchema" in definition


class TestListLogSourceTypesToolExecution:
    """Tests for ListLogSourceTypesTool execute method."""

    @pytest.fixture
    def sample_log_source_types(self):
        """Sample log source type data."""
        return [
            {
                "id": 1,
                "name": "Cisco ASA",
                "custom": False,
                "version": "8.4",
                "protocol_types": [{"protocol_id": 0, "protocol_text": "Syslog"}]
            },
            {
                "id": 2,
                "name": "Microsoft Windows Security Event Log",
                "custom": False,
                "version": "2008",
                "protocol_types": [{"protocol_id": 1, "protocol_text": "WMI"}]
            },
            {
                "id": 100,
                "name": "Custom Application",
                "custom": True,
                "version": "1.0",
                "protocol_types": [{"protocol_id": 0, "protocol_text": "Syslog"}]
            }
        ]

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_log_source_types):
        """Test executing tool with fields parameter."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=[{"id": 1, "name": "Cisco ASA"}], request=mock_request)

        tool = ListLogSourceTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,name"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'config/event_sources/log_source_management/log_source_types',
            params={"fields": "id,name"},
            headers={}
        )

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self, sample_log_source_types):
        """Test executing tool with limit and offset."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=sample_log_source_types, request=mock_request)

        tool = ListLogSourceTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"limit": 50, "offset": 10})

        # Verify Range header was set
        call_args = tool.client.get.call_args
        assert 'headers' in call_args[1]
        assert 'Range' in call_args[1]['headers']
        assert call_args[1]['headers']['Range'] == "items=10-59"

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self, sample_log_source_types):
        """Test executing tool with all parameters."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=[sample_log_source_types[0]], request=mock_request)

        tool = ListLogSourceTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "filter": "custom=false",
            "fields": "id,name,custom",
            "limit": 10,
            "offset": 0
        })

        # Verify client was called with all params
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['filter'] == "custom=false"
        assert call_args[1]['params']['fields'] == "id,name,custom"
        assert call_args[1]['headers']['Range'] == "items=0-9"

    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self):
        """Test executing tool with empty result."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=[], request=mock_request)

        tool = ListLogSourceTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "[]" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_filters_custom_types(self, sample_log_source_types):
        """Test executing tool with filter for custom types."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=[sample_log_source_types[2]], request=mock_request)

        tool = ListLogSourceTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "custom=true"})

        # Verify MCP result
        assert "content" in result
        assert "Custom Application" in result["content"][0]["text"]

class TestListLogSourceTypesToolErrorHandling:
    """Tests for ListLogSourceTypesTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        # Setup mock to raise error
        tool = ListLogSourceTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" == result["content"][0]["text"].lower()
        assert "API connection failed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Setup mock to raise ValueError
        tool = ListLogSourceTypesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()
