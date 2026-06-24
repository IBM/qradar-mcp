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
Tests for ListQidRecordsTool, GetQidRecordTool, CreateQidRecordTool, and UpdateQidRecordTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.data_classification.list_qid_records import ListQidRecordsTool
from qradar_mcp.tools.data_classification.get_qid_record import GetQidRecordTool
from qradar_mcp.tools.data_classification.create_qid_record import CreateQidRecordTool
from qradar_mcp.tools.data_classification.update_qid_record import UpdateQidRecordTool


SAMPLE_QID_RECORD = {
    "id": 63998,
    "qid": 2500001,
    "name": "spp_portscan: Portscan Detected",
    "description": "spp_portscan: Portscan Detected",
    "severity": 4,
    "low_level_category_id": 1008,
    "log_source_type_id": None,
    "uuid": None
}


class TestListQidRecordsMetadata:
    """Test ListQidRecordsTool metadata."""

    def test_tool_name(self):
        assert ListQidRecordsTool().name == "list_qid_records"

    def test_description_mentions_qid(self):
        assert "qid" in ListQidRecordsTool().description.lower()

    def test_approval_not_required(self):
        assert ListQidRecordsTool().approval_required is False

    def test_schema_optional_only(self):
        schema = ListQidRecordsTool().input_schema
        assert schema.get("required", []) == []


class TestListQidRecordsExecution:
    """Test ListQidRecordsTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_QID_RECORD],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListQidRecordsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert isinstance(data, list)
        assert data[0]["id"] == 63998

        call_args = tool.client.get.call_args
        assert "/data_classification/qid_records" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_with_filter(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_QID_RECORD],
            request=httpx.Request("GET", "http://test")
        )
        tool = ListQidRecordsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"filter": "severity>=7"})

        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["filter"] == "severity>=7"

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        tool = ListQidRecordsTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Server error"))

        result = await tool.execute({})
        assert result["isError"] is True


class TestGetQidRecordMetadata:
    """Test GetQidRecordTool metadata."""

    def test_tool_name(self):
        assert GetQidRecordTool().name == "get_qid_record"

    def test_input_schema_required_fields(self):
        schema = GetQidRecordTool().input_schema
        assert "qid_record_id" in schema["required"]

    def test_approval_not_required(self):
        assert GetQidRecordTool().approval_required is False


class TestGetQidRecordExecution:
    """Test GetQidRecordTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=SAMPLE_QID_RECORD,
            request=httpx.Request("GET", "http://test")
        )
        tool = GetQidRecordTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"qid_record_id": 63998})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["id"] == 63998
        assert data["severity"] == 4

        call_args = tool.client.get.call_args
        assert "/data_classification/qid_records/63998" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_missing_id(self):
        tool = GetQidRecordTool()
        result = await tool.execute({})
        assert result["isError"] is True
        assert "qid_record_id is required" in result["content"][0]["text"]


class TestCreateQidRecordMetadata:
    """Test CreateQidRecordTool metadata."""

    def test_tool_name(self):
        assert CreateQidRecordTool().name == "create_qid_record"

    def test_approval_required(self):
        assert CreateQidRecordTool().approval_required is True

    def test_required_fields(self):
        schema = CreateQidRecordTool().input_schema
        required = schema["required"]
        assert "log_source_type_id" in required
        assert "name" in required
        assert "low_level_category_id" in required


class TestCreateQidRecordExecution:
    """Test CreateQidRecordTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            201,
            json=SAMPLE_QID_RECORD,
            request=httpx.Request("POST", "http://test")
        )
        tool = CreateQidRecordTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({
            "log_source_type_id": 199,
            "name": "spp_portscan: Portscan Detected",
            "low_level_category_id": 1008,
            "severity": 4
        })

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["id"] == 63998

        call_args = tool.client.post.call_args
        assert "/data_classification/qid_records" in call_args[0][0]
        body = call_args[1]["data"]
        assert body["log_source_type_id"] == 199
        assert body["name"] == "spp_portscan: Portscan Detected"
        assert body["low_level_category_id"] == 1008
        assert body["severity"] == 4

    @pytest.mark.asyncio
    async def test_missing_name(self):
        tool = CreateQidRecordTool()
        result = await tool.execute({"log_source_type_id": 199, "low_level_category_id": 1008})
        assert result["isError"] is True
        assert "name is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_missing_log_source_type_id(self):
        tool = CreateQidRecordTool()
        result = await tool.execute({"name": "Test", "low_level_category_id": 1008})
        assert result["isError"] is True
        assert "log_source_type_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_missing_low_level_category_id(self):
        tool = CreateQidRecordTool()
        result = await tool.execute({"log_source_type_id": 199, "name": "Test"})
        assert result["isError"] is True
        assert "low_level_category_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_optional_description_included(self):
        mock_response = httpx.Response(
            201,
            json=SAMPLE_QID_RECORD,
            request=httpx.Request("POST", "http://test")
        )
        tool = CreateQidRecordTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        await tool.execute({
            "log_source_type_id": 199,
            "name": "Test",
            "low_level_category_id": 1008,
            "description": "My description"
        })

        call_args = tool.client.post.call_args
        assert call_args[1]["data"]["description"] == "My description"


class TestUpdateQidRecordMetadata:
    """Test UpdateQidRecordTool metadata."""

    def test_tool_name(self):
        assert UpdateQidRecordTool().name == "update_qid_record"

    def test_approval_required(self):
        assert UpdateQidRecordTool().approval_required is True

    def test_required_fields(self):
        schema = UpdateQidRecordTool().input_schema
        assert "qid_record_id" in schema["required"]


class TestUpdateQidRecordExecution:
    """Test UpdateQidRecordTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        updated = {**SAMPLE_QID_RECORD, "name": "Updated Name", "severity": 7}
        mock_response = httpx.Response(
            200,
            json=updated,
            request=httpx.Request("POST", "http://test")
        )
        tool = UpdateQidRecordTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        result = await tool.execute({"qid_record_id": 63998, "name": "Updated Name", "severity": 7})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        assert data["name"] == "Updated Name"
        assert data["severity"] == 7

        call_args = tool.client.post.call_args
        assert "/data_classification/qid_records/63998" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_missing_qid_record_id(self):
        tool = UpdateQidRecordTool()
        result = await tool.execute({"name": "Test"})
        assert result["isError"] is True
        assert "qid_record_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_no_update_fields_provided(self):
        tool = UpdateQidRecordTool()
        result = await tool.execute({"qid_record_id": 63998})
        assert result["isError"] is True
        assert "at least one updatable field" in result["content"][0]["text"]
