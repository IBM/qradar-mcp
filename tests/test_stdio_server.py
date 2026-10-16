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
Tests for the stdio transport entry point.

stdio_server.py configures the client at import time and exits on missing
credentials, so it is exercised as a subprocess rather than imported.
"""

import os
import subprocess
import sys

import pytest

STDIO_SERVER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'stdio_server.py'
)

MISSING_CREDENTIALS = 'No QRadar credentials configured'
SERVER_STARTED = 'QRadar MCP stdio server starting'

# Cleared so the developer's own shell does not leak credentials into the cases
CREDENTIAL_VARS = (
    'QRADAR_AUTH_TOKEN',
    'QRADAR_SEC_TOKEN',
    'QRADAR_CSRF_TOKEN',
    'QRADAR_USERNAME',
    'QRADAR_PASSWORD',
)


def run_stdio_server(**credentials):
    """
    Start stdio_server.py with the given credential env vars.

    stdin is closed immediately so that a server which does start reaches EOF
    and shuts down instead of blocking. Returns (returncode, output), with a
    returncode of None when the process had to be killed.
    """
    env = dict(os.environ)
    for name in CREDENTIAL_VARS:
        env.pop(name, None)
    env['QRADAR_CONSOLE_FQDN'] = 'https://test.qradar.com'
    env.update(credentials)

    try:
        completed = subprocess.run(
            [sys.executable, STDIO_SERVER],
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
        return completed.returncode, completed.stdout + completed.stderr
    except subprocess.TimeoutExpired as expired:
        return None, (expired.stdout or '') + (expired.stderr or '')


class TestStdioServerCredentialGuard:
    """Test which credential combinations are accepted at startup."""

    def test_exits_without_any_credentials(self):
        """Test that the server refuses to start with no credentials at all."""
        returncode, output = run_stdio_server()

        assert returncode == 1
        assert MISSING_CREDENTIALS in output

    def test_exits_with_username_but_no_password(self):
        """Test that a half-configured Basic credential is rejected."""
        returncode, output = run_stdio_server(QRADAR_USERNAME='admin')

        assert returncode == 1
        assert MISSING_CREDENTIALS in output

    def test_exits_with_password_but_no_username(self):
        """Test that a password alone is rejected."""
        returncode, output = run_stdio_server(QRADAR_PASSWORD='s3cret')

        assert returncode == 1
        assert MISSING_CREDENTIALS in output

    def test_error_message_names_the_basic_auth_variables(self):
        """Test that the failure tells the user about the Basic auth option."""
        _, output = run_stdio_server()

        assert 'QRADAR_USERNAME' in output
        assert 'QRADAR_PASSWORD' in output

    def test_starts_with_basic_credentials(self):
        """Test that username and password alone are enough to start."""
        returncode, output = run_stdio_server(
            QRADAR_USERNAME='admin', QRADAR_PASSWORD='s3cret'
        )

        assert MISSING_CREDENTIALS not in output
        assert SERVER_STARTED in output
        assert returncode == 0

    def test_starts_with_auth_token(self):
        """Test that the pre-existing token path is unaffected."""
        returncode, output = run_stdio_server(QRADAR_AUTH_TOKEN='service_token')

        assert MISSING_CREDENTIALS not in output
        assert SERVER_STARTED in output
        assert returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
