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
List Source Addresses Tool

Retrieves source IP addresses with offense associations from QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints
from qradar_mcp.utils.parameters import (
    build_headers,
    build_query_params,
    parse_range_from_limit_offset,
)


class ListSourceAddressesTool(MCPTool):
    """Tool for listing source IP addresses with offense context."""

    @property
    def name(self) -> str:
        return "list_source_addresses"

    @property
    def description(self) -> str:
        return """Retrieve source IP addresses that are associated with offenses in QRadar SIEM.

Use cases:
  - Identify the most active or highest-magnitude attacking source IPs
  - Find IPs involved in multiple offenses (cross-offense correlation)
  - Analyze attack timelines using first_event_flow_seen / last_event_flow_seen
  - Understand source network classifications (internal segment, DMZ, etc.)
  - Pivot from a source IP to its associated local destination addresses

=== FIELDS REFERENCE ===

domain_id: Number
event_flow_count: Number
first_event_flow_seen: Number
id: Number
last_event_flow_seen: Number
local_destination_address_ids: Array<Number>
magnitude: Number
network: String
offense_ids: Array<Number>
source_ip: String

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
            .integer("offset")
                .description("Starting position for pagination (0-based)")
                .minimum(0)
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.SIEM_SOURCE_ADDRESSES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_source_addresses tool.

        Args:
            arguments: Dict containing optional parameters:
                - filter: AQL filter expression
                - sort: Sort expression
                - limit: Maximum results to return
                - offset: Starting position
                - fields: Field selection

        Returns:
            MCP response with source addresses list or error
        """

        fields = arguments.get("fields")
        params = build_query_params(
            filter_expr=arguments.get("filter"),
            fields=fields.split(",") if fields else None,
        )

        headers = {}
        if arguments.get("limit") is not None:
            start, end = parse_range_from_limit_offset(
                arguments.get("limit"),
                arguments.get("offset", 0),
            )
            headers = build_headers(start=start, end=end)

        response = await self.client.get(
            self.endpoint, params=params, headers=headers
        )
        response.raise_for_status()

        source_addresses = response.json()

        return self.create_success_response(json.dumps(source_addresses, indent=2))
