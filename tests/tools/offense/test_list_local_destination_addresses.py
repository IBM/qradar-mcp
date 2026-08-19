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
Unit tests for the ListLocalDestinationAddressesTool.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.offense.list_local_destination_addresses import ListLocalDestinationAddressesTool


class TestListLocalDestinationAddressesTool:
    """Tests for ListLocalDestinationAddressesTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListLocalDestinationAddressesTool()
        assert tool.name == "list_local_destination_addresses"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListLocalDestinationAddressesTool()
        assert "local destination IP addresses" in tool.description
        assert "offenses" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListLocalDestinationAddressesTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

        # Check all expected properties exist
        expected_props = ["filter", "fields"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_input_schema_types(self):
        """Test that input schema has correct types."""
        tool = ListLocalDestinationAddressesTool()
        schema = tool.input_schema

        # Check string properties
        assert schema["properties"]["filter"]["type"] == "string"
        assert schema["properties"]["fields"]["type"] == "string"

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListLocalDestinationAddressesTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_local_destination_addresses"
        assert "local destination IP addresses" in definition["description"]
        assert "inputSchema" in definition


class TestListLocalDestinationAddressesToolExecution:
    """Tests for ListLocalDestinationAddressesTool execute method."""

    @pytest.mark.asyncio
    async def test_execute_with_no_parameters(self):
        """Test executing tool with no parameters."""
        # Setup mock
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "local_destination_ip": "10.0.1.50",
                    "magnitude": 6,
                    "network": "Net-10-0-1-0",
                    "offense_ids": [1, 2],
                    "source_address_ids": [10, 11, 12],
                    "event_flow_count": 200,
                    "first_event_flow_seen": 1234567890000,
                    "last_event_flow_seen": 1234567900000
                },
                {
                    "id": 2,
                    "local_destination_ip": "10.0.2.100",
                    "magnitude": 4,
                    "network": "Net-10-0-2-0",
                    "offense_ids": [3],
                    "source_address_ids": [13],
                    "event_flow_count": 100,
                    "first_event_flow_seen": 1234567890000,
                    "last_event_flow_seen": 1234567900000
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify client was called correctly — default limit=10 always sends Range
        tool.client.get.assert_called_once_with(
            'siem/local_destination_addresses',
            params={},
            headers={'Range': 'items=0-9'},
        )

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "10.0.1.50" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_filter(self):
        """Test executing tool with filter parameter."""
        # Setup mock
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "local_destination_ip": "10.0.1.50",
                    "magnitude": 6
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "magnitude>5"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/local_destination_addresses',
            params={"filter": "magnitude>5"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_fields(self):
        """Test executing tool with fields parameter."""
        # Setup mock
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "local_destination_ip": "10.0.1.50", "magnitude": 6}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,local_destination_ip,magnitude"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/local_destination_addresses',
            params={"fields": "id,local_destination_ip,magnitude"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self):
        """Test executing tool with all parameters."""
        # Setup mock
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "local_destination_ip": "10.0.1.50", "magnitude": 6}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "filter": "magnitude>4",
            "fields": "id,local_destination_ip,magnitude,offense_ids"
        })

        # Verify client was called with all params
        tool.client.get.assert_called_once_with(
            'siem/local_destination_addresses',
            params={
                "filter": "magnitude>4",
                "fields": "id,local_destination_ip,magnitude,offense_ids",
            },
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self):
        """Test executing tool with empty result."""
        # Setup mock
        tool = ListLocalDestinationAddressesTool()
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
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "local_destination_ip": "10.0.1.50",
                    "offense_ids": [456]
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "offense_ids contains 456"})

        # Verify MCP result
        assert "content" in result
        assert "10.0.1.50" in result["content"][0]["text"]
        assert "456" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_filters_by_network(self):
        """Test executing tool with filter for network."""
        # Setup mock
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {
                    "id": 1,
                    "local_destination_ip": "10.0.1.50",
                    "network": "Net-10-0-1-0"
                }
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "network='Net-10-0-1-0'"})

        # Verify MCP result
        assert "content" in result
        assert "10.0.1.50" in result["content"][0]["text"]
        assert "Net-10-0-1-0" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_filters_high_magnitude(self):
        """Test executing tool with filter for high magnitude destinations."""
        # Setup mock
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "local_destination_ip": "10.0.1.50", "magnitude": 9}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "magnitude>=8"})

        # Verify MCP result
        assert "content" in result
        assert "10.0.1.50" in result["content"][0]["text"]
        assert '"magnitude": 9' in result["content"][0]["text"]



    @pytest.mark.asyncio
    async def test_execute_with_explicit_limit(self):
        """Test that an explicit limit sets the Range header correctly."""
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[{"id": 1, "local_destination_ip": "10.0.1.50"}],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        await tool.execute({"limit": 5})

        tool.client.get.assert_called_once_with(
            'siem/local_destination_addresses',
            params={},
            headers={'Range': 'items=0-4'},
        )

    @pytest.mark.asyncio
    async def test_execute_default_limit_sends_range(self):
        """Test that the default limit of 10 always sends a Range header."""
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        await tool.execute({})

        _, kwargs = tool.client.get.call_args
        assert kwargs["headers"] == {'Range': 'items=0-9'}



class TestListLocalDestinationAddressesToolErrorHandling:
    """Tests for error handling in ListLocalDestinationAddressesTool."""

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()

        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(
            status_code=404,
            text="Not found",
            request=mock_request
        )
        tool.client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "404 Error",
            request=mock_request,
            response=mock_response
        ))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "Error executing list_local_destination_addresses: 404 Error" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_value_error(self):
        """Test handling of ValueError."""
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid value"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_runtime_error(self):
        """Test handling of RuntimeError."""
        tool = ListLocalDestinationAddressesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Runtime error occurred"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()
