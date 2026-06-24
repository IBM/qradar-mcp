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
List Servers Tool

Lists all QRadar server hosts in the deployment.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import (
    build_query_params,
    build_headers,
    parse_range_from_limit_offset
)


class ListServersTool(MCPTool):
    """Tool for listing QRadar server hosts."""

    @property
    def name(self) -> str:
        return "list_servers"

    @property
    def description(self) -> str:
        return """List all QRadar server hosts in the deployment.

Retrieves information about all servers including hostname, IP address, status,
and managed host ID. Useful for understanding deployment topology and monitoring
server health.

Use cases:
  - Deployment topology mapping and documentation
  - Health monitoring across distributed deployments
  - Capacity planning and resource allocation
  - Troubleshooting distributed deployment issues
  - Compliance and architecture documentation

Example:
  list_servers()
  list_servers(filter='status="ACTIVE"')
  list_servers(limit=10, offset=0)
  list_servers(fields="hostname,private_ip,status")

Note: Returns all servers in the QRadar deployment. In distributed deployments,
this includes console, processors, and other appliances."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .string("filter")
                .description("Optional filter expression (e.g., 'status=\"ACTIVE\"')")
            .integer("limit")
                .description("Maximum number of servers to return (1-100)")
                .minimum(1)
                .maximum(100)
            .integer("offset")
                .description("Number of servers to skip for pagination")
                .minimum(0)
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
        Execute the list_servers tool.

        Args:
            arguments: Optional parameters for filtering, pagination, field selection

        Returns:
            MCP response with server list or error
        """

        # Build query parameters
        fields = arguments.get("fields")
        params = build_query_params(
            fields=fields.split(",") if fields else None,
            filter_expr=arguments.get("filter")
        )

        # Build headers with Range for pagination
        limit = arguments.get("limit")
        offset = arguments.get("offset")
        headers = {}

        if limit is not None or offset is not None:
            start, end = parse_range_from_limit_offset(limit, offset)
            headers = build_headers(start=start, end=end)

        # Make API call
        response = await self.client.get('/system/servers', params=params, headers=headers)
        response.raise_for_status()

        servers = response.json()

        return self.create_success_response(json.dumps(servers, indent=2))
