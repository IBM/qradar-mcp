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
from qradar_mcp.tools import endpoints


class GetSavedSearchTool(MCPTool):
    """Tool for retrieving Ariel saved search details."""

    @property
    def name(self) -> str:
        return "get_saved_search"

    @property
    def description(self) -> str:
        return """Retrieve detailed information about a specific Ariel saved search.

Use this to inspect the saved AQL before execution or modification. Execute
it by ID with create_ariel_search.

Returns 404 if the search does not exist or the user lacks permission."""

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
    def endpoint(self) -> str:
        return endpoints.ARIEL_SAVED_SEARCH

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
        response = await self.client.get(self.endpoint.format(search_id=int(search_id)), params=params)
        response.raise_for_status()

        data = response.json()

        return self.create_success_response(json.dumps(data, indent=2))
