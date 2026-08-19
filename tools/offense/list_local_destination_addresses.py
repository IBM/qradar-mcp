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
List Local Destination Addresses Tool

Retrieves local destination IP addresses with offense associations from QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints
from qradar_mcp.utils.parameters import build_query_params, build_headers


class ListLocalDestinationAddressesTool(MCPTool):
    """Tool for listing local destination IP addresses with offense context."""

    @property
    def name(self) -> str:
        return "list_local_destination_addresses"

    @property
    def description(self) -> str:
        return """Retrieve local destination IP addresses that are associated with offenses in QRadar SIEM.

Use cases:
  - Identify the most targeted or highest-magnitude internal assets
  - Find internal hosts involved in multiple offenses (lateral movement analysis)
  - Analyze targeting timelines using first_event_flow_seen / last_event_flow_seen
  - Understand destination network classifications (server segment, workstation, DMZ)
  - Pivot from a destination IP to the source addresses attacking it

=== FIELDS REFERENCE ===

domain_id: Number
event_flow_count: Number
first_event_flow_seen: Number
id: Number
last_event_flow_seen: Number
local_destination_ip: String
magnitude: Number
network: String
offense_ids: Array<Number>
source_address_ids: Array<Number>

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional filter expression.")
            .integer("limit")
                .description("Maximum number of results to return (default: 10)")
                .minimum(1)
                .default(10)
            .string("fields")
                .description("Optional comma-separated list of fields to return.")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.SIEM_LOCAL_DESTINATION_ADDRESSES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_local_destination_addresses tool.

        Args:
            arguments: Dict containing optional parameters:
                - filter: AQL filter expression
                - limit: Maximum results to return
                - fields: Field selection

        Returns:
            MCP response with local destination addresses list or error
        """
        fields = arguments.get("fields")
        params = build_query_params(
            filter_expr=arguments.get("filter"),
            fields=fields.split(",") if fields else None,
        )

        limit = arguments.get("limit", 10)
        headers = build_headers(start=0, end=limit - 1)

        response = await self.client.get(self.endpoint, params=params, headers=headers)
        response.raise_for_status()

        destination_addresses = response.json()

        return self.create_success_response(json.dumps(destination_addresses, indent=2))
