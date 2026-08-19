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
Unit tests for the ListQvmAssetsTool.
"""

import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.qvm.list_qvm_assets import ListQvmAssetsTool


class TestListQvmAssetsToolMetadata:
    """Tests for ListQvmAssetsTool metadata properties."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListQvmAssetsTool()
        assert tool.name == "list_qvm_assets"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListQvmAssetsTool()
        assert "List assets with vulnerability information from QVM" in tool.description
        assert "QVM" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListQvmAssetsTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListQvmAssetsTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # Check expected properties exist
        expected_props = ["saved_search_id", "saved_search_name", "filters"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListQvmAssetsTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_qvm_assets"
        assert "List assets with vulnerability information from QVM" in definition["description"]
        assert "inputSchema" in definition


class TestListQvmAssetsToolExecution:
    """Tests for ListQvmAssetsTool execute method."""

    @pytest.fixture
    def sample_qvm_assets(self):
        """Sample QVM asset data."""
        return [
            {
                "id": 1,
                "ip_address": "192.168.1.100",
                "hostname": "server1.example.com",
                "vulnerability_count": 15,
                "risk_score": 85.5,
                "last_scan_date": 1234567890000
            },
            {
                "id": 2,
                "ip_address": "192.168.1.101",
                "hostname": "server2.example.com",
                "vulnerability_count": 3,
                "risk_score": 25.0,
                "last_scan_date": 1234567891000
            }
        ]


    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self):
        """Test executing tool with empty result."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "[]" in result["content"][0]["text"]

class TestListQvmAssetsToolErrorHandling:
    """Tests for ListQvmAssetsTool error handling."""

    @pytest.mark.asyncio
    async def test_qvm_module_not_available(self):
        """Test handling when QVM module is not available (404)."""
        # Setup mock to raise 404 HTTPStatusError
        mock_response = httpx.Response(
            404,
            request=httpx.Request("GET", "http://test")
        )
        http_error = httpx.HTTPStatusError("404 Not Found", request=mock_response.request, response=mock_response)

        # Execute
        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "Error executing list_qvm_assets: 404 Not Found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_permission_denied_error(self):
        """Test handling when user lacks permissions (403)."""
        # Setup mock to raise 403 HTTPStatusError
        mock_response = httpx.Response(
            403,
            request=httpx.Request("GET", "http://test")
        )
        http_error = httpx.HTTPStatusError("403 Forbidden", request=mock_response.request, response=mock_response)

        # Execute
        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({})

        # Verify error response mentions permissions
        assert result["isError"] is True
        assert "permission" in result["content"][0]["text"].lower() or "403" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of general API errors."""
        # Setup mock to raise error
        tool = ListQvmAssetsTool()
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
        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()


class TestListQvmAssetsToolParameterHandling:
    """Tests for parameter handling in ListQvmAssetsTool."""

    @pytest.mark.asyncio
    async def test_execute_with_saved_search_id(self):
        """Test executing with saved_search_id parameter."""
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"saved_search_id": 123})

        # Verify savedSearchId was passed
        tool.client.get.assert_called_once_with('qvm/assets', params={"savedSearchId": 123})

    @pytest.mark.asyncio
    async def test_execute_with_saved_search_name(self):
        """Test executing with saved_search_name parameter."""
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"saved_search_name": "My Search"})

        # Verify savedSearchName was passed
        tool.client.get.assert_called_once_with('qvm/assets', params={"savedSearchName": "My Search"})

    @pytest.mark.asyncio
    async def test_execute_with_filters(self):
        """Test executing with filters parameter."""
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filters": "risk_score>50"})

        # Verify filters was passed
        tool.client.get.assert_called_once_with('qvm/assets', params={"filters": "risk_score>50"})

    @pytest.mark.asyncio
    async def test_execute_with_dict_response(self):
        """Test handling dict response with data key."""
        mock_response = httpx.Response(
            200,
            json={"data": [{"id": 1}, {"id": 2}]},
            request=httpx.Request("GET", "http://test")
        )

        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert result.get("isError") is not True
        assert "data" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_invalid_search_parameters(self):
        """Test handling invalid search parameters (420)."""
        mock_response = httpx.Response(
            420,
            request=httpx.Request("GET", "http://test")
        )
        http_error = httpx.HTTPStatusError("420 Error", request=mock_response.request, response=mock_response)

        tool = ListQvmAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({"saved_search_id": 999})

        assert result["isError"] is True
        assert "Error executing list_qvm_assets: 420 Error" in result["content"][0]["text"]