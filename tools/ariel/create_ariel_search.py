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
Create Ariel Search Tool

Creates a new asynchronous Ariel search using AQL query or saved search ID.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class CreateArielSearchTool(MCPTool):
    """Tool for creating new Ariel searches in QRadar."""

    @property
    def name(self) -> str:
        return "create_ariel_search"

    @property
    def description(self) -> str:
        return (
            "Create a new asynchronous Ariel search using an AQL query expression or a "
            "saved search ID. Returns a UUID search_id string used to monitor status and "
            "retrieve results via get_ariel_search_status and get_ariel_search_results.\n\n"
            "NOTE: saved_search_id is an INTEGER from list_saved_searches — it is "
            "NOT the UUID search_id string returned by this tool or get_ariel_search_status.\n\n"
            "IMPORTANT: Before using this tool with a query_expression:\n"
            "1. Read qradar://aql/fields/events or qradar://aql/fields/flows to get valid field names\n"
            "2. Read qradar://aql/functions to discover available functions\n"
            "3. Read qradar://aql/guide for syntax rules and patterns\n"
            "4. Use validate_aql tool to check query syntax before execution\n\n"
            "This workflow prevents errors and ensures queries use correct field names for this QRadar deployment."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("query_expression")
                .description(
                    "The AQL query to execute (e.g., 'SELECT sourceip, destinationip "
                    "FROM events LAST 1 HOURS'). Mutually exclusive with saved_search_id."
                )
            .integer("saved_search_id")
                .description(
                    "Integer ID of a saved Ariel search to execute. Get this integer from "
                    "list_saved_searches or get_saved_search. "
                    "Mutually exclusive with query_expression."
                )
                .minimum(1)
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.ARIEL_SEARCHES

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the create_ariel_search tool.

        Args:
            arguments: Must contain either 'query_expression' (string) OR 'saved_search_id' (integer)

        Returns:
            MCP response with search object including search_id, status, and metadata
        """
        query_expression = arguments.get("query_expression")
        saved_search_id = arguments.get("saved_search_id")

        # Validate that exactly one parameter is provided
        if not query_expression and saved_search_id is None:
            return self.create_error_response(
                "Error: Either query_expression or saved_search_id must be provided"
            )

        if query_expression and saved_search_id is not None:
            return self.create_error_response(
                "Error: query_expression and saved_search_id are mutually exclusive. "
                "Provide only one."
            )

        # Build query parameters - QRadar Ariel API expects QUERY parameters even for POST
        params = {}
        if query_expression:
            params["query_expression"] = query_expression
        else:
            params["saved_search_id"] = saved_search_id

        # Make API request - parameters go in query string per QRadar API spec
        response = await self.client.post(self.endpoint, params=params)
        response.raise_for_status()
        search_data = response.json()
        return self.create_success_response(json.dumps(search_data, indent=2))
