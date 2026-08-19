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
Tests for CreateDsmEventMappingTool and UpdateDsmEventMappingTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.data_classification.create_dsm_event_mapping import CreateDsmEventMappingTool
from qradar_mcp.tools.data_classification.update_dsm_event_mapping import UpdateDsmEventMappingTool


SAMPLE_MAPPING = {
    "id": 1001,
    "log_source_type_id": 123,
    "log_source_event_id": "LoginFailure",
    "log_source_event_category": "Authentication",
    "custom_event": True,
    "qid_record_id": 64280,
    "uuid": "abc-123"
}


class TestCreateDsmEventMappingMetadata:
    """Test CreateDsmEventMappingTool metadata."""

    def test_tool_name(self):
        assert CreateDsmEventMappingTool().name == "create_dsm_event_mapping"

    def test_approval_required(self):
        assert CreateDsmEventMappingTool().approval_required is True

    def test_input_schema_required_fields(self):
        schema = CreateDsmEventMappingTool().input_schema
        required = schema["required"]
        assert "log_source_type_id" in required
        assert "log_source_event_id" in required
        assert "log_source_event_category" in required
        assert "qid_record_id" in required


class TestCreateDsmEventMappingExecution:
    """Test CreateDsmEventMappingTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            201,
            json=SAMPLE_MAPPING,
            request=httpx.Request("POST", "http://test")
        )
        tool = CreateDsmEventMappingTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "log_source_type_id": 123,
            "log_source_event_id": "LoginFailure",
            "log_source_event_category": "Authentication",
            "qid_record_id": 64280
        })

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["id"] == 1001

        call_args = tool.client.post.call_args
        assert "data_classification/dsm_event_mappings" in call_args[0][0]
        body = call_args[1]["data"]
        assert body["log_source_type_id"] == 123
        assert body["log_source_event_id"] == "LoginFailure"
        assert body["qid_record_id"] == 64280

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        tool = CreateDsmEventMappingTool()
        result = await tool.execute({})
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_missing_log_source_type_id(self):
        tool = CreateDsmEventMappingTool()
        result = await tool.execute({
            "log_source_event_id": "test",
            "log_source_event_category": "cat",
            "qid_record_id": 100
        })
        assert result["isError"] is True
        assert "log_source_type_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_missing_qid_record_id(self):
        tool = CreateDsmEventMappingTool()
        result = await tool.execute({
            "log_source_type_id": 123,
            "log_source_event_id": "test",
            "log_source_event_category": "cat"
        })
        assert result["isError"] is True
        assert "qid_record_id is required" in result["content"][0]["text"]


class TestUpdateDsmEventMappingMetadata:
    """Test UpdateDsmEventMappingTool metadata."""

    def test_tool_name(self):
        assert UpdateDsmEventMappingTool().name == "update_dsm_event_mapping"

    def test_approval_required(self):
        assert UpdateDsmEventMappingTool().approval_required is True

    def test_input_schema_required_fields(self):
        schema = UpdateDsmEventMappingTool().input_schema
        assert "dsm_event_mapping_id" in schema["required"]
        assert "qid_record_id" in schema["required"]


class TestUpdateDsmEventMappingExecution:
    """Test UpdateDsmEventMappingTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        updated = {**SAMPLE_MAPPING, "qid_record_id": 99999}
        mock_response = httpx.Response(
            200,
            json=updated,
            request=httpx.Request("POST", "http://test")
        )
        tool = UpdateDsmEventMappingTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({"dsm_event_mapping_id": 1001, "qid_record_id": 99999})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["qid_record_id"] == 99999

        call_args = tool.client.post.call_args
        assert "data_classification/dsm_event_mappings/1001" in call_args[0][0]
        assert call_args[1]["data"]["qid_record_id"] == 99999

    @pytest.mark.asyncio
    async def test_missing_mapping_id(self):
        tool = UpdateDsmEventMappingTool()
        result = await tool.execute({"qid_record_id": 100})
        assert result["isError"] is True
        assert "dsm_event_mapping_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_missing_qid_record_id(self):
        tool = UpdateDsmEventMappingTool()
        result = await tool.execute({"dsm_event_mapping_id": 1001})
        assert result["isError"] is True
        assert "qid_record_id is required" in result["content"][0]["text"]
