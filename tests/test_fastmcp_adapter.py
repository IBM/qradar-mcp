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
Tests for FastMCP Adapter

Tests the adapter pattern that bridges MCPTool implementations with FastMCP.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from qradar_mcp.tools.fastmcp_adapter import (
    _json_schema_type_to_python,
    _create_pydantic_fields,
    register_mcp_tool_with_fastmcp
)
from qradar_mcp.tools.offense.get_offense import GetOffenseTool
from qradar_mcp.tools.ariel.validate_aql import ValidateAQLTool
from qradar_mcp.tools.system.get_system_info import GetSystemInfoTool


class TestJsonSchemaConversion:
    """Test JSON Schema to Python type conversion."""

    def test_string_type(self):
        """Test string type conversion."""
        assert _json_schema_type_to_python("string") == str

    def test_integer_type(self):
        """Test integer type conversion."""
        assert _json_schema_type_to_python("integer") == int

    def test_number_type(self):
        """Test number type conversion."""
        assert _json_schema_type_to_python("number") == float

    def test_boolean_type(self):
        """Test boolean type conversion."""
        assert _json_schema_type_to_python("boolean") == bool

    def test_array_type(self):
        """Test array type conversion."""
        assert _json_schema_type_to_python("array") == list

    def test_object_type(self):
        """Test object type conversion."""
        assert _json_schema_type_to_python("object") == dict

    def test_unknown_type_defaults_to_string(self):
        """Test unknown type defaults to string."""
        assert _json_schema_type_to_python("unknown") == str


class TestPydanticFieldCreation:
    """Test Pydantic field creation from JSON Schema."""

    def test_required_field(self):
        """Test required field creation."""
        schema = {
            "properties": {
                "offense_id": {
                    "type": "integer",
                    "description": "The offense ID"
                }
            },
            "required": ["offense_id"]
        }

        fields = _create_pydantic_fields(schema)
        assert "offense_id" in fields
        field_type, field_def = fields["offense_id"]
        assert field_type == int
        assert field_def.description == "The offense ID"

    def test_optional_field(self):
        """Test optional field creation."""
        schema = {
            "properties": {
                "fields": {
                    "type": "string",
                    "description": "Optional fields"
                }
            },
            "required": []
        }

        fields = _create_pydantic_fields(schema)
        assert "fields" in fields
        # Optional fields should have Optional type annotation
        assert "fields" in fields

    def test_field_with_constraints(self):
        """Test field with numeric constraints."""
        schema = {
            "properties": {
                "offense_id": {
                    "type": "integer",
                    "description": "The offense ID",
                    "minimum": 0,
                    "maximum": 999999
                }
            },
            "required": ["offense_id"]
        }

        fields = _create_pydantic_fields(schema)
        field_type, field_def = fields["offense_id"]
        # Pydantic FieldInfo stores constraints in metadata
        assert field_def.metadata is not None or field_def.ge == 0

    def test_field_with_string_constraints(self):
        """Test field with string length constraints."""
        schema = {
            "properties": {
                "query": {
                    "type": "string",
                    "description": "AQL query",
                    "minLength": 1,
                    "maxLength": 10000
                }
            },
            "required": ["query"]
        }

        fields = _create_pydantic_fields(schema)
        field_type, field_def = fields["query"]
        # Pydantic FieldInfo stores constraints in metadata
        assert field_def.metadata is not None or field_def.min_length == 1


class TestToolSchemaExtraction:
    """Test schema extraction from MCPTool instances."""

    def test_get_offense_tool_schema(self):
        """Test GetOffenseTool schema extraction."""
        tool = GetOffenseTool()

        assert tool.name == "get_offense"
        assert "offense" in tool.description.lower()

        schema = tool.input_schema
        assert "properties" in schema
        assert "offense_id" in schema["properties"]
        assert schema["properties"]["offense_id"]["type"] == "integer"
        assert "offense_id" in schema["required"]

    def test_validate_aql_tool_schema(self):
        """Test ValidateAQLTool schema extraction."""
        tool = ValidateAQLTool()

        assert tool.name == "validate_aql"
        assert "aql" in tool.description.lower()

        schema = tool.input_schema
        assert "properties" in schema
        assert "query_expression" in schema["properties"]
        assert schema["properties"]["query_expression"]["type"] == "string"
        assert "query_expression" in schema["required"]

    def test_get_system_info_tool_schema(self):
        """Test GetSystemInfoTool schema extraction."""
        tool = GetSystemInfoTool()

        assert tool.name == "get_system_info"
        assert "system" in tool.description.lower()

        schema = tool.input_schema
        assert "properties" in schema
        # This tool has optional parameters
        assert "fields" in schema["properties"]


class TestAdapterRegistration:
    """Test adapter registration with FastMCP."""

    @patch('qradar_mcp.tools.fastmcp_adapter.FastMCP')
    def test_register_tool_with_fastmcp(self, mock_fastmcp):
        """Test registering a tool with FastMCP."""
        # Create mock FastMCP instance
        mcp = Mock()
        mock_tool_decorator = Mock()
        mcp.tool.return_value = mock_tool_decorator

        # Create a tool instance
        tool = GetOffenseTool()

        # Register the tool
        register_mcp_tool_with_fastmcp(mcp, tool)

        # Verify tool decorator was called
        mcp.tool.assert_called_once()
        mock_tool_decorator.assert_called_once()

    def test_tool_wrapper_preserves_name(self):
        """Test that tool wrapper preserves the tool name."""
        tool = GetOffenseTool()

        # The wrapper function should have the same name as the tool
        assert tool.name == "get_offense"

    def test_tool_wrapper_preserves_description(self):
        """Test that tool wrapper preserves the tool description."""
        tool = GetOffenseTool()

        # The wrapper function should have the same description
        assert "offense" in tool.description.lower()
    @patch('qradar_mcp.tools.fastmcp_adapter.FastMCP')
    def test_get_tool_approval_required_false(self, mock_fastmcp):
        """Test that GET tools have approval_required=False in metadata."""
        # Create mock FastMCP instance
        mcp = Mock()
        mock_tool_decorator = Mock()
        mcp.tool.return_value = mock_tool_decorator

        # Create a GET tool instance
        tool = GetOffenseTool()
        
        # Verify the tool has approval_required=False
        assert tool.approval_required is False

        # Register the tool
        register_mcp_tool_with_fastmcp(mcp, tool)

        # Verify mcp.tool was called with meta containing approval_required=False
        mcp.tool.assert_called_once()
        call_args = mcp.tool.call_args
        assert call_args is not None
        assert 'meta' in call_args.kwargs
        assert call_args.kwargs['meta']['approval_required'] is False

    @patch('qradar_mcp.tools.fastmcp_adapter.FastMCP')
    def test_non_get_tool_approval_required_true(self, mock_fastmcp):
        """Test that non-GET tools have approval_required=True in metadata."""
        # Create mock FastMCP instance
        mcp = Mock()
        mock_tool_decorator = Mock()
        mcp.tool.return_value = mock_tool_decorator

        # Create a non-GET tool instance (ValidateAQLTool is POST)
        tool = ValidateAQLTool()
        
        # Verify the tool has approval_required=True (default)
        assert tool.approval_required is True

        # Register the tool
        register_mcp_tool_with_fastmcp(mcp, tool)

        # Verify mcp.tool was called with meta containing approval_required=True
        mcp.tool.assert_called_once()
        call_args = mcp.tool.call_args
        assert call_args is not None
        assert 'meta' in call_args.kwargs
        assert call_args.kwargs['meta']['approval_required'] is True

    def test_base_tool_approval_required_default(self):
        """Test that base MCPTool has approval_required=True by default."""
        # Non-GET tools should have the default value of True
        tool = ValidateAQLTool()
        assert tool.approval_required is True

    def test_get_tools_override_approval_required(self):
        """Test that GET tools override approval_required to False."""
        # GET tools should override to False
        get_tool = GetOffenseTool()
        assert get_tool.approval_required is False
        
        # Another GET tool
        system_tool = GetSystemInfoTool()
        assert system_tool.approval_required is False



class TestToolExecution:
    """Test tool execution through the adapter."""

    @pytest.mark.asyncio
    async def test_get_offense_execution(self):
        """Test GetOffenseTool execution."""
        # Mock the REST client
        mock_client = AsyncMock()
        mock_response = httpx.Response(200, json={"id": 123, "description": "Test offense"}, request=httpx.Request("GET", "http://test"))
        mock_client.get = AsyncMock(return_value=mock_response)

        # Create and execute tool with mocked client
        tool = GetOffenseTool()
        tool.client = mock_client
        result = await tool.execute({"offense_id": 123})

        # Verify result
        assert "content" in result
        assert len(result["content"]) > 0
        assert "text" in result["content"][0]
        assert "123" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_validate_aql_execution(self):
        """Test ValidateAQLTool execution."""
        # Mock the REST client
        mock_client = AsyncMock()
        mock_response = httpx.Response(200, json={"warnings": []}, request=httpx.Request("POST", "http://test"))
        mock_client.post = AsyncMock(return_value=mock_response)

        # Create and execute tool with mocked client
        tool = ValidateAQLTool()
        tool.client = mock_client
        result = await tool.execute({"query_expression": "SELECT * FROM events"})

        # Verify result
        assert "content" in result
        assert len(result["content"]) > 0
        assert "text" in result["content"][0]
        assert "valid" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test tool error handling."""
        tool = GetOffenseTool()

        # Execute with missing required parameter
        result = await tool.execute({})

        # Verify error response
        assert "content" in result
        assert result.get("isError") is True
        assert "offense_id" in result["content"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_adapter_returns_error_text_not_raises(self):
        """Adapter must return error text as string, not raise, when tool returns isError."""
        mock_client = AsyncMock()
        mock_response = httpx.Response(
            500,
            json={"message": "Endpoint invocation returned an unexpected error"},
            request=httpx.Request("GET", "http://test")
        )
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=mock_response.request,
                response=mock_response
            )
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        tool = GetOffenseTool()
        tool.client = mock_client

        # Tool.execute() returns isError response — adapter must NOT raise
        result = await tool.execute({"offense_id": 1})
        assert result.get("isError") is True
        error_text = result["content"][0]["text"]

        # Now verify the adapter's _execute_tool closure returns it as a string
        from qradar_mcp.tools.fastmcp_adapter import register_mcp_tool_with_fastmcp
        from unittest.mock import patch as _patch

        mcp = Mock()
        captured = {}

        def capture_tool(meta=None):
            def decorator(fn):
                captured["fn"] = fn
                return fn
            return decorator

        mcp.tool = capture_tool
        register_mcp_tool_with_fastmcp(mcp, tool)

        # Call the registered wrapper — should return the error string, not raise
        returned = await captured["fn"](offense_id=1)
        assert isinstance(returned, str)
        assert returned == error_text


class TestSchemaValidation:
    """Test schema validation for different parameter types."""

    def test_integer_parameter_validation(self):
        """Test integer parameter schema."""
        tool = GetOffenseTool()
        schema = tool.input_schema

        offense_id_schema = schema["properties"]["offense_id"]
        assert offense_id_schema["type"] == "integer"
        assert "minimum" in offense_id_schema
        assert offense_id_schema["minimum"] == 0

    def test_string_parameter_validation(self):
        """Test string parameter schema."""
        tool = ValidateAQLTool()
        schema = tool.input_schema

        query_schema = schema["properties"]["query_expression"]
        assert query_schema["type"] == "string"
        assert "description" in query_schema

    def test_optional_parameter_validation(self):
        """Test optional parameter schema."""
        tool = GetSystemInfoTool()
        schema = tool.input_schema

        # fields parameter is optional
        assert "fields" in schema["properties"]
        assert "fields" not in schema.get("required", [])


class TestRegisterAllTools:
    """Test register_all_tools function."""

    @pytest.fixture
    def all_enabled_config(self, tmp_path):
        """Create a config file with all toggles enabled."""
        from qradar_mcp.utils.feature_toggle_manager import FeatureToggleManager
        config_file = tmp_path / "feature_toggles.json"
        config_file.write_text("""{
            "verb_toggles": {
                "GET": true,
                "POST": true,
                "PUT": true,
                "DELETE": true
            },
            "group_toggles": {
                "offense": true,
                "ariel": true,
                "reference_data": true,
                "asset": true,
                "log_source": true,
                "analytics": true,
                "system": true,
                "config": true,
                "services": true,
                "forensics": true,
                "qvm": true,
                "data_classification": true
            },
            "per_tool_toggles": {}
        }""")
        return FeatureToggleManager(str(config_file))

    @pytest.fixture
    def some_disabled_config(self, tmp_path):
        """Create a config file with some tools disabled."""
        from qradar_mcp.utils.feature_toggle_manager import FeatureToggleManager
        config_file = tmp_path / "feature_toggles.json"
        config_file.write_text("""{
            "verb_toggles": {
                "GET": true,
                "POST": true,
                "PUT": true,
                "DELETE": false
            },
            "group_toggles": {
                "offense": true,
                "ariel": true,
                "reference_data": true,
                "asset": true,
                "log_source": true,
                "analytics": true,
                "system": true,
                "config": true,
                "services": true,
                "forensics": true,
                "qvm": false,
                "data_classification": true
            },
            "per_tool_toggles": {
                "GetOffenseTool": false
            }
        }""")
        return FeatureToggleManager(str(config_file))

    def test_all_tools_registered_when_all_enabled(self, all_enabled_config):
        """Test that all 84 tools are registered when all toggles are enabled."""
        from qradar_mcp.tools.fastmcp_adapter import register_all_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)
        mock_qradar_client = AsyncMock()

        registered_tools, skipped_tools = register_all_tools(mock_mcp, all_enabled_config, mock_qradar_client)

        # Should register all 83 toggle-managed tools
        assert len(registered_tools) == 83
        assert len(skipped_tools) == 0

    def test_returns_tuple(self, all_enabled_config):
        """Test that register_all_tools returns a tuple of (registered, skipped)."""
        from qradar_mcp.tools.fastmcp_adapter import register_all_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)
        mock_qradar_client = AsyncMock()

        result = register_all_tools(mock_mcp, all_enabled_config, mock_qradar_client)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], list)

    def test_some_tools_skipped_when_disabled(self, some_disabled_config):
        """Test that disabled tools are skipped during registration."""
        from qradar_mcp.tools.fastmcp_adapter import register_all_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)
        mock_qradar_client = AsyncMock()

        registered_tools, skipped_tools = register_all_tools(mock_mcp, some_disabled_config, mock_qradar_client)

        # Should have some registered and some skipped
        assert len(registered_tools) > 0
        assert len(skipped_tools) > 0
        assert len(registered_tools) + len(skipped_tools) == 83

    def test_delete_verb_disabled_skips_delete_tools(self, some_disabled_config):
        """Test that tools with DELETE verb are skipped when DELETE is disabled."""
        from qradar_mcp.tools.fastmcp_adapter import register_all_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)
        mock_qradar_client = AsyncMock()

        registered_tools, skipped_tools = register_all_tools(mock_mcp, some_disabled_config, mock_qradar_client)

        # Check that no registered tools have DELETE verb
        for tool in registered_tools:
            assert tool.http_verb != "DELETE"

        # Check that all DELETE tools are in skipped list
        delete_tools = [t for t in skipped_tools if t.http_verb == "DELETE"]
        assert len(delete_tools) > 0

    def test_qvm_group_disabled_skips_qvm_tools(self, some_disabled_config):
        """Test that QVM tools are skipped when qvm group is disabled."""
        from qradar_mcp.tools.fastmcp_adapter import register_all_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)
        mock_qradar_client = AsyncMock()

        registered_tools, skipped_tools = register_all_tools(mock_mcp, some_disabled_config, mock_qradar_client)

        # Check that no registered tools are from qvm group
        for tool in registered_tools:
            assert tool.tool_group != "qvm"

        # Check that all qvm tools are in skipped list
        qvm_tools = [t for t in skipped_tools if t.tool_group == "qvm"]
        assert len(qvm_tools) == 2  # There are 2 QVM tools

    def test_per_tool_override_skips_specific_tool(self, some_disabled_config):
        """Test that per-tool override disables specific tool."""
        from qradar_mcp.tools.fastmcp_adapter import register_all_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)
        mock_qradar_client = AsyncMock()

        registered_tools, skipped_tools = register_all_tools(mock_mcp, some_disabled_config, mock_qradar_client)

        # Check that get_offense is not registered
        registered_names = [t.name for t in registered_tools]
        assert "get_offense" not in registered_names

        # Check that get_offense is in skipped list
        skipped_names = [t.name for t in skipped_tools]
        assert "get_offense" in skipped_names

    def test_no_duplicate_tools(self, some_disabled_config):
        """Test that no tool appears in both registered and skipped lists."""
        from qradar_mcp.tools.fastmcp_adapter import register_all_tools

        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)
        mock_qradar_client = AsyncMock()

        registered_tools, skipped_tools = register_all_tools(mock_mcp, some_disabled_config, mock_qradar_client)

        registered_names = set(t.name for t in registered_tools)
        skipped_names = set(t.name for t in skipped_tools)

        # No overlap between registered and skipped
        assert len(registered_names & skipped_names) == 0

        # All 83 toggle-managed tools accounted for
        assert len(registered_names | skipped_names) == 83


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
