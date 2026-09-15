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
Authentication Context Management

Provides context variables and middleware for passing QRadar authentication
tokens across async boundaries in the FastMCP server.
"""

from contextvars import ContextVar
from typing import Optional, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


# Context variable to store auth tokens for the current request
_request_auth_tokens: ContextVar[Optional[Dict[str, str]]] = ContextVar(
    'request_auth_tokens',
    default=None
)


def get_request_auth_tokens() -> Optional[Dict[str, str]]:
    """
    Get auth tokens from the current request context.

    Returns:
        Dictionary containing auth tokens (sec_token, csrf_token, etc.) or None
    """
    return _request_auth_tokens.get()


def set_request_auth_tokens(tokens: Optional[Dict[str, str]]) -> None:
    """
    Set auth tokens in the current request context.

    Args:
        tokens: Dictionary containing auth tokens or None to clear
    """
    _request_auth_tokens.set(tokens)


class AuthTokenMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract QRadar authentication tokens from HTTP headers.

    Extracts SEC and QRadarCSRF tokens from request headers and makes them
    available to tools via context variables that work across async boundaries.

    Supported headers:
    - SEC: QRadar security token (required for all API calls)
    - QRadarCSRF: CSRF token (required for user authentication)
    """

    async def dispatch(self, request: Request, call_next):
        """Extract auth tokens from headers and add to request context."""
        auth_tokens = {}

        # Extract SEC token (required for all QRadar API calls)
        if 'SEC' in request.headers:
            auth_tokens['sec_token'] = request.headers['SEC']
        elif 'SEC' in request.cookies:
            auth_tokens['sec_token'] = request.cookies['SEC']

        # Extract CSRF token (required for user authentication)
        if 'QRadarCSRF' in request.headers:
            auth_tokens['csrf_token'] = request.headers['QRadarCSRF']
        elif 'QRadarCSRF' in request.cookies:
            auth_tokens['csrf_token'] = request.cookies['QRadarCSRF']

        # Store auth tokens in both request state and context variable
        request.state.auth_tokens = auth_tokens if auth_tokens else None
        set_request_auth_tokens(auth_tokens if auth_tokens else None)

        try:
            response = await call_next(request)
            return response
        finally:
            # Clean up context after request
            set_request_auth_tokens(None)
