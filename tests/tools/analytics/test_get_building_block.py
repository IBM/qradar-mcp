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
Tests for GetBuildingBlockTool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.analytics.get_building_block import GetBuildingBlockTool


class TestGetBuildingBlockMetadata:
    """Test GetBuildingBlockTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = GetBuildingBlockTool()
        assert tool.name == "get_building_block"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = GetBuildingBlockTool()
        assert tool.description
        assert "building block" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = GetBuildingBlockTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test building_block_id is required."""
        tool = GetBuildingBlockTool()
        schema = tool.input_schema

        assert "building_block_id" in schema["required"]
        assert "building_block_id" in schema["properties"]

    def test_input_schema_optional_fields(self):
        """Test fields parameter is optional."""
        tool = GetBuildingBlockTool()
        schema = tool.input_schema

        assert "fields" in schema["properties"]
        assert "fields" not in schema.get("required", [])


class TestGetBuildingBlockExecution:
    """Test GetBuildingBlockTool execution."""

    @pytest.fixture
    def sample_building_block(self):
        """Sample building block data."""
        return {
            "id": 100001,
            "name": "Failed Login Attempts",
            "type": "EVENT",
            "enabled": True,
            "owner": "admin",
            "origin": "USER",
            "base_capacity": 1000,
            "base_host_id": 42,
            "average_capacity": 950,
            "capacity_timestamp": 1640000000000,
            "identifier": "550e8400-e29b-41d4-a716-446655440001",
            "linked_rule_identifier": None,
            "creation_date": 1630000000000,
            "modification_date": 1640000000000
        }

    @pytest.mark.asyncio
    async def test_execute_with_building_block_id(self, sample_building_block):
        """Test execution with building_block_id."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_building_block,
            request=mock_request
        )

        tool = GetBuildingBlockTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"building_block_id": 100001})

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "isError" not in result
        assert "Building Block ID: 100001" in result["content"][0]["text"]
        assert "Failed Login Attempts" in result["content"][0]["text"]

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'analytics/building_blocks/100001'

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_building_block):
        """Test execution with fields parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_building_block,
            request=mock_request
        )

        tool = GetBuildingBlockTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "building_block_id": 100001,
            "fields": "id,name,type,enabled"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['fields'] == "id,name,type,enabled"

    @pytest.mark.asyncio
    async def test_execute_without_building_block_id(self):
        """Test execution without building_block_id returns error."""
        tool = GetBuildingBlockTool()
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "building_block_id is required" in result["content"][0]["text"]


class TestGetBuildingBlockErrorHandling:
    """Test GetBuildingBlockTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        tool = GetBuildingBlockTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        result = await tool.execute({"building_block_id": 100001})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        tool = GetBuildingBlockTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid building block ID"))

        result = await tool.execute({"building_block_id": 100001})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid building block id" in result["content"][0]["text"].lower()


class TestGetBuildingBlockFormatting:
    """Test GetBuildingBlockTool output formatting."""

    def test_format_building_block_complete_data(self):
        """Test formatting building block with complete data."""
        tool = GetBuildingBlockTool()
        building_block = {
            "id": 123,
            "name": "Test Building Block",
            "type": "EVENT",
            "origin": "USER",
            "enabled": True,
            "owner": "admin",
            "average_capacity": 1000,
            "base_capacity": 950,
            "base_host_id": 42,
            "capacity_timestamp": 1640000000000,
            "identifier": "550e8400-e29b-41d4-a716-446655440000",
            "linked_rule_identifier": None,
            "creation_date": 1630000000000,
            "modification_date": 1640000000000
        }

        result = tool._format_building_block(building_block)

        assert "Building Block ID: 123" in result
        assert "Test Building Block" in result
        assert "Type: EVENT | Origin: USER" in result
        assert "✓ Enabled" in result
        assert "Owner: admin" in result
        assert "Capacity:" in result
        assert "Avg: 1000 EPS" in result
        assert "Base: 950 EPS" in result
        assert "Base Host ID: 42" in result
        assert "Identifier: 550e8400-e29b-41d4-a716-446655440000" in result
        assert "Created: 1630000000000" in result
        assert "Modified: 1640000000000" in result
        assert "Full JSON:" in result

    def test_format_building_block_disabled(self):
        """Test formatting disabled building block."""
        tool = GetBuildingBlockTool()
        building_block = {
            "id": 1,
            "name": "Disabled Building Block",
            "type": "FLOW",
            "origin": "SYSTEM",
            "enabled": False,
            "owner": "admin"
        }

        result = tool._format_building_block(building_block)

        assert "✗ Disabled" in result

    def test_format_building_block_with_linked_identifier(self):
        """Test formatting building block with linked identifier."""
        tool = GetBuildingBlockTool()
        building_block = {
            "id": 1,
            "name": "Override Building Block",
            "type": "EVENT",
            "origin": "OVERRIDE",
            "enabled": True,
            "owner": "admin",
            "identifier": "550e8400-e29b-41d4-a716-446655440001",
            "linked_rule_identifier": "550e8400-e29b-41d4-a716-446655440000"
        }

        result = tool._format_building_block(building_block)

        assert "Linked Rule: 550e8400-e29b-41d4-a716-446655440000" in result

    def test_format_building_block_minimal_data(self):
        """Test formatting building block with minimal data."""
        tool = GetBuildingBlockTool()
        building_block = {
            "id": 1,
            "name": "Simple Building Block",
            "type": "EVENT",
            "origin": "USER",
            "enabled": True
        }

        result = tool._format_building_block(building_block)

        assert "Building Block ID: 1" in result
        assert "Simple Building Block" in result
        assert "Type: EVENT | Origin: USER" in result
        # Should not have capacity or timestamps sections
        assert "Capacity:" not in result
        assert "Timestamps:" not in result

    def test_format_building_block_system_origin(self):
        """Test formatting system building block."""
        tool = GetBuildingBlockTool()
        building_block = {
            "id": 1,
            "name": "System Building Block",
            "type": "COMMON",
            "origin": "SYSTEM",
            "enabled": True,
            "owner": "system"
        }

        result = tool._format_building_block(building_block)

        assert "Origin: SYSTEM" in result
        assert "Owner: system" in result

    def test_format_building_block_json_output(self):
        """Test that JSON output is included."""
        tool = GetBuildingBlockTool()
        building_block = {
            "id": 123,
            "name": "Test Building Block",
            "type": "EVENT",
            "enabled": True
        }

        result = tool._format_building_block(building_block)

        assert "Full JSON:" in result
        # Verify JSON can be parsed
        json_start = result.find("Full JSON:") + len("Full JSON:\n")
        json_str = result[json_start:]
        parsed = json.loads(json_str)
        assert parsed["id"] == 123
        assert parsed["name"] == "Test Building Block"
