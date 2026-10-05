"""
Tests for QRadarRestClient HTTP methods (POST, PUT, DELETE)
"""

import pytest
from unittest.mock import patch, AsyncMock
import httpx
from qradar_mcp.client.qradar_rest_client import QRadarRestClient


class TestQRadarRestClientPOST:
    """Tests for POST method."""

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_post_with_dict_data(self, mock_load_config, mock_log):
        """Test POST request with dictionary data."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "verify_ssl": False
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(201, request=httpx.Request("POST", "http://test"))
        mock_client.post = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        data = {"key": "value", "number": 123}

        response = await client.post('test/endpoint', data=data)

        assert response.status_code == 201
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args[1]
        # httpx uses 'json' parameter for dict data
        assert call_kwargs.get('json') == data or call_kwargs.get('content')
        assert 'Content-Type' in call_kwargs['headers']
        assert call_kwargs['headers']['Content-Type'] == 'application/json'

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_post_with_string_data(self, mock_load_config, mock_log):
        """Test POST request with string data."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "verify_ssl": False
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("POST", "http://test"))
        mock_client.post = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        data = "raw string data"

        response = await client.post('test/endpoint', data=data)

        assert response.status_code == 200
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args[1]
        # httpx uses 'content' parameter for string data
        assert call_kwargs.get('content') == data or call_kwargs.get('data') == data

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_post_with_params(self, mock_load_config, mock_log):
        """Test POST request with query parameters."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("POST", "http://test"))
        mock_client.post = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        params = {"filter": "test", "limit": 10}

        response = await client.post('test/endpoint', params=params)

        assert response.status_code == 200
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs['params'] == params

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_post_with_custom_headers(self, mock_load_config, mock_log):
        """Test POST request with custom headers."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("POST", "http://test"))
        mock_client.post = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        custom_headers = {"Content-Type": "application/xml"}

        response = await client.post('test/endpoint', headers=custom_headers, data={"test": "data"})

        assert response.status_code == 200
        call_kwargs = mock_client.post.call_args[1]
        # Should not override existing Content-Type
        assert call_kwargs['headers']['Content-Type'] == 'application/xml'

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_post_with_proxy(self, mock_load_config, mock_log):
        """Test POST request with proxy configuration."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "proxy": "http://proxy.local:8080"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("POST", "http://test"))
        mock_client.post = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)

        response = await client.post('test/endpoint')

        assert response.status_code == 200
        # httpx handles proxies differently, just verify call was made
        assert mock_client.post.called


class TestQRadarRestClientPUT:
    """Tests for PUT method."""

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_put_with_dict_data(self, mock_load_config, mock_log):
        """Test PUT request with dictionary data uses json= parameter."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "verify_ssl": False
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("PUT", "http://test"))
        mock_client.put = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        data = {"id": 1, "name": "updated"}

        response = await client.put('test/endpoint', data=data)

        assert response.status_code == 200
        mock_client.put.assert_called_once()
        call_kwargs = mock_client.put.call_args[1]
        assert call_kwargs.get('json') == data

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_put_with_list_data(self, mock_load_config, mock_log):
        """Test PUT request with list data uses json= parameter."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "verify_ssl": False
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("PUT", "http://test"))
        mock_client.put = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        data = [{"id": 1, "name": "net-a"}, {"id": 2, "name": "net-b"}]

        response = await client.put('test/endpoint', data=data)

        assert response.status_code == 200
        call_kwargs = mock_client.put.call_args[1]
        assert call_kwargs.get('json') == data

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_put_with_string_data(self, mock_load_config, mock_log):
        """Test PUT request with string data uses content= parameter."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "verify_ssl": False
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("PUT", "http://test"))
        mock_client.put = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        data = "raw string data"

        response = await client.put('test/endpoint', data=data)

        assert response.status_code == 200
        call_kwargs = mock_client.put.call_args[1]
        assert call_kwargs.get('content') == data

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_put_with_version(self, mock_load_config, mock_log):
        """Test PUT request sets Version header."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("PUT", "http://test"))
        mock_client.put = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)

        response = await client.put('test/endpoint', data={}, version="15.0")

        assert response.status_code == 200
        call_kwargs = mock_client.put.call_args[1]
        assert call_kwargs['headers']['Version'] == "15.0"

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_put_logs_request(self, mock_load_config, mock_log):
        """Test PUT request logs a structured entry."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("PUT", "http://test"))
        mock_client.put = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        await client.put('config/network_hierarchy/staged_networks', data=[])

        mock_log.assert_called()
        log_args = mock_log.call_args
        assert log_args[1].get('method') == 'PUT'


class TestQRadarRestClientDELETE:
    """Tests for DELETE method."""

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_delete_basic(self, mock_load_config, mock_log):
        """Test basic DELETE request."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "verify_ssl": False
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(204, request=httpx.Request("DELETE", "http://test"))
        mock_client.delete = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)

        response = await client.delete('test/endpoint/123')

        assert response.status_code == 204
        mock_client.delete.assert_called_once()
        mock_log.assert_called()

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_delete_with_params(self, mock_load_config, mock_log):
        """Test DELETE request with query parameters."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("DELETE", "http://test"))
        mock_client.delete = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        params = {"force": "true"}

        response = await client.delete('test/endpoint/123', params=params)

        assert response.status_code == 200
        call_kwargs = mock_client.delete.call_args[1]
        assert call_kwargs['params'] == params

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_delete_with_version(self, mock_load_config, mock_log):
        """Test DELETE request with API version."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("DELETE", "http://test"))
        mock_client.delete = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)

        response = await client.delete('test/endpoint/123', version="15.0")

        assert response.status_code == 200
        call_kwargs = mock_client.delete.call_args[1]
        assert call_kwargs['headers']['Version'] == "15.0"

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.log_structured')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_delete_with_proxy(self, mock_load_config, mock_log):
        """Test DELETE request with proxy configuration."""
        mock_config = {
            "qradar": {
                "host": "https://qradar.local",
                "sec_token": "test_token",
                "proxy": "http://proxy.local:8080"
            }
        }
        mock_load_config.return_value = mock_config

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(204, request=httpx.Request("DELETE", "http://test"))
        mock_client.delete = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)

        response = await client.delete('test/endpoint/123')

        assert response.status_code == 204
        # httpx handles proxies differently, just verify call was made
        assert mock_client.delete.called
