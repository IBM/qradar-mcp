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
Delete Ariel Search Tool

Deletes an Ariel search and its associated results.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class DeleteArielSearchTool(MCPTool):
    """Tool for deleting Ariel searches."""

    @property
    def name(self) -> str:
        return "delete_ariel_search"

    @property
    def description(self) -> str:
        return (
            "Delete an Ariel search and its associated results. This discards any "
            "collected results and stops the search if it is still in progress. "
            "The search is deleted regardless of whether results were saved."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("search_id")
                .description("The ID of the Ariel search to delete")
                .required()
            .build())

    @property
    def http_verb(self) -> str:
        return "DELETE"

    @property
    def endpoint(self) -> str:
        return endpoints.ARIEL_SEARCH

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the delete_ariel_search tool.

        Args:
            arguments: Must contain 'search_id' (string)

        Returns:
            MCP response confirming deletion
        """
        search_id = arguments.get("search_id")

        if not search_id:
            return self.create_error_response("Error: search_id is required")


        # Make API request
        api_path = self.endpoint.format(search_id=search_id)
        response = await self.client.delete(api_path=api_path)

        # Handle response based on status code
        if response.status_code == 202:
            # Deletion accepted - return the search metadata
            search_data = response.json()
            return self.create_success_response(json.dumps(search_data, indent=2))

        if response.status_code == 404:
            raise RuntimeError(f"Search {search_id} not found")
        if response.status_code == 422:
            error_detail = response.text
            raise RuntimeError(f"Invalid request parameters: {error_detail}")
        if response.status_code == 503:
            raise RuntimeError("Ariel server temporarily unavailable")

        raise RuntimeError(
            f"Failed to delete search. Status: {response.status_code}, "
            f"Response: {response.text}"
        )
