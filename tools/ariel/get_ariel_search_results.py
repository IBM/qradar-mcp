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
Get Ariel Search Results Tool

Retrieves the results of a completed Ariel search.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetArielSearchResultsTool(MCPTool):
    """Tool for retrieving Ariel search results."""

    @property
    def name(self) -> str:
        return "get_ariel_search_results"

    @property
    def description(self) -> str:
        return (
            "Retrieve the results of a completed Ariel search. The search must be "
            "in COMPLETED status before results can be retrieved. Supports pagination "
            "via start and limit parameters to retrieve subsets of large result sets."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("search_id")
                .description("The ID of the completed Ariel search to retrieve results for")
                .required()
            .integer("start")
                .description(
                    "Starting index for pagination (0-based). Use with limit to retrieve "
                    "a specific range of results."
                )
                .minimum(0)
            .integer("limit")
                .description(
                    "Maximum number of results to return. Use with start for pagination. "
                    "Default returns all results."
                )
                .minimum(1)
                .maximum(10000)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.ARIEL_SEARCH_RESULTS

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_ariel_search_results tool.

        Args:
            arguments: Must contain 'search_id' (string), optional 'start' and 'limit' (integers)

        Returns:
            MCP response with search results
        """
        search_id = arguments.get("search_id")

        if not search_id:
            return self.create_error_response("Error: search_id is required")

        # Build headers with optional Range header for pagination
        headers = self._build_range_header(arguments.get("start"), arguments.get("limit"))

        # Make API request
        api_path = self.endpoint.format(search_id=search_id)
        response = await self.client.get(api_path=api_path, headers=headers)

        # Handle response
        response.raise_for_status()
        results_data = response.json()

        return self.create_success_response(json.dumps(results_data, indent=2))

    def _build_range_header(self, start: Any, limit: Any) -> Dict[str, str]:
        """Build Range header for pagination."""
        headers = {}
        if start is not None or limit is not None:
            start_idx = start if start is not None else 0
            if limit is not None:
                end_idx = start_idx + limit - 1
                range_header = f"items={start_idx}-{end_idx}"
            else:
                range_header = f"items={start_idx}-"

            headers["Range"] = range_header
        return headers

    def _count_results(self, results_data: Any) -> int:
        """Count the number of results in the response."""
        if isinstance(results_data, dict):
            return sum(len(v) if isinstance(v, list) else 0 for v in results_data.values())
        if isinstance(results_data, list):
            return len(results_data)
        return 0

    def _handle_error_response(self, response: Any, search_id: str) -> Dict[str, Any]:
        """Handle error responses from the API."""
        if response.status_code == 404:
            if "not found" in response.text.lower():
                raise RuntimeError(f"Search {search_id} not found")
            raise RuntimeError(
                "Search results not found. The search may still be in progress. "
                "Check search status before retrieving results."
            )
        if response.status_code == 422:
            raise RuntimeError(f"Invalid request parameters: {response.text}")
        if response.status_code == 503:
            raise RuntimeError("Ariel server temporarily unavailable")

        raise RuntimeError(
            f"Failed to retrieve search results. Status: {response.status_code}, "
            f"Response: {response.text}"
        )
