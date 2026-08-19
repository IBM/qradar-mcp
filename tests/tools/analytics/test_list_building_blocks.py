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
Tests for ListBuildingBlocksTool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.analytics.list_building_blocks import ListBuildingBlocksTool


class TestListBuildingBlocksMetadata:
    """Test ListBuildingBlocksTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = ListBuildingBlocksTool()
        assert tool.name == "list_building_blocks"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = ListBuildingBlocksTool()
        assert tool.description
        assert "building block" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = ListBuildingBlocksTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListBuildingBlocksTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # But these fields should exist in properties
        optional_fields = ["filter", "fields", "limit", "offset", "format_output"]
        for field in optional_fields:
            assert field in schema["properties"]


class TestListBuildingBlocksExecution:
    """Test ListBuildingBlocksTool execution."""

    @pytest.fixture
    def sample_building_blocks(self):
        """Sample building blocks data."""
        return [
            {
                "id": 100001,
                "name": "Failed Login Attempts",
                "type": "EVENT",
                "enabled": True,
                "owner": "admin",
                "origin": "USER",
                "base_capacity": 1000,
                "average_capacity": 950,
                "capacity_timestamp": 1640000000000,
                "identifier": "550e8400-e29b-41d4-a716-446655440001",
                "linked_rule_identifier": None,
                "creation_date": 1630000000000,
                "modification_date": 1640000000000
            },
            {
                "id": 100002,
                "name": "Network Anomaly Detection",
                "type": "FLOW",
                "enabled": True,
                "owner": "admin",
                "origin": "SYSTEM",
                "base_capacity": 5000,
                "average_capacity": 4800,
                "capacity_timestamp": 1640000000000,
                "identifier": "550e8400-e29b-41d4-a716-446655440002",
                "linked_rule_identifier": None,
                "creation_date": 1620000000000,
                "modification_date": 1635000000000
            }
        ]

    @pytest.mark.asyncio
    async def test_execute_no_parameters(self, sample_building_blocks):
        """Test execution with no parameters."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_building_blocks,
            request=mock_request
        )

        tool = ListBuildingBlocksTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "isError" not in result
        assert "Building Block ID: 100001" in result["content"][0]["text"]
        assert "Building Block ID: 100002" in result["content"][0]["text"]
        assert "Failed Login Attempts" in result["content"][0]["text"]

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'analytics/building_blocks'

    @pytest.mark.asyncio
    async def test_execute_with_filter(self, sample_building_blocks):
        """Test execution with filter parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=[sample_building_blocks[0]],
            request=mock_request
        )

        tool = ListBuildingBlocksTool()
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
    async def test_execute_with_fields(self, sample_building_blocks):
        """Test execution with fields parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_building_blocks,
            request=mock_request
        )

        tool = ListBuildingBlocksTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "fields": "id,name,type,enabled"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['fields'] == "id,name,type,enabled"

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self, sample_building_blocks):
        """Test execution with limit and offset."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_building_blocks,
            request=mock_request
        )

        tool = ListBuildingBlocksTool()
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
    async def test_execute_format_output_false(self, sample_building_blocks):
        """Test execution with format_output=false returns JSON."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_building_blocks,
            request=mock_request
        )

        tool = ListBuildingBlocksTool()
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
        assert parsed[0]["id"] == 100001


class TestListBuildingBlocksErrorHandling:
    """Test ListBuildingBlocksTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        tool = ListBuildingBlocksTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" == result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        tool = ListBuildingBlocksTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()


class TestListBuildingBlocksFormatting:
    """Test ListBuildingBlocksTool output formatting."""

    def test_format_building_blocks_empty_list(self):
        """Test formatting empty building blocks list."""
        tool = ListBuildingBlocksTool()
        result = tool._format_building_blocks([])
        assert result == "No building blocks found"

    def test_format_building_blocks_with_data(self):
        """Test formatting building blocks list with data."""
        tool = ListBuildingBlocksTool()
        building_blocks = [{
            "id": 123,
            "name": "Test Building Block",
            "type": "EVENT",
            "origin": "USER",
            "enabled": True,
            "owner": "admin",
            "average_capacity": 1000,
            "base_capacity": 950,
            "identifier": "550e8400-e29b-41d4-a716-446655440000",
            "creation_date": 1630000000000,
            "modification_date": 1640000000000
        }]

        result = tool._format_building_blocks(building_blocks)

        assert "Building Block ID: 123" in result
        assert "Test Building Block" in result
        assert "Type: EVENT | Origin: USER" in result
        assert "✓ Enabled" in result
        assert "Owner: admin" in result
        assert "Capacity:" in result
        assert "Avg: 1000 EPS" in result
        assert "Base: 950 EPS" in result
        assert "Identifier: 550e8400-e29b-41d4-a716-446655440000" in result

    def test_format_building_blocks_disabled(self):
        """Test formatting disabled building block."""
        tool = ListBuildingBlocksTool()
        building_blocks = [{
            "id": 1,
            "name": "Disabled Building Block",
            "type": "FLOW",
            "origin": "SYSTEM",
            "enabled": False,
            "owner": "admin"
        }]

        result = tool._format_building_blocks(building_blocks)

        assert "✗ Disabled" in result

    def test_format_building_blocks_with_linked_identifier(self):
        """Test formatting building block with linked identifier."""
        tool = ListBuildingBlocksTool()
        building_blocks = [{
            "id": 1,
            "name": "Override Building Block",
            "type": "EVENT",
            "origin": "OVERRIDE",
            "enabled": True,
            "owner": "admin",
            "identifier": "550e8400-e29b-41d4-a716-446655440001",
            "linked_rule_identifier": "550e8400-e29b-41d4-a716-446655440000"
        }]

        result = tool._format_building_blocks(building_blocks)

        assert "Linked Rule: 550e8400-e29b-41d4-a716-446655440000" in result

    def test_format_building_blocks_system_origin(self):
        """Test formatting system building block."""
        tool = ListBuildingBlocksTool()
        building_blocks = [{
            "id": 1,
            "name": "System Building Block",
            "type": "COMMON",
            "origin": "SYSTEM",
            "enabled": True,
            "owner": "system"
        }]

        result = tool._format_building_blocks(building_blocks)

        assert "Origin: SYSTEM" in result
        assert "Owner: system" in result

    def test_format_building_blocks_without_capacity(self):
        """Test formatting building block without capacity metrics."""
        tool = ListBuildingBlocksTool()
        building_blocks = [{
            "id": 1,
            "name": "Simple Building Block",
            "type": "EVENT",
            "origin": "USER",
            "enabled": True,
            "owner": "admin"
        }]

        result = tool._format_building_blocks(building_blocks)

        # Should not have capacity line
        assert "Capacity:" not in result
        assert "Building Block ID: 1" in result
        assert "Simple Building Block" in result
