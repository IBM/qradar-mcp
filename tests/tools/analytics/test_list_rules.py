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
Tests for ListRulesTool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.analytics.list_rules import ListRulesTool


class TestListRulesMetadata:
    """Test ListRulesTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = ListRulesTool()
        assert tool.name == "list_rules"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = ListRulesTool()
        assert tool.description
        assert "rule" in tool.description.lower()
        assert "analytics" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = ListRulesTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListRulesTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # But these fields should exist in properties
        optional_fields = ["filter", "fields", "limit", "offset", "format_output"]
        for field in optional_fields:
            assert field in schema["properties"]


class TestListRulesExecution:
    """Test ListRulesTool execution."""

    @pytest.fixture
    def sample_rules(self):
        """Sample rules data."""
        return [
            {
                "id": 100001,
                "name": "Suspicious Login Activity",
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
                "name": "Port Scan Detection",
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
    async def test_execute_no_parameters(self, sample_rules):
        """Test execution with no parameters."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_rules,
            request=mock_request
        )

        tool = ListRulesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "isError" not in result
        assert "Rule ID: 100001" in result["content"][0]["text"]
        assert "Rule ID: 100002" in result["content"][0]["text"]
        assert "Suspicious Login Activity" in result["content"][0]["text"]

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'analytics/rules'

    @pytest.mark.asyncio
    async def test_execute_with_filter(self, sample_rules):
        """Test execution with filter parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=[sample_rules[0]],
            request=mock_request
        )

        tool = ListRulesTool()
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
    async def test_execute_with_fields(self, sample_rules):
        """Test execution with fields parameter."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_rules,
            request=mock_request
        )

        tool = ListRulesTool()
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
    async def test_execute_with_pagination(self, sample_rules):
        """Test execution with limit and offset."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_rules,
            request=mock_request
        )

        tool = ListRulesTool()
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
    async def test_execute_format_output_false(self, sample_rules):
        """Test execution with format_output=false returns JSON."""
        mock_request = httpx.Request("GET", "http://test.com")
        mock_response = httpx.Response(
            200,
            json=sample_rules,
            request=mock_request
        )

        tool = ListRulesTool()
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


class TestListRulesErrorHandling:
    """Test ListRulesTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        tool = ListRulesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        tool = ListRulesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" in result["content"][0]["text"].lower()


class TestListRulesFormatting:
    """Test ListRulesTool output formatting."""

    def test_format_rules_empty_list(self):
        """Test formatting empty rules list."""
        tool = ListRulesTool()
        result = tool._format_rules([])
        assert result == "No rules found"

    def test_format_rules_with_data(self):
        """Test formatting rules list with data."""
        tool = ListRulesTool()
        rules = [{
            "id": 123,
            "name": "Test Rule",
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

        result = tool._format_rules(rules)

        assert "Rule ID: 123" in result
        assert "Test Rule" in result
        assert "Type: EVENT | Origin: USER" in result
        assert "✓ Enabled" in result
        assert "Owner: admin" in result
        assert "Capacity:" in result
        assert "Avg: 1000 EPS" in result
        assert "Base: 950 EPS" in result
        assert "Identifier: 550e8400-e29b-41d4-a716-446655440000" in result

    def test_format_rules_disabled(self):
        """Test formatting disabled rule."""
        tool = ListRulesTool()
        rules = [{
            "id": 1,
            "name": "Disabled Rule",
            "type": "FLOW",
            "origin": "SYSTEM",
            "enabled": False,
            "owner": "admin"
        }]

        result = tool._format_rules(rules)

        assert "✗ Disabled" in result

    def test_format_rules_with_linked_identifier(self):
        """Test formatting rule with linked identifier."""
        tool = ListRulesTool()
        rules = [{
            "id": 1,
            "name": "Override Rule",
            "type": "EVENT",
            "origin": "OVERRIDE",
            "enabled": True,
            "owner": "admin",
            "identifier": "550e8400-e29b-41d4-a716-446655440001",
            "linked_rule_identifier": "550e8400-e29b-41d4-a716-446655440000"
        }]

        result = tool._format_rules(rules)

        assert "Linked Rule: 550e8400-e29b-41d4-a716-446655440000" in result

    def test_format_rules_system_origin(self):
        """Test formatting system rule."""
        tool = ListRulesTool()
        rules = [{
            "id": 1,
            "name": "System Rule",
            "type": "COMMON",
            "origin": "SYSTEM",
            "enabled": True,
            "owner": "system"
        }]

        result = tool._format_rules(rules)

        assert "Origin: SYSTEM" in result

    def test_format_rules_without_capacity(self):
        """Test formatting rule without capacity metrics."""
        tool = ListRulesTool()
        rules = [{
            "id": 1,
            "name": "Simple Rule",
            "type": "EVENT",
            "origin": "USER",
            "enabled": True,
            "owner": "admin"
        }]

        result = tool._format_rules(rules)

        # Should not have capacity line
        assert "Capacity:" not in result
        assert "Rule ID: 1" in result
        assert "Simple Rule" in result
