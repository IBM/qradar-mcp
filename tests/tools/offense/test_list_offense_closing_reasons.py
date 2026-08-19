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
Unit tests for the ListOffenseClosingReasonsTool.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.offense.list_offense_closing_reasons import ListOffenseClosingReasonsTool


class TestListOffenseClosingReasonsTool:
    """Tests for ListOffenseClosingReasonsTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = ListOffenseClosingReasonsTool()
        assert tool.name == "list_offense_closing_reasons"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = ListOffenseClosingReasonsTool()
        assert "List valid offense closing reasons" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = ListOffenseClosingReasonsTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema

        # Check all expected properties exist
        expected_props = ["include_reserved", "include_deleted", "filter", "fields"]
        for prop in expected_props:
            assert prop in schema["properties"]

    def test_input_schema_types(self):
        """Test that input schema has correct types."""
        tool = ListOffenseClosingReasonsTool()
        schema = tool.input_schema

        # Check boolean properties
        assert schema["properties"]["include_reserved"]["type"] == "boolean"
        assert schema["properties"]["include_deleted"]["type"] == "boolean"

        # Check string properties
        assert schema["properties"]["filter"]["type"] == "string"
        assert schema["properties"]["fields"]["type"] == "string"

    def test_input_schema_defaults(self):
        """Test that input schema has correct defaults."""
        tool = ListOffenseClosingReasonsTool()
        schema = tool.input_schema

        # These properties don't have defaults in the schema
        assert "default" not in schema["properties"]["include_reserved"]
        assert "default" not in schema["properties"]["include_deleted"]

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP definition."""
        tool = ListOffenseClosingReasonsTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "list_offense_closing_reasons"
        assert "List valid offense closing reasons" in definition["description"]
        assert "inputSchema" in definition


class TestListOffenseClosingReasonsToolExecution:
    """Tests for ListOffenseClosingReasonsTool execute method."""

    @pytest.mark.asyncio
    async def test_execute_with_no_parameters(self):
        """Test executing tool with no parameters."""
        # Setup mock
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "text": "False-Positive, Tuned", "is_reserved": True, "is_deleted": False},
                {"id": 2, "text": "Non-Issue", "is_reserved": True, "is_deleted": False}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify client was called correctly
        tool.client.get.assert_called_once_with(
            'siem/offense_closing_reasons',
            params={},
            headers={'Range': 'items=0-9'},
        )

        # Verify MCP result structure
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "False-Positive, Tuned" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_include_reserved(self):
        """Test executing tool with include_reserved parameter."""
        # Setup mock
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "text": "False-Positive, Tuned", "is_reserved": True}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"include_reserved": True})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/offense_closing_reasons',
            params={"include_reserved": "true"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_include_deleted(self):
        """Test executing tool with include_deleted parameter."""
        # Setup mock
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 99, "text": "Deleted Reason", "is_deleted": True}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"include_deleted": True})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/offense_closing_reasons',
            params={"include_deleted": "true"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_filter(self):
        """Test executing tool with filter parameter."""
        # Setup mock
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "text": "False-Positive, Tuned"}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "text='False-Positive, Tuned'"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/offense_closing_reasons',
            params={"filter": "text='False-Positive, Tuned'"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_fields(self):
        """Test executing tool with fields parameter."""
        # Setup mock
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "text": "False-Positive, Tuned"}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"fields": "id,text"})

        # Verify client was called with correct params
        tool.client.get.assert_called_once_with(
            'siem/offense_closing_reasons',
            params={"fields": "id,text"},
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self):
        """Test executing tool with all parameters."""
        # Setup mock
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json=[
                {"id": 1, "text": "Custom Reason"}
            ],
            request=httpx.Request("GET", "http://test")
        )
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "include_reserved": True,
            "include_deleted": True,
            "filter": "is_reserved=false",
            "fields": "id,text,is_reserved"
        })

        # Verify client was called with all params
        tool.client.get.assert_called_once_with(
            'siem/offense_closing_reasons',
            params={
                "include_reserved": "true",
                "include_deleted": "true",
                "filter": "is_reserved=false",
                "fields": "id,text,is_reserved",
            },
            headers={'Range': 'items=0-9'},
        )

    @pytest.mark.asyncio
    async def test_execute_with_empty_result(self):
        """Test executing tool with empty result."""
        # Setup mock
        tool = ListOffenseClosingReasonsTool()
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


class TestListOffenseClosingReasonsToolErrorHandling:
    """Tests for error handling in ListOffenseClosingReasonsTool."""

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()

        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(
            status_code=500,
            text="Internal server error",
            request=mock_request
        )
        tool.client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "500 Error",
            request=mock_request,
            response=mock_response
        ))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "Error executing list_offense_closing_reasons: 500 Error" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_value_error(self):
        """Test handling of ValueError."""
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid value"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_runtime_error(self):
        """Test handling of RuntimeError."""
        tool = ListOffenseClosingReasonsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Runtime error occurred"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()
