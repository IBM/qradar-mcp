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
Tests for AddToReferenceSetTool
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.reference_data.add_to_reference_set import AddToReferenceSetTool


class TestAddToReferenceSetMetadata:
    """Test AddToReferenceSetTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = AddToReferenceSetTool()
        assert tool.name == "add_to_reference_set"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = AddToReferenceSetTool()
        assert tool.description
        assert "add" in tool.description.lower()
        assert "ioc" in tool.description.lower()
        assert "reference" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = AddToReferenceSetTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test set_name and value are required in schema."""
        tool = AddToReferenceSetTool()
        schema = tool.input_schema

        assert "set_name" in schema["required"]
        assert "value" in schema["required"]
        assert "set_name" in schema["properties"]
        assert "value" in schema["properties"]

    def test_input_schema_optional_fields(self):
        """Test optional fields are in schema but not required."""
        tool = AddToReferenceSetTool()
        schema = tool.input_schema

        optional_fields = ["source", "notes", "fields"]

        for field in optional_fields:
            assert field not in schema["required"]
            assert field in schema["properties"]


class TestAddToReferenceSetExecution:
    """Test AddToReferenceSetTool execution."""

    def _setup_mock_client(self, tool, response_data, status_code):
        """Helper to setup mock client with GET and POST responses."""
        # Mock GET request for set lookup
        mock_get_response = httpx.Response(
            200,
            json=[{"id": 123, "name": "threat_ips"}],
            request=httpx.Request("GET", "http://test")
        )

        # Mock POST request for adding entry
        mock_post_response = httpx.Response(
            status_code,
            json=response_data,
            request=httpx.Request("POST", "http://test")
        )

        # Configure mock client
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_get_response)
        tool.client.post = AsyncMock(return_value=mock_post_response)

    @pytest.fixture
    def sample_entry_created(self):
        """Sample created entry data (201 response)."""
        return {
            "id": 456,
            "collection_id": 123,
            "value": "192.168.1.100",
            "first_seen": 1640000000000,
            "last_seen": 1640000000000,
            "source": "threat_feed",
            "notes": "Suspicious IP from investigation",
            "domain_id": 0
        }

    @pytest.fixture
    def sample_entry_updated(self):
        """Sample updated entry data (200 response)."""
        return {
            "id": 456,
            "collection_id": 123,
            "value": "192.168.1.100",
            "first_seen": 1639000000000,
            "last_seen": 1640000000000,
            "source": "manual_investigation",
            "notes": "Updated notes",
            "domain_id": 0
        }

    @pytest.mark.asyncio
    async def test_execute_minimal_request_created(self, sample_entry_created):
        """Test basic execution with only required fields (new entry)."""
        tool = AddToReferenceSetTool()
        self._setup_mock_client(tool, sample_entry_created, 201)

        # Execute
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        })

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "added successfully" in result["content"][0]["text"].lower()
        assert "192.168.1.100" in result["content"][0]["text"]

        # Verify API calls
        tool.client.get.assert_called_once()
        tool.client.post.assert_called_once()
        call_args = tool.client.post.call_args
        assert call_args[0][0] == 'reference_data_collections/set_entries'
        assert call_args[1]['data']['collection_id'] == 123
        assert call_args[1]['data']['value'] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_execute_entry_updated(self, sample_entry_updated):
        """Test execution when entry already exists (200 response)."""
        tool = AddToReferenceSetTool()
        self._setup_mock_client(tool, sample_entry_updated, 200)

        # Execute
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        })

        # Verify
        assert result["content"][0]["type"] == "text"
        assert "updated successfully" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_with_source(self, sample_entry_created):
        """Test execution with source parameter."""
        tool = AddToReferenceSetTool()
        self._setup_mock_client(tool, sample_entry_created, 201)

        # Execute
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "source": "threat_feed"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.post.call_args
        assert call_args[1]['data']['source'] == "threat_feed"

    @pytest.mark.asyncio
    async def test_execute_with_notes(self, sample_entry_created):
        """Test execution with notes parameter."""
        tool = AddToReferenceSetTool()
        self._setup_mock_client(tool, sample_entry_created, 201)

        # Execute
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "notes": "Suspicious activity detected"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.post.call_args
        assert call_args[1]['data']['notes'] == "Suspicious activity detected"

    @pytest.mark.asyncio
    async def test_execute_with_all_optional_params(self, sample_entry_created):
        """Test execution with all optional parameters."""
        tool = AddToReferenceSetTool()
        self._setup_mock_client(tool, sample_entry_created, 201)

        # Execute
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "source": "threat_feed",
            "notes": "High confidence IOC",
            "fields": "id,value,first_seen"
        })

        # Verify
        assert "isError" not in result
        call_args = tool.client.post.call_args
        assert call_args[1]['data']['source'] == "threat_feed"
        assert call_args[1]['data']['notes'] == "High confidence IOC"
        assert call_args[1]['headers']['fields'] == "id,value,first_seen"

    @pytest.mark.asyncio
    async def test_execute_with_fields_header(self, sample_entry_created):
        """Test that fields parameter is sent as header."""
        tool = AddToReferenceSetTool()
        self._setup_mock_client(tool, sample_entry_created, 201)

        # Execute
        await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "fields": "id,value"
        })

        # Verify headers
        call_args = tool.client.post.call_args
        assert 'headers' in call_args[1]
        assert call_args[1]['headers']['fields'] == "id,value"


class TestAddToReferenceSetValidation:
    """Test AddToReferenceSetTool input validation."""

    @pytest.mark.asyncio
    async def test_missing_set_name(self):
        """Test error when set_name is missing."""
        tool = AddToReferenceSetTool()
        result = await tool.execute({
            "value": "192.168.1.100"
        })

        assert result["isError"] is True
        assert "set_name is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_missing_value(self):
        """Test error when value is missing."""
        tool = AddToReferenceSetTool()
        result = await tool.execute({
            "set_name": "threat_ips"
        })

        assert result["isError"] is True
        assert "value is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_empty_set_name(self):
        """Test error when set_name is empty."""
        tool = AddToReferenceSetTool()
        result = await tool.execute({
            "set_name": "",
            "value": "192.168.1.100"
        })

        assert result["isError"] is True
        assert "set_name is required" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_empty_value(self):
        """Test error when value is empty."""
        tool = AddToReferenceSetTool()
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": ""
        })

        assert result["isError"] is True
        assert "value is required" in result["content"][0]["text"]


class TestAddToReferenceSetErrorHandling:
    """Test AddToReferenceSetTool error handling."""

    @pytest.mark.asyncio
    async def test_set_not_found(self):
        """Test handling when reference set is not found."""
        # Setup mock to return empty list
        mock_get_response = httpx.Response(
            200,
            json=[],  # Empty list - set not found
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = AddToReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_get_response)
        result = await tool.execute({
            "set_name": "nonexistent_set",
            "value": "192.168.1.100"
        })

        # Verify error response
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()
        assert "nonexistent_set" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test handling of HTTP errors."""
        # Mock GET request for set lookup
        mock_get_response = httpx.Response(
            200,
            json=[{"id": 123, "name": "threat_ips"}],
            request=httpx.Request("GET", "http://test")
        )

        # Mock POST to raise HTTPError
        mock_post_response = httpx.Response(
            500,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = AddToReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_get_response)
        tool.client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("500 Server Error", request=mock_post_response.request, response=mock_post_response)
        )
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        })

        # Verify error response
        assert result["isError"] is True
        assert "error" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        # Mock GET request for set lookup
        mock_get_response = httpx.Response(
            200,
            json=[{"id": 123, "name": "nonexistent_set"}],
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = AddToReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_get_response)
        tool.client.post = AsyncMock(side_effect=RuntimeError("Set not found"))
        result = await tool.execute({
            "set_name": "nonexistent_set",
            "value": "192.168.1.100"
        })

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: set not found" == result["content"][0]["text"].lower()
        assert "Set not found" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Mock GET request for set lookup
        mock_get_response = httpx.Response(
            200,
            json=[{"id": 123, "name": "threat_ips"}],
            request=httpx.Request("GET", "http://test")
        )

        # Execute
        tool = AddToReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_get_response)
        tool.client.post = AsyncMock(side_effect=ValueError("Invalid value format"))
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "invalid_ip"
        })

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed: invalid value format" == result["content"][0]["text"].lower()


class TestAddToReferenceSetBodyBuilding:
    """Test AddToReferenceSetTool body building."""

    def test_build_body_minimal(self):
        """Test building body with only required fields."""
        tool = AddToReferenceSetTool()
        body = tool._build_body({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        }, 123)

        assert body["collection_id"] == 123
        assert body["value"] == "192.168.1.100"
        assert "source" not in body
        assert "notes" not in body

    def test_build_body_with_source(self):
        """Test building body with source."""
        tool = AddToReferenceSetTool()
        body = tool._build_body({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "source": "threat_feed"
        }, 123)

        assert body["collection_id"] == 123
        assert body["value"] == "192.168.1.100"
        assert body["source"] == "threat_feed"

    def test_build_body_with_notes(self):
        """Test building body with notes."""
        tool = AddToReferenceSetTool()
        body = tool._build_body({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "notes": "Suspicious activity"
        }, 123)

        assert body["collection_id"] == 123
        assert body["value"] == "192.168.1.100"
        assert body["notes"] == "Suspicious activity"

    def test_build_body_with_all_optional(self):
        """Test building body with all optional fields."""
        tool = AddToReferenceSetTool()
        body = tool._build_body({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "source": "threat_feed",
            "notes": "High confidence IOC"
        }, 123)
        assert body["collection_id"] == 123
        assert body["value"] == "192.168.1.100"
        assert body["source"] == "threat_feed"
        assert body["notes"] == "High confidence IOC"


class TestAddToReferenceSetHeaderBuilding:
    """Test AddToReferenceSetTool header building."""

    def test_build_headers_no_fields(self):
        """Test building headers without fields parameter."""
        tool = AddToReferenceSetTool()
        headers = tool._build_headers({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        })

        assert headers == {}

    def test_build_headers_with_fields(self):
        """Test building headers with fields parameter."""
        tool = AddToReferenceSetTool()
        headers = tool._build_headers({
            "set_name": "threat_ips",
            "value": "192.168.1.100",
            "fields": "id,value,first_seen"
        })

        assert headers["fields"] == "id,value,first_seen"


class TestAddToReferenceSetResponseFormatting:
    """Test AddToReferenceSetTool response formatting."""

    @pytest.mark.asyncio
    async def test_response_includes_json(self):
        """Test that response includes JSON data."""
        # Mock GET request for set lookup
        mock_get_response = httpx.Response(
            200,
            json=[{"id": 123, "name": "threat_ips"}],
            request=httpx.Request("GET", "http://test")
        )

        # Mock POST request
        entry_data = {
            "id": 456,
            "value": "192.168.1.100",
            "collection_id": 123
        }
        mock_post_response = httpx.Response(
            201,
            json=entry_data,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = AddToReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_get_response)
        tool.client.post = AsyncMock(return_value=mock_post_response)
        result = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        })

        # Verify JSON is in response
        response_text = result["content"][0]["text"]
        assert "192.168.1.100" in response_text
        assert "456" in response_text

    @pytest.mark.asyncio
    async def test_response_distinguishes_create_vs_update(self):
        """Test that response message differs for create vs update."""
        # Mock GET request for set lookup
        mock_get_response = httpx.Response(
            200,
            json=[{"id": 123, "name": "threat_ips"}],
            request=httpx.Request("GET", "http://test")
        )

        tool = AddToReferenceSetTool()
        tool.client = AsyncMock()
        tool.client.get = AsyncMock(return_value=mock_get_response)

        # Test 201 (created)
        mock_post_response_created = httpx.Response(
            201,
            json={"id": 456, "value": "192.168.1.100"},
            request=httpx.Request("POST", "http://test")
        )
        tool.client.post = AsyncMock(return_value=mock_post_response_created)
        result_created = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        })
        assert "added successfully" in result_created["content"][0]["text"].lower()

        # Test 200 (updated)
        mock_post_response_updated = httpx.Response(
            200,
            json={"id": 456, "value": "192.168.1.100"},
            request=httpx.Request("POST", "http://test")
        )
        tool.client.post = AsyncMock(return_value=mock_post_response_updated)
        result_updated = await tool.execute({
            "set_name": "threat_ips",
            "value": "192.168.1.100"
        })
        assert "updated successfully" in result_updated["content"][0]["text"].lower()