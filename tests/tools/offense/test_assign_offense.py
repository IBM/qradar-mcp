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
Unit tests for the AssignOffenseTool.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.offense.assign_offense import AssignOffenseTool


class TestAssignOffenseTool:
    """Tests for AssignOffenseTool class."""

    def test_tool_name(self):
        """Test that tool has correct name."""
        tool = AssignOffenseTool()
        assert tool.name == "assign_offense"

    def test_tool_description(self):
        """Test that tool has correct description."""
        tool = AssignOffenseTool()
        assert "Assign" in tool.description

    def test_input_schema_structure(self):
        """Test that input schema has correct structure."""
        tool = AssignOffenseTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "offense_id" in schema["properties"]
        assert "assigned_to" in schema["properties"]
        assert "fields" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_assign_offense(self):
        """Test assigning offense to user."""
        tool = AssignOffenseTool()
        tool.client = AsyncMock()

        mock_response = httpx.Response(
            status_code=200,
            json={
                "id": 123,
                "assigned_to": "admin"
            },
            request=httpx.Request("POST", "http://test")
        )
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "offense_id": 123,
            "assigned_to": "admin"
        })

        call_args = tool.client.post.call_args
        assert call_args[1]["api_path"] == "siem/offenses/123"
        assert call_args[1]["params"]["assigned_to"] == "admin"
        assert "content" in result
        assert "admin" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_missing_assigned_to(self):
        """Test error when assigned_to is missing."""
        tool = AssignOffenseTool()
        result = await tool.execute({"offense_id": 123})

        assert result["isError"] is True
        assert "assigned_to is required" in result["content"][0]["text"].lower()
