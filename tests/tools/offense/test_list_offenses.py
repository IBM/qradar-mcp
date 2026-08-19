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
Unit tests for the ListOffensesTool.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from qradar_mcp.tools.offense.list_offenses import ListOffensesTool


class TestListOffensesTool:
    """Tests for ListOffensesTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListOffensesTool()
        assert tool.name == "list_offenses"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListOffensesTool()
        assert "List offenses from QRadar SIEM" in tool.description
        assert "filtering" in tool.description
        assert "sorting" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListOffensesTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

        # Check all expected properties exist
        expected_props = ["filter", "sort", "fields", "limit", "offset", "format_output"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_input_schema_constraints(self):
        """Test that input schema has correct constraints."""
        tool = ListOffensesTool()
        schema = tool.input_schema

        # Check limit constraints
        limit_schema = schema["properties"]["limit"]
        assert limit_schema["type"] == "integer"
        assert limit_schema["minimum"] == 1
        assert limit_schema["maximum"] == 10000
        assert limit_schema["default"] == 10

        # Check offset constraints
        offset_schema = schema["properties"]["offset"]
        assert offset_schema["type"] == "integer"
        assert offset_schema["minimum"] == 0
        assert offset_schema["default"] == 0

        # Check format_output
        format_schema = schema["properties"]["format_output"]
        assert format_schema["type"] == "boolean"
        assert format_schema["default"] is False

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListOffensesTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_offenses"
        assert "List offenses" in definition["description"]
        assert "inputSchema" in definition


class TestListOffensesToolExecution:
    """Tests for ListOffensesTool execute method."""

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_with_no_parameters(self, mock_format):
        """Test executing tool with no parameters (defaults)."""
        # Setup mocks
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "description": "Test offense 1"},
                {"id": 2, "description": "Test offense 2"}
            ],
            headers={"Content-Range": "items 0-1/100"},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Formatted offense list"

        result = await tool.execute({})

        # Verify API was called with correct defaults
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[1]["api_path"] == "siem/offenses"

        # Verify headers contain range
        headers = call_args[1]["headers"]
        assert "Range" in headers
        assert headers["Range"] == "items=0-49"  # Default limit=50, offset=0

        # Verify result
        assert "content" in result
        assert result["content"][0]["text"] == "Formatted offense list"
        assert "isError" not in result

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_with_filter(self, mock_format):
        """Test executing tool with filter parameter."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[{"id": 1}],
            headers={},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Filtered offenses"

        result = await tool.execute({"filter": "status='OPEN'"})

        # Verify filter was passed to API
        call_args = tool.client.get.call_args
        params = call_args[1]["params"]
        assert "filter" in params
        assert params["filter"] == "status='OPEN'"

        assert "isError" not in result

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_with_sort(self, mock_format):
        """Test executing tool with sort parameter."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[],
            headers={},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Sorted offenses"

        result = await tool.execute({"sort": "-severity"})

        # Verify sort was passed to API
        call_args = tool.client.get.call_args
        params = call_args[1]["params"]
        assert "sort" in params
        assert params["sort"] == "-severity"

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_with_fields(self, mock_format):
        """Test executing tool with fields parameter."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[],
            headers={},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Offenses with fields"

        result = await tool.execute({"fields": "id,description,severity"})

        # Verify fields were passed to API
        call_args = tool.client.get.call_args
        params = call_args[1]["params"]
        assert "fields" in params
        assert params["fields"] == "id,description,severity"


    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_with_pagination(self, mock_format):
        """Test executing tool with limit and offset."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[],
            headers={},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Paginated offenses"

        result = await tool.execute({"limit": 100, "offset": 50})

        # Verify range header
        call_args = tool.client.get.call_args
        headers = call_args[1]["headers"]
        assert headers["Range"] == "items=50-149"  # offset=50, limit=100

    @pytest.mark.asyncio
    async def test_execute_with_format_output_false(self):
        """Test executing tool with format_output=false returns raw JSON."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_offenses = [
            {"id": 1, "description": "Test 1"},
            {"id": 2, "description": "Test 2"}
        ]
        mock_response = httpx.Response(
            status_code=200,
            json=mock_offenses,
            headers={"Content-Range": "items 0-1/50"},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"format_output": False})

        # Verify raw JSON is returned
        assert "content" in result
        response_text = result["content"][0]["text"]
        assert '"offenses"' in response_text
        assert '"count": 2' in response_text
        assert '"total_count": 50' in response_text

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.validate_filter_expression')
    async def test_execute_with_invalid_filter(self, mock_validate):
        """Test executing tool with invalid filter expression."""
        mock_validate.return_value = (False, "Unbalanced parentheses")

        tool = ListOffensesTool()
        result = await tool.execute({"filter": "status='OPEN' and ("})

        assert "content" in result
        assert "Invalid filter expression" in result["content"][0]["text"]
        assert "Unbalanced parentheses" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.validate_sort_expression')
    async def test_execute_with_invalid_sort(self, mock_validate):
        """Test executing tool with invalid sort expression."""
        mock_validate.return_value = (False, "Invalid field name")

        tool = ListOffensesTool()
        result = await tool.execute({"sort": "invalid@field"})

        assert "content" in result
        assert "Invalid sort expression" in result["content"][0]["text"]
        assert "Invalid field name" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_execute_with_api_error(self):
        """Test executing tool when API returns error."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API Error"))

        result = await tool.execute({})

        assert "content" in result
        assert "Tool execution failed: API Error" in result["content"][0]["text"]
        assert result["isError"] is True

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_extracts_total_count(self, mock_format):
        """Test that total count is extracted from Content-Range header."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[{"id": 1}],
            headers={"Content-Range": "items 0-0/500"},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Formatted"

        await tool.execute({})

        # Verify format_offense_list was called with total_count
        mock_format.assert_called_once()
        call_args = mock_format.call_args
        assert call_args[0][1] == 500  # total_count

    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_handles_missing_content_range(self, mock_format):
        """Test that missing Content-Range header is handled gracefully."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[{"id": 1}],
            headers={},  # No Content-Range
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Formatted"

        result = await tool.execute({})

        # Verify format_offense_list was called with None for total_count
        mock_format.assert_called_once()
        call_args = mock_format.call_args
        assert call_args[0][1] is None

        assert "isError" not in result


    @pytest.mark.asyncio
    @patch('qradar_mcp.tools.offense.list_offenses.format_offense_list')
    async def test_execute_with_all_parameters(self, mock_format):
        """Test executing tool with all parameters specified."""
        tool = ListOffensesTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[{"id": 1}],
            headers={"Content-Range": "items 10-10/100"},
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        mock_format.return_value = "Complete result"

        result = await tool.execute({
            "filter": "severity > 5",
            "sort": "-start_time",
            "fields": "id,severity,description",
            "limit": 25,
            "offset": 10,
            "format_output": True
        })

        # Verify all parameters were used
        call_args = tool.client.get.call_args
        params = call_args[1]["params"]
        headers = call_args[1]["headers"]

        assert params["filter"] == "severity > 5"
        assert params["sort"] == "-start_time"
        assert params["fields"] == "id,severity,description"
        assert headers["Range"] == "items=10-34"  # offset=10, limit=25

        assert "isError" not in result
        assert result["content"][0]["text"] == "Complete result"
