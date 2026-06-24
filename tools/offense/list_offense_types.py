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
List Offense Types Tool

Retrieves offense type categories from QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class ListOffenseTypesTool(MCPTool):
    """Tool for listing offense type categories."""

    @property
    def name(self) -> str:
        return "list_offense_types"

    @property
    def description(self) -> str:
        return """List all offense type categories.

Use cases:
  - Understand offense classification and categorization
  - Filter offenses by specific types
  - Identify custom property-based offense types
  - Determine if offense is event-based, flow-based, or both

Offense types indicate what property triggered the offense (e.g., sourceip, destinationip,
username). Custom properties appear only if used in rule actions or response limiters.

Database types:
  - EVENTS: Event-based offense type
  - FLOWS: Flow-based offense type
  - COMMON: Present in both events and flows"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional AQL filter expression (e.g., 'custom=false')")
            .string("sort")
                .description("Optional sort expression (e.g., '+id,-name')")
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
        Execute the list_offense_types tool.

        Args:
            arguments: Dict containing optional parameters:
                - filter: AQL filter expression
                - sort: Sort expression
                - fields: Field selection

        Returns:
            MCP response with offense types list or error
        """

        # Build query parameters
        params = {}

        if arguments.get("filter"):
            params["filter"] = arguments["filter"]

        if arguments.get("sort"):
            params["sort"] = arguments["sort"]

        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        response = await self.client.get('/siem/offense_types', params=params)
        response.raise_for_status()

        offense_types = response.json()

        return self.create_success_response(json.dumps(offense_types, indent=2))
