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
Tests for Add Staged Network Tool
"""

import json
from unittest.mock import AsyncMock, call
import pytest
import httpx
from qradar_mcp.tools.config.add_staged_network import AddStagedNetworkTool


@pytest.fixture
def tool():
    """Create an AddStagedNetworkTool instance for testing."""
    return AddStagedNetworkTool()


@pytest.fixture
def existing_networks():
    """Mock staged network hierarchy with one existing entry."""
    return [
        {
            "id": 1,
            "network_id": 1,
            "group": "Internal",
            "name": "Corporate Network",
            "cidr": "10.0.0.0/8",
            "description": "Main corporate network",
            "domain_id": 0,
        }
    ]


@pytest.fixture
def updated_networks(existing_networks):
    """Mock PUT response containing existing plus new entry."""
    return existing_networks + [
        {
            "id": 2,
            "network_id": 1,
            "group": "DMZ",
            "name": "Web Servers",
            "cidr": "203.0.113.0/24",
            "domain_id": 0,
        }
    ]


class TestAddStagedNetworkMetadata:
    """Test tool metadata properties."""

    def test_tool_name(self, tool):
        """Test that tool name is correct."""
        assert tool.name == "add_staged_network"

    def test_tool_description(self, tool):
        """Test that tool has a description."""
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert "staged" in tool.description.lower()

    def test_input_schema(self, tool):
        """Test that input schema is properly defined."""
        input_schema = tool.input_schema
        assert isinstance(input_schema, dict)
        assert input_schema["type"] == "object"
        props = input_schema["properties"]
        assert "group" in props
        assert "name" in props
        assert "cidr" in props
        required = input_schema.get("required", [])
        assert "group" in required
        assert "name" in required
        assert "cidr" in required

    def test_approval_required(self, tool):
        """Test that tool requires approval (write operation)."""
        assert tool.approval_required is True

    def test_http_verb(self, tool):
        """Test that http_verb is PUT."""
        assert tool.http_verb == "PUT"


class TestAddStagedNetworkExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_add(self, tool, existing_networks, updated_networks):
        """Test successful addition of a new network entry."""
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )
        put_response = httpx.Response(
            200,
            json=updated_networks,
            request=httpx.Request("PUT", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(return_value=put_response)

        result = await tool.execute({
            "group": "DMZ",
            "name": "Web Servers",
            "cidr": "203.0.113.0/24",
        })

        assert "content" in result
        assert result.get("isError") is not True
        content = json.loads(result["content"][0]["text"])
        assert len(content) == 2
        assert content[1]["name"] == "Web Servers"

        tool.client.get.assert_called_once_with(
            'config/network_hierarchy/staged_networks', params={})

        put_call_args = tool.client.put.call_args
        sent_body = put_call_args[1]["data"]
        assert len(sent_body) == 2
        new_entry = sent_body[1]
        assert new_entry["group"] == "DMZ"
        assert new_entry["name"] == "Web Servers"
        assert new_entry["cidr"] == "203.0.113.0/24"
        assert "id" not in new_entry

    @pytest.mark.asyncio
    async def test_add_with_optional_fields(
        self, tool, existing_networks, updated_networks
    ):
        """Test addition with optional description, domain_id, country_code."""
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )
        put_response = httpx.Response(
            200,
            json=updated_networks,
            request=httpx.Request("PUT", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(return_value=put_response)

        await tool.execute({
            "group": "DMZ",
            "name": "Web Servers",
            "cidr": "203.0.113.0/24",
            "description": "Public-facing servers",
            "domain_id": 0,
            "country_code": "US",
        })

        put_call_args = tool.client.put.call_args
        sent_body = put_call_args[1]["data"]
        new_entry = sent_body[1]
        assert new_entry["description"] == "Public-facing servers"
        assert new_entry["domain_id"] == 0
        assert new_entry["country_code"] == "US"

    @pytest.mark.asyncio
    async def test_missing_group(self, tool):
        """Test that missing group returns an error."""
        result = await tool.execute({"name": "Web Servers", "cidr": "203.0.113.0/24"})
        assert result["isError"] is True
        assert "group" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_missing_name(self, tool):
        """Test that missing name returns an error."""
        result = await tool.execute({"group": "DMZ", "cidr": "203.0.113.0/24"})
        assert result["isError"] is True
        assert "name" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_missing_cidr(self, tool):
        """Test that missing cidr returns an error."""
        result = await tool.execute({"group": "DMZ", "name": "Web Servers"})
        assert result["isError"] is True
        assert "cidr" in result["content"][0]["text"].lower()


class TestAddStagedNetworkErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_get_http_error(self, tool):
        """Test that GET errors are propagated."""
        mock_response = httpx.Response(
            500,
            text="Server error",
            request=httpx.Request("GET", "http://test"),
        )
        http_error = httpx.HTTPStatusError(
            "Server error",
            request=mock_response.request,
            response=mock_response,
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({
            "group": "DMZ",
            "name": "Web Servers",
            "cidr": "203.0.113.0/24",
        })

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_put_http_error(self, tool, existing_networks):
        """Test that PUT errors are propagated."""
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )
        mock_put_response = httpx.Response(
            422,
            text="Invalid CIDR",
            request=httpx.Request("PUT", "http://test"),
        )
        http_error = httpx.HTTPStatusError(
            "Invalid CIDR",
            request=mock_put_response.request,
            response=mock_put_response,
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(side_effect=http_error)

        result = await tool.execute({
            "group": "DMZ",
            "name": "Web Servers",
            "cidr": "not-a-cidr",
        })

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()
