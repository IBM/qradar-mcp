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
Get Network Hierarchy Tool

Retrieves the deployed network hierarchy.
"""

from typing import Any, Dict
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params
from qradar_mcp.tools import endpoints


class GetNetworkHierarchyTool(MCPTool):
    """Tool for retrieving the deployed network hierarchy."""

    @property
    def name(self) -> str:
        return "get_network_hierarchy"

    @property
    def description(self) -> str:
        return """Retrieve the deployed network hierarchy.

Returns the active QRadar network hierarchy including network groups, names,
CIDR ranges, descriptions, domain assignments, and optional geographic
location data.

Use cases:
  - Review current network segmentation
  - Inspect deployed CIDR ranges and groups
  - Understand domain-based network organization
  - Check geographic metadata assigned to networks"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("fields")
                .description(
                    "Optional comma-separated list of fields to return "
                    "(e.g., 'id,name,cidr,group')")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.CONFIG_NETWORK_HIERARCHY

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the get_network_hierarchy tool."""
        fields = arguments.get("fields")
        params = build_query_params(fields=fields.split(",") if fields else None)

        response = await self.client.get(
            self.endpoint, params=params)
        response.raise_for_status()

        networks = response.json()
        return self.create_success_response(json.dumps(networks, indent=2))
