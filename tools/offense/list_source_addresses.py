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


class ListSourceAddressesTool(MCPTool):
    """Tool for listing source IP addresses with offense context."""

    @property
    def name(self) -> str:
        return "list_source_addresses"

    @property
    def description(self) -> str:
        return """List source IP addresses with offense associations.

Use cases:
  - Identify most active attacking source IPs
  - Find IPs involved in multiple offenses (cross-offense correlation)
  - Prioritize investigation by magnitude
  - Analyze attack timelines (first/last seen)
  - Understand source network classifications
  - Track which sources target which destinations

Filterable Fields:
  - id (numeric source address ID)
  - source_ip (IP address string, use = for exact match)
  - magnitude (0-10)
  - event_flow_count (numeric)
  - first_event_flow_seen, last_event_flow_seen (in epoch milliseconds)
  - network (text string)
  - domain_id (numeric domain ID)
  - offense_ids (array of offense IDs)
  - local_destination_address_ids (array of destination IDs)
"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional AQL filter expression (e.g., 'magnitude > 5')")
            .string("fields")
                .description("Optional comma-separated list of fields to return")
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
        Execute the list_source_addresses tool.

        Args:
            arguments: Dict containing optional parameters:
                - filter: AQL filter expression
                - fields: Field selection

        Returns:
            MCP response with source addresses list or error
        """

        # Build query parameters
        params = {}

        if arguments.get("filter"):
            params["filter"] = arguments["filter"]

        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        response = await self.client.get('/siem/source_addresses', params=params)
        response.raise_for_status()

        source_addresses = response.json()

        return self.create_success_response(json.dumps(source_addresses, indent=2))
