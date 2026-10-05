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
Pytest configuration and fixtures for the test suite.
Provides fixtures for FastMCP-based tests.
"""

import atexit
import os
import pytest
from unittest.mock import Mock

# Set up environment variables before any imports
os.environ.setdefault('QRADAR_CONSOLE_FQDN', 'test.qradar.com')
os.environ.setdefault('QRADAR_APP_ID', 'test_app_id')
os.environ.setdefault('QRADAR_CONSOLE_IP', '127.0.0.1')
os.environ.setdefault('SEC_ADMIN_TOKEN', 'test_token')


@pytest.fixture(autouse=True)
def mock_qpylib(monkeypatch):
    """
    Auto-mock qpylib module for all tests.
    This fixture automatically patches qpylib imports to avoid initialization errors.
    """
    mock = Mock()
    mock.log = Mock()
    mock.get_app_id = Mock(return_value='test_app_id')
    mock.create_log = Mock()
    mock.q_url_for = Mock(return_value='/test/url')
    mock.get_console_fqdn = Mock(return_value='test.qradar.com')
    mock.get_console_address = Mock(return_value='127.0.0.1')

    # Patch qpylib in common locations
    monkeypatch.setattr('qpylib.qpylib.log', mock.log)
    monkeypatch.setattr('qpylib.qpylib.get_app_id', mock.get_app_id)
    monkeypatch.setattr('qpylib.qpylib.create_log', mock.create_log)
    monkeypatch.setattr('qpylib.qpylib.q_url_for', mock.q_url_for)
    monkeypatch.setattr('qpylib.qpylib.get_console_fqdn', mock.get_console_fqdn)
    monkeypatch.setattr('qpylib.qpylib.get_console_address', mock.get_console_address)

    return mock


@pytest.fixture(autouse=True, scope="session")
def suppress_atexit_logging():
    """
    Unregister the httpx client atexit handler before pytest teardown.

    The handler calls log_structured after the client closes. When pytest
    shuts down its worker processes sys.stderr is already closed, so the
    logging framework raises 'I/O operation on closed file' and prints
    '--- Logging error ---' noise to the terminal. Removing the handler
    here means the httpx client is simply not closed during test teardown
    (it has no real connection to close in tests anyway).
    """
    yield
    try:
        from qradar_mcp.server import cleanup_httpx_client
        atexit.unregister(cleanup_httpx_client)
    except Exception:  # pylint: disable=broad-exception-caught
        pass

@pytest.fixture
def mock_requests():
    """Mock requests module for testing."""
    mock = Mock()
    mock.get = Mock()
    mock.post = Mock()
    mock.put = Mock()
    mock.delete = Mock()
    return mock


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.json = Mock(return_value={})
    response.text = ""
    response.raise_for_status = Mock()
    return response


# FastMCP Fixtures

@pytest.fixture
def mcp_server():
    """
    Fixture for FastMCP server instance.
    Returns the FastMCP server from server.py.
    """
    from qradar_mcp.server import mcp
    return mcp


@pytest.fixture
def mock_qradar_client(monkeypatch):
    """
    Mock QRadar REST client for testing.
    This fixture mocks the QRadarRestClient to avoid actual API calls.
    """
    from qradar_mcp.client.qradar_rest_client import QRadarRestClient
    
    mock_client = Mock(spec=QRadarRestClient)
    mock_client.get = Mock()
    mock_client.post = Mock()
    mock_client.delete = Mock()
    mock_client.identify_user = Mock(return_value=(1, "test_user"))
    mock_client.identify_authorized_service = Mock(return_value=(None, None))
    
    # Mock the constructor to return our mock client
    def mock_init(self, auth_tokens=None):
        return mock_client
    
    monkeypatch.setattr(QRadarRestClient, '__init__', lambda self, auth_tokens=None: None)
    monkeypatch.setattr(QRadarRestClient, 'get', mock_client.get)
    monkeypatch.setattr(QRadarRestClient, 'post', mock_client.post)
    monkeypatch.setattr(QRadarRestClient, 'delete', mock_client.delete)
    
    return mock_client


@pytest.fixture
def sample_tool_response():
    """
    Sample tool response in MCP format.
    Useful for testing tool execution.
    """
    return {
        "content": [
            {
                "type": "text",
                "text": "Sample tool response"
            }
        ]
    }


@pytest.fixture
def sample_error_response():
    """
    Sample error response in MCP format.
    Useful for testing error handling.
    """
    return {
        "isError": True,
        "content": [
            {
                "type": "text",
                "text": "Sample error message"
            }
        ]
    }
