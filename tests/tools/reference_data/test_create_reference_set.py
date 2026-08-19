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
Tests for CreateReferenceSetTool
"""

import json
import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.reference_data.create_reference_set import CreateReferenceSetTool


class TestCreateReferenceSetMetadata:
    """Test CreateReferenceSetTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = CreateReferenceSetTool()
        assert tool.name == "create_reference_set"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = CreateReferenceSetTool()
        assert tool.description
        assert "create" in tool.description.lower()
        assert "reference" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = CreateReferenceSetTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test name and entry_type are required in schema."""
        tool = CreateReferenceSetTool()
        schema = tool.input_schema

        assert "name" in schema["required"]
        assert "entry_type" in schema["required"]
        assert "name" in schema["properties"]
        assert "entry_type" in schema["properties"]

    def test_input_schema_entry_type_enum(self):
        """Test entry_type has valid enum values."""
        tool = CreateReferenceSetTool()
        schema = tool.input_schema

        entry_type_prop = schema["properties"]["entry_type"]
        assert "enum" in entry_type_prop
        expected_types = ["IP", "ALN", "ALNIC", "NUM", "PORT", "DATE", "CIDR"]
        assert set(entry_type_prop["enum"]) == set(expected_types)

    def test_input_schema_optional_fields(self):
        """Test optional fields are in schema but not required."""
        tool = CreateReferenceSetTool()
        schema = tool.input_schema

        optional_fields = [
            "description", "namespace", "time_to_live",
            "expiry_type", "expired_log_option", "tenant_id", "fields"
        ]

        for field in optional_fields:
            assert field not in schema["required"]
            assert field in schema["properties"]


class TestCreateReferenceSetExecution:
    """Test CreateReferenceSetTool execution."""

    @pytest.fixture
    def sample_created_set(self):
        """Sample created reference set data."""
        return {
            "id": 123,
            "name": "new_threat_ips",
            "description": "Newly created threat list",
            "entry_type": "IP",
            "number_of_entries": 0,
            "creation_time": 1640000000000,
            "namespace": "PRIVATE",
            "time_to_live": 86400,
            "expiry_type": "LAST_SEEN",
            "expired_log_option": "LOG_BATCH"
        }

    @pytest.mark.asyncio
    async def test_execute_minimal_request(self, sample_created_set):
        """Test basic execution with only required fields."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_created_set,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "name": "new_threat_ips",
            "entry_type": "IP"
        })

        # Verify
        assert "isError" not in result
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify API call
        tool.client.post.assert_called_once()
        call_args = tool.client.post.call_args
        assert call_args[0][0] == 'reference_data_collections/sets'

        # Verify body
        body = call_args[1]["data"]
        assert body["name"] == "new_threat_ips"
        assert body["entry_type"] == "IP"

    @pytest.mark.asyncio
    async def test_execute_with_all_optional_fields(self, sample_created_set):
        """Test execution with all optional fields."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_created_set,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "name": "new_threat_ips",
            "entry_type": "IP",
            "description": "Test description",
            "namespace": "SHARED",
            "time_to_live": 3600,
            "expiry_type": "FIRST_SEEN",
            "expired_log_option": "LOG_EACH"
        })

        # Verify
        assert "isError" not in result

        # Verify body includes all fields
        body = tool.client.post.call_args[1]["data"]
        assert body["description"] == "Test description"
        assert body["namespace"] == "SHARED"
        assert body["time_to_live"] == 3600
        assert body["expiry_type"] == "FIRST_SEEN"
        assert body["expired_log_option"] == "LOG_EACH"

    @pytest.mark.asyncio
    async def test_execute_with_fields_header(self, sample_created_set):
        """Test execution with fields parameter."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_created_set,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "name": "new_threat_ips",
            "entry_type": "IP",
            "fields": "id,name,entry_type"
        })

        # Verify
        assert "isError" not in result

        # Verify fields header
        headers = tool.client.post.call_args[1]["headers"]
        assert headers["fields"] == "id,name,entry_type"

    @pytest.mark.asyncio
    async def test_execute_response_format(self, sample_created_set):
        """Test response is properly formatted as JSON."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_created_set,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "name": "new_threat_ips",
            "entry_type": "IP"
        })

        # Verify JSON formatting
        content_text = result["content"][0]["text"]
        parsed_data = json.loads(content_text)
        assert parsed_data["id"] == 123
        assert parsed_data["name"] == "new_threat_ips"
        assert parsed_data["entry_type"] == "IP"

    @pytest.mark.asyncio
    async def test_execute_missing_name(self):
        """Test execution fails when name is missing."""
        tool = CreateReferenceSetTool()
        result = await tool.execute({"entry_type": "IP"})

        assert result["isError"] is True
        assert "name is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_missing_entry_type(self):
        """Test execution fails when entry_type is missing."""
        tool = CreateReferenceSetTool()
        result = await tool.execute({"name": "test_set"})

        assert result["isError"] is True
        assert "entry_type is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_empty_name(self):
        """Test execution fails when name is empty."""
        tool = CreateReferenceSetTool()
        result = await tool.execute({"name": "", "entry_type": "IP"})

        assert result["isError"] is True
        assert "name is required" in result["content"][0]["text"]


class TestCreateReferenceSetErrorHandling:
    """Test CreateReferenceSetTool error handling."""

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test handling of API errors."""
        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=RuntimeError("API connection failed"))
        result = await tool.execute({
            "name": "test_set",
            "entry_type": "IP"
        })

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed: API connection failed" in result["content"][0]["text"]
        assert "API connection failed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_duplicate_name_error(self):
        """Test handling of duplicate name errors."""
        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=RuntimeError("409: Set already exists"))
        result = await tool.execute({
            "name": "existing_set",
            "entry_type": "IP"
        })

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed: 409: Set already exists" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_invalid_entry_type_error(self):
        """Test handling of invalid entry type errors."""
        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=RuntimeError("422: Invalid entry_type"))
        result = await tool.execute({
            "name": "test_set",
            "entry_type": "IP"
        })

        # Verify error response
        assert result["isError"] is True
        assert "422" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_value_error(self):
        """Test handling of ValueError."""
        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=ValueError("Invalid parameter format"))
        result = await tool.execute({
            "name": "test_set",
            "entry_type": "IP"
        })

        # Verify error response
        assert result["isError"] is True
        assert "Tool execution failed:" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        # Setup mock to raise HTTPError
        mock_response = httpx.Response(
            500,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("500 Server Error", request=mock_response.request, response=mock_response)
        )
        result = await tool.execute({
            "name": "test_set",
            "entry_type": "IP"
        })

        # Verify error response
        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()


class TestCreateReferenceSetIntegration:
    """Integration tests for CreateReferenceSetTool."""

    @pytest.mark.asyncio
    async def test_create_different_entry_types(self):
        """Test creating sets with different entry types."""
        entry_types = ["IP", "ALN", "ALNIC", "NUM", "PORT", "DATE", "CIDR"]

        for entry_type in entry_types:
            # Setup mock
            mock_response = httpx.Response(
                200,
                json={
                    "id": 1,
                    "name": f"test_{entry_type.lower()}",
                    "entry_type": entry_type,
                    "number_of_entries": 0
                },
                request=httpx.Request("POST", "http://test")
            )

            # Execute
            tool = CreateReferenceSetTool()
            tool.client = AsyncMock()
            tool.client.post = AsyncMock(return_value=mock_response)
            result = await tool.execute({
                "name": f"test_{entry_type.lower()}",
                "entry_type": entry_type
            })

            # Verify
            assert "isError" not in result
            content_text = result["content"][0]["text"]
            parsed_data = json.loads(content_text)
            assert parsed_data["entry_type"] == entry_type

    @pytest.mark.asyncio
    async def test_create_with_different_namespaces(self):
        """Test creating sets with different namespaces."""
        namespaces = ["PRIVATE", "SHARED", "TENANT"]

        for namespace in namespaces:
            # Setup mock
            mock_response = httpx.Response(
                200,
                json={
                    "id": 1,
                    "name": f"test_{namespace.lower()}",
                    "namespace": namespace,
                    "entry_type": "IP",
                    "number_of_entries": 0
                },
                request=httpx.Request("POST", "http://test")
            )

            # Execute
            tool = CreateReferenceSetTool()
            tool.client = AsyncMock()
            tool.client.post = AsyncMock(return_value=mock_response)
            args = {
                "name": f"test_{namespace.lower()}",
                "entry_type": "IP",
                "namespace": namespace
            }

            # Add tenant_id for TENANT namespace
            if namespace == "TENANT":
                args["tenant_id"] = 1

            result = await tool.execute(args)

            # Verify
            assert "isError" not in result
            content_text = result["content"][0]["text"]
            parsed_data = json.loads(content_text)
            assert parsed_data["namespace"] == namespace

    @pytest.mark.asyncio
    async def test_create_with_ttl_configurations(self):
        """Test creating sets with different TTL configurations."""
        ttl_configs = [
            {"time_to_live": 3600, "expiry_type": "FIRST_SEEN"},
            {"time_to_live": 86400, "expiry_type": "LAST_SEEN"},
            {"expiry_type": "NO_EXPIRY"}
        ]

        for config in ttl_configs:
            # Setup mock
            response_data = {
                "id": 1,
                "name": "test_ttl",
                "entry_type": "IP",
                "number_of_entries": 0
            }
            response_data.update(config)
            mock_response = httpx.Response(
                200,
                json=response_data,
                request=httpx.Request("POST", "http://test")
            )

            # Execute
            tool = CreateReferenceSetTool()
            tool.client = AsyncMock()
            tool.client.post = AsyncMock(return_value=mock_response)
            args = {"name": "test_ttl", "entry_type": "IP"}
            args.update(config)
            result = await tool.execute(args)

            # Verify
            assert "isError" not in result
            content_text = result["content"][0]["text"]
            parsed_data = json.loads(content_text)
            assert parsed_data["expiry_type"] == config["expiry_type"]
