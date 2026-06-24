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


class ListLocalDestinationAddressesTool(MCPTool):
    """Tool for listing local destination IP addresses with offense context."""

    @property
    def name(self) -> str:
        return "list_local_destination_addresses"

    @property
    def description(self) -> str:
        return """List local destination IP addresses with offense associations.

Use cases:
  - Identify most targeted internal assets
  - Find destinations involved in multiple offenses (cross-offense correlation)
  - Prioritize asset protection by magnitude
  - Analyze attack patterns (which sources target which destinations)
  - Track attack timelines (first/last seen)
  - Focus security controls on frequently targeted IPs

Each destination address includes:
  - Associated offense IDs
  - Magnitude (calculated severity)
  - Event/flow counts
  - First and last seen timestamps
  - Network classification
  - Associated source address IDs

"Local" indicates internal/protected assets within your network.

Use filtering to find specific destinations (e.g., 'magnitude > 7' or
'local_destination_ip = \"10.0.1.50\"')."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional AQL filter expression (e.g., 'magnitude > 7')")
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
        Execute the list_local_destination_addresses tool.

        Args:
            arguments: Dict containing optional parameters:
                - filter: AQL filter expression
                - fields: Field selection

        Returns:
            MCP response with local destination addresses list or error
        """

        # Build query parameters
        params = {}

        if arguments.get("filter"):
            params["filter"] = arguments["filter"]

        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        response = await self.client.get('/siem/local_destination_addresses', params=params)
        response.raise_for_status()

        destination_addresses = response.json()

        return self.create_success_response(json.dumps(destination_addresses, indent=2))
