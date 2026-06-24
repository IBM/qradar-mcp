"""
Tests for AQL Fields Resources
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from qradar_mcp.resources.aql_fields import AQLEventsFieldsResource, AQLFlowsFieldsResource


class TestAQLEventsFieldsResource:
    """Test AQLEventsFieldsResource class."""

    def test_uri_property(self):
        """Test that uri property returns correct value."""
        resource = AQLEventsFieldsResource()
        assert resource.uri == "qradar://aql/fields/events"

    def test_name_property(self):
        """Test that name property returns correct value."""
        resource = AQLEventsFieldsResource()
        assert resource.name == "AQL Events Fields"

    def test_description_property(self):
        """Test that description property returns correct value."""
        resource = AQLEventsFieldsResource()
        assert "events" in resource.description.lower()
        assert "ALWAYS read" in resource.description

    def test_mime_type_property(self):
        """Test that mime_type property returns correct value."""
        resource = AQLEventsFieldsResource()
        assert resource.mime_type == "application/json"

    @patch('qradar_mcp.resources.aql_fields.log_mcp')
    @patch('qradar_mcp.resources.aql_fields.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_success(self, mock_client_class, mock_log_mcp):
        """Test successful read of events fields."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'columns': [
                {
                    'name': 'sourceip',
                    'type': 'IP',
                    'description': 'Source IP address',
                    'argument_type': None
                },
                {
                    'name': 'destinationip',
                    'type': 'IP',
                    'description': 'Destination IP address',
                    'argument_type': None
                },
                {
                    'name': 'username',
                    'type': 'VARCHAR',
                    'description': 'Username',
                    'argument_type': 'STRING'
                }
            ]
        }

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLEventsFieldsResource()
        result = await resource.read()

        # Verify API call
        mock_client.get.assert_called_once_with('ariel/databases/events')
        mock_log_mcp.assert_called()

        # Verify result structure
        assert 'contents' in result
        assert len(result['contents']) == 1
        content = result['contents'][0]
        assert content['uri'] == "qradar://aql/fields/events"
        assert content['mimeType'] == "application/json"

        # Parse and verify JSON content
        text_data = json.loads(content['text'])
        assert text_data['table'] == 'events'
        assert text_data['field_count'] == 3
        assert len(text_data['fields']) == 3
        assert text_data['fields'][0]['name'] == 'sourceip'
        assert text_data['fields'][1]['name'] == 'destinationip'
        assert text_data['fields'][2]['name'] == 'username'
        assert 'usage' in text_data

    @patch('qradar_mcp.resources.aql_fields.log_mcp')
    @patch('qradar_mcp.resources.aql_fields.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_api_error(self, mock_client_class, mock_log_mcp):
        """Test read when API returns error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLEventsFieldsResource()

        with pytest.raises(RuntimeError) as exc_info:
            await resource.read()

        assert "Failed to fetch events fields" in str(exc_info.value)
        assert "500" in str(exc_info.value)

    @patch('qradar_mcp.resources.aql_fields.log_mcp')
    @patch('qradar_mcp.resources.aql_fields.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_no_columns(self, mock_client_class, mock_log_mcp):
        """Test read when response has no columns."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLEventsFieldsResource()
        result = await resource.read()

        # Should handle missing columns gracefully
        text_data = json.loads(result['contents'][0]['text'])
        assert text_data['field_count'] == 0
        assert text_data['fields'] == []

    @patch('qradar_mcp.resources.aql_fields.log_mcp')
    @patch('qradar_mcp.resources.aql_fields.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_exception_handling(self, mock_client_class, mock_log_mcp):
        """Test read handles exceptions properly."""
        mock_client = Mock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection error"))
        mock_client_class.return_value = mock_client

        resource = AQLEventsFieldsResource()

        with pytest.raises(Exception) as exc_info:
            await resource.read()

        assert "Connection error" in str(exc_info.value)
        mock_log_mcp.assert_called()


class TestAQLFlowsFieldsResource:
    """Test AQLFlowsFieldsResource class."""

    def test_uri_property(self):
        """Test that uri property returns correct value."""
        resource = AQLFlowsFieldsResource()
        assert resource.uri == "qradar://aql/fields/flows"

    def test_name_property(self):
        """Test that name property returns correct value."""
        resource = AQLFlowsFieldsResource()
        assert resource.name == "AQL Flows Fields"

    def test_description_property(self):
        """Test that description property returns correct value."""
        resource = AQLFlowsFieldsResource()
        assert "flows" in resource.description.lower()
        assert "ALWAYS read" in resource.description

    def test_mime_type_property(self):
        """Test that mime_type property returns correct value."""
        resource = AQLFlowsFieldsResource()
        assert resource.mime_type == "application/json"

    @patch('qradar_mcp.resources.aql_fields.log_mcp')
    @patch('qradar_mcp.resources.aql_fields.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_success(self, mock_client_class, mock_log_mcp):
        """Test successful read of flows fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'columns': [
                {
                    'name': 'sourceip',
                    'type': 'IP',
                    'description': 'Source IP',
                    'argument_type': None
                },
                {
                    'name': 'protocolid',
                    'type': 'INT',
                    'description': 'Protocol ID',
                    'argument_type': 'NUMERIC'
                }
            ]
        }

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFlowsFieldsResource()
        result = await resource.read()

        # Verify API call
        mock_client.get.assert_called_once_with('ariel/databases/flows')

        # Verify result structure
        assert 'contents' in result
        content = result['contents'][0]
        assert content['uri'] == "qradar://aql/fields/flows"

        # Parse and verify JSON content
        text_data = json.loads(content['text'])
        assert text_data['table'] == 'flows'
        assert text_data['field_count'] == 2
        assert len(text_data['fields']) == 2

    @patch('qradar_mcp.resources.aql_fields.log_mcp')
    @patch('qradar_mcp.resources.aql_fields.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_api_error(self, mock_client_class, mock_log_mcp):
        """Test read when API returns error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        mock_client = Mock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        resource = AQLFlowsFieldsResource()

        with pytest.raises(RuntimeError) as exc_info:
            await resource.read()

        assert "Failed to fetch flows fields" in str(exc_info.value)
        assert "404" in str(exc_info.value)

    @patch('qradar_mcp.resources.aql_fields.log_mcp')
    @patch('qradar_mcp.resources.aql_fields.QRadarRestClient')
    @pytest.mark.asyncio
    async def test_read_exception_handling(self, mock_client_class, mock_log_mcp):
        """Test read handles exceptions properly."""
        mock_client = Mock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        mock_client_class.return_value = mock_client

        resource = AQLFlowsFieldsResource()

        with pytest.raises(Exception) as exc_info:
            await resource.read()

        assert "Network error" in str(exc_info.value)
        mock_log_mcp.assert_called()
