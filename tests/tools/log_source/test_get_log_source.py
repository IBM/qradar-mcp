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
Tests for GetLogSourceTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.log_source.get_log_source import GetLogSourceTool


class TestGetLogSourceMetadata:
    """Test GetLogSourceTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = GetLogSourceTool()
        assert tool.name == "get_log_source"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = GetLogSourceTool()
        assert tool.description
        assert "log source" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = GetLogSourceTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test log_source_id is required."""
        tool = GetLogSourceTool()
        schema = tool.input_schema

        assert "log_source_id" in schema["required"]
        assert "log_source_id" in schema["properties"]

    def test_input_schema_optional_fields(self):
        """Test fields parameter is optional."""
        tool = GetLogSourceTool()
        schema = tool.input_schema

        assert "fields" in schema["properties"]
        assert "fields" not in schema.get("required", [])


class TestGetLogSourceExecution:
    """Test GetLogSourceTool execution."""

    @pytest.fixture
    def sample_log_source(self):
        """Sample log source data."""
        return {
            "id": 123,
            "name": "Test-Firewall",
            "description": "Test firewall log source",
            "type_id": 42,
            "protocol_type_id": 1,
            "protocol_parameters": [
                {"id": 1, "name": "port", "value": "514"},
                {"id": 2, "name": "protocol", "value": "UDP"}
            ],
            "enabled": True,
            "gateway": False,
            "internal": False,
            "credibility": 8,
            "target_event_collector_id": 10,
            "disconnected_log_collector_id": None,
            "coalesce_events": True,
            "store_event_payload": True,
            "log_source_extension_id": None,
            "language_id": 1,
            "group_ids": [1, 2],
            "requires_deploy": False,
            "status": {
                "status": "ACTIVE",
                "last_updated": 1640000000000,
                "messages": []
            },
            "auto_discovered": False,
            "average_eps": 150,
            "creation_date": 1630000000000,
            "modified_date": 1640000000000,
            "last_event_time": 1640000100000,
            "wincollect_internal_destination_id": None,
            "wincollect_external_destination_ids": [],
            "legacy_bulk_group_name": None,
            "sending_ip": "192.168.1.100",
            "parsing_order": 1,
            "syslog_event_timeout": 30
        }

    @pytest.mark.asyncio
    async def test_execute_success(self, sample_log_source):
        """Test successful execution."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_log_source,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"log_source_id": 123})

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "isError" not in result

        # Parse and verify JSON response
        response_data = json.loads(result["content"][0]["text"])
        assert response_data["id"] == 123
        assert response_data["name"] == "Test-Firewall"
        assert response_data["enabled"] is True

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert "config/event_sources/log_source_management/log_sources/123" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_log_source):
        """Test execution with fields parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_log_source,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "log_source_id": 123,
            "fields": "id,name,enabled"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['fields'] == "id,name,enabled"

    @pytest.mark.asyncio
    async def test_execute_without_fields(self, sample_log_source):
        """Test execution without fields parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_log_source,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"log_source_id": 123})

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        # params should be None when no fields specified
        assert call_args[1]['params'] is None


class TestGetLogSourceValidation:
    """Test GetLogSourceTool input validation."""

    @pytest.mark.asyncio
    async def test_missing_log_source_id(self):
        """Test error when log_source_id is missing."""
        tool = GetLogSourceTool()
        result = await tool.execute({})

        assert result["isError"] is True
        assert "log_source_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_none_log_source_id(self):
        """Test error when log_source_id is None."""
        tool = GetLogSourceTool()
        result = await tool.execute({"log_source_id": None})

        assert result["isError"] is True
        assert "log_source_id is required" in result["content"][0]["text"]


class TestGetLogSourceErrorHandling:
    """Test GetLogSourceTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        # Setup mock to raise error
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        # Execute
        result = await tool.execute({"log_source_id": 123})

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed: API connection failed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_not_found_error(self):
        """Test handling of 404 not found error."""
        # Setup mock to raise error
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("404 Not Found"))

        # Execute
        result = await tool.execute({"log_source_id": 999})

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed: 404 Not Found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Setup mock to raise ValueError
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid log source ID"))

        # Execute
        result = await tool.execute({"log_source_id": 123})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid log source id" == result["content"][0]["text"].lower()


class TestGetLogSourceResponseFormat:
    """Test GetLogSourceTool response formatting."""

    @pytest.mark.asyncio
    async def test_response_is_valid_json(self):
        """Test that response is valid JSON."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json={
                "id": 1,
                "name": "Test",
                "enabled": True
            },
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"log_source_id": 1})

        # Verify JSON is valid
        assert "isError" not in result
        response_text = result["content"][0]["text"]
        parsed = json.loads(response_text)
        assert isinstance(parsed, dict)
        assert parsed["id"] == 1

    @pytest.mark.asyncio
    async def test_response_includes_all_fields(self):
        """Test that response includes all returned fields."""
        # Setup mock with comprehensive data
        comprehensive_data = {
            "id": 1,
            "name": "Comprehensive-Source",
            "description": "Full data test",
            "type_id": 42,
            "protocol_type_id": 1,
            "enabled": True,
            "gateway": False,
            "internal": False,
            "credibility": 7,
            "status": {"status": "ACTIVE"},
            "requires_deploy": False
        }
        mock_response = httpx.Response(
            200,
            json=comprehensive_data,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = GetLogSourceTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"log_source_id": 1})

        # Verify all fields are present
        response_text = result["content"][0]["text"]
        parsed = json.loads(response_text)

        for key in comprehensive_data:
            assert key in parsed
            assert parsed[key] == comprehensive_data[key]
