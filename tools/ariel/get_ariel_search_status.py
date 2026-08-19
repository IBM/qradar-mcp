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
Get Ariel Search Status Tool

Retrieves status and metadata for an Ariel search by search ID.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetArielSearchStatusTool(MCPTool):
    """Tool for retrieving Ariel search status and metadata."""

    @property
    def name(self) -> str:
        return "get_ariel_search_status"

    @property
    def description(self) -> str:
        return (
            "Retrieve status and metadata for an Ariel search by search ID. "
            "Returns search progress, status (WAIT, EXECUTE, SORTING, COMPLETED, "
            "CANCELED, ERROR), record count, and other metadata."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("search_id")
                .description("The ID of the Ariel search to retrieve status for")
                .required()
            .integer("wait_seconds")
                .description(
                    "Optional number of seconds to wait for search completion. "
                    "If specified, the API will wait up to this many seconds for "
                    "the search to reach COMPLETED status before returning."
                )
                .minimum(0)
                .maximum(300)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.ARIEL_SEARCH

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_ariel_search_status tool.

        Args:
            arguments: Must contain 'search_id' (string), optional 'wait_seconds' (integer)

        Returns:
            MCP response with search status and metadata
        """
        search_id = arguments.get("search_id")
        wait_seconds = arguments.get("wait_seconds")

        if not search_id:
            return self.create_error_response("Error: search_id is required")

        # Build headers with optional Prefer header for wait
        headers = {}
        if wait_seconds is not None:
            headers["Prefer"] = f"wait={wait_seconds}"

        # Make API request
        api_path = self.endpoint.format(search_id=search_id)
        response = await self.client.get(api_path=api_path, headers=headers)

        # Handle response based on status code
        if response.status_code == 200:
            search_data = response.json()
            return self.create_success_response(json.dumps(search_data, indent=2))

        if response.status_code == 206:
            # Partial content - wait timeout expired before completion
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
            f"Failed to retrieve search status. Status: {response.status_code}, "
            f"Response: {response.text}"
        )
