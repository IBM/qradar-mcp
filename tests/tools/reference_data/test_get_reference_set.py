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
Tests for GetReferenceSetTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.reference_data.get_reference_set import GetReferenceSetTool


class TestGetReferenceSetMetadata:
    """Test GetReferenceSetTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = GetReferenceSetTool()
        assert tool.name == "get_reference_set"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = GetReferenceSetTool()
        assert tool.description
        assert "reference set" in tool.description.lower()
        assert "metadata" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = GetReferenceSetTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_set_id_required(self):
        """Test set_id is required in schema."""
        tool = GetReferenceSetTool()
        schema = tool.input_schema

        assert "set_id" in schema["required"]
        assert "set_id" in schema["properties"]
        assert schema["properties"]["set_id"]["type"] == "integer"

    def test_input_schema_fields_optional(self):
        """Test fields is optional in schema."""
        tool = GetReferenceSetTool()
        schema = tool.input_schema

        assert "fields" not in schema["required"]
        assert "fields" in schema["properties"]
        assert schema["properties"]["fields"]["type"] == "string"


class TestGetReferenceSetExecution:
    """Test GetReferenceSetTool execution."""

    @pytest.fixture
    def sample_set_data(self):
        """Sample reference set data."""
        return {
            "id": 123,
            "name": "threat_ips",
            "description": "Known malicious IP addresses",
            "entry_type": "IP",
            "number_of_entries": 1500,
            "creation_time": 1640000000000,
            "namespace": "SHARED",
            "time_to_live": 86400,
            "expiry_type": "LAST_SEEN",
            "expired_log_option": "LOG_BATCH"
        }

    @pytest.mark.asyncio
    async def test_execute_basic_request(self, sample_set_data):
        """Test basic execution with set_id only."""
        # Setup mock
        mock_response = httpx.Response(200, json=sample_set_data, request=httpx.Request("GET", "http://test"))

        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)
        result = await tool.execute({"set_id": 123})

        # Verify
        assert "isError" not in result
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'reference_data_collections/sets/123'
        assert call_args[1]["params"] == {}

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_set_data):
        """Test execution with fields parameter."""
        # Setup mock
        mock_response = httpx.Response(200, json=sample_set_data, request=httpx.Request("GET", "http://test"))

        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "set_id": 123,
            "fields": "id,name,entry_type,number_of_entries"
        })

        # Verify
        assert "isError" not in result

        # Verify API call with fields
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["fields"] == "id,name,entry_type,number_of_entries"

    @pytest.mark.asyncio
    async def test_execute_response_format(self, sample_set_data):
        """Test response is properly formatted as JSON."""
        # Setup mock
        mock_response = httpx.Response(200, json=sample_set_data, request=httpx.Request("GET", "http://test"))

        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)
        result = await tool.execute({"set_id": 123})

        # Verify JSON formatting
        content_text = result["content"][0]["text"]
        parsed_data = json.loads(content_text)
        assert parsed_data["id"] == 123
        assert parsed_data["name"] == "threat_ips"
        assert parsed_data["entry_type"] == "IP"

    @pytest.mark.asyncio
    async def test_execute_missing_set_id(self):
        """Test execution fails when set_id is missing."""
        tool = GetReferenceSetTool()
        result = await tool.execute({})

        assert result["isError"] is True
        assert "set_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_none_set_id(self):
        """Test execution fails when set_id is None."""
        tool = GetReferenceSetTool()
        result = await tool.execute({"set_id": None})

        assert result["isError"] is True
        assert "set_id is required" in result["content"][0]["text"]


class TestGetReferenceSetErrorHandling:
    """Test GetReferenceSetTool error handling."""

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test handling of API errors."""
        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))
        result = await tool.execute({"set_id": 123})

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed:" in result["content"][0]["text"]
        assert "API connection failed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_not_found_error(self):
        """Test handling of 404 not found errors."""
        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("404: Reference set not found"))
        result = await tool.execute({"set_id": 999})

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed: 404: Reference set not found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_value_error(self):
        """Test handling of ValueError."""
        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid set ID format"))
        result = await tool.execute({"set_id": 123})

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed:" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        # Setup mock to raise HTTPStatusError
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(404, request=mock_request)
        http_error = httpx.HTTPStatusError("404 Not Found", request=mock_request, response=mock_response)

        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)
        result = await tool.execute({"set_id": 999})

        # Verify error response
        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()


class TestGetReferenceSetIntegration:
    """Integration tests for GetReferenceSetTool."""

    @pytest.mark.asyncio
    async def test_different_entry_types(self):
        """Test retrieving sets with different entry types."""
        entry_types = ["IP", "ALN", "NUM", "PORT", "DATE", "CIDR"]

        for entry_type in entry_types:
            # Setup mock
            set_data = {
                "id": 1,
                "name": f"test_{entry_type.lower()}",
                "entry_type": entry_type,
                "number_of_entries": 100
            }
            mock_response = httpx.Response(200, json=set_data, request=httpx.Request("GET", "http://test"))

            # Execute
            tool = GetReferenceSetTool()
            tool.client = AsyncMock()
            tool.client.get = AsyncMock(return_value=mock_response)
            result = await tool.execute({"set_id": 1})

            # Verify
            assert "isError" not in result
            content_text = result["content"][0]["text"]
            parsed_data = json.loads(content_text)
            assert parsed_data["entry_type"] == entry_type

    @pytest.mark.asyncio
    async def test_different_namespaces(self):
        """Test retrieving sets with different namespaces."""
        namespaces = ["PRIVATE", "SHARED", "TENANT"]

        for namespace in namespaces:
            # Setup mock
            set_data = {
                "id": 1,
                "name": f"test_{namespace.lower()}",
                "namespace": namespace,
                "number_of_entries": 50
            }
            mock_response = httpx.Response(200, json=set_data, request=httpx.Request("GET", "http://test"))

            # Execute
            tool = GetReferenceSetTool()
            tool.client = AsyncMock()
            tool.client.get = AsyncMock(return_value=mock_response)
            result = await tool.execute({"set_id": 1})

            # Verify
            assert "isError" not in result
            content_text = result["content"][0]["text"]
            parsed_data = json.loads(content_text)
            assert parsed_data["namespace"] == namespace

    @pytest.mark.asyncio
    async def test_empty_set(self):
        """Test retrieving an empty reference set."""
        # Setup mock
        set_data = {
            "id": 1,
            "name": "empty_set",
            "entry_type": "IP",
            "number_of_entries": 0
        }
        mock_response = httpx.Response(200, json=set_data, request=httpx.Request("GET", "http://test"))

        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)
        result = await tool.execute({"set_id": 1})

        # Verify
        assert "isError" not in result
        content_text = result["content"][0]["text"]
        parsed_data = json.loads(content_text)
        assert parsed_data["number_of_entries"] == 0

    @pytest.mark.asyncio
    async def test_large_set(self):
        """Test retrieving a large reference set."""
        # Setup mock
        set_data = {
            "id": 1,
            "name": "large_set",
            "entry_type": "IP",
            "number_of_entries": 1000000
        }
        mock_response = httpx.Response(200, json=set_data, request=httpx.Request("GET", "http://test"))

        # Execute
        tool = GetReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)
        result = await tool.execute({"set_id": 1})

        # Verify
        assert "isError" not in result
        content_text = result["content"][0]["text"]
        parsed_data = json.loads(content_text)
        assert parsed_data["number_of_entries"] == 1000000
