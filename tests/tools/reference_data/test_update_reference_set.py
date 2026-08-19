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
Tests for Update Reference Set Tool
"""

import pytest
from unittest.mock import AsyncMock
import httpx
from qradar_mcp.tools.reference_data.update_reference_set import UpdateReferenceSetTool


@pytest.fixture
def update_reference_set_tool():
    """Fixture providing UpdateReferenceSetTool instance."""
    return UpdateReferenceSetTool()


@pytest.fixture
def mock_reference_set_response():
    """Fixture providing mock reference set response."""
    return {
        "id": 123,
        "name": "threat_ips",
        "entry_type": "IP",
        "description": "Updated description",
        "time_to_live": 7200,
        "expiry_type": "LAST_SEEN",
        "expired_log_option": "LOG_EACH",
        "number_of_entries": 42,
        "creation_time": 1234567890000,
        "namespace": "SHARED"
    }


class TestUpdateReferenceSetToolProperties:
    """Test UpdateReferenceSetTool properties."""

    def test_name(self, update_reference_set_tool):
        """Test tool name property."""
        assert update_reference_set_tool.name == "update_reference_set"

    def test_description(self, update_reference_set_tool):
        """Test tool description property."""
        description = update_reference_set_tool.description
        assert "Update properties" in description
        assert "reference data set" in description
        assert "TTL" in description
        assert "expiry" in description

    def test_input_schema(self, update_reference_set_tool):
        """Test input schema structure."""
        schema = update_reference_set_tool.input_schema
        assert schema["type"] == "object"
        assert "set_id" in schema["properties"]
        assert "description" in schema["properties"]
        assert "time_to_live" in schema["properties"]
        assert "expiry_type" in schema["properties"]
        assert "expired_log_option" in schema["properties"]
        assert "delete_entries" in schema["properties"]
        assert "fields" in schema["properties"]
        assert schema["required"] == ["set_id"]


class TestUpdateReferenceSetToolExecution:
    """Test UpdateReferenceSetTool execution."""

    @pytest.mark.asyncio
    async def test_update_description(self, update_reference_set_tool,
                               mock_reference_set_response):
        """Test updating reference set description."""
        mock_response = httpx.Response(200, json=mock_reference_set_response, request=httpx.Request("POST", "http://test"))

        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(return_value=mock_response)

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "description": "Updated description"
        })

        assert result["content"][0]["type"] == "text"
        assert "threat_ips" in result["content"][0]["text"]
        assert "Updated description" in result["content"][0]["text"]
        update_reference_set_tool.client.post.assert_called_once()
        call_args = update_reference_set_tool.client.post.call_args
        assert call_args[0][0] == 'reference_data_collections/sets/123'
        assert call_args[1]["data"]["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_ttl(self, update_reference_set_tool,
                       mock_reference_set_response):
        """Test updating reference set TTL."""
        mock_response = httpx.Response(200, json=mock_reference_set_response, request=httpx.Request("POST", "http://test"))

        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(return_value=mock_response)

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "time_to_live": 7200
        })

        assert result["content"][0]["type"] == "text"
        update_reference_set_tool.client.post.assert_called_once()
        call_args = update_reference_set_tool.client.post.call_args
        assert call_args[1]["data"]["time_to_live"] == 7200

    @pytest.mark.asyncio
    async def test_update_expiry_type(self, update_reference_set_tool,
                                mock_reference_set_response):
        """Test updating reference set expiry type."""
        mock_response = httpx.Response(200, json=mock_reference_set_response, request=httpx.Request("POST", "http://test"))

        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(return_value=mock_response)

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "expiry_type": "LAST_SEEN"
        })

        assert result["content"][0]["type"] == "text"
        update_reference_set_tool.client.post.assert_called_once()
        call_args = update_reference_set_tool.client.post.call_args
        assert call_args[1]["data"]["expiry_type"] == "LAST_SEEN"

    @pytest.mark.asyncio
    async def test_update_expired_log_option(self, update_reference_set_tool,
                                       mock_reference_set_response):
        """Test updating reference set expired log option."""
        mock_response = httpx.Response(200, json=mock_reference_set_response, request=httpx.Request("POST", "http://test"))

        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(return_value=mock_response)

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "expired_log_option": "LOG_EACH"
        })

        assert result["content"][0]["type"] == "text"
        update_reference_set_tool.client.post.assert_called_once()
        call_args = update_reference_set_tool.client.post.call_args
        assert call_args[1]["data"]["expired_log_option"] == "LOG_EACH"

    @pytest.mark.asyncio
    async def test_delete_entries(self, update_reference_set_tool,
                           mock_reference_set_response):
        """Test deleting all entries from reference set."""
        mock_response = httpx.Response(200, json=mock_reference_set_response, request=httpx.Request("POST", "http://test"))

        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(return_value=mock_response)

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "delete_entries": True
        })

        assert result["content"][0]["type"] == "text"
        update_reference_set_tool.client.post.assert_called_once()
        call_args = update_reference_set_tool.client.post.call_args
        assert call_args[1]["data"]["delete_entries"] is True

    @pytest.mark.asyncio
    async def test_update_multiple_properties(self, update_reference_set_tool,
                                        mock_reference_set_response):
        """Test updating multiple properties at once."""
        mock_response = httpx.Response(200, json=mock_reference_set_response, request=httpx.Request("POST", "http://test"))

        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(return_value=mock_response)

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "description": "Updated description",
            "time_to_live": 7200,
            "expiry_type": "LAST_SEEN",
            "expired_log_option": "LOG_EACH"
        })

        assert result["content"][0]["type"] == "text"
        update_reference_set_tool.client.post.assert_called_once()
        call_args = update_reference_set_tool.client.post.call_args
        body = call_args[1]["data"]
        assert body["description"] == "Updated description"
        assert body["time_to_live"] == 7200
        assert body["expiry_type"] == "LAST_SEEN"
        assert body["expired_log_option"] == "LOG_EACH"

    @pytest.mark.asyncio
    async def test_with_fields_parameter(self, update_reference_set_tool,
                                   mock_reference_set_response):
        """Test updating with fields parameter."""
        mock_response = httpx.Response(200, json=mock_reference_set_response, request=httpx.Request("POST", "http://test"))

        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(return_value=mock_response)

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "description": "Updated",
            "fields": "id,name,description"
        })

        assert result["content"][0]["type"] == "text"
        update_reference_set_tool.client.post.assert_called_once()
        call_args = update_reference_set_tool.client.post.call_args
        assert call_args[1]["headers"]["fields"] == "id,name,description"


class TestUpdateReferenceSetToolValidation:
    """Test UpdateReferenceSetTool validation."""

    @pytest.mark.asyncio
    async def test_missing_set_id(self, update_reference_set_tool):
        """Test error when set_id is missing."""
        result = await update_reference_set_tool.execute({
            "description": "Updated"
        })

        assert result["isError"] is True
        assert "set_id is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_no_update_parameters(self, update_reference_set_tool):
        """Test error when no update parameters provided."""
        result = await update_reference_set_tool.execute({
            "set_id": 123
        })

        assert result["isError"] is True
        assert "At least one update parameter must be provided" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_only_fields_parameter(self, update_reference_set_tool):
        """Test error when only fields parameter provided (no updates)."""
        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "fields": "id,name"
        })

        assert result["isError"] is True
        assert "At least one update parameter must be provided" in result["content"][0]["text"]


class TestUpdateReferenceSetToolErrorHandling:
    """Test UpdateReferenceSetTool error handling."""

    @pytest.mark.asyncio
    async def test_api_error(self, update_reference_set_tool):
        """Test handling of API errors."""
        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(side_effect=RuntimeError("API Error: 404 Not Found"))

        result = await update_reference_set_tool.execute({
            "set_id": 999,
            "description": "Updated"
        })

        assert result["isError"] is True
        assert "Tool execution failed: API Error: 404 Not Found" in result["content"][0]["text"]
        assert "API Error" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_value_error(self, update_reference_set_tool):
        """Test handling of value errors."""
        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(side_effect=ValueError("Invalid value"))

        result = await update_reference_set_tool.execute({
            "set_id": 123,
            "description": "Updated"
        })

        assert result["isError"] is True
        assert "Tool execution failed: Invalid value" in result["content"][0]["text"]
        assert "Invalid value" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_http_error(self, update_reference_set_tool):
        """Test handling of HTTP errors."""
        # Setup mock to raise HTTPStatusError
        mock_request = httpx.Request("POST", "http://test")
        mock_response = httpx.Response(404, request=mock_request)
        http_error = httpx.HTTPStatusError("404 Not Found", request=mock_request, response=mock_response)

        # Execute
        update_reference_set_tool.client = AsyncMock()
        update_reference_set_tool.client.post = AsyncMock(side_effect=http_error)
        result = await update_reference_set_tool.execute({
            "set_id": 999,
            "description": "Updated"
        })

        # Verify error response
        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()


class TestUpdateReferenceSetToolBodyBuilder:
    """Test UpdateReferenceSetTool body building."""

    def test_build_body_single_field(self, update_reference_set_tool):
        """Test building body with single field."""
        body = update_reference_set_tool._build_body({
            "set_id": 123,
            "description": "Updated"
        })

        assert body == {"description": "Updated"}

    def test_build_body_multiple_fields(self, update_reference_set_tool):
        """Test building body with multiple fields."""
        body = update_reference_set_tool._build_body({
            "set_id": 123,
            "description": "Updated",
            "time_to_live": 7200,
            "expiry_type": "LAST_SEEN"
        })

        assert body["description"] == "Updated"
        assert body["time_to_live"] == 7200
        assert body["expiry_type"] == "LAST_SEEN"

    def test_build_body_excludes_non_update_fields(self, update_reference_set_tool):
        """Test that body excludes non-update fields."""
        body = update_reference_set_tool._build_body({
            "set_id": 123,
            "description": "Updated",
            "fields": "id,name"
        })

        assert "description" in body
        assert "set_id" not in body
        assert "fields" not in body

    def test_build_body_with_none_values(self, update_reference_set_tool):
        """Test that None values are excluded from body."""
        body = update_reference_set_tool._build_body({
            "set_id": 123,
            "description": "Updated",
            "time_to_live": None
        })

        assert "description" in body
        assert "time_to_live" not in body

    def test_build_body_with_boolean_false(self, update_reference_set_tool):
        """Test that boolean False is included in body."""
        body = update_reference_set_tool._build_body({
            "set_id": 123,
            "delete_entries": False
        })

        assert "delete_entries" in body
        assert body["delete_entries"] is False


class TestUpdateReferenceSetToolHeadersBuilder:
    """Test UpdateReferenceSetTool headers building."""

    def test_build_headers_with_fields(self, update_reference_set_tool):
        """Test building headers with fields parameter."""
        headers = update_reference_set_tool._build_headers({
            "fields": "id,name,description"
        })

        assert headers == {"fields": "id,name,description"}

    def test_build_headers_without_fields(self, update_reference_set_tool):
        """Test building headers without fields parameter."""
        headers = update_reference_set_tool._build_headers({
            "set_id": 123
        })

        assert headers == {}

    def test_build_headers_with_none_fields(self, update_reference_set_tool):
        """Test building headers with None fields value."""
        headers = update_reference_set_tool._build_headers({
            "fields": None
        })

        assert headers == {}
