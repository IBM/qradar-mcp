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
Unit tests for the ListAssetPropertiesTool.
"""
import httpx
import pytest
from unittest.mock import AsyncMock
from qradar_mcp.tools.asset.list_asset_properties import ListAssetPropertiesTool


class TestListAssetPropertiesToolMetadata:
    """Tests for ListAssetPropertiesTool metadata properties."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListAssetPropertiesTool()
        assert tool.name == "list_asset_properties"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListAssetPropertiesTool()
        assert "List available asset property types" in tool.description
        assert "custom properties" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListAssetPropertiesTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListAssetPropertiesTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # Check expected properties exist (no sort parameter)
        expected_props = ["filter", "fields", "limit", "offset"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListAssetPropertiesTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_asset_properties"
        assert "List available asset property types" in definition["description"]
        assert "inputSchema" in definition


class TestListAssetPropertiesToolExecution:
    """Tests for ListAssetPropertiesTool execute method."""

    @pytest.fixture
    def sample_properties(self):
        """Sample asset property data."""
        return [
            {
                "id": 1001,
                "name": "Location",
                "type_id": 1,
                "type": "String",
                "last_reported": 1234567890000
            },
            {
                "id": 1002,
                "name": "Department",
                "type_id": 1,
                "type": "String",
                "last_reported": 1234567891000
            }
        ]

    @pytest.mark.asyncio
    async def test_execute_with_no_parameters(self, sample_properties):
        """Test executing tool with no parameters."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_properties,
            request=httpx.Request("GET", "http://test")
        )

        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify client was called correctly
        tool.client.get.assert_called_once_with('asset_model/properties', params={}, headers={})

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "Location" in result["content"][0]["text"]
        assert "Department" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_filter(self, sample_properties):
        """Test executing tool with filter parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=[sample_properties[0]],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "name='Location'"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'asset_model/properties',
            params={"filter": "name='Location'"},
            headers={}
        )

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_properties):
        """Test executing tool with fields parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=[{"id": 1001, "name": "Location"}],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,name"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'asset_model/properties',
            params={"fields": "id,name"},
            headers={}
        )

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self, sample_properties):
        """Test executing tool with limit and offset."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_properties,
            request=httpx.Request("GET", "http://test")
        )

        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"limit": 10, "offset": 5})

        # Verify Range header was set
        call_args = tool.client.get.call_args
        # Headers are passed as keyword argument
        assert call_args[1]['headers']['Range'] == "items=5-14"

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self, sample_properties):
        """Test executing tool with all parameters."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=[sample_properties[0]],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "filter": "type='String'",
            "fields": "id,name,type",
            "limit": 5,
            "offset": 0
        })

        # Verify client was called with all params (no sort)
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['filter'] == "type='String'"
        assert call_args[1]['params']['fields'] == "id,name,type"
        assert call_args[1]['headers']['Range'] == "items=0-4"

    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self):
        """Test executing tool with empty result."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "[]" in result["content"][0]["text"]

class TestListAssetPropertiesToolErrorHandling:
    """Tests for ListAssetPropertiesTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        # Setup mock to raise error
        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" == result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Setup mock to raise ValueError
        tool = ListAssetPropertiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()
