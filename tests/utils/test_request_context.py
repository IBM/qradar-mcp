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
Unit tests for request context management.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import Headers, QueryParams

from utils.request_context import (
    RequestContextMiddleware,
    get_request_method,
    get_request_path,
    get_request_url,
    get_request_remote_addr,
    get_request_user_agent,
    get_request_referer,
    get_request_content_type,
    get_request_query_params,
    get_request_headers,
    get_request_context,
    set_request_context,
    clear_request_context
)


@pytest.fixture
def mock_request():
    """Create a mock Starlette request."""
    request = Mock(spec=Request)
    request.method = "POST"
    request.url = Mock()
    request.url.path = "/api/v1/offenses"
    request.url.__str__ = Mock(return_value="https://example.com/api/v1/offenses?filter=status='OPEN'")
    request.client = Mock()
    request.client.host = "192.168.1.100"
    request.headers = Headers({
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'referer': 'https://example.com/dashboard',
        'content-type': 'application/json',
        'authorization': 'Bearer token123',
        'x-custom-header': 'custom-value'
    })
    request.query_params = QueryParams("filter=status='OPEN'")
    return request


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function."""
    async def call_next(request):
        return Response(content="OK", status_code=200)
    return call_next


class TestRequestContextGetters:
    """Test context variable getter functions."""
    
    def test_get_request_method_default(self):
        """Test getting request method when not set."""
        clear_request_context()
        assert get_request_method() is None
    
    def test_get_request_path_default(self):
        """Test getting request path when not set."""
        clear_request_context()
        assert get_request_path() is None
    
    def test_get_request_url_default(self):
        """Test getting request URL when not set."""
        clear_request_context()
        assert get_request_url() is None
    
    def test_get_request_remote_addr_default(self):
        """Test getting remote address when not set."""
        clear_request_context()
        assert get_request_remote_addr() is None
    
    def test_get_request_user_agent_default(self):
        """Test getting user agent when not set."""
        clear_request_context()
        assert get_request_user_agent() is None
    
    def test_get_request_referer_default(self):
        """Test getting referer when not set."""
        clear_request_context()
        assert get_request_referer() is None
    
    def test_get_request_content_type_default(self):
        """Test getting content type when not set."""
        clear_request_context()
        assert get_request_content_type() is None
    
    def test_get_request_query_params_default(self):
        """Test getting query params when not set."""
        clear_request_context()
        assert get_request_query_params() is None
    
    def test_get_request_headers_default(self):
        """Test getting headers when not set."""
        clear_request_context()
        assert get_request_headers() is None
    
    def test_get_request_context_default(self):
        """Test getting full context when not set."""
        clear_request_context()
        context = get_request_context()
        assert context == {
            'method': None,
            'path': None,
            'url': None,
            'remote_addr': None,
            'user_agent': None,
            'referer': None,
            'content_type': None,
            'query_params': None,
            'headers': None
        }


class TestRequestContextSetters:
    """Test context variable setter functions."""
    
    def test_set_request_context_all_fields(self):
        """Test setting all request context fields."""
        clear_request_context()
        
        query_params = {'filter': "status='OPEN'"}
        headers = {'user-agent': 'test-agent', 'content-type': 'application/json'}
        
        set_request_context(
            method='POST',
            path='/api/v1/offenses',
            url='https://example.com/api/v1/offenses',
            remote_addr='192.168.1.100',
            user_agent='test-agent',
            referer='https://example.com/dashboard',
            content_type='application/json',
            query_params=query_params,
            headers=headers
        )
        
        assert get_request_method() == 'POST'
        assert get_request_path() == '/api/v1/offenses'
        assert get_request_url() == 'https://example.com/api/v1/offenses'
        assert get_request_remote_addr() == '192.168.1.100'
        assert get_request_user_agent() == 'test-agent'
        assert get_request_referer() == 'https://example.com/dashboard'
        assert get_request_content_type() == 'application/json'
        assert get_request_query_params() == query_params
        assert get_request_headers() == headers
    
    def test_set_request_context_partial_fields(self):
        """Test setting only some request context fields."""
        clear_request_context()
        
        set_request_context(
            method='GET',
            path='/api/v1/rules'
        )
        
        assert get_request_method() == 'GET'
        assert get_request_path() == '/api/v1/rules'
        assert get_request_url() is None
        assert get_request_remote_addr() is None
    
    def test_clear_request_context(self):
        """Test clearing all request context fields."""
        set_request_context(
            method='POST',
            path='/api/v1/offenses',
            remote_addr='192.168.1.100'
        )
        
        clear_request_context()
        
        assert get_request_method() is None
        assert get_request_path() is None
        assert get_request_remote_addr() is None
    
    def test_get_request_context_after_set(self):
        """Test getting full context after setting values."""
        clear_request_context()
        
        query_params = {'limit': '50'}
        headers = {'authorization': 'Bearer token'}
        
        set_request_context(
            method='GET',
            path='/api/v1/assets',
            url='https://example.com/api/v1/assets?limit=50',
            remote_addr='10.0.0.1',
            user_agent='curl/7.68.0',
            query_params=query_params,
            headers=headers
        )
        
        context = get_request_context()
        assert context['method'] == 'GET'
        assert context['path'] == '/api/v1/assets'
        assert context['url'] == 'https://example.com/api/v1/assets?limit=50'
        assert context['remote_addr'] == '10.0.0.1'
        assert context['user_agent'] == 'curl/7.68.0'
        assert context['referer'] is None
        assert context['content_type'] is None
        assert context['query_params'] == query_params
        assert context['headers'] == headers


class TestRequestContextMiddleware:
    """Test RequestContextMiddleware."""
    
    @pytest.mark.asyncio
    async def test_middleware_extracts_request_info(self, mock_request, mock_call_next):
        """Test middleware extracts and sets request information."""
        clear_request_context()
        
        middleware = RequestContextMiddleware(app=None)
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify response
        assert response.status_code == 200
        
        # Context should be cleared after request
        assert get_request_method() is None
        assert get_request_path() is None
    
    @pytest.mark.asyncio
    async def test_middleware_sets_context_during_request(self, mock_request):
        """Test middleware sets context that's accessible during request processing."""
        clear_request_context()
        
        # Track what context was available during call_next
        captured_context = {}
        
        async def call_next_with_capture(request):
            captured_context.update(get_request_context())
            return Response(content="OK", status_code=200)
        
        middleware = RequestContextMiddleware(app=None)
        await middleware.dispatch(mock_request, call_next_with_capture)
        
        # Verify context was set during request
        assert captured_context['method'] == 'POST'
        assert captured_context['path'] == '/api/v1/offenses'
        assert captured_context['url'] == "https://example.com/api/v1/offenses?filter=status='OPEN'"
        assert captured_context['remote_addr'] == '192.168.1.100'
        assert captured_context['user_agent'] == 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        assert captured_context['referer'] == 'https://example.com/dashboard'
        assert captured_context['content_type'] == 'application/json'
        assert captured_context['query_params'] == {"filter": "status='OPEN'"}
        assert 'authorization' in captured_context['headers']
        assert 'x-custom-header' in captured_context['headers']
    
    @pytest.mark.asyncio
    async def test_middleware_clears_context_after_request(self, mock_request, mock_call_next):
        """Test middleware clears context after request completes."""
        clear_request_context()
        
        middleware = RequestContextMiddleware(app=None)
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Context should be cleared
        context = get_request_context()
        assert all(value is None for value in context.values())
    
    @pytest.mark.asyncio
    async def test_middleware_clears_context_on_exception(self, mock_request):
        """Test middleware clears context even if handler raises exception."""
        clear_request_context()
        
        async def call_next_with_error(request):
            raise ValueError("Test error")
        
        middleware = RequestContextMiddleware(app=None)
        
        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, call_next_with_error)
        
        # Context should still be cleared
        context = get_request_context()
        assert all(value is None for value in context.values())
    
    @pytest.mark.asyncio
    async def test_middleware_handles_missing_client(self, mock_call_next):
        """Test middleware handles request without client information."""
        clear_request_context()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/v1/rules"
        request.url.__str__ = Mock(return_value="https://example.com/api/v1/rules")
        request.client = None  # No client info
        request.headers = Headers({})
        request.query_params = QueryParams("")
        
        captured_context = {}
        
        async def call_next_with_capture(req):
            captured_context.update(get_request_context())
            return Response(content="OK", status_code=200)
        
        middleware = RequestContextMiddleware(app=None)
        await middleware.dispatch(request, call_next_with_capture)
        
        # Verify remote_addr is None when client is missing
        assert captured_context['remote_addr'] is None
        assert captured_context['method'] == 'GET'
        assert captured_context['path'] == '/api/v1/rules'
    
    @pytest.mark.asyncio
    async def test_middleware_handles_empty_headers(self, mock_call_next):
        """Test middleware handles request with no headers."""
        clear_request_context()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/v1/assets"
        request.url.__str__ = Mock(return_value="https://example.com/api/v1/assets")
        request.client = Mock()
        request.client.host = "10.0.0.1"
        request.headers = Headers({})
        request.query_params = QueryParams("")
        
        captured_context = {}
        
        async def call_next_with_capture(req):
            captured_context.update(get_request_context())
            return Response(content="OK", status_code=200)
        
        middleware = RequestContextMiddleware(app=None)
        await middleware.dispatch(request, call_next_with_capture)
        
        # Verify optional headers are None when not present
        assert captured_context['user_agent'] is None
        assert captured_context['referer'] is None
        assert captured_context['content_type'] is None
        assert captured_context['headers'] == {}
    
    @pytest.mark.asyncio
    async def test_middleware_handles_empty_query_params(self, mock_call_next):
        """Test middleware handles request with no query parameters."""
        clear_request_context()
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/v1/offenses"
        request.url.__str__ = Mock(return_value="https://example.com/api/v1/offenses")
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = Headers({'content-type': 'application/json'})
        request.query_params = QueryParams("")
        
        captured_context = {}
        
        async def call_next_with_capture(req):
            captured_context.update(get_request_context())
            return Response(content="OK", status_code=200)
        
        middleware = RequestContextMiddleware(app=None)
        await middleware.dispatch(request, call_next_with_capture)
        
        # Verify query_params is empty dict when no params
        assert captured_context['query_params'] == {}
