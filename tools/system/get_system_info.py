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
Get System Info Tool

Retrieves QRadar system version and configuration information.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params


class GetSystemInfoTool(MCPTool):
    """Tool for retrieving QRadar system information."""

    @property
    def name(self) -> str:
        return "get_system_info"

    @property
    def description(self) -> str:
        return """Get QRadar system version and configuration information.

Retrieves system metadata including build version, external version, release name,
and FIPS enablement status.

Use cases:
  - Version verification before using version-specific features
  - Compliance reporting and documentation
  - Troubleshooting and support diagnostics
  - Deployment validation after upgrades

Example:
  get_system_info()
  get_system_info(fields="build_version,external_version")

Note: This endpoint provides read-only system information and requires no special
permissions beyond basic API access."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("fields")
                .description("Optional comma-separated list of fields to return "
                           "(e.g., 'build_version,external_version')")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_system_info tool.

        Args:
            arguments: Optional 'fields' parameter for field selection

        Returns:
            MCP response with system information or error
        """

        # Build query parameters
        fields = arguments.get("fields")
        params = build_query_params(
            fields=fields.split(",") if fields else None
        )

        # Make API call
        response = await self.client.get('/system/about', params=params)
        response.raise_for_status()

        system_info = response.json()

        return self.create_success_response(json.dumps(system_info, indent=2))
