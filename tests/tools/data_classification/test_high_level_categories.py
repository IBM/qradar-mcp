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
Tests for ListHighLevelCategoriesTool and GetHighLevelCategoryTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.data_classification.list_high_level_categories import ListHighLevelCategoriesTool
from qradar_mcp.tools.data_classification.get_high_level_category import GetHighLevelCategoryTool


SAMPLE_CATEGORY = {"id": 19000, "name": "Audit", "description": "Audit"}


class TestListHighLevelCategoriesMetadata:
    """Test ListHighLevelCategoriesTool metadata."""

    def test_tool_name(self):
        assert ListHighLevelCategoriesTool().name == "list_high_level_categories"

    def test_description_mentions_categories(self):
        assert "categor" in ListHighLevelCategoriesTool().description.lower()

    def test_approval_not_required(self):
        assert ListHighLevelCategoriesTool().approval_required is False

    def test_schema_optional_only(self):
        schema = ListHighLevelCategoriesTool().input_schema
        assert schema.get("required", []) == []


class TestListHighLevelCategoriesExecution:
    """Test ListHighLevelCategoriesTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_CATEGORY],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListHighLevelCategoriesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert isinstance(data, list)
        assert data[0]["id"] == 19000

        call_args = tool.client.get.call_args
        assert "/data_classification/high_level_categories" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_with_sort(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_CATEGORY],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListHighLevelCategoriesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"sort": "+name"})

        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["sort"] == "+name"

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        tool = ListHighLevelCategoriesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Server error"))

        result = await tool.execute({})
        assert result["isError"] is True


class TestGetHighLevelCategoryMetadata:
    """Test GetHighLevelCategoryTool metadata."""

    def test_tool_name(self):
        assert GetHighLevelCategoryTool().name == "get_high_level_category"

    def test_input_schema_required_fields(self):
        schema = GetHighLevelCategoryTool().input_schema
        assert "high_level_category_id" in schema["required"]

    def test_approval_not_required(self):
        assert GetHighLevelCategoryTool().approval_required is False


class TestGetHighLevelCategoryExecution:
    """Test GetHighLevelCategoryTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=SAMPLE_CATEGORY,
            request=httpx.Request("GET", "http://test")
        )
        tool = GetHighLevelCategoryTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"high_level_category_id": 19000})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["id"] == 19000
        assert data["name"] == "Audit"

        call_args = tool.client.get.call_args
        assert "/data_classification/high_level_categories/19000" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_missing_id(self):
        tool = GetHighLevelCategoryTool()
        result = await tool.execute({})
        assert result["isError"] is True
        assert "high_level_category_id is required" in result["content"][0]["text"]
