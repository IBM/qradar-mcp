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
Tests for Update Staged Network Tool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.config.update_staged_network import UpdateStagedNetworkTool


@pytest.fixture
def tool():
    """Create an UpdateStagedNetworkTool instance for testing."""
    return UpdateStagedNetworkTool()


@pytest.fixture
def existing_networks():
    """Mock staged network hierarchy with two entries."""
    return [
        {
            "id": 1,
            "network_id": 1,
            "group": "Internal",
            "name": "Corporate Network",
            "cidr": "10.0.0.0/8",
            "description": "Main corporate network",
            "domain_id": 0,
        },
        {
            "id": 2,
            "network_id": 1,
            "group": "DMZ",
            "name": "Web Servers",
            "cidr": "203.0.113.0/24",
            "description": "Public-facing web servers",
            "domain_id": 0,
        },
    ]


class TestUpdateStagedNetworkMetadata:
    """Test tool metadata properties."""

    def test_tool_name(self, tool):
        """Test that tool name is correct."""
        assert tool.name == "update_staged_network"

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
        assert "network_id" in input_schema["properties"]
        assert "network_id" in input_schema.get("required", [])

    def test_approval_required(self, tool):
        """Test that tool requires approval (write operation)."""
        assert tool.approval_required is True

    def test_http_verb(self, tool):
        """Test that http_verb is PUT."""
        assert tool.http_verb == "PUT"


class TestUpdateStagedNetworkExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_partial_update(self, tool, existing_networks):
        """Test that only supplied fields are updated; others are preserved."""
        updated_list = [
            dict(existing_networks[0], name="Corp LAN"),
            existing_networks[1],
        ]
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )
        put_response = httpx.Response(
            200,
            json=updated_list,
            request=httpx.Request("PUT", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(return_value=put_response)

        result = await tool.execute({"network_id": 1, "name": "Corp LAN"})

        assert "content" in result
        assert result.get("isError") is not True

        put_call_args = tool.client.put.call_args
        sent_body = put_call_args[1]["data"]
        # Entry with id=1 should have the new name
        entry_1 = next(e for e in sent_body if e["id"] == 1)
        assert entry_1["name"] == "Corp LAN"
        # Other fields on entry 1 should be preserved
        assert entry_1["cidr"] == "10.0.0.0/8"
        assert entry_1["group"] == "Internal"
        # Entry with id=2 must be unchanged
        entry_2 = next(e for e in sent_body if e["id"] == 2)
        assert entry_2["name"] == "Web Servers"

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, tool, existing_networks):
        """Test updating several fields at once."""
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )
        put_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("PUT", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(return_value=put_response)

        await tool.execute({
            "network_id": 2,
            "name": "DMZ Servers",
            "description": "Updated DMZ description",
            "country_code": "CA",
        })

        put_call_args = tool.client.put.call_args
        sent_body = put_call_args[1]["data"]
        entry_2 = next(e for e in sent_body if e["id"] == 2)
        assert entry_2["name"] == "DMZ Servers"
        assert entry_2["description"] == "Updated DMZ description"
        assert entry_2["country_code"] == "CA"
        # Unchanged fields preserved
        assert entry_2["cidr"] == "203.0.113.0/24"

    @pytest.mark.asyncio
    async def test_network_id_not_found(self, tool, existing_networks):
        """Test that a missing network_id returns an error."""
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)

        result = await tool.execute({"network_id": 999, "name": "Ghost"})

        assert result["isError"] is True
        assert "999" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_no_update_fields_provided(self, tool):
        """Test that providing only network_id with no update fields errors."""
        result = await tool.execute({"network_id": 1})

        assert result["isError"] is True
        assert "at least one update field" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_missing_network_id(self, tool):
        """Test that missing network_id returns an error."""
        result = await tool.execute({"name": "New Name"})
        assert result["isError"] is True
        assert "network_id" in result["content"][0]["text"].lower()


class TestUpdateStagedNetworkErrorHandling:
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

        result = await tool.execute({"network_id": 1, "name": "New Name"})

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

        result = await tool.execute({"network_id": 1, "cidr": "bad-cidr"})

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()
