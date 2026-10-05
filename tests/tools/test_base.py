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
Unit tests for the base MCPTool class.
"""

import pytest
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.utils.feature_toggle_manager import set_feature_toggle_manager
from qradar_mcp.utils.validators import validate_path_segment


@pytest.fixture(autouse=True)
def reset_feature_toggles():
    """Reset feature toggle manager before each test to ensure test isolation."""
    # Clear the global feature toggle manager before each test
    set_feature_toggle_manager(None)
    yield
    # Clean up after test
    set_feature_toggle_manager(None)


class ConcreteTool(MCPTool):
    """Concrete implementation of MCPTool for testing."""

    @property
    def name(self) -> str:
        return "test_tool"

    @property
    def description(self) -> str:
        return "A test tool for unit testing"

    @property
    def input_schema(self):
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                }
            },
            "required": ["param1"]
        }
    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return "test/tool"

    async def _execute_impl(self, arguments):
        param1 = arguments.get("param1")
        if not param1:
            return self.create_error_response("param1 is required")
        return self.create_success_response(f"Executed with param1: {param1}")


class TestMCPTool:
    """Tests for MCPTool base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that MCPTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MCPTool()  # type: ignore

    def test_concrete_tool_has_name(self):
        """Test that concrete tool has a name property."""
        tool = ConcreteTool()
        assert tool.name == "test_tool"

    def test_concrete_tool_has_description(self):
        """Test that concrete tool has a description property."""
        tool = ConcreteTool()
        assert tool.description == "A test tool for unit testing"

    def test_concrete_tool_has_input_schema(self):
        """Test that concrete tool has an input_schema property."""
        tool = ConcreteTool()
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "param1" in schema["properties"]

    def test_to_mcp_tool_definition(self):
        """Test converting tool to MCP tool definition format."""
        tool = ConcreteTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "test_tool"
        assert definition["description"] == "A test tool for unit testing"
        assert "inputSchema" in definition
        assert definition["inputSchema"]["type"] == "object"

    def test_create_success_response(self):
        """Test creating a success response."""
        tool = ConcreteTool()
        response = tool.create_success_response("Operation successful")

        assert "content" in response
        assert len(response["content"]) == 1
        assert response["content"][0]["type"] == "text"
        assert response["content"][0]["text"] == "Operation successful"
        assert "isError" not in response

    def test_create_error_response(self):
        """Test creating an error response."""
        tool = ConcreteTool()
        response = tool.create_error_response("Something went wrong")

        assert "content" in response
        assert len(response["content"]) == 1
        assert response["content"][0]["type"] == "text"
        assert response["content"][0]["text"] == "Something went wrong"
        assert response["isError"] is True

    @pytest.mark.asyncio
    async def test_execute_with_valid_arguments(self):
        """Test executing tool with valid arguments."""
        tool = ConcreteTool()
        result = await tool.execute({"param1": "test_value"})

        assert "content" in result
        assert result["content"][0]["text"] == "Executed with param1: test_value"
        assert "isError" not in result

    @pytest.mark.asyncio
    async def test_execute_with_missing_arguments(self):
        """Test executing tool with missing required arguments."""
        tool = ConcreteTool()
        result = await tool.execute({})

        assert "content" in result
        assert result["content"][0]["text"] == "param1 is required"
        assert result["isError"] is True


class MinimalTool(MCPTool):
    """Minimal tool implementation for testing."""

    @property
    def name(self) -> str:
        return "minimal"

    @property
    def description(self) -> str:
        return "Minimal tool"

    @property
    def input_schema(self):
        return {"type": "object", "properties": {}}

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return "test/endpoint"

    async def _execute_impl(self, arguments):
        return self.create_success_response("Done")


class TestMCPToolEdgeCases:
    """Test edge cases for MCPTool."""

    def test_minimal_tool_definition(self):
        """Test tool with minimal implementation."""
        tool = MinimalTool()
        definition = tool.to_mcp_tool_definition()

        assert definition["name"] == "minimal"
        assert definition["description"] == "Minimal tool"
        assert definition["inputSchema"]["type"] == "object"

    def test_empty_success_response(self):
        """Test creating success response with empty string."""
        tool = MinimalTool()
        response = tool.create_success_response("")

        assert response["content"][0]["text"] == ""
        assert "isError" not in response

    def test_empty_error_response(self):
        """Test creating error response with empty string."""
        tool = MinimalTool()
        response = tool.create_error_response("")

        assert response["content"][0]["text"] == ""
        assert response["isError"] is True

    def test_multiline_response_text(self):
        """Test response with multiline text."""
        tool = MinimalTool()
        multiline_text = "Line 1\nLine 2\nLine 3"
        response = tool.create_success_response(multiline_text)

        assert response["content"][0]["text"] == multiline_text

    def test_response_with_special_characters(self):
        """Test response with special characters."""
        tool = MinimalTool()
        special_text = "Test with special chars: <>&\"'\n\t"
        response = tool.create_success_response(special_text)

        assert response["content"][0]["text"] == special_text


class PathParamTool(MCPTool):
    """Tool with a path parameter for testing path traversal validation."""

    @property
    def name(self) -> str:
        return "path_param_tool"

    @property
    def description(self) -> str:
        return "Tool with a path parameter"

    @property
    def input_schema(self):
        return {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return "reference_data/maps/{name}"

    async def _execute_impl(self, arguments):
        return self.create_success_response("ok")


class MultiPathParamTool(MCPTool):
    """Tool with multiple path parameters for testing."""

    @property
    def name(self) -> str:
        return "multi_path_param_tool"

    @property
    def description(self) -> str:
        return "Tool with multiple path parameters"

    @property
    def input_schema(self):
        return {"type": "object", "properties": {}}

    @property
    def http_verb(self) -> str:
        return "DELETE"

    @property
    def endpoint(self) -> str:
        return "reference_data/tables/{name}/{outer_key}/{inner_key}"

    async def _execute_impl(self, arguments):
        return self.create_success_response("ok")


class TestValidatePathSegment:
    """Tests for validate_path_segment."""

    def test_clean_name_passes(self):
        assert validate_path_segment("my_reference_map", "name") == "my_reference_map"

    def test_clean_name_with_hyphens_passes(self):
        assert validate_path_segment("my-map-01", "name") == "my-map-01"

    def test_forward_slash_rejected(self):
        with pytest.raises(ValueError, match="name"):
            validate_path_segment("../../config/access/users", "name")

    def test_double_dot_rejected(self):
        with pytest.raises(ValueError, match="name"):
            validate_path_segment("..maps", "name")

    def test_backslash_rejected(self):
        with pytest.raises(ValueError, match="key"):
            validate_path_segment("foo\\bar", "key")

    def test_embedded_slash_rejected(self):
        with pytest.raises(ValueError, match="outer_key"):
            validate_path_segment("valid/but/not", "outer_key")


class TestSanitizeArguments:
    """Tests for MCPTool._sanitize_arguments path-traversal checks."""

    def test_clean_name_passes_through(self):
        tool = PathParamTool()
        args = {"name": "my_map"}
        assert tool._sanitize_arguments(args) == args

    def test_traversal_in_name_raises(self):
        tool = PathParamTool()
        with pytest.raises(ValueError, match="name"):
            tool._sanitize_arguments({"name": "../../config/access/users"})

    def test_traversal_in_name_via_execute_returns_error_response(self):
        """ValueError from _sanitize_arguments is caught by execute_with_enhancements."""
        import asyncio
        tool = PathParamTool()
        result = asyncio.run(
            tool.execute({"name": "../../config/access/users"})
        )
        assert result["isError"] is True
        assert "path traversal" in result["content"][0]["text"]

    def test_non_path_param_not_validated(self):
        """Arguments that are not endpoint placeholders are not checked."""
        tool = PathParamTool()
        # 'filter' is not a placeholder in the endpoint, so slashes are fine
        args = {"name": "good_name", "filter": "field=value/something"}
        assert tool._sanitize_arguments(args) == args

    def test_multiple_path_params_all_checked(self):
        tool = MultiPathParamTool()
        with pytest.raises(ValueError, match="outer_key"):
            tool._sanitize_arguments({"name": "valid", "outer_key": "../escape", "inner_key": "fine"})

    def test_integer_path_param_not_checked(self):
        """Integer values for path params are skipped (only str is validated)."""
        tool = PathParamTool()
        # If a tool passes an int (e.g. after int() coercion), it must not raise
        args = {"name": 42}
        assert tool._sanitize_arguments(args) == args

    def test_endpoint_without_placeholders_unaffected(self):
        tool = MinimalTool()  # endpoint = "test/endpoint"
        args = {"some_field": "../../anything"}
        assert tool._sanitize_arguments(args) == args
