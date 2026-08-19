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
Tests for Delete Staged Network Tool
"""

from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.config.delete_staged_network import DeleteStagedNetworkTool


@pytest.fixture
def tool():
    """Create a DeleteStagedNetworkTool instance for testing."""
    return DeleteStagedNetworkTool()


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
            "domain_id": 0,
        },
        {
            "id": 2,
            "network_id": 1,
            "group": "DMZ",
            "name": "Web Servers",
            "cidr": "203.0.113.0/24",
            "domain_id": 0,
        },
    ]


class TestDeleteStagedNetworkMetadata:
    """Test tool metadata properties."""

    def test_tool_name(self, tool):
        """Test that tool name is correct."""
        assert tool.name == "delete_staged_network"

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


class TestDeleteStagedNetworkExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_delete(self, tool, existing_networks):
        """Test successful removal of a network entry."""
        remaining = [existing_networks[1]]
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )
        put_response = httpx.Response(
            200,
            json=remaining,
            request=httpx.Request("PUT", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(return_value=put_response)

        result = await tool.execute({"network_id": 1})

        assert "content" in result
        assert result.get("isError") is not True
        assert "1" in result["content"][0]["text"]
        assert "removed" in result["content"][0]["text"].lower()

        put_call_args = tool.client.put.call_args
        sent_body = put_call_args[1]["data"]
        assert len(sent_body) == 1
        assert sent_body[0]["id"] == 2

    @pytest.mark.asyncio
    async def test_deleted_entry_absent_from_put_body(self, tool, existing_networks):
        """Test that the deleted entry's id is not present in the PUT payload."""
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )
        put_response = httpx.Response(
            200,
            json=[existing_networks[0]],
            request=httpx.Request("PUT", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(return_value=put_response)

        await tool.execute({"network_id": 2})

        put_call_args = tool.client.put.call_args
        sent_body = put_call_args[1]["data"]
        ids_in_body = [e["id"] for e in sent_body]
        assert 2 not in ids_in_body

    @pytest.mark.asyncio
    async def test_network_id_not_found(self, tool, existing_networks):
        """Test that an unknown network_id returns an error."""
        get_response = httpx.Response(
            200,
            json=existing_networks,
            request=httpx.Request("GET", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)

        result = await tool.execute({"network_id": 999})

        assert result["isError"] is True
        assert "999" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_missing_network_id(self, tool):
        """Test that missing network_id returns an error."""
        result = await tool.execute({})
        assert result["isError"] is True
        assert "network_id" in result["content"][0]["text"].lower()


class TestDeleteStagedNetworkErrorHandling:
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

        result = await tool.execute({"network_id": 1})

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
            500,
            text="Server error",
            request=httpx.Request("PUT", "http://test"),
        )
        http_error = httpx.HTTPStatusError(
            "Server error",
            request=mock_put_response.request,
            response=mock_put_response,
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=get_response)
        tool.client.put = AsyncMock(side_effect=http_error)

        result = await tool.execute({"network_id": 1})

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()
