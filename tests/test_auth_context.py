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
Tests for authentication context management.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from qradar_mcp.auth_context import (
    get_request_auth_tokens,
    set_request_auth_tokens,
    AuthTokenMiddleware
)


class TestAuthContextVariables:
    """Test context variable get/set operations"""
    
    def test_get_auth_tokens_default_none(self):
        """Test that get_request_auth_tokens returns None by default"""
        # Context should be clean at start of test
        result = get_request_auth_tokens()
        assert result is None
    
    def test_set_and_get_auth_tokens(self):
        """Test setting and getting auth tokens"""
        test_tokens = {
            'sec_token': 'test_sec_123',
            'csrf_token': 'test_csrf_456'
        }
        
        set_request_auth_tokens(test_tokens)
        result = get_request_auth_tokens()
        
        assert result == test_tokens
        assert result['sec_token'] == 'test_sec_123'
        assert result['csrf_token'] == 'test_csrf_456'
        
        # Clean up
        set_request_auth_tokens(None)
    
    def test_set_auth_tokens_to_none(self):
        """Test clearing auth tokens by setting to None"""
        test_tokens = {'sec_token': 'test_123'}
        
        set_request_auth_tokens(test_tokens)
        assert get_request_auth_tokens() is not None
        
        set_request_auth_tokens(None)
        assert get_request_auth_tokens() is None
    
    def test_auth_tokens_isolation(self):
        """Test that auth tokens are isolated per context"""
        tokens1 = {'sec_token': 'token1'}
        tokens2 = {'sec_token': 'token2'}
        
        set_request_auth_tokens(tokens1)
        assert get_request_auth_tokens() == tokens1
        
        set_request_auth_tokens(tokens2)
        assert get_request_auth_tokens() == tokens2
        
        # Clean up
        set_request_auth_tokens(None)


class TestAuthTokenMiddleware:
    """Test AuthTokenMiddleware functionality"""
    
    @pytest.mark.asyncio
    async def test_middleware_extracts_sec_token(self):
        """Test middleware extracts SEC token from headers"""
        middleware = AuthTokenMiddleware(app=Mock())
        
        # Mock request with SEC header
        request = Mock()
        request.headers = {'SEC': 'test_sec_token_123'}
        request.state = Mock()
        
        # Mock call_next
        async def mock_call_next(req):
            # Verify tokens were set in context
            tokens = get_request_auth_tokens()
            assert tokens is not None
            assert tokens['sec_token'] == 'test_sec_token_123'
            return Mock()
        
        await middleware.dispatch(request, mock_call_next)
        
        # Verify tokens were stored in request state
        assert request.state.auth_tokens is not None
        assert request.state.auth_tokens['sec_token'] == 'test_sec_token_123'
    
    @pytest.mark.asyncio
    async def test_middleware_extracts_csrf_token(self):
        """Test middleware extracts QRadarCSRF token from headers"""
        middleware = AuthTokenMiddleware(app=Mock())
        
        request = Mock()
        request.headers = {'QRadarCSRF': 'test_csrf_token_456'}
        request.state = Mock()
        
        async def mock_call_next(req):
            tokens = get_request_auth_tokens()
            assert tokens is not None
            assert tokens['csrf_token'] == 'test_csrf_token_456'
            return Mock()
        
        await middleware.dispatch(request, mock_call_next)
        
        assert request.state.auth_tokens['csrf_token'] == 'test_csrf_token_456'
    
    @pytest.mark.asyncio
    async def test_middleware_extracts_all_tokens(self):
        """Test middleware extracts all token types simultaneously"""
        middleware = AuthTokenMiddleware(app=Mock())
        
        request = Mock()
        request.headers = {
            'SEC': 'sec_123',
            'QRadarCSRF': 'csrf_456',
        }
        request.state = Mock()
        
        async def mock_call_next(req):
            tokens = get_request_auth_tokens()
            assert tokens is not None
            assert len(tokens) == 2
            assert tokens['sec_token'] == 'sec_123'
            assert tokens['csrf_token'] == 'csrf_456'
            return Mock()
        
        await middleware.dispatch(request, mock_call_next)
    
    @pytest.mark.asyncio
    async def test_middleware_handles_no_tokens(self):
        """Test middleware handles requests with no auth tokens"""
        middleware = AuthTokenMiddleware(app=Mock())
        
        request = Mock()
        request.headers = {}
        request.state = Mock()
        
        async def mock_call_next(req):
            tokens = get_request_auth_tokens()
            assert tokens is None
            return Mock()
        
        await middleware.dispatch(request, mock_call_next)
        
        assert request.state.auth_tokens is None
    
    @pytest.mark.asyncio
    async def test_middleware_cleans_up_context(self):
        """Test middleware cleans up context after request"""
        middleware = AuthTokenMiddleware(app=Mock())
        
        request = Mock()
        request.headers = {'SEC': 'test_token'}
        request.state = Mock()
        
        async def mock_call_next(req):
            # Tokens should be available during request
            assert get_request_auth_tokens() is not None
            return Mock()
        
        await middleware.dispatch(request, mock_call_next)
        
        # Tokens should be cleaned up after request
        assert get_request_auth_tokens() is None
    
    @pytest.mark.asyncio
    async def test_middleware_cleans_up_on_exception(self):
        """Test middleware cleans up context even if handler raises exception"""
        middleware = AuthTokenMiddleware(app=Mock())
        
        request = Mock()
        request.headers = {'SEC': 'test_token'}
        request.state = Mock()
        
        async def mock_call_next(req):
            raise ValueError("Test exception")
        
        with pytest.raises(ValueError):
            await middleware.dispatch(request, mock_call_next)
        
        # Tokens should still be cleaned up
        assert get_request_auth_tokens() is None


class TestAuthContextIntegration:
    """Integration tests for auth context with tools"""
    
    def test_auth_tokens_available_to_tools(self):
        """Test that tools can access auth tokens from context"""
        test_tokens = {
            'sec_token': 'integration_test_token',
            'csrf_token': 'integration_csrf_token'
        }
        
        # Simulate middleware setting tokens
        set_request_auth_tokens(test_tokens)
        
        # Simulate tool accessing tokens
        tokens = get_request_auth_tokens()
        
        assert tokens is not None
        assert tokens['sec_token'] == 'integration_test_token'
        assert tokens['csrf_token'] == 'integration_csrf_token'
        
        # Clean up
        set_request_auth_tokens(None)
    
    def test_multiple_sequential_requests(self):
        """Test handling multiple sequential requests with different tokens"""
        # First request
        tokens1 = {'sec_token': 'request1_token'}
        set_request_auth_tokens(tokens1)
        assert get_request_auth_tokens() == tokens1
        set_request_auth_tokens(None)
        
        # Second request
        tokens2 = {'sec_token': 'request2_token'}
        set_request_auth_tokens(tokens2)
        assert get_request_auth_tokens() == tokens2
        set_request_auth_tokens(None)
        
        # Third request with no tokens
        set_request_auth_tokens(None)
        assert get_request_auth_tokens() is None
