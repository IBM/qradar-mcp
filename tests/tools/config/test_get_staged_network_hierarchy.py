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
Tests for Get Staged Network Hierarchy Tool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.config.get_staged_network_hierarchy import (
    GetStagedNetworkHierarchyTool,
)


@pytest.fixture
def tool():
    """Create a GetStagedNetworkHierarchyTool instance for testing."""
    return GetStagedNetworkHierarchyTool()


@pytest.fixture
def mock_networks():
    """Mock staged network hierarchy response."""
    return [
        {
            "id": 1,
            "network_id": 1,
            "group": "Internal",
            "name": "Corporate Network - Updated",
            "cidr": "10.0.0.0/8",
            "description": "Pending update",
            "domain_id": 0,
            "country_code": "CA",
        }
    ]


class TestGetStagedNetworkHierarchyMetadata:
    """Test tool metadata properties."""

    def test_tool_name(self, tool):
        """Test that tool name is correct."""
        assert tool.name == "get_staged_network_hierarchy"

    def test_tool_description(self, tool):
        """Test that tool has a description."""
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert "staged network hierarchy" in tool.description.lower()

    def test_input_schema(self, tool):
        """Test that input schema is properly defined."""
        schema = tool.input_schema
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "fields" in schema["properties"]


class TestGetStagedNetworkHierarchyExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_execution(self, tool, mock_networks):
        """Test successful staged network hierarchy retrieval."""
        mock_response = httpx.Response(
            200,
            json=mock_networks,
            request=httpx.Request("GET", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "content" in result
        assert len(result["content"]) == 1
        content = json.loads(result["content"][0]["text"])
        assert len(content) == 1
        assert content[0]["name"] == "Corporate Network - Updated"
        tool.client.get.assert_called_once_with(
            'config/network_hierarchy/staged_networks', params={}
        )

    @pytest.mark.asyncio
    async def test_execution_with_fields(self, tool, mock_networks):
        """Test execution with field selection."""
        mock_response = httpx.Response(
            200,
            json=mock_networks,
            request=httpx.Request("GET", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,name,cidr,group"})

        assert "content" in result
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["fields"] == "id,name,cidr,group"


class TestGetStagedNetworkHierarchyErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_http_error_handling(self, tool):
        """Test handling of HTTP errors."""
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

        result = await tool.execute({})

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()
