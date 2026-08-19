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
Unit tests for the SetOffenseFollowUpTool.
"""

import httpx
import pytest
from unittest.mock import AsyncMock

from qradar_mcp.tools.offense.set_offense_follow_up import SetOffenseFollowUpTool


class TestSetOffenseFollowUpTool:
    """Tests for SetOffenseFollowUpTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = SetOffenseFollowUpTool()
        assert tool.name == "set_offense_follow_up"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = SetOffenseFollowUpTool()
        assert "follow-up" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = SetOffenseFollowUpTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "offense_id" in schema["properties"]
        assert "follow_up" in schema["properties"]
        assert "fields" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_set_follow_up(self):
        """Test setting follow-up flag."""
        tool = SetOffenseFollowUpTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json={"id": 123, "follow_up": True},
            request=httpx.Request("POST", "http://test")
        )
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "offense_id": 123,
            "follow_up": True
        })

        call_args = tool.client.post.call_args
        assert call_args[1]["api_path"] == "siem/offenses/123"
        assert call_args[1]["params"]["follow_up"] is True
        assert "content" in result

    @pytest.mark.asyncio
    async def test_execute_missing_follow_up(self):
        """Test error when follow_up is missing."""
        tool = SetOffenseFollowUpTool()
        result = await tool.execute({"offense_id": 123})

        assert result["isError"] is True
        assert "follow_up is required" in result["content"][0]["text"].lower()
