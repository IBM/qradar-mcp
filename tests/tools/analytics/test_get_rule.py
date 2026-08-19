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
Tests for GetRuleTool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.analytics.get_rule import GetRuleTool


class TestGetRuleMetadata:
    """Test GetRuleTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = GetRuleTool()
        assert tool.name == "get_rule"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = GetRuleTool()
        assert tool.description
        assert "rule" in tool.description.lower()
        assert "analytics" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = GetRuleTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test rule_id is required."""
        tool = GetRuleTool()
        schema = tool.input_schema

        assert "rule_id" in schema["required"]
        assert "rule_id" in schema["properties"]

    def test_input_schema_optional_fields(self):
        """Test fields parameter is optional."""
        tool = GetRuleTool()
        schema = tool.input_schema

        assert "fields" in schema["properties"]
        assert "fields" not in schema.get("required", [])


class TestGetRuleExecution:
    """Test GetRuleTool execution."""

    @pytest.fixture
    def sample_rule(self):
        """Sample rule data."""
        return {
            "id": 100001,
            "name": "Suspicious Login Activity",
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
    async def test_execute_with_rule_id(self, sample_rule):
        """Test execution with rule_id."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_rule,
            request=mock_request
        )

        tool = GetRuleTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"rule_id": 100001})

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "isError" not in result
        assert "Rule ID: 100001" in result["content"][0]["text"]
        assert "Suspicious Login Activity" in result["content"][0]["text"]

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'analytics/rules/100001'

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_rule):
        """Test execution with fields parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_rule,
            request=mock_request
        )

        tool = GetRuleTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "rule_id": 100001,
            "fields": "id,name,type,enabled"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['fields'] == "id,name,type,enabled"

    @pytest.mark.asyncio
    async def test_execute_without_rule_id(self):
        """Test execution without rule_id returns error."""
        tool = GetRuleTool()
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "rule_id is required" in result["content"][0]["text"]


class TestGetRuleErrorHandling:
    """Test GetRuleTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        tool = GetRuleTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        result = await tool.execute({"rule_id": 100001})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" == result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        tool = GetRuleTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid rule ID"))

        result = await tool.execute({"rule_id": 100001})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid rule id" == result["content"][0]["text"].lower()


class TestGetRuleFormatting:
    """Test GetRuleTool output formatting."""

    def test_format_rule_complete_data(self):
        """Test formatting rule with complete data."""
        tool = GetRuleTool()
        rule = {
            "id": 123,
            "name": "Test Rule",
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

        result = tool._format_rule(rule)

        assert "Rule ID: 123" in result
        assert "Test Rule" in result
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

    def test_format_rule_disabled(self):
        """Test formatting disabled rule."""
        tool = GetRuleTool()
        rule = {
            "id": 1,
            "name": "Disabled Rule",
            "type": "FLOW",
            "origin": "SYSTEM",
            "enabled": False,
            "owner": "admin"
        }

        result = tool._format_rule(rule)

        assert "✗ Disabled" in result

    def test_format_rule_with_linked_identifier(self):
        """Test formatting rule with linked identifier."""
        tool = GetRuleTool()
        rule = {
            "id": 1,
            "name": "Override Rule",
            "type": "EVENT",
            "origin": "OVERRIDE",
            "enabled": True,
            "owner": "admin",
            "identifier": "550e8400-e29b-41d4-a716-446655440001",
            "linked_rule_identifier": "550e8400-e29b-41d4-a716-446655440000"
        }

        result = tool._format_rule(rule)

        assert "Linked Rule: 550e8400-e29b-41d4-a716-446655440000" in result

    def test_format_rule_minimal_data(self):
        """Test formatting rule with minimal data."""
        tool = GetRuleTool()
        rule = {
            "id": 1,
            "name": "Simple Rule",
            "type": "EVENT",
            "origin": "USER",
            "enabled": True
        }

        result = tool._format_rule(rule)

        assert "Rule ID: 1" in result
        assert "Simple Rule" in result
        assert "Type: EVENT | Origin: USER" in result
        # Should not have capacity or timestamps sections
        assert "Capacity:" not in result
        assert "Timestamps:" not in result

    def test_format_rule_system_origin(self):
        """Test formatting system rule."""
        tool = GetRuleTool()
        rule = {
            "id": 1,
            "name": "System Rule",
            "type": "COMMON",
            "origin": "SYSTEM",
            "enabled": True,
            "owner": "system"
        }

        result = tool._format_rule(rule)

        assert "Origin: SYSTEM" in result
        assert "Owner: system" in result

    def test_format_rule_json_output(self):
        """Test that JSON output is included."""
        tool = GetRuleTool()
        rule = {
            "id": 123,
            "name": "Test Rule",
            "type": "EVENT",
            "enabled": True
        }

        result = tool._format_rule(rule)

        assert "Full JSON:" in result
        # Verify JSON can be parsed
        json_start = result.find("Full JSON:") + len("Full JSON:\n")
        json_str = result[json_start:]
        parsed = json.loads(json_str)
        assert parsed["id"] == 123
        assert parsed["name"] == "Test Rule"
