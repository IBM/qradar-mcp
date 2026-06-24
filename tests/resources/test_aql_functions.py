"""
Tests for AQL Functions Resource
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from qradar_mcp.resources.aql_functions import AQLFunctionsResource


class TestAQLFunctionsResource:
    """Test AQLFunctionsResource class."""

    def test_uri_property(self):
        """Test that uri property returns correct value."""
        resource = AQLFunctionsResource()
        assert resource.uri == "qradar://aql/functions"

    def test_name_property(self):
        """Test that name property returns correct value."""
        resource = AQLFunctionsResource()
        assert resource.name == "AQL Functions"

    def test_description_property(self):
        """Test that description property returns correct value."""
        resource = AQLFunctionsResource()
        assert "functions" in resource.description.lower()
        assert "aggregation" in resource.description.lower()

    def test_mime_type_property(self):
        """Test that mime_type property returns correct value."""
        resource = AQLFunctionsResource()
        assert resource.mime_type == "application/json"

    @patch('qradar_mcp.resources.aql_functions.log_mcp')
    @patch('qradar_mcp.resources.aql_functions.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_success_with_categorization(self, mock_client_class, mock_log_mcp):
        """Test successful read with function categorization."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'LOGSOURCENAME',
                'description': 'Get log source name',
                'return_data_type': 'VARCHAR',
                'argument_types': ['INT'],
                'database_type': 'COMMON'
            },
            {
                'name': 'COUNT',
                'description': 'Count rows',
                'return_data_type': 'BIGINT',
                'argument_types': [],
                'database_type': 'EVENTS'
            },
            {
                'name': 'SUM',
                'description': 'Sum values',
                'return_data_type': 'BIGINT',
                'argument_types': ['NUMERIC'],
                'database_type': 'EVENTS'
            },
            {
                'name': 'CUSTOM_FUNC',
                'description': 'Custom function',
                'return_data_type': 'VARCHAR',
                'argument_types': [],
                'database_type': 'EVENTS'
            }
        ]

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFunctionsResource()
        result = await resource.read()

        # Verify API call
        mock_client.get.assert_called_once_with('ariel/functions')
        mock_log_mcp.assert_called()

        # Verify result structure
        assert 'contents' in result
        assert len(result['contents']) == 1
        content = result['contents'][0]
        assert content['uri'] == "qradar://aql/functions"
        assert content['mimeType'] == "application/json"

        # Parse and verify JSON content
        text_data = json.loads(content['text'])
        assert text_data['total_functions'] == 4
        assert 'categories' in text_data

        # Verify categorization
        categories = text_data['categories']
        assert 'data_retrieval' in categories
        assert 'aggregation' in categories
        assert 'other' in categories

        # Data retrieval should have LOGSOURCENAME (database_type=COMMON)
        assert categories['data_retrieval']['count'] == 1
        assert categories['data_retrieval']['functions'][0]['name'] == 'LOGSOURCENAME'

        # Aggregation should have COUNT and SUM
        assert categories['aggregation']['count'] == 2
        agg_names = [f['name'] for f in categories['aggregation']['functions']]
        assert 'COUNT' in agg_names
        assert 'SUM' in agg_names

        # Other should have CUSTOM_FUNC
        assert categories['other']['count'] == 1
        assert categories['other']['functions'][0]['name'] == 'CUSTOM_FUNC'

        assert 'usage' in text_data

    @patch('qradar_mcp.resources.aql_functions.log_mcp')
    @patch('qradar_mcp.resources.aql_functions.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_all_aggregation_functions(self, mock_client_class, mock_log_mcp):
        """Test that all standard aggregation functions are categorized correctly."""
        aggregation_funcs = ['AVG', 'MAX', 'MIN', 'SUM', 'COUNT', 'DISTINCTCOUNT',
                            'UNIQUECOUNT', 'FIRST', 'LAST']

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': func,
                'description': f'{func} function',
                'return_data_type': 'NUMERIC',
                'argument_types': [],
                'database_type': 'EVENTS'
            }
            for func in aggregation_funcs
        ]

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFunctionsResource()
        result = await resource.read()

        text_data = json.loads(result['contents'][0]['text'])

        # All should be in aggregation category
        assert text_data['categories']['aggregation']['count'] == len(aggregation_funcs)
        agg_names = [f['name'] for f in text_data['categories']['aggregation']['functions']]
        for func in aggregation_funcs:
            assert func in agg_names

    @patch('qradar_mcp.resources.aql_functions.log_mcp')
    @patch('qradar_mcp.resources.aql_functions.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_empty_response(self, mock_client_class, mock_log_mcp):
        """Test read when API returns empty list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFunctionsResource()
        result = await resource.read()

        text_data = json.loads(result['contents'][0]['text'])
        assert text_data['total_functions'] == 0
        assert text_data['categories']['data_retrieval']['count'] == 0
        assert text_data['categories']['aggregation']['count'] == 0
        assert text_data['categories']['other']['count'] == 0

    @patch('qradar_mcp.resources.aql_functions.log_mcp')
    @patch('qradar_mcp.resources.aql_functions.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_api_error(self, mock_client_class, mock_log_mcp):
        """Test read when API returns error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFunctionsResource()

        with pytest.raises(RuntimeError) as exc_info:
            await resource.read()

        assert "Failed to fetch AQL functions" in str(exc_info.value)
        assert "500" in str(exc_info.value)

    @patch('qradar_mcp.resources.aql_functions.log_mcp')
    @patch('qradar_mcp.resources.aql_functions.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_unauthorized(self, mock_client_class, mock_log_mcp):
        """Test read when API returns unauthorized."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFunctionsResource()

        with pytest.raises(RuntimeError) as exc_info:
            await resource.read()

        assert "Failed to fetch AQL functions" in str(exc_info.value)
        assert "401" in str(exc_info.value)

    @patch('qradar_mcp.resources.aql_functions.log_mcp')
    @patch('qradar_mcp.resources.aql_functions.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_exception_handling(self, mock_client_class, mock_log_mcp):
        """Test read handles exceptions properly."""
        mock_client = Mock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection timeout"))
        mock_client_class.return_value = mock_client

        resource = AQLFunctionsResource()

        with pytest.raises(Exception) as exc_info:
            await resource.read()

        assert "Connection timeout" in str(exc_info.value)
        mock_log_mcp.assert_called()

    @patch('qradar_mcp.resources.aql_functions.log_mcp')
    @patch('qradar_mcp.resources.aql_functions.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_mixed_case_aggregation_functions(self, mock_client_class, mock_log_mcp):
        """Test that aggregation functions are matched case-insensitively."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'count',  # lowercase
                'description': 'Count function',
                'return_data_type': 'BIGINT',
                'argument_types': [],
                'database_type': 'EVENTS'
            },
            {
                'name': 'Sum',  # mixed case
                'description': 'Sum function',
                'return_data_type': 'BIGINT',
                'argument_types': [],
                'database_type': 'EVENTS'
            }
        ]

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFunctionsResource()
        result = await resource.read()

        text_data = json.loads(result['contents'][0]['text'])

        # Should still be categorized as aggregation (uppercase comparison)
        assert text_data['categories']['aggregation']['count'] == 2
