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
Unit tests for the SetOffenseStatusTool.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.offense.set_offense_status import SetOffenseStatusTool


class TestSetOffenseStatusTool:
    """Tests for SetOffenseStatusTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = SetOffenseStatusTool()
        assert tool.name == "set_offense_status"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = SetOffenseStatusTool()
        assert "status" in tool.description.lower()
        assert "closing_reason_id" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = SetOffenseStatusTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "offense_id" in schema["properties"]
        assert "status" in schema["properties"]
        assert "closing_reason_id" in schema["properties"]
        assert "fields" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_close_offense(self):
        """Test closing offense."""
        tool = SetOffenseStatusTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json={
                "id": 123,
                "status": "CLOSED",
                "closing_reason_id": 1
            },
            request=httpx.Request("POST", "http://test")
        )
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "offense_id": 123,
            "status": "CLOSED",
            "closing_reason_id": 1
        })

        call_args = tool.client.post.call_args
        assert call_args[1]["api_path"] == "siem/offenses/123"
        assert call_args[1]["params"]["status"] == "CLOSED"
        assert call_args[1]["params"]["closing_reason_id"] == 1
        assert "content" in result

    @pytest.mark.asyncio
    async def test_execute_hide_offense(self):
        """Test hiding offense."""
        tool = SetOffenseStatusTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123, "status": "HIDDEN"},
            request=httpx.Request("POST", "http://test")
        )
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "offense_id": 123,
            "status": "HIDDEN"
        })

        call_args = tool.client.post.call_args
        assert call_args[1]["params"]["status"] == "HIDDEN"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_execute_close_without_reason(self):
        """Test error when closing offense without closing_reason_id."""
        tool = SetOffenseStatusTool()
        result = await tool.execute({
            "offense_id": 123,
            "status": "CLOSED"
        })

        assert result["isError"] is True
        assert "closing_reason_id is required" in result["content"][0]["text"].lower()
