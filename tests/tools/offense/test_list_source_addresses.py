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
Unit tests for the ListSourceAddressesTool.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.offense.list_source_addresses import ListSourceAddressesTool


class TestListSourceAddressesTool:
    """Tests for ListSourceAddressesTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListSourceAddressesTool()
        assert tool.name == "list_source_addresses"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListSourceAddressesTool()
        assert "source IP addresses" in tool.description
        assert "offenses" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListSourceAddressesTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

        # Check all expected properties exist
        expected_props = ["filter", "limit", "offset", "fields"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_input_schema_types(self):
        """Test that input schema has correct types."""
        tool = ListSourceAddressesTool()
        schema = tool.input_schema

        # Check string properties
        assert schema["properties"]["filter"]["type"] == "string"
        assert schema["properties"]["fields"]["type"] == "string"

        # Check integer properties
        assert schema["properties"]["limit"]["type"] == "integer"
        assert schema["properties"]["offset"]["type"] == "integer"

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListSourceAddressesTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_source_addresses"
        assert "source IP addresses" in definition["description"]
        assert "inputSchema" in definition


class TestListSourceAddressesToolExecution:
    """Tests for ListSourceAddressesTool execute method."""

    @pytest.mark.asyncio
    async def test_execute_with_no_parameters(self):
        """Test executing tool with no parameters."""
        # Setup mock
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "source_ip": "192.168.1.100",
                    "magnitude": 5,
                    "network": "Net-192-168-1-0",
                    "offense_ids": [1, 2, 3],
                    "local_destination_count": 10,
                    "event_flow_count": 150,
                    "first_event_flow_seen": 1234567890000,
                    "last_event_flow_seen": 1234567900000
                },
                {
                    "id": 2,
                    "source_ip": "10.0.0.50",
                    "magnitude": 3,
                    "network": "Net-10-0-0-0",
                    "offense_ids": [4],
                    "local_destination_count": 5,
                    "event_flow_count": 75,
                    "first_event_flow_seen": 1234567890000,
                    "last_event_flow_seen": 1234567900000
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify client was called correctly
        tool.client.get.assert_called_once_with(
            'siem/source_addresses', params={}, headers={}
        )

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "192.168.1.100" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_filter(self):
        """Test executing tool with filter parameter."""
        # Setup mock
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "source_ip": "192.168.1.100",
                    "magnitude": 5
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "magnitude>4"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/source_addresses',
            params={"filter": "magnitude>4"},
            headers={},
        )

    @pytest.mark.asyncio
    async def test_execute_with_fields(self):
        """Test executing tool with fields parameter."""
        # Setup mock
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "source_ip": "192.168.1.100", "magnitude": 5}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,source_ip,magnitude"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/source_addresses',
            params={"fields": "id,source_ip,magnitude"},
            headers={},
        )

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self):
        """Test executing tool with all parameters."""
        # Setup mock
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "source_ip": "192.168.1.100", "magnitude": 5}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "filter": "magnitude>3",
            "fields": "id,source_ip,magnitude,offense_ids"
        })

        # Verify client was called with all params
        tool.client.get.assert_called_once_with(
            'siem/source_addresses',
            params={
                "filter": "magnitude>3",
                "fields": "id,source_ip,magnitude,offense_ids"
            },
            headers={},
        )

    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self):
        """Test executing tool with empty result."""
        # Setup mock
        tool = ListSourceAddressesTool()
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
    async def test_execute_filters_by_offense_id(self):
        """Test executing tool with filter for specific offense."""
        # Setup mock
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "source_ip": "192.168.1.100",
                    "offense_ids": [123]
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "offense_ids contains 123"})

        # Verify MCP result
        assert "content" in result
        assert "192.168.1.100" in result["content"][0]["text"]
        assert "123" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_filters_by_network(self):
        """Test executing tool with filter for network."""
        # Setup mock
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "source_ip": "192.168.1.100",
                    "network": "Net-192-168-1-0"
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "network='Net-192-168-1-0'"})

        # Verify MCP result
        assert "content" in result
        assert "192.168.1.100" in result["content"][0]["text"]
        assert "Net-192-168-1-0" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_filters_high_magnitude(self):
        """Test executing tool with filter for high magnitude sources."""
        # Setup mock
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "source_ip": "192.168.1.100", "magnitude": 8}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "magnitude>=7"})

        # Verify MCP result
        assert "content" in result
        assert "192.168.1.100" in result["content"][0]["text"]
        assert '"magnitude": 8' in result["content"][0]["text"]

class TestListSourceAddressesToolErrorHandling:
    """Tests for error handling in ListSourceAddressesTool."""

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()

        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(
            status_code=401,
            text="Unauthorized",
            request=mock_request
        )
        tool.client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "401 Error",
            request=mock_request,
            response=mock_response
        ))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "Error executing list_source_addresses: 401 Error" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_value_error(self):
        """Test handling of ValueError."""
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid value"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_runtime_error(self):
        """Test handling of RuntimeError."""
        tool = ListSourceAddressesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Runtime error occurred"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()
