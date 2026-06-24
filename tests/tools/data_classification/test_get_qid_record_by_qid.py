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
Tests for GetQidRecordByQidTool
"""

import json
import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.data_classification.get_qid_record_by_qid import GetQidRecordByQidTool


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


class TestGetQidRecordByQidMetadata:
    """Test GetQidRecordByQidTool metadata."""

    def test_tool_name(self):
        assert GetQidRecordByQidTool().name == "get_qid_record_by_qid"

    def test_description_mentions_qid(self):
        desc = GetQidRecordByQidTool().description.lower()
        assert "qid" in desc

    def test_input_schema_required_fields(self):
        schema = GetQidRecordByQidTool().input_schema
        assert "qid" in schema["required"]
        assert "qid" in schema["properties"]

    def test_input_schema_optional_fields(self):
        schema = GetQidRecordByQidTool().input_schema
        assert "fields" in schema["properties"]
        assert "fields" not in schema.get("required", [])

    def test_approval_not_required(self):
        assert GetQidRecordByQidTool().approval_required is False

    def test_http_verb_is_get(self):
        assert GetQidRecordByQidTool().http_verb == "GET"


class TestGetQidRecordByQidExecution:
    """Test GetQidRecordByQidTool execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_QID_RECORD],
            request=httpx.Request("GET", "http://test")
        )
        tool = GetQidRecordByQidTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"qid": 2500001})

        assert "isError" not in result
        data = json.loads(result["content"][0]["text"])
        # Returns the single record object, not a list
        assert isinstance(data, dict)
        assert data["qid"] == 2500001
        assert data["id"] == 63998

        call_args = tool.client.get.call_args
        assert "/data_classification/qid_records" in call_args[0][0]
        assert call_args[1]["params"]["filter"] == "qid=2500001"

    @pytest.mark.asyncio
    async def test_execute_with_fields(self):
        mock_response = httpx.Response(
            200,
            json=[SAMPLE_QID_RECORD],
            request=httpx.Request("GET", "http://test")
        )
        tool = GetQidRecordByQidTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"qid": 2500001, "fields": "id,qid,name"})

        assert "isError" not in result
        call_args = tool.client.get.call_args
        assert call_args[1]["params"]["fields"] == "id,qid,name"

    @pytest.mark.asyncio
    async def test_execute_not_found(self):
        """Returns an error when the API returns an empty list."""
        mock_response = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "http://test")
        )
        tool = GetQidRecordByQidTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_response)

        result = await tool.execute({"qid": 9999999})

        assert result["isError"] is True
        assert "no QID record found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_missing_qid(self):
        tool = GetQidRecordByQidTool()
        result = await tool.execute({})
        assert result["isError"] is True
        assert "qid is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        tool = GetQidRecordByQidTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(side_effect=RuntimeError("Connection failed"))

        result = await tool.execute({"qid": 2500001})
        assert result["isError"] is True
