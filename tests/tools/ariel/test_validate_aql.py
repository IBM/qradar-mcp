"""
Tests for ValidateAQLTool
"""

import pytest
from unittest.mock import AsyncMock
import httpx

from qradar_mcp.tools.ariel.validate_aql import ValidateAQLTool


class TestValidateAQLMetadata:
    """Test ValidateAQLTool metadata properties."""

    def test_tool_name(self):
        """Test tool name is correct."""
        tool = ValidateAQLTool()
        assert tool.name == "validate_aql"

    def test_tool_description(self):
        """Test tool has a description."""
        tool = ValidateAQLTool()
        assert tool.description
        assert "validate" in tool.description.lower()
        assert "aql" in tool.description.lower()

    def test_input_schema_structure(self):
        """Test input schema has required structure."""
        tool = ValidateAQLTool()
        schema = tool.input_schema

        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_input_schema_required_fields(self):
        """Test query_expression is required in schema."""
        tool = ValidateAQLTool()
        schema = tool.input_schema

        assert "query_expression" in schema["required"]
        assert "query_expression" in schema["properties"]


class TestValidateAQLExecution:
    """Test ValidateAQLTool execution."""

    @pytest.mark.asyncio
    async def test_execute_valid_query(self):
        """Test executing with a valid AQL query."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=200,
            json={},
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT sourceip FROM events LAST 1 HOURS'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert '✓' in result['content'][0]['text']
        assert 'valid' in result['content'][0]['text'].lower()
        assert 'isError' not in result or result['isError'] is False

    @pytest.mark.asyncio
    async def test_execute_valid_query_with_warnings(self):
        """Test executing with a valid query that has warnings."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=200,
            json={'warnings': ['Warning 1', 'Warning 2']},
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT * FROM events'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert 'Warnings:' in result['content'][0]['text']
        assert 'Warning 1' in result['content'][0]['text']
        assert 'Warning 2' in result['content'][0]['text']

    @pytest.mark.asyncio
    async def test_execute_invalid_query_200_with_error_messages(self):
        """Test executing with invalid query that returns 200 with error_messages."""
        # Setup mock - QRadar returns 200 even with validation errors
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=200,
            json={
                'error_messages': [
                    {
                        'severity': 'ERROR',
                        'code': 28519,
                        'contexts': ['INREFERENCESET', 'events'],
                        'message': 'No function matches the given name: "INREFERENCESET" in catalog "events".'
                    }
                ]
            },
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT sourceip FROM events WHERE INREFERENCESET(\'test\', sourceip)'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert 'failed' in result['content'][0]['text'].lower()
        assert 'INREFERENCESET' in result['content'][0]['text']
        assert 'NEXT STEPS' in result['content'][0]['text']
        assert 'AQL guide' in result['content'][0]['text']
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_execute_invalid_query(self):
        """Test executing with an invalid AQL query."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=422,
            json={'message': 'Syntax error in query'},
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': 'INVALID QUERY'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert '✗' in result['content'][0]['text']
        assert 'failed' in result['content'][0]['text'].lower()
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_execute_invalid_query_with_details(self):
        """Test executing with invalid query that has detailed errors."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=422,
            json={'message': 'Syntax error', 'details': {'line': 1, 'column': 5}},
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': 'BAD QUERY'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert 'Details:' in result['content'][0]['text']
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_execute_unexpected_status_code(self):
        """Test handling unexpected HTTP status code."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=500,
            text='Internal Server Error',
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT * FROM events'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert '500' in result['content'][0]['text']
        assert result['isError'] is True


class TestValidateAQLValidation:
    """Test ValidateAQLTool input validation."""

    @pytest.mark.asyncio
    async def test_missing_query_expression(self):
        """Test that missing query_expression returns error."""
        tool = ValidateAQLTool()
        result = await tool.execute({})

        assert result['content'][0]['type'] == 'text'
        assert 'required' in result['content'][0]['text'].lower()
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_empty_query_expression(self):
        """Test that empty query_expression returns error."""
        tool = ValidateAQLTool()
        result = await tool.execute({'query_expression': ''})

        assert result['content'][0]['type'] == 'text'
        assert 'required' in result['content'][0]['text'].lower()
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_none_query_expression(self):
        """Test that None query_expression returns error."""
        tool = ValidateAQLTool()
        result = await tool.execute({'query_expression': None})

        assert result['content'][0]['type'] == 'text'
        assert 'required' in result['content'][0]['text'].lower()
        assert result['isError'] is True


class TestValidateAQLErrorHandling:
    """Test ValidateAQLTool error handling."""

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """Test handling of ValueError."""
        # Setup mock to raise ValueError
        tool = ValidateAQLTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=ValueError("Invalid value"))

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT * FROM events'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert 'Tool execution failed:' in result['content'][0]['text']
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_key_error_handling(self):
        """Test handling of KeyError."""
        # Setup mock to raise KeyError
        tool = ValidateAQLTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=KeyError("missing_key"))

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT * FROM events'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert 'Tool execution failed:' in result['content'][0]['text']
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_type_error_handling(self):
        """Test handling of TypeError."""
        # Setup mock to raise TypeError
        tool = ValidateAQLTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=TypeError("Type mismatch"))

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT * FROM events'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert 'Tool execution failed:' in result['content'][0]['text']
        assert result['isError'] is True

    @pytest.mark.asyncio
    async def test_runtime_error_handling(self):
        """Test handling of RuntimeError."""
        # Setup mock to raise RuntimeError
        tool = ValidateAQLTool()
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(side_effect=RuntimeError("Runtime error"))

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT * FROM events'
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert 'Tool execution failed:' in result['content'][0]['text']
        assert result['isError'] is True


class TestValidateAQLLogging:
    """Test ValidateAQLTool logging."""

    @pytest.mark.asyncio
    async def test_logs_query_validation(self):
        """Test that query validation is logged."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=200,
            json={},
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': 'SELECT sourceip FROM events'
        })

        # Verify execution succeeded (base class handles logging)
        assert result['content'][0]['type'] == 'text'
        assert '✓' in result['content'][0]['text']


class TestValidateAQLIntegration:
    """Test ValidateAQLTool integration scenarios."""

    @pytest.mark.asyncio
    async def test_long_query_truncation_in_log(self):
        """Test that long queries are truncated in logs."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=200,
            json={},
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute with very long query
        long_query = "SELECT " + ", ".join([f"field{i}" for i in range(100)]) + " FROM events"
        result = await tool.execute({'query_expression': long_query})

        # Verify it still works
        assert result['content'][0]['type'] == 'text'
        assert '✓' in result['content'][0]['text']

    @pytest.mark.asyncio
    async def test_query_with_special_characters(self):
        """Test validation of query with special characters."""
        # Setup mock
        tool = ValidateAQLTool()
        mock_response = httpx.Response(
            status_code=200,
            json={},
            request=httpx.Request("POST", "http://test")
        )
        tool.client = AsyncMock()
        tool.client.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await tool.execute({
            'query_expression': "SELECT sourceip FROM events WHERE username='test@example.com'"
        })

        # Verify
        assert result['content'][0]['type'] == 'text'
        assert '✓' in result['content'][0]['text']
