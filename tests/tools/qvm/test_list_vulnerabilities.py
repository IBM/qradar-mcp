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
Unit tests for the ListVulnerabilitiesTool.
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.qvm.list_vulnerabilities import ListVulnerabilitiesTool


class TestListVulnerabilitiesToolMetadata:
    """Tests for ListVulnerabilitiesTool metadata properties."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListVulnerabilitiesTool()
        assert tool.name == "list_vulnerabilities"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListVulnerabilitiesTool()
        assert "List vulnerabilities" in tool.description
        assert "QVM" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListVulnerabilitiesTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListVulnerabilitiesTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # Check expected properties exist
        expected_props = ["saved_search_id", "saved_search_name", "filters"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListVulnerabilitiesTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_vulnerabilities"
        assert "List vulnerabilities" in definition["description"]
        assert "inputSchema" in definition


class TestListVulnerabilitiesToolExecution:
    """Tests for ListVulnerabilitiesTool execute method."""

    @pytest.fixture
    def sample_vulnerabilities(self):
        """Sample vulnerability data."""
        return [
            {
                "id": 1001,
                "name": "CVE-2021-44228",
                "cvss_score": 10.0,
                "severity": "CRITICAL",
                "published_date": 1639094400000,
                "description": "Log4j Remote Code Execution"
            },
            {
                "id": 1002,
                "name": "CVE-2021-45046",
                "cvss_score": 9.0,
                "severity": "HIGH",
                "published_date": 1639180800000,
                "description": "Log4j Denial of Service"
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

        tool = ListVulnerabilitiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "[]" in result["content"][0]["text"]

class TestListVulnerabilitiesToolErrorHandling:
    """Tests for ListVulnerabilitiesTool error handling."""

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
        tool = ListVulnerabilitiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "Error executing list_vulnerabilities: 404 Not Found" in result["content"][0]["text"]

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
        tool = ListVulnerabilitiesTool()
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
        tool = ListVulnerabilitiesTool()
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
        tool = ListVulnerabilitiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()


class TestListVulnerabilitiesToolParameterHandling:
    """Tests for parameter handling in ListVulnerabilitiesTool."""

    @pytest.mark.asyncio
    async def test_execute_with_saved_search_id(self):
        """Test executing with saved_search_id parameter."""
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListVulnerabilitiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"saved_search_id": 456})

        # Verify savedSearchId was passed
        tool.client.get.assert_called_once_with('qvm/vulns', params={"savedSearchId": 456})

    @pytest.mark.asyncio
    async def test_execute_with_saved_search_name(self):
        """Test executing with saved_search_name parameter."""
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListVulnerabilitiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"saved_search_name": "Critical Vulns"})

        # Verify savedSearchName was passed
        tool.client.get.assert_called_once_with('qvm/vulns', params={"savedSearchName": "Critical Vulns"})

    @pytest.mark.asyncio
    async def test_execute_with_filters(self):
        """Test executing with filters parameter."""
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )

        tool = ListVulnerabilitiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filters": "cvss_score>7"})

        # Verify filters was passed
        tool.client.get.assert_called_once_with('qvm/vulns', params={"filters": "cvss_score>7"})

    @pytest.mark.asyncio
    async def test_execute_with_dict_response(self):
        """Test handling dict response with data key."""
        mock_response = httpx.Response(
            200,
            json={"data": [{"id": 1001}, {"id": 1002}]},
            request=httpx.Request("GET", "http://test")
        )

        tool = ListVulnerabilitiesTool()
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

        tool = ListVulnerabilitiesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({"saved_search_id": 999})

        assert result["isError"] is True
        assert "Error executing list_vulnerabilities: 420 Error" in result["content"][0]["text"]