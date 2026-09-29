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
QRadar MCP Server - stdio transport entry point

Runs the QRadar MCP server over stdin/stdout for use with any MCP client
that supports the stdio transport (e.g. Claude Desktop, watsonx Orchestrate
local MCP toolkits, or any MCP-compatible agent framework).

Credentials and connection settings are read from environment variables:
    QRADAR_CONSOLE_FQDN   QRadar hostname (required)
    QRADAR_AUTH_TOKEN     Authorized service token (recommended)
    QRADAR_SEC_TOKEN      SEC token - alternative to QRADAR_AUTH_TOKEN
    QRADAR_CSRF_TOKEN     CSRF token - only needed alongside QRADAR_SEC_TOKEN
    REQUESTS_CA_BUNDLE    Path to CA bundle for SSL verification (optional)

Proxy configuration (standard env vars respected by httpx automatically):
    HTTPS_PROXY           Proxy URL for HTTPS traffic (e.g. http://proxy.example.com:8080)
    HTTP_PROXY            Proxy URL for HTTP traffic
    NO_PROXY              Comma-separated list of hosts to bypass the proxy
    QRADAR_REST_PROXY     QRadar-specific proxy override - takes precedence over
                          HTTPS_PROXY/HTTP_PROXY for QRadar API calls when set
"""

import os
import sys
import atexit
import asyncio
import httpx

# Ensure the repo root is on sys.path so qradar_mcp package imports resolve
# when this file is invoked directly as an entry point.
_repo_root = os.path.dirname(os.path.abspath(__file__))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from fastmcp import FastMCP
from qradar_mcp.client.qradar_rest_client import QRadarRestClient
from qradar_mcp.tools.fastmcp_adapter import register_all_tools
from qradar_mcp.utils.feature_toggle_manager import (
    FeatureToggleManager,
    set_feature_toggle_manager,
)
from qradar_mcp.utils.structured_logger import log_structured


# Feature toggles
_toggles_path = os.path.join(_repo_root, 'feature_toggles.json')
toggle_manager = FeatureToggleManager(_toggles_path)
set_feature_toggle_manager(toggle_manager)

# QRadar client - configured from environment variables
# In stdio mode all credentials come from env vars; there is no per-request
# header injection, so the client always uses the configured credentials.
_console_fqdn = os.getenv('QRADAR_CONSOLE_FQDN')
_auth_token = os.getenv('QRADAR_AUTH_TOKEN')
_sec_token = os.getenv('QRADAR_SEC_TOKEN')
_csrf_token = os.getenv('QRADAR_CSRF_TOKEN')

if not _console_fqdn:
    log_structured("FATAL: QRADAR_CONSOLE_FQDN environment variable is not set", level='ERROR')
    sys.exit(1)
if not (_auth_token or _sec_token):
    log_structured("FATAL: No QRadar credentials configured. Set QRADAR_AUTH_TOKEN or QRADAR_SEC_TOKEN", level='ERROR')
    sys.exit(1)

qradar_client = QRadarRestClient()
qradar_client._url = _console_fqdn
qradar_client._authorized_service_token = _auth_token
qradar_client._sec_token = _sec_token
qradar_client._csrf_token = _csrf_token
qradar_client._local_mode = True

# Proxy resolution: QRADAR_REST_PROXY takes precedence; fall back to the
# standard HTTPS_PROXY / HTTP_PROXY env vars which httpx reads automatically
# when no explicit proxy argument is passed.
_proxy = os.getenv('QRADAR_REST_PROXY') or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')

httpx_client = httpx.AsyncClient(
    verify=os.getenv('REQUESTS_CA_BUNDLE', False),
    proxy=_proxy or None,
)
QRadarRestClient.set_shared_client(httpx_client)


async def _cleanup():
    await QRadarRestClient.close_shared_client()

atexit.register(lambda: asyncio.run(_cleanup()))

# MCP server
mcp = FastMCP("qradar-mcp", version="1.0.0")
register_all_tools(mcp, toggle_manager, qradar_client)

log_structured("QRadar MCP stdio server starting", level='INFO',
               host=qradar_client._url, local_mode=qradar_client._local_mode)

if __name__ == "__main__":
    mcp.run()
