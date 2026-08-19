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
Tests for ListAssetsTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.asset.list_assets import ListAssetsTool


class TestListAssetsMetadata:
    """Test ListAssetsTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = ListAssetsTool()
        assert tool.name == "list_assets"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = ListAssetsTool()
        assert tool.description
        assert "asset" in tool.description.lower()
        assert "list" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = ListAssetsTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_input_schema_optional_fields(self):
        """Test all fields are optional."""
        tool = ListAssetsTool()
        schema = tool.input_schema

        # All parameters should be optional
        assert "required" not in schema or len(schema.get("required", [])) == 0

        # But these fields should exist in properties
        optional_fields = ["filter", "fields", "sort", "limit", "offset", "format_output"]
        for field in optional_fields:
            assert field in schema["properties"]


class TestListAssetsExecution:
    """Test ListAssetsTool execution."""

    @pytest.fixture
    def sample_assets(self):
        """Sample asset data."""
        return [
            {
                "id": 1,
                "domain_id": 0,
                "hostnames": [{"name": "server1.example.com", "type": "DNS"}],
                "interfaces": [{
                    "ip_addresses": [{"value": "192.168.1.100", "type": "IPV4"}]
                }],
                "risk_score_sum": 45.5,
                "vulnerability_count": 3
            },
            {
                "id": 2,
                "domain_id": 0,
                "hostnames": [{"name": "server2.example.com", "type": "DNS"}],
                "interfaces": [{
                    "ip_addresses": [{"value": "192.168.1.101", "type": "IPV4"}]
                }],
                "risk_score_sum": 12.0,
                "vulnerability_count": 1
            }
        ]

    @pytest.mark.asyncio
    async def test_execute_no_parameters(self, sample_assets):
        """Test execution with no parameters."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_assets,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = ListAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "isError" not in result
        assert "Asset ID: 1" in result["content"][0]["text"]
        assert "Asset ID: 2" in result["content"][0]["text"]

        # Verify API call
        tool.client.get.assert_called_once()
        call_args = tool.client.get.call_args
        assert call_args[0][0] == 'asset_model/assets'

    @pytest.mark.asyncio
    async def test_execute_with_filter(self, sample_assets):
        """Test execution with filter parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=[sample_assets[0]],
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = ListAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "filter": "risk_score_sum > 40"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['filter'] == "risk_score_sum > 40"

    @pytest.mark.asyncio
    async def test_execute_with_sort(self, sample_assets):
        """Test execution with sort parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_assets,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = ListAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "sort": "-risk_score_sum"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['sort'] == "-risk_score_sum"

    @pytest.mark.asyncio
    async def test_execute_with_fields(self, sample_assets):
        """Test execution with fields parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_assets,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = ListAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "fields": "id,hostnames,risk_score_sum"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]['params']['fields'] == "id,hostnames,risk_score_sum"

    @pytest.mark.asyncio
    async def test_execute_with_pagination(self, sample_assets):
        """Test execution with limit and offset."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_assets,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = ListAssetsTool()
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
    async def test_execute_format_output_false(self, sample_assets):
        """Test execution with format_output=false returns JSON."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_assets,
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = ListAssetsTool()
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


class TestListAssetsErrorHandling:
    """Test ListAssetsTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        # Setup mock to raise error
        tool = ListAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("API connection failed"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: api connection failed" == result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Setup mock to raise ValueError
        tool = ListAssetsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=ValueError("Invalid parameter"))

        # Execute
        result = await tool.execute({})

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid parameter" == result["content"][0]["text"].lower()


class TestListAssetsFormatting:
    """Test ListAssetsTool output formatting."""

    def test_format_assets_empty_list(self):
        """Test formatting empty asset list."""
        tool = ListAssetsTool()
        result = tool._format_assets([])
        assert result == "No assets found"

    def test_format_assets_with_data(self):
        """Test formatting asset list with data."""
        tool = ListAssetsTool()
        assets = [{
            "id": 123,
            "domain_id": 0,
            "hostnames": [{"name": "test.example.com"}],
            "interfaces": [{
                "ip_addresses": [{"value": "10.0.0.1"}]
            }],
            "risk_score_sum": 25.5,
            "vulnerability_count": 2
        }]

        result = tool._format_assets(assets)

        assert "Asset ID: 123" in result
        assert "test.example.com" in result
        assert "10.0.0.1" in result
        assert "Risk Score: 25.5" in result
        assert "Vulnerabilities: 2" in result
        assert "Domain ID: 0" in result

    def test_format_assets_multiple_hostnames(self):
        """Test formatting asset with multiple hostnames."""
        tool = ListAssetsTool()
        assets = [{
            "id": 1,
            "domain_id": 0,
            "hostnames": [
                {"name": "server1.local"},
                {"name": "server1.example.com"}
            ],
            "interfaces": [],
            "risk_score_sum": 0,
            "vulnerability_count": 0
        }]

        result = tool._format_assets(assets)

        assert "server1.local" in result
        assert "server1.example.com" in result

    def test_format_assets_multiple_ips(self):
        """Test formatting asset with multiple IP addresses."""
        tool = ListAssetsTool()
        assets = [{
            "id": 1,
            "domain_id": 0,
            "hostnames": [],
            "interfaces": [
                {"ip_addresses": [{"value": "192.168.1.1"}]},
                {"ip_addresses": [{"value": "10.0.0.1"}]}
            ],
            "risk_score_sum": 0,
            "vulnerability_count": 0
        }]

        result = tool._format_assets(assets)

        assert "192.168.1.1" in result
        assert "10.0.0.1" in result

    def test_format_assets_no_hostnames_or_ips(self):
        """Test formatting asset with no hostnames or IPs."""
        tool = ListAssetsTool()
        assets = [{
            "id": 1,
            "domain_id": 0,
            "hostnames": [],
            "interfaces": [],
            "risk_score_sum": 0,
            "vulnerability_count": 0
        }]

        result = tool._format_assets(assets)

        # Should still show asset ID and other info
        assert "Asset ID: 1" in result
        assert "Risk Score: 0" in result
