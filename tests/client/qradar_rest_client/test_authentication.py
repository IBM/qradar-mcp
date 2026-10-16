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
Tests for QRadarRestClient authentication methods.

Tests authentication modes including context-based auth and local mode auth.
"""

import base64
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from qradar_mcp.client.qradar_rest_client import (
    QRadarRestClient,
    QRADAR_CSRF,
    SEC_HEADER,
    AUTHORIZATION_HEADER,
    build_basic_auth_header
)


class TestContextAuthMode:
    """Test _context_auth_mode method for request context authentication."""

    def test_context_auth_with_authorized_service_token(self):
        """Test context auth with authorized service token (service-to-service auth)."""
        client = QRadarRestClient()

        context_tokens = {
            'authorized_service_token': 'service_token_123'
        }

        result = client._context_auth_mode(context_tokens)

        # Should only include SEC header with service token
        assert SEC_HEADER in result
        assert result[SEC_HEADER] == 'service_token_123'
        assert QRADAR_CSRF not in result

    def test_context_auth_with_user_tokens(self):
        """Test context auth with user tokens (user authentication)."""
        client = QRadarRestClient()

        context_tokens = {
            'sec_token': 'user_sec_token_456',
            'csrf_token': 'user_csrf_token_789'
        }

        result = client._context_auth_mode(context_tokens)

        # Should include both SEC and CSRF headers
        assert SEC_HEADER in result
        assert result[SEC_HEADER] == 'user_sec_token_456'
        assert QRADAR_CSRF in result
        assert result[QRADAR_CSRF] == 'user_csrf_token_789'

    def test_context_auth_with_only_sec_token(self):
        """Test context auth with only SEC token."""
        client = QRadarRestClient()

        context_tokens = {
            'sec_token': 'sec_only_token'
        }

        result = client._context_auth_mode(context_tokens)

        # Should include SEC header only
        assert SEC_HEADER in result
        assert result[SEC_HEADER] == 'sec_only_token'
        assert QRADAR_CSRF not in result

    def test_context_auth_with_only_csrf_token(self):
        """Test context auth with only CSRF token."""
        client = QRadarRestClient()

        context_tokens = {
            'csrf_token': 'csrf_only_token'
        }

        result = client._context_auth_mode(context_tokens)

        # Should include CSRF header only
        assert QRADAR_CSRF in result
        assert result[QRADAR_CSRF] == 'csrf_only_token'
        assert SEC_HEADER not in result

    def test_context_auth_with_empty_tokens(self):
        """Test context auth with empty token dictionary."""
        client = QRadarRestClient()

        context_tokens = {}

        result = client._context_auth_mode(context_tokens)

        # Should return empty dict
        assert result == {}

    def test_context_auth_prioritizes_service_token(self):
        """Test that authorized_service_token takes priority over user tokens."""
        client = QRadarRestClient()

        context_tokens = {
            'authorized_service_token': 'service_token_priority',
            'sec_token': 'user_sec_token',
            'csrf_token': 'user_csrf_token'
        }

        result = client._context_auth_mode(context_tokens)

        # Should only use service token, ignoring user tokens
        assert SEC_HEADER in result
        assert result[SEC_HEADER] == 'service_token_priority'
        assert QRADAR_CSRF not in result
        assert len(result) == 1


class TestLocalModeAuth:
    """Test _local_mode_auth method for local development authentication."""

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_local_mode_with_authorized_service_token(self, mock_load_config):
        """Test local mode auth with authorized service token."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'https://test.qradar.com',
                'authorized_service_token': 'local_service_token',
                'sec_token': 'local_sec_token',
                'csrf_token': 'local_csrf_token'
            }
        }

        client = QRadarRestClient()
        result = client._local_mode_auth()

        # Should prioritize authorized_service_token
        assert SEC_HEADER in result
        assert result[SEC_HEADER] == 'local_service_token'
        assert QRADAR_CSRF not in result

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_local_mode_with_user_tokens(self, mock_load_config):
        """Test local mode auth with user tokens."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'https://test.qradar.com',
                'sec_token': 'local_sec_token',
                'csrf_token': 'local_csrf_token'
            }
        }

        client = QRadarRestClient()
        result = client._local_mode_auth()

        # Should include both SEC and CSRF headers
        assert SEC_HEADER in result
        assert result[SEC_HEADER] == 'local_sec_token'
        assert QRADAR_CSRF in result
        assert result[QRADAR_CSRF] == 'local_csrf_token'

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_local_mode_with_only_sec_token(self, mock_load_config):
        """Test local mode auth with only SEC token."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'https://test.qradar.com',
                'sec_token': 'local_sec_only'
            }
        }

        client = QRadarRestClient()
        result = client._local_mode_auth()

        # Should include SEC header only
        assert SEC_HEADER in result
        assert result[SEC_HEADER] == 'local_sec_only'
        assert QRADAR_CSRF not in result


class TestAddHeadersAuthentication:
    """Test _add_headers method authentication priority."""

    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_add_headers_prioritizes_context_tokens(self, mock_load_config, mock_get_tokens):
        """Test that context tokens take priority over config tokens."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'https://test.qradar.com',
                'sec_token': 'config_sec_token',
                'csrf_token': 'config_csrf_token'
            }
        }

        mock_get_tokens.return_value = {
            'sec_token': 'context_sec_token',
            'csrf_token': 'context_csrf_token'
        }

        client = QRadarRestClient()
        headers = client._add_headers({})

        # Should use context tokens, not config tokens
        assert headers[SEC_HEADER] == 'context_sec_token'
        assert headers[QRADAR_CSRF] == 'context_csrf_token'

    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_add_headers_uses_config_when_no_context(self, mock_load_config, mock_get_tokens):
        """Test that config tokens are used when no context tokens."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'https://test.qradar.com',
                'sec_token': 'config_sec_token',
                'csrf_token': 'config_csrf_token'
            }
        }

        mock_get_tokens.return_value = None

        client = QRadarRestClient()
        headers = client._add_headers({})

        # Should use config tokens
        assert headers[SEC_HEADER] == 'config_sec_token'
        assert headers[QRADAR_CSRF] == 'config_csrf_token'

    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_add_headers_with_version(self, mock_load_config, mock_get_tokens):
        """Test that version header is added when specified."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'https://test.qradar.com',
                'sec_token': 'test_token'
            }
        }

        mock_get_tokens.return_value = None

        client = QRadarRestClient()
        headers = client._add_headers({}, version='15.0')

        # Should include version header
        assert 'Version' in headers
        assert headers['Version'] == '15.0'

    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_add_headers_preserves_existing_headers(self, mock_load_config, mock_get_tokens):
        """Test that existing headers are preserved."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'https://test.qradar.com',
                'sec_token': 'test_token'
            }
        }

        mock_get_tokens.return_value = None

        client = QRadarRestClient()
        existing_headers = {'Custom-Header': 'custom_value'}
        headers = client._add_headers(existing_headers)

        # Should preserve existing headers
        assert 'Custom-Header' in headers
        assert headers['Custom-Header'] == 'custom_value'
        assert SEC_HEADER in headers


class TestAuthenticationIntegration:
    """Test authentication integration with HTTP methods."""

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_get_request_includes_auth_headers(self, mock_load_config, mock_get_tokens):
        """Test that GET requests include authentication headers."""
        mock_load_config.return_value = None
        mock_get_tokens.return_value = {
            'sec_token': 'test_sec_token',
            'csrf_token': 'test_csrf_token'
        }

        # Create mock httpx client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(200, request=httpx.Request("GET", "http://test"))
        mock_client.get = AsyncMock(return_value=mock_response)

        client = QRadarRestClient(client=mock_client)
        await client.get('siem/offenses')

        # Verify auth headers were included in the request
        call_args = mock_client.get.call_args
        headers = call_args.kwargs['headers']
        assert SEC_HEADER in headers
        assert headers[SEC_HEADER] == 'test_sec_token'
        assert QRADAR_CSRF in headers
        assert headers[QRADAR_CSRF] == 'test_csrf_token'


class TestBasicAuth:
    """Test HTTP Basic authentication (username/password)."""

    def test_build_basic_auth_header(self):
        """Test that credentials are base64 encoded per RFC 7617."""
        # base64("admin:s3cret") == "YWRtaW46czNjcmV0"
        assert build_basic_auth_header('admin', 's3cret') == 'Basic YWRtaW46czNjcmV0'

    def test_build_basic_auth_header_non_ascii(self):
        """Test that non-ASCII credentials are UTF-8 encoded before base64."""
        header = build_basic_auth_header('user', 'pässwörd')

        scheme, encoded = header.split(' ', 1)
        assert scheme == 'Basic'
        assert base64.b64decode(encoded).decode('utf-8') == 'user:pässwörd'

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_local_mode_with_basic_credentials(self, mock_load_config):
        """Test local mode auth falls back to Basic when no tokens are configured."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'test.qradar.com',
                'username': 'admin',
                'password': 's3cret'
            }
        }

        client = QRadarRestClient()
        result = client._local_mode_auth()

        assert result == {AUTHORIZATION_HEADER: 'Basic YWRtaW46czNjcmV0'}
        assert SEC_HEADER not in result
        assert QRADAR_CSRF not in result

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_local_mode_sec_token_takes_priority_over_basic(self, mock_load_config):
        """Test that a configured SEC token wins over Basic credentials."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'test.qradar.com',
                'sec_token': 'sec_token_wins',
                'username': 'admin',
                'password': 's3cret'
            }
        }

        client = QRadarRestClient()
        result = client._local_mode_auth()

        assert result == {SEC_HEADER: 'sec_token_wins'}
        assert AUTHORIZATION_HEADER not in result

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_local_mode_service_token_takes_priority_over_basic(self, mock_load_config):
        """Test that an authorized service token wins over Basic credentials."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'test.qradar.com',
                'authorized_service_token': 'service_token_wins',
                'username': 'admin',
                'password': 's3cret'
            }
        }

        client = QRadarRestClient()
        result = client._local_mode_auth()

        assert result == {SEC_HEADER: 'service_token_wins'}
        assert AUTHORIZATION_HEADER not in result

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_local_mode_partial_basic_credentials_ignored(self, mock_load_config):
        """Test that a username without a password produces no auth header."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'test.qradar.com',
                'username': 'admin'
            }
        }

        client = QRadarRestClient()

        assert client._local_mode_auth() == {}

    def test_context_auth_with_authorization_header(self):
        """Test context auth forwards a Basic header supplied per request."""
        client = QRadarRestClient()

        result = client._context_auth_mode({'authorization': 'Basic YWRtaW46czNjcmV0'})

        assert result == {AUTHORIZATION_HEADER: 'Basic YWRtaW46czNjcmV0'}

    def test_context_auth_sec_token_takes_priority_over_authorization(self):
        """Test that SEC/CSRF tokens win over a forwarded Basic header."""
        client = QRadarRestClient()

        result = client._context_auth_mode({
            'sec_token': 'sec_token_wins',
            'authorization': 'Basic YWRtaW46czNjcmV0'
        })

        assert result == {SEC_HEADER: 'sec_token_wins'}
        assert AUTHORIZATION_HEADER not in result

    @pytest.mark.asyncio
    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    async def test_get_request_includes_basic_auth_header(self, mock_load_config, mock_get_tokens):
        """Test that GET requests carry the Basic header from config.json."""
        mock_load_config.return_value = {
            'qradar': {
                'host': 'test.qradar.com',
                'username': 'admin',
                'password': 's3cret'
            }
        }
        mock_get_tokens.return_value = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(
            return_value=httpx.Response(200, request=httpx.Request("GET", "http://test"))
        )

        client = QRadarRestClient(client=mock_client)
        await client.get('ariel/searches')

        call_args = mock_client.get.call_args
        assert call_args.kwargs['headers'][AUTHORIZATION_HEADER] == 'Basic YWRtaW46czNjcmV0'
        assert call_args.kwargs['url'] == 'https://test.qradar.com/api/ariel/searches'


class TestEnvironmentCredentials:
    """Test credentials supplied via environment variables (app / stdio mode)."""

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_app_mode_reads_all_credentials_from_env(self, mock_load_config):
        """Test that the documented QRADAR_* env vars populate the client."""
        mock_load_config.return_value = None

        env = {
            'QRADAR_CONSOLE_FQDN': 'https://test.qradar.com',
            'QRADAR_AUTH_TOKEN': 'env_service_token',
            'QRADAR_SEC_TOKEN': 'env_sec_token',
            'QRADAR_CSRF_TOKEN': 'env_csrf_token',
            'QRADAR_USERNAME': 'admin',
            'QRADAR_PASSWORD': 's3cret'
        }
        with patch.dict('os.environ', env, clear=False):
            client = QRadarRestClient()

        assert client._authorized_service_token == 'env_service_token'
        assert client._sec_token == 'env_sec_token'
        assert client._csrf_token == 'env_csrf_token'
        assert client._username == 'admin'
        assert client._password == 's3cret'
        assert client._local_mode is False

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_app_mode_without_env_has_no_ambient_credentials(self, mock_load_config):
        """Test that an unconfigured multi user deployment stays credential-less."""
        mock_load_config.return_value = None

        env = {k: '' for k in (
            'QRADAR_AUTH_TOKEN', 'QRADAR_SEC_TOKEN', 'QRADAR_CSRF_TOKEN',
            'QRADAR_USERNAME', 'QRADAR_PASSWORD'
        )}
        with patch.dict('os.environ', env, clear=False):
            client = QRadarRestClient()

        assert client._has_ambient_credentials() is False

    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_app_mode_no_credentials_adds_no_auth_headers(
        self, mock_load_config, mock_get_tokens
    ):
        """Test unchanged behaviour: no env creds and no headers means no auth."""
        mock_load_config.return_value = None
        mock_get_tokens.return_value = None

        env = {k: '' for k in (
            'QRADAR_AUTH_TOKEN', 'QRADAR_SEC_TOKEN', 'QRADAR_CSRF_TOKEN',
            'QRADAR_USERNAME', 'QRADAR_PASSWORD'
        )}
        with patch.dict('os.environ', env, clear=False):
            client = QRadarRestClient()
            headers = client._add_headers(None)

        assert SEC_HEADER not in headers
        assert QRADAR_CSRF not in headers
        assert AUTHORIZATION_HEADER not in headers

    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_app_mode_env_basic_credentials_are_used(
        self, mock_load_config, mock_get_tokens
    ):
        """Test that env username/password produce a Basic header in app mode."""
        mock_load_config.return_value = None
        mock_get_tokens.return_value = None

        env = {
            'QRADAR_AUTH_TOKEN': '', 'QRADAR_SEC_TOKEN': '', 'QRADAR_CSRF_TOKEN': '',
            'QRADAR_USERNAME': 'admin', 'QRADAR_PASSWORD': 's3cret'
        }
        with patch.dict('os.environ', env, clear=False):
            client = QRadarRestClient()
            headers = client._add_headers(None)

        assert headers[AUTHORIZATION_HEADER] == 'Basic YWRtaW46czNjcmV0'

    @patch('qradar_mcp.client.qradar_rest_client.get_request_auth_tokens')
    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_request_headers_take_precedence_over_env_credentials(
        self, mock_load_config, mock_get_tokens
    ):
        """Test that per-request credentials still win over ambient env ones."""
        mock_load_config.return_value = None
        mock_get_tokens.return_value = {'sec_token': 'per_request_token'}

        env = {'QRADAR_USERNAME': 'admin', 'QRADAR_PASSWORD': 's3cret'}
        with patch.dict('os.environ', env, clear=False):
            client = QRadarRestClient()
            headers = client._add_headers(None)

        assert headers[SEC_HEADER] == 'per_request_token'
        assert AUTHORIZATION_HEADER not in headers

    @patch('qradar_mcp.client.qradar_rest_client.load_config')
    def test_has_ambient_credentials_requires_both_basic_parts(self, mock_load_config):
        """Test that a username with no password is not treated as a credential."""
        mock_load_config.return_value = None

        env = {
            'QRADAR_AUTH_TOKEN': '', 'QRADAR_SEC_TOKEN': '', 'QRADAR_CSRF_TOKEN': '',
            'QRADAR_USERNAME': 'admin', 'QRADAR_PASSWORD': ''
        }
        with patch.dict('os.environ', env, clear=False):
            client = QRadarRestClient()

        assert client._has_ambient_credentials() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
