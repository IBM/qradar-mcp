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
Get Saved Search Tool

Retrieves detailed information about a specific Ariel saved search.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params


class GetSavedSearchTool(MCPTool):
    """Tool for retrieving Ariel saved search details."""

    @property
    def name(self) -> str:
        return "get_saved_search"

    @property
    def description(self) -> str:
        return """Retrieve detailed information about a specific Ariel saved search.

Use cases:
  - View the complete AQL query before execution
  - Study well-crafted queries from experienced analysts
  - Get query details to create a modified version
  - Extract query details for investigation runbooks
  - Verify search parameters before running via create_ariel_search

Integration example:
  1. Get saved search details: get_saved_search(search_id=42)
  2. Execute the AQL: create_ariel_search(query_expression=details['aql'])
  3. Get results: get_ariel_search_results(search_id=search_id)

Note: Returns 404 if search doesn't exist or user lacks permission."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("search_id")
                .description("ID of the saved search to retrieve")
                .minimum(1)
                .required()
            .string("fields")
                .description("Comma-separated list of fields to return (e.g., 'id,name,aql,owner')")
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
        Execute the get_saved_search tool.

        Args:
            arguments: Must contain:
                - search_id: ID of the saved search (required)
                - fields: Comma-separated fields (optional)

        Returns:
            MCP response with saved search details or error
        """
        search_id = arguments.get("search_id")

        if search_id is None:
            return self.create_error_response("Error: search_id is required")

        # Build query parameters
        fields = arguments.get("fields")
        params = build_query_params(
            fields=fields.split(",") if fields else None
        )

        # Make API call
        response = await self.client.get(f'/ariel/saved_searches/{int(search_id)}', params=params)
        response.raise_for_status()

        data = response.json()

        return self.create_success_response(json.dumps(data, indent=2))
