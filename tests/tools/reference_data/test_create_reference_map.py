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
Tests for CreateReferenceMap
"""

import json
import pytest
import httpx
from unittest.mock import AsyncMock
from qradar_mcp.tools.reference_data.create_reference_map import CreateReferenceMap


class TestCreateReferenceMapMetadata:
    """Test CreateReferenceMap metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = CreateReferenceMap()
        assert tool.name == "create_reference_map"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = CreateReferenceMap()
        assert tool.description
        assert "create" in tool.description.lower()
        assert "map" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = CreateReferenceMap()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test name and element_type are required in schema."""
        tool = CreateReferenceMap()
        schema = tool.input_schema

        assert "name" in schema["required"]
        assert "element_type" in schema["required"]
        assert "name" in schema["properties"]
        assert "element_type" in schema["properties"]

    def test_input_schema_element_type_enum(self):
        """Test element_type has valid enum values."""
        tool = CreateReferenceMap()
        schema = tool.input_schema

        element_type_prop = schema["properties"]["element_type"]
        assert "enum" in element_type_prop
        expected_types = ["IP", "ALN", "ALNIC", "NUM", "PORT", "DATE", "CIDR"]
        assert set(element_type_prop["enum"]) == set(expected_types)

    def test_input_schema_optional_fields(self):
        """Test optional fields are in schema but not required."""
        tool = CreateReferenceMap()
        schema = tool.input_schema

        optional_fields = [
            "key_label", "value_label", "description",
            "timeout_type", "time_to_live", "fields"
        ]

        for field in optional_fields:
            assert field not in schema["required"]
            assert field in schema["properties"]


class TestCreateReferenceMapExecution:
    """Test CreateReferenceMap execution."""

    @pytest.fixture
    def sample_created_map(self):
        """Sample created reference map data."""
        return {
            "name": "ip_country_map",
            "element_type": "ALN",
            "key_label": "IP Address",
            "value_label": "Country",
            "number_of_elements": 0,
            "creation_time": 1640000000000,
            "timeout_type": "UNKNOWN"
        }

    @pytest.mark.asyncio
    async def test_execute_minimal_request(self, sample_created_map):
        """Test basic execution with only required fields."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_created_map,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceMap()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "name": "ip_country_map",
            "element_type": "ALN"
        })

        # Verify
        assert "isError" not in result
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        # Verify API call
        tool.client.post.assert_called_once()
        call_args = tool.client.post.call_args
        assert call_args[0][0] == 'reference_data/maps'

    @pytest.mark.asyncio
    async def test_execute_with_all_optional_fields(self, sample_created_map):
        """Test execution with all optional fields."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_created_map,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceMap()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "name": "ip_country_map",
            "element_type": "ALN",
            "key_label": "IP Address",
            "value_label": "Country",
            "description": "IP to country mappings",
            "timeout_type": "FIRST_SEEN",
            "time_to_live": 3600
        })

        # Verify
        assert "isError" not in result

        # Verify params include all fields
        params = tool.client.post.call_args[1]["params"]
        assert params["key_label"] == "IP Address"
        assert params["value_label"] == "Country"
        assert params["description"] == "IP to country mappings"
        assert params["timeout_type"] == "FIRST_SEEN"
        assert params["time_to_live"] == 3600

    @pytest.mark.asyncio
    async def test_execute_response_format(self, sample_created_map):
        """Test response is properly formatted as JSON."""
        # Setup mock
        mock_response = httpx.Response(
            200,
            json=sample_created_map,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceMap()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)
        result = await tool.execute({
            "name": "ip_country_map",
            "element_type": "ALN"
        })

        # Verify JSON formatting
        content_text = result["content"][0]["text"]
        parsed_data = json.loads(content_text)
        assert parsed_data["name"] == "ip_country_map"
        assert parsed_data["element_type"] == "ALN"

    @pytest.mark.asyncio
    async def test_execute_missing_name(self):
        """Test execution fails when name is missing."""
        tool = CreateReferenceMap()
        result = await tool.execute({"element_type": "ALN"})

        assert result["isError"] is True
        assert "name" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_missing_element_type(self):
        """Test execution fails when element_type is missing."""
        tool = CreateReferenceMap()
        result = await tool.execute({"name": "test_map"})

        assert result["isError"] is True
        assert "element_type" in result["content"][0]["text"].lower()


class TestCreateReferenceMapErrorHandling:
    """Test CreateReferenceMap error handling."""

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test handling of API errors."""
        # Execute
        tool = CreateReferenceMap()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=RuntimeError("API connection failed"))
        result = await tool.execute({
            "name": "test_map",
            "element_type": "ALN"
        })

        # Verify error response
        assert result["isError"] is True
        assert "tool execution failed:" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_execute_value_error(self):
        """Test handling of ValueError."""
        # Execute
        tool = CreateReferenceMap()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=ValueError("Invalid parameter format"))
        result = await tool.execute({
            "name": "test_map",
            "element_type": "ALN"
        })

        # Verify error response
        assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        # Setup mock to raise HTTPError
        mock_response = httpx.Response(
            500,
            request=httpx.Request("POST", "http://test")
        )

        # Execute
        tool = CreateReferenceMap()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError("500 Server Error", request=mock_response.request, response=mock_response)
        )
        result = await tool.execute({
            "name": "test_map",
            "element_type": "ALN"
        })

        # Verify error response
        assert result["isError"] is True
        assert "Error executing create_reference_map: 500 Server Error" in result["content"][0]["text"]


class TestCreateReferenceMapIntegration:
    """Integration tests for CreateReferenceMap."""

    @pytest.mark.asyncio
    async def test_create_different_element_types(self):
        """Test creating maps with different element types."""
        element_types = ["IP", "ALN", "ALNIC", "NUM", "PORT", "DATE", "CIDR"]

        for element_type in element_types:
            # Setup mock
            mock_response = httpx.Response(
                200,
                json={
                    "name": f"test_{element_type.lower()}",
                    "element_type": element_type,
                    "number_of_elements": 0
                },
                request=httpx.Request("POST", "http://test")
            )

            # Execute
            tool = CreateReferenceMap()
            tool.client = AsyncMock()
            tool.client.post = AsyncMock(return_value=mock_response)
            result = await tool.execute({
                "name": f"test_{element_type.lower()}",
                "element_type": element_type
            })

            # Verify
            assert "isError" not in result
            content_text = result["content"][0]["text"]
            parsed_data = json.loads(content_text)
            assert parsed_data["element_type"] == element_type
