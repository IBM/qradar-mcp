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


import base64
import json
import os
from typing import Dict, Optional
import httpx
from qradar_mcp.utils.retry import retry_on_failure_async
from qradar_mcp.utils.structured_logger import log_structured
from qradar_mcp.utils.mcp_logger import log_mcp
from qradar_mcp.auth_context import get_request_auth_tokens

QRADAR_CSRF = 'QRadarCSRF'
SEC_HEADER = 'SEC'
AUTHORIZATION_HEADER = 'Authorization'
BASIC_SCHEME = 'Basic'


def build_basic_auth_header(username: str, password: str) -> str:
    """
    Build an HTTP Basic ``Authorization`` header value.

    QRadar accepts HTTP Basic authentication as an alternative to SEC token
    authentication, which is useful for deployments where an authorized service
    token cannot be issued.

    Args:
        username: QRadar username
        password: QRadar password

    Returns:
        The header value, e.g. ``Basic dXNlcjpwYXNz``
    """
    credentials = f"{username}:{password}".encode('utf-8')
    return f"{BASIC_SCHEME} {base64.b64encode(credentials).decode('ascii')}"


def load_config():
    """Load configuration from config.json file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


class QRadarRestClient():  # pylint: disable=too-many-instance-attributes
    """
    Async REST client for QRadar REST API calls using httpx.
    Supports both QRadar App environment and local development with config.json.

    Authentication modes:
    1. Auth tokens from request context (set by middleware) - for FastMCP usage
    2. Config file - for local development
    3. QRadar App mode (uses qpylib for console FQDN)

    Supported credential types (both context and config): SEC + QRadarCSRF
    tokens, an authorized service token, or HTTP Basic username/password.

    This client uses a shared httpx.AsyncClient instance for connection pooling.
    """

    # Class-level shared client for connection pooling
    _shared_client: Optional[httpx.AsyncClient] = None

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        Initialize QRadar REST client.

        Auth tokens are automatically retrieved from:
        1. Request context (set by AuthTokenMiddleware) - for FastMCP
        2. Config file - for local development

        Args:
            client: Optional httpx.AsyncClient instance. If not provided, uses shared client.
        """
        # Try to load local config first
        self.config = load_config()

        if self.config:
            # Local development mode
            self._url = self.config['qradar']['host']
            self._sec_token = self.config['qradar'].get('sec_token')
            self._csrf_token = self.config['qradar'].get('csrf_token')
            self._authorized_service_token = self.config['qradar'].get('authorized_service_token')
            self._username = self.config['qradar'].get('username')
            self._password = self.config['qradar'].get('password')
            self._verify_ssl = self.config['qradar'].get('verify_ssl', False)
            self._proxy = self.config['qradar'].get('proxy')
            self._local_mode = True
        else:
            # QRadar App mode
            self._url = os.getenv('QRADAR_CONSOLE_FQDN')
            # Credentials normally arrive per request via headers. These env
            # vars are the documented fallback for deployments that run the
            # server for a single identity (stdio transport, or a container
            # with no config.json); requests that carry their own headers
            # always take precedence over them in _add_headers().
            self._authorized_service_token = os.getenv('QRADAR_AUTH_TOKEN')
            self._sec_token = os.getenv('QRADAR_SEC_TOKEN')
            self._csrf_token = os.getenv('QRADAR_CSRF_TOKEN')
            self._username = os.getenv('QRADAR_USERNAME')
            self._password = os.getenv('QRADAR_PASSWORD')
            self._is_fvt_env = os.getenv('FUNCTIONAL_TEST_ENV') is not None
            self._cert_path = os.getenv('REQUESTS_CA_BUNDLE')
            self._proxy = os.getenv('QRADAR_REST_PROXY')
            self._local_mode = False

        # Use provided client or shared client
        self._client = client

    @classmethod
    def set_shared_client(cls, client: httpx.AsyncClient):
        """
        Set the shared httpx.AsyncClient instance for connection pooling.

        Args:
            client: The httpx.AsyncClient instance to use for all requests
        """
        cls._shared_client = client

    @classmethod
    async def close_shared_client(cls):
        """Close the shared httpx.AsyncClient instance."""
        if cls._shared_client:
            await cls._shared_client.aclose()
            cls._shared_client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the httpx client to use for requests."""
        if self._client:
            return self._client
        if self._shared_client:
            return self._shared_client
        raise RuntimeError("No httpx client available. Call set_shared_client() first.")

    def _get_verify(self):
        """
        Returns the verify parameter for the request.
        """
        if self._local_mode:
            return self._verify_ssl

        if hasattr(self, '_is_fvt_env') and self._is_fvt_env:
            # Will disable SSL
            return False
        if hasattr(self, '_cert_path') and self._cert_path:
            # Will use the certificate path defined at this location.
            return self._cert_path
        # Default to not verifying in local dev
        return False

    @retry_on_failure_async(max_attempts=3, backoff_factor=2.0)
    async def get(self, api_path, headers=None, params=None, version=None, timeout=None):  # pylint: disable=too-many-positional-arguments
        """
        Perform a GET request to the QRadar API with automatic retry on transient failures.

        Args:
            api_path: The API path (e.g., 'siem/offenses/123')
            headers: Optional headers dictionary
            params: Optional query parameters
            version: Optional API version
            timeout: Optional request timeout

        Returns:
            httpx.Response object
        """
        full_url = self._generate_full_url(api_path)
        headers = self._add_headers(headers, version)

        log_structured(
            f"QRadar API GET request: {api_path}",
            level='DEBUG',
            api_path=api_path,
            method='GET'
        )

        client = self._get_client()
        return await client.get(
            url=full_url,
            headers=headers,
            timeout=timeout,
            params=params
        )

    @retry_on_failure_async(max_attempts=3, backoff_factor=2.0)
    async def post(self, api_path, headers=None, params=None, data=None, version=None, timeout=None):  # pylint: disable=too-many-positional-arguments,too-many-arguments
        """
        Perform a POST request to the QRadar API with automatic retry on transient failures.

        Args:
            api_path: The API path (e.g., 'siem/offenses/123')
            headers: Optional headers dictionary
            params: Optional query parameters
            data: Optional request body data (will be JSON encoded if dict)
            version: Optional API version
            timeout: Optional request timeout

        Returns:
            httpx.Response object
        """
        full_url = self._generate_full_url(api_path)
        headers = self._add_headers(headers, version)

        # Set Content-Type header if data is provided
        if data is not None and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        log_structured(
            f"QRadar API POST request: {api_path}",
            level='DEBUG',
            api_path=api_path,
            method='POST'
        )

        client = self._get_client()
        if isinstance(data, dict):
            return await client.post(
                url=full_url,
                headers=headers,
                timeout=timeout,
                params=params,
                json=data
            )
        return await client.post(
            url=full_url,
            headers=headers,
            timeout=timeout,
            params=params,
            content=data
        )

    @retry_on_failure_async(max_attempts=3, backoff_factor=2.0)
    async def put(self, api_path, headers=None, params=None, data=None, version=None, timeout=None):  # pylint: disable=too-many-positional-arguments,too-many-arguments
        """
        Perform a PUT request to the QRadar API with automatic retry on transient failures.

        Args:
            api_path: The API path
            headers: Optional headers dictionary
            params: Optional query parameters
            data: Optional request body data (will be JSON encoded if dict or list)
            version: Optional API version
            timeout: Optional request timeout

        Returns:
            httpx.Response object
        """
        full_url = self._generate_full_url(api_path)
        headers = self._add_headers(headers, version)

        log_structured(
            f"QRadar API PUT request: {api_path}",
            level='DEBUG',
            api_path=api_path,
            method='PUT'
        )

        client = self._get_client()
        if isinstance(data, (dict, list)):
            return await client.put(
                url=full_url,
                headers=headers,
                timeout=timeout,
                params=params,
                json=data
            )
        return await client.put(
            url=full_url,
            headers=headers,
            timeout=timeout,
            params=params,
            content=data
        )

    @retry_on_failure_async(max_attempts=3, backoff_factor=2.0)
    async def delete(self, api_path, headers=None, params=None, version=None, timeout=None):  # pylint: disable=too-many-positional-arguments
        """
        Perform a DELETE request to the QRadar API with automatic retry on transient failures.

        Args:
            api_path: The API path (e.g., 'ariel/searches/s123')
            headers: Optional headers dictionary
            params: Optional query parameters
            version: Optional API version
            timeout: Optional request timeout

        Returns:
            httpx.Response object
        """
        full_url = self._generate_full_url(api_path)
        headers = self._add_headers(headers, version)

        log_structured(
            f"QRadar API DELETE request: {api_path}",
            level='DEBUG',
            api_path=api_path,
            method='DELETE'
        )

        client = self._get_client()
        return await client.delete(
            url=full_url,
            headers=headers,
            timeout=timeout,
            params=params
        )

    def _add_headers(self, headers, version=None):
        """
        Add required headers for QRadar API requests.

        Priority for authentication (in order):
        1. Auth tokens from request context (set by middleware) - for FastMCP usage
        2. The credentials this process was configured with - config.json in
           local mode, or the QRADAR_* environment variables otherwise

        For user authentication, both CSRF and SEC tokens are required.
        For service authentication, only SEC token is required.
        For basic authentication, a username and password are required.

        In local mode, if authorized_service_token is configured, it takes priority
        over sec_token to simulate service authentication. HTTP Basic credentials are
        used only when no SEC/CSRF token is configured.
        """
        if headers is None:
            headers = {}

        if version is not None:
            headers['Version'] = version

        # Priority 1: Try to get auth tokens from request context (set by middleware)
        context_tokens = get_request_auth_tokens()
        if context_tokens:
            headers.update(self._context_auth_mode(context_tokens))
        # Priority 2: Fall back to the credentials this process was configured
        # with. A multi user deployment configures none of these, so a request
        # that supplies no credentials of its own still fails exactly as before.
        elif self._local_mode or self._has_ambient_credentials():
            headers.update(self._local_mode_auth())

        return headers

    def _has_ambient_credentials(self) -> bool:
        """
        Whether this process holds credentials of its own, as opposed to
        relying on each request to supply them.
        """
        return bool(
            self._authorized_service_token
            or self._sec_token
            or self._csrf_token
            or (self._username and self._password)
        )

    def _context_auth_mode(self, context_tokens: Dict[str, str]) -> Dict[str, str]:
        """
        Get auth headers from request context (set by middleware).

        Args:
            context_tokens: Auth tokens from request context

        Returns:
            Dictionary of auth headers
        """
        auth_headers = {}

        # Check for authorized service token (service-to-service auth)
        if 'authorized_service_token' in context_tokens:
            auth_headers[SEC_HEADER] = context_tokens['authorized_service_token']
        # Otherwise use user tokens (user auth)
        elif 'sec_token' in context_tokens or 'csrf_token' in context_tokens:
            if 'sec_token' in context_tokens:
                auth_headers[SEC_HEADER] = context_tokens['sec_token']
            if 'csrf_token' in context_tokens:
                auth_headers[QRADAR_CSRF] = context_tokens['csrf_token']
        # Fall back to a pre-built HTTP Basic header forwarded by the middleware
        elif 'authorization' in context_tokens:
            auth_headers[AUTHORIZATION_HEADER] = context_tokens['authorization']

        return auth_headers

    def _local_mode_auth(self) -> Dict[str, str]:
        auth_headers = {}
        # Prioritize authorized_service_token if present (simulates service auth)
        if self._authorized_service_token:
            auth_headers[SEC_HEADER] = self._authorized_service_token
        # Otherwise use user tokens (simulates user auth)
        elif self._sec_token or self._csrf_token:
            if self._sec_token:
                auth_headers[SEC_HEADER] = self._sec_token
            if self._csrf_token:
                auth_headers[QRADAR_CSRF] = self._csrf_token
        # Fall back to HTTP Basic credentials (username/password auth)
        elif self._username and self._password:
            auth_headers[AUTHORIZATION_HEADER] = build_basic_auth_header(
                self._username, self._password
            )

        return auth_headers


    def _generate_full_url(self, api_path):
        """Generate the full URL for the API request."""
        # Strip protocol if present in URL
        url = self._url.replace('https://', '').replace('http://', '') # NOSONAR
        return f"https://{url}/api/{api_path}"

    def _get_proxy_url(self):
        """Get proxy URL for requests. Returns None if no proxy is configured."""
        return self._proxy

    async def get_current_user(self):
        """
        Retrieve the current user's details using the QRadar Core config/access/users API.
        This method is mainly used to retrieve the caller's username for auditing purposes.

        Returns:
            dict: User details including username and id

        Raises:
            RuntimeError: If the API call fails or returns unexpected data
        """
        resp = await self.get(
            api_path='config/access/users',
            params={'current_user': True}
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Response code from users endpoint was {resp.status_code}")

        resp_json = resp.json()

        if len(resp_json) != 1:
            raise RuntimeError(f"Response json had length of {len(resp_json)}")

        return resp_json[0]

    async def get_current_authorized_service(self):
        """
        Retrieve the current authorized service details using the SEC token.
        Uses the QRadar Core config/access/authorized_services API.

        Returns:
            dict: Authorized service details including label and id

        Raises:
            RuntimeError: If the API call fails or returns unexpected data
        """
        resp = await self.get(
            api_path='config/access/authorized_services',
            params={'current_authorized_service': True}
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Response code from authorized_services endpoint was {resp.status_code}")

        resp_json = resp.json()

        if len(resp_json) != 1:
            raise RuntimeError(f"Response json had length of {len(resp_json)}")

        return resp_json[0]

    async def identify_user(self):
        """
        Using the QRadar core API, get the username and ID of the current user.
        This information is typically used for audit logging.

        Returns:
            tuple: (user_id, username) where user_id is an int and username is a string.
                   Returns (-1, "") if authentication fails.
        """
        user_id = -1
        username = ""
        try:
            user_details = await self.get_current_user()
            username = user_details["username"]
            user_id = user_details["id"]
        except RuntimeError as e:
            msg = "Failed to retrieve username of caller"
            log_mcp(msg, level='DEBUG')
            log_mcp(str(e), level='DEBUG')
            username = ""

        return user_id, username

    async def identify_authorized_service(self):
        """
        Using the QRadar core API, get the authorized service details using the SEC token.
        This is used for service-to-service authentication.

        Returns:
            tuple: (service_id, service_label) where service_id is an int and service_label is a string.
                   Returns (-1, "") if authentication fails.
        """
        service_id = -1
        service_label = ""
        try:
            service_details = await self.get_current_authorized_service()
            service_label = service_details["label"]
            service_id = service_details["id"]
        except RuntimeError as e:
            msg = "Failed to retrieve authorized service details"
            log_mcp(msg, level='DEBUG')
            log_mcp(str(e), level='DEBUG')
            service_label = ""

        return service_id, service_label
