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
Tests for ListLowLevelCategoriesTool and GetLowLevelCategoryTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.data_classification.list_low_level_categories import ListLowLevelCategoriesTool
from qradar_mcp.tools.data_classification.get_low_level_category import GetLowLevelCategoryTool


SAMPLE_CATEGORY = {
    "id": 19001,
    "name": "General Audit Event",
    "description": "General Audit Event",
    "high_level_category_id": 19000,
    "severity": 0
}


class TestListLowLevelCategoriesMetadata:
    """Test ListLowLevelCategoriesTool metadata."""

    def test_tool_name(self):
        assert ListLowLevelCategoriesTool().name == "list_low_level_categories"

    def test_description_mentions_categories(self):
        assert "low level" in ListLowLevelCategoriesTool().description.lower()

    def test_approval_not_required(self):
        assert ListLowLevelCategoriesTool().approval_required is False

    def test_schema_optional_only(self):
        schema = ListLowLevelCategoriesTool().input_schema
        assert schema.get("required", []) == []


class TestListLowLevelCategoriesExecution:
    """Test ListLowLevelCategoriesTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_CATEGORY],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListLowLevelCategoriesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert isinstance(data, list)
        assert data[0]["id"] == 19001
        assert data[0]["severity"] == 0

        call_args = tool.client.get.call_args
        assert "data_classification/low_level_categories" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_filter_by_high_level_category(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_CATEGORY],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListLowLevelCategoriesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "high_level_category_id=19000"})

        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["filter"] == "high_level_category_id=19000"

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        tool = ListLowLevelCategoriesTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Server error"))

        result = await tool.execute({})
        assert result["isError"] is True


class TestGetLowLevelCategoryMetadata:
    """Test GetLowLevelCategoryTool metadata."""

    def test_tool_name(self):
        assert GetLowLevelCategoryTool().name == "get_low_level_category"

    def test_input_schema_required_fields(self):
        schema = GetLowLevelCategoryTool().input_schema
        assert "low_level_category_id" in schema["required"]

    def test_approval_not_required(self):
        assert GetLowLevelCategoryTool().approval_required is False


class TestGetLowLevelCategoryExecution:
    """Test GetLowLevelCategoryTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=SAMPLE_CATEGORY,
            request=httpx.Request("GET", "http://test")
        )
        tool = GetLowLevelCategoryTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"low_level_category_id": 19001})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["id"] == 19001
        assert data["high_level_category_id"] == 19000

        call_args = tool.client.get.call_args
        assert "data_classification/low_level_categories/19001" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_missing_id(self):
        tool = GetLowLevelCategoryTool()
        result = await tool.execute({})
        assert result["isError"] is True
        assert "low_level_category_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_fields(self):
        mock_response = httpx.Response(
            200,
            json=SAMPLE_CATEGORY,
            request=httpx.Request("GET", "http://test")
        )
        tool = GetLowLevelCategoryTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"low_level_category_id": 19001, "fields": "id,name,severity"})

        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["fields"] == "id,name,severity"
