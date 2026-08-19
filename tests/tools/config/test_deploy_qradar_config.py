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
Tests for Deploy QRadar Config Tool
"""

import json
from unittest.mock import AsyncMock
import pytest
import httpx
from qradar_mcp.tools.config.deploy_qradar_config import DeployQrConfigTool


@pytest.fixture
def tool():
    """Create a DeployQrConfigTool instance for testing."""
    return DeployQrConfigTool()


@pytest.fixture
def mock_deploy_status():
    """Mock deploy status response."""
    return {
        "hosts": [
            {
                "host_status": "INITIATING",
                "ip": "10.15.236.253",
                "status": "INITIATING",
            }
        ],
        "percent_complete": 0,
        "initiated_from": "10.17.0.30",
        "type": "INCREMENTAL",
        "initiated_by": "admin",
        "status": "INITIALIZING",
    }


class TestDeployQrConfigMetadata:
    """Test tool metadata properties."""

    def test_tool_name(self, tool):
        """Test that tool name is correct."""
        assert tool.name == "deploy_qradar_config"

    def test_tool_description(self, tool):
        """Test that tool has a description."""
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
        assert "get_deploy_status" in tool.description

    def test_input_schema(self, tool):
        """Test that input schema is properly defined."""
        schema = tool.input_schema
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "type" in schema["properties"]
        assert "type" in schema["required"]


class TestDeployQrConfigExecution:
    """Test tool execution."""

    @pytest.mark.asyncio
    async def test_successful_execution(self, tool, mock_deploy_status):
        """Test successful deploy execution."""
        mock_response = httpx.Response(
            200,
            json=mock_deploy_status,
            request=httpx.Request("POST", "http://test"),
        )

        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({"type": "INCREMENTAL"})

        assert "content" in result
        assert len(result["content"]) == 1
        content = json.loads(result["content"][0]["text"])
        assert content["type"] == "INCREMENTAL"
        tool.client.post.assert_called_once_with(
            'staged_config/deploy_status',
            data={"type": "INCREMENTAL"},
        )

    @pytest.mark.asyncio
    async def test_missing_type(self, tool):
        """Test missing required type."""
        result = await tool.execute({})

        assert result["isError"] is True
        assert result["content"][0]["text"] == "Error: type is required"


class TestDeployQrConfigErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_http_error_handling(self, tool):
        """Test handling of HTTP errors."""
        mock_response = httpx.Response(
            409,
            text="Deploy already in progress",
            request=httpx.Request("POST", "http://test"),
        )
        http_error = httpx.HTTPStatusError(
            "Deploy already in progress",
            request=mock_response.request,
            response=mock_response,
        )

        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=http_error)

        result = await tool.execute({"type": "INCREMENTAL"})

        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()
