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
Tests for list_reference_sets tool.
"""

import pytest
from unittest.mock import AsyncMock, Mock
import httpx
from qradar_mcp.tools.reference_data.list_reference_sets import ListReferenceSets


@pytest.fixture
def tool():
    """Create ListReferenceSets tool instance."""
    return ListReferenceSets()


@pytest.fixture
def sample_reference_sets():
    """Sample reference sets data."""
    return [
        {
            "name": "suspicious_ips",
            "element_type": "IP",
            "namespace": "SHARED",
            "number_of_elements": 150,
            "creation_time": 1640000000000,
            "timeout_type": "LAST_SEEN"
        },
        {
            "name": "malicious_domains",
            "element_type": "ALN",
            "namespace": "PRIVATE",
            "number_of_elements": 75,
            "creation_time": 1640100000000,
            "timeout_type": "FIRST_SEEN"
        }
    ]


class TestListReferenceSetsMetadata:
    """Test tool metadata."""

    def test_name(self, tool):
        """Test tool name."""
        assert tool.name == "list_reference_sets"

    def test_description(self, tool):
        """Test tool description."""
        assert "List reference data sets" in tool.description

    def test_input_schema(self, tool):
        """Test input schema structure."""
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "properties" in schema

        # Check optional parameters
        props = schema["properties"]
        assert "filter" in props
        assert "sort" in props
        assert "limit" in props
        assert "offset" in props
        assert "fields" in props
        assert "format_output" in props

        # Verify no required parameters
        assert "required" not in schema or len(schema["required"]) == 0


class TestListReferenceSetsExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_execute_default_parameters(self, tool, sample_reference_sets):
        """Test execution with default parameters."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "isError" not in result
        assert "content" in result
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == "reference_data_collections/sets"

    @pytest.mark.asyncio
    async def test_execute_with_filter(self, tool, sample_reference_sets):
        """Test execution with filter parameter."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"filter": "element_type='IP'"}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        call_args = tool.client.get.call_args
        assert "filter" in call_args[1]["params"]
        assert call_args[1]["params"]["filter"] == "element_type='IP'"

    @pytest.mark.asyncio
    async def test_execute_with_sort(self, tool, sample_reference_sets):
        """Test execution with sort parameter."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"sort": "-number_of_elements"}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        call_args = tool.client.get.call_args
        assert "sort" in call_args[1]["params"]
        assert call_args[1]["params"]["sort"] == "-number_of_elements"

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self, tool, sample_reference_sets):
        """Test execution with pagination parameters."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"limit": 100, "offset": 50}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        call_args = tool.client.get.call_args
        assert "Range" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Range"] == "items=50-149"

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, tool, sample_reference_sets):
        """Test execution with fields parameter."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"fields": "name,element_type,number_of_elements"}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        call_args = tool.client.get.call_args
        assert "fields" in call_args[1]["params"]
        assert call_args[1]["params"]["fields"] == "name,element_type,number_of_elements"

    @pytest.mark.asyncio
    async def test_execute_with_formatted_output(
        self, tool, sample_reference_sets, monkeypatch
    ):
        """Test execution with formatted output."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        from qradar_mcp.tools.reference_data import list_reference_sets
        # format_reference_sets_table is a regular function, not async
        mock_format = Mock(return_value="Formatted table")
        monkeypatch.setattr(list_reference_sets, "format_reference_sets_table", mock_format)

        arguments = {"format_output": True}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        mock_format.assert_called_once_with(sample_reference_sets)
        assert "Formatted table" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_without_formatted_output(
        self, tool, sample_reference_sets
    ):
        """Test execution without formatted output."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"format_output": False}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        assert "suspicious_ips" in result["content"][0]["text"]
        assert "malicious_domains" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self, tool, sample_reference_sets):
        """Test execution with all parameters."""
        mock_response = httpx.Response(200, json=sample_reference_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {
            "filter": "namespace='SHARED'",
            "sort": "+name",
            "limit": 25,
            "offset": 10,
            "fields": "name,element_type",
            "format_output": False
        }
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        call_args = tool.client.get.call_args

        # Verify params
        assert call_args[1]["params"]["filter"] == "namespace='SHARED'"
        assert call_args[1]["params"]["sort"] == "+name"
        assert call_args[1]["params"]["fields"] == "name,element_type"

        # Verify headers
        assert call_args[1]["headers"]["Range"] == "items=10-34"


class TestListReferenceSetsErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_execute_api_error(self, tool):
        """Test handling of API errors."""
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        result = await tool.execute({})

        assert result["isError"] is True
        assert "API connection failed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_http_error(self, tool):
        """Test handling of HTTP errors."""
        # Setup mock to raise HTTPStatusError
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(500, request=mock_request)
        http_error = httpx.HTTPStatusError("500 Server Error", request=mock_request, response=mock_response)

        # Execute
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "Error executing list_reference_sets: 500 Server Error" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_value_error(self, tool):
        """Test handling of ValueError."""
        # Execute
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_empty_result(self, tool):
        """Test handling of empty results."""
        mock_response = httpx.Response(200, json=[], request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "isError" not in result
        assert "content" in result
        assert "No reference sets found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_invalid_filter(self, tool):
        """Test handling of invalid filter."""
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Invalid filter expression"))

        arguments = {"filter": "invalid syntax"}
        result = await tool.execute(arguments)

        assert result["isError"] is True
        assert "Invalid filter expression" in result["content"][0]["text"]


class TestListReferenceSetsIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_filter_by_element_type(self, tool, sample_reference_sets):
        """Test filtering by element type."""
        ip_sets = [s for s in sample_reference_sets if s["element_type"] == "IP"]
        mock_response = httpx.Response(200, json=ip_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"filter": "element_type='IP'"}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        assert "suspicious_ips" in result["content"][0]["text"]
        assert "malicious_domains" not in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_sort_by_name_ascending(self, tool, sample_reference_sets):
        """Test sorting by name ascending."""
        sorted_sets = sorted(sample_reference_sets, key=lambda x: x["name"])
        mock_response = httpx.Response(200, json=sorted_sets, request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"sort": "+name"}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        # Verify order in output
        text = result["content"][0]["text"]
        malicious_pos = text.find("malicious_domains")
        suspicious_pos = text.find("suspicious_ips")
        assert malicious_pos < suspicious_pos

    @pytest.mark.asyncio
    async def test_pagination_first_page(self, tool, sample_reference_sets):
        """Test first page of results."""
        mock_response = httpx.Response(200, json=sample_reference_sets[:1], request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"limit": 1, "offset": 0}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        call_args = tool.client.get.call_args
        assert call_args[1]["headers"]["Range"] == "items=0-0"

    @pytest.mark.asyncio
    async def test_pagination_second_page(self, tool, sample_reference_sets):
        """Test second page of results."""
        mock_response = httpx.Response(200, json=sample_reference_sets[1:], request=httpx.Request("GET", "http://test"))

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        arguments = {"limit": 1, "offset": 1}
        result = await tool.execute(arguments)

        assert "isError" not in result
        assert "content" in result
        call_args = tool.client.get.call_args
        assert call_args[1]["headers"]["Range"] == "items=1-1"
