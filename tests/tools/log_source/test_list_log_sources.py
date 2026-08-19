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
Tests for ListLogSourcesTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.log_source.list_log_sources import ListLogSourcesTool


class TestListLogSourcesMetadata:
    """Test ListLogSourcesTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = ListLogSourcesTool()
        assert tool.name == "list_log_sources"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = ListLogSourcesTool()
        assert tool.description
        assert "log source" in tool.description.lower()
        assert "list" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = ListLogSourcesTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListLogSourcesTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # But these fields should exist in properties
        optional_fields = ["filter", "fields", "sort", "limit", "offset", "format_output"]
        for field in optional_fields:
            assert field in schema["properties"]


class TestListLogSourcesExecution:
    """Test ListLogSourcesTool execution."""

    @pytest.fixture
    def sample_log_sources(self):
        """Sample log source data."""
        return [
            {
                "id": 1,
                "name": "Firewall-01",
                "description": "Main firewall log source",
                "type_id": 42,
                "protocol_type_id": 1,
                "enabled": True,
                "gateway": False,
                "internal": False,
                "credibility": 8,
                "average_eps": 150,
                "last_event_time": 1640000000000,
                "status": {
                    "status": "ACTIVE",
                    "messages": []
                },
                "target_event_collector_id": 10,
                "requires_deploy": False
            },
            {
                "id": 2,
                "name": "IDS-01",
                "description": "Intrusion detection system",
                "type_id": 43,
                "protocol_type_id": 2,
                "enabled": True,
                "gateway": False,
                "internal": False,
                "credibility": 9,
                "average_eps": 200,
                "last_event_time": 1640000100000,
                "status": {
                    "status": "ACTIVE",
                    "messages": []
                },
                "target_event_collector_id": 10,
                "requires_deploy": False
            }
        ]

    @pytest.mark.asyncio
    async def test_execute_no_parameters(self, sample_log_sources):
        """Test execution with no parameters."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=sample_log_sources, request=mock_request)

        # Execute
        tool = ListLogSourcesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "isError" not in result
        assert "Log Source ID: 1" in result["content"][0]["text"]
        assert "Log Source ID: 2" in result["content"][0]["text"]
        assert "Firewall-01" in result["content"][0]["text"]

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'config/event_sources/log_source_management/log_sources'

    @pytest.mark.asyncio
    async def test_execute_with_filter(self, sample_log_sources):
        """Test execution with filter parameter."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=[sample_log_sources[0]], request=mock_request)

        # Execute
        tool = ListLogSourcesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "filter": "enabled=true"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['filter'] == "enabled=true"

    @pytest.mark.asyncio
    async def test_execute_with_sort(self, sample_log_sources):
        """Test execution with sort parameter."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=sample_log_sources, request=mock_request)

        # Execute
        tool = ListLogSourcesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "sort": "-average_eps"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['sort'] == "-average_eps"

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_log_sources):
        """Test execution with fields parameter."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=sample_log_sources, request=mock_request)

        # Execute
        tool = ListLogSourcesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "fields": "id,name,enabled"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['fields'] == "id,name,enabled"

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self, sample_log_sources):
        """Test execution with limit and offset."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=sample_log_sources, request=mock_request)

        # Execute
        tool = ListLogSourcesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "limit": 10,
            "offset": 5
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert 'Range' in call_args[1]['headers']
        assert call_args[1]['headers']['Range'] == "items=5-14"

    @pytest.mark.asyncio
    async def test_execute_format_output_false(self, sample_log_sources):
        """Test execution with format_output=false returns JSON."""
        # Setup mock
        mock_request = httpx.Request("GET", "http://test")
        mock_response = httpx.Response(200, json=sample_log_sources, request=mock_request)

        # Execute
        tool = ListLogSourcesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "format_output": False
        })

        # Verify JSON output
        assert "isError" not in result
        response_text = result["content"][0]["text"]
        parsed = json.loads(response_text)
        assert len(parsed) == 2
        assert parsed[0]["id"] == 1


class TestListLogSourcesErrorHandling:
    """Test ListLogSourcesTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        # Setup mock to raise error
        tool = ListLogSourcesTool()
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
        tool = ListLogSourcesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()


class TestListLogSourcesFormatting:
    """Test ListLogSourcesTool output formatting."""

    def test_format_log_sources_empty_list(self):
        """Test formatting empty log source list."""
        tool = ListLogSourcesTool()
        result = tool._format_log_sources([])
        assert result == "No log sources found"

    def test_format_log_sources_with_data(self):
        """Test formatting log source list with data."""
        tool = ListLogSourcesTool()
        log_sources = [{
            "id": 123,
            "name": "Test-Source",
            "description": "Test log source",
            "type_id": 42,
            "protocol_type_id": 1,
            "enabled": True,
            "gateway": False,
            "internal": False,
            "credibility": 7,
            "average_eps": 100,
            "last_event_time": 1640000000000,
            "status": {
                "status": "ACTIVE",
                "messages": []
            },
            "target_event_collector_id": 10,
            "requires_deploy": False
        }]

        result = tool._format_log_sources(log_sources)

        assert "Log Source ID: 123" in result
        assert "Test-Source" in result
        assert "Test log source" in result
        assert "Type ID: 42" in result
        assert "Protocol Type ID: 1" in result
        assert "Enabled: Yes" in result
        assert "Credibility: 7/10" in result
        assert "Average EPS: 100" in result
        assert "Status: ACTIVE" in result

    def test_format_log_sources_with_gateway(self):
        """Test formatting log source that is a gateway."""
        tool = ListLogSourcesTool()
        log_sources = [{
            "id": 1,
            "name": "Gateway-Source",
            "type_id": 42,
            "protocol_type_id": 1,
            "enabled": True,
            "gateway": True,
            "internal": False,
            "credibility": 5
        }]

        result = tool._format_log_sources(log_sources)

        assert "Gateway: Yes" in result

    def test_format_log_sources_with_internal(self):
        """Test formatting internal log source."""
        tool = ListLogSourcesTool()
        log_sources = [{
            "id": 1,
            "name": "Internal-Source",
            "type_id": 42,
            "protocol_type_id": 1,
            "enabled": True,
            "gateway": False,
            "internal": True,
            "credibility": 5
        }]

        result = tool._format_log_sources(log_sources)

        assert "Internal: Yes" in result

    def test_format_log_sources_requires_deploy(self):
        """Test formatting log source that requires deployment."""
        tool = ListLogSourcesTool()
        log_sources = [{
            "id": 1,
            "name": "New-Source",
            "type_id": 42,
            "protocol_type_id": 1,
            "enabled": True,
            "gateway": False,
            "internal": False,
            "credibility": 5,
            "requires_deploy": True
        }]

        result = tool._format_log_sources(log_sources)

        assert "Requires Deploy: Yes" in result
        assert "⚠️" in result

    def test_format_log_sources_with_status_messages(self):
        """Test formatting log source with status messages."""
        tool = ListLogSourcesTool()
        log_sources = [{
            "id": 1,
            "name": "Source-With-Messages",
            "type_id": 42,
            "protocol_type_id": 1,
            "enabled": True,
            "gateway": False,
            "internal": False,
            "credibility": 5,
            "status": {
                "status": "WARNING",
                "messages": [
                    {"severity": "WARN", "text": "Connection timeout"},
                    {"severity": "INFO", "text": "Retrying connection"}
                ]
            }
        }]

        result = tool._format_log_sources(log_sources)

        assert "Status: WARNING" in result
        assert "Status Messages:" in result
        assert "[WARN] Connection timeout" in result
        assert "[INFO] Retrying connection" in result

    def test_format_log_sources_disabled(self):
        """Test formatting disabled log source."""
        tool = ListLogSourcesTool()
        log_sources = [{
            "id": 1,
            "name": "Disabled-Source",
            "type_id": 42,
            "protocol_type_id": 1,
            "enabled": False,
            "gateway": False,
            "internal": False,
            "credibility": 5
        }]

        result = tool._format_log_sources(log_sources)

        assert "Enabled: No" in result
