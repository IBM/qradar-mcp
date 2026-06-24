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
Tests for ListDsmEventMappingsTool and GetDsmEventMappingTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.data_classification.list_dsm_event_mappings import ListDsmEventMappingsTool
from qradar_mcp.tools.data_classification.get_dsm_event_mapping import GetDsmEventMappingTool


SAMPLE_MAPPING = {
    "id": 1001,
    "log_source_type_id": 123,
    "log_source_event_id": "LoginFailure",
    "log_source_event_category": "Authentication",
    "custom_event": True,
    "qid_record_id": 64280,
    "uuid": "abc-123"
}


class TestListDsmEventMappingsMetadata:
    """Test ListDsmEventMappingsTool metadata."""

    def test_tool_name(self):
        assert ListDsmEventMappingsTool().name == "list_dsm_event_mappings"

    def test_tool_description(self):
        tool = ListDsmEventMappingsTool()
        assert tool.description
        assert "dsm" in tool.description.lower()

    def test_input_schema_structure(self):
        schema = ListDsmEventMappingsTool().input_schema
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_approval_not_required(self):
        assert ListDsmEventMappingsTool().approval_required is False


class TestListDsmEventMappingsExecution:
    """Test ListDsmEventMappingsTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_MAPPING],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListDsmEventMappingsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert isinstance(data, list)
        assert data[0]["id"] == 1001

    @pytest.mark.asyncio
    async def test_execute_with_filter(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_MAPPING],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListDsmEventMappingsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "custom_event=true"})

        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["filter"] == "custom_event=true"

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        tool = ListDsmEventMappingsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Connection failed"))

        result = await tool.execute({})

        assert result["isError"] is True


class TestGetDsmEventMappingMetadata:
    """Test GetDsmEventMappingTool metadata."""

    def test_tool_name(self):
        assert GetDsmEventMappingTool().name == "get_dsm_event_mapping"

    def test_input_schema_required_fields(self):
        schema = GetDsmEventMappingTool().input_schema
        assert "dsm_event_mapping_id" in schema["required"]

    def test_approval_not_required(self):
        assert GetDsmEventMappingTool().approval_required is False


class TestGetDsmEventMappingExecution:
    """Test GetDsmEventMappingTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=SAMPLE_MAPPING,
            request=httpx.Request("GET", "http://test")
        )
        tool = GetDsmEventMappingTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"dsm_event_mapping_id": 1001})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["id"] == 1001
        call_args = tool.client.get.call_args
        assert "/data_classification/dsm_event_mappings/1001" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_missing_id(self):
        tool = GetDsmEventMappingTool()
        result = await tool.execute({})
        assert result["isError"] is True
        assert "dsm_event_mapping_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_with_fields(self):
        mock_response = httpx.Response(
            200,
            json=SAMPLE_MAPPING,
            request=httpx.Request("GET", "http://test")
        )
        tool = GetDsmEventMappingTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"dsm_event_mapping_id": 1001, "fields": "id,qid_record_id"})

        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["fields"] == "id,qid_record_id"
