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
Tests for Get Deploy Status Tool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.config.get_deploy_status import GetDeployStatusTool


@pytest.fixture
def tool():
    """Create a GetDeployStatusTool instance for testing."""
    return GetDeployStatusTool()


@pytest.fixture
def mock_deploy_status():
    """Mock deploy status response."""
    return {
        "hosts": [
            {
                "host_status": "SUCCESS",
                "ip": "10.15.236.253",
                "status": "SUCCESS",
            }
        ],
        "percent_complete": 100,
        "initiated_from": "10.17.0.30",
        "type": "INCREMENTAL",
        "initiated_by": "admin",
        "status": "COMPLETE",
    }


class TestGetDeployStatusMetadata:
    """Test tool metadata properties."""

    def test_tool_name(self, tool):
        """Test that tool name is correct."""
        assert tool.name == "get_deploy_status"

    def test_tool_description(self, tool):
        """Test that tool has a description."""
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert "deploy status" in tool.description.lower()

    def test_input_schema(self, tool):
        """Test that input schema is properly defined."""
        schema = tool.input_schema
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert schema["properties"] == {}

    def test_approval_required(self, tool):
        """Test GET tool approval behavior."""
        assert tool.approval_required is False


class TestGetDeployStatusExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_execution(self, tool, mock_deploy_status):
        """Test successful deploy status retrieval."""
        mock_response = httpx.Response(
            200,
            json=mock_deploy_status,
            request=httpx.Request("GET", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "content" in result
        assert len(result["content"]) == 1
        content = json.loads(result["content"][0]["text"])
        assert content["status"] == "COMPLETE"
        tool.client.get.assert_called_once_with(
            'staged_config/deploy_status', params={}
        )


class TestGetDeployStatusErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_http_error_handling(self, tool):
        """Test handling of HTTP errors."""
        mock_response = httpx.Response(
            500,
            text="Server error",
            request=httpx.Request("GET", "http://test"),
        )
        http_error = httpx.HTTPStatusError(
            "Server error",
            request=mock_response.request,
            response=mock_response,
        )

        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=http_error)

        result = await tool.execute({})

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()
