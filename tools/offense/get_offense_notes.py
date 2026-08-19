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
Get Offense Notes Tool

Retrieves investigation notes for an offense from QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints
from qradar_mcp.utils.validators import validate_offense_id
from qradar_mcp.utils.parameters import build_headers


class GetOffenseNotesTool(MCPTool):
    """Tool for retrieving notes from QRadar offenses."""

    @property
    def name(self) -> str:
        return "get_offense_notes"

    @property
    def description(self) -> str:
        return """Retrieve investigation notes for an offense in QRadar SIEM.

Use cases:
  - Review investigation history
  - Check analyst observations
  - Track remediation progress
  - Understand offense context
"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("offense_id")
                .description("The ID of the offense to retrieve notes for")
                .minimum(0)
                .required()
            .string("filter")
                .description("Optional filter to restrict notes")
            .string("fields")
                .description("Optional comma-separated list of fields to return (e.g., 'id,note_text,create_time')")
            .integer("start")
                .description("Starting index for pagination (0-based)")
                .minimum(0)
                .default(0)
            .integer("limit")
                .description("Maximum number of notes to return")
                .minimum(1)
                .maximum(100)
                .default(50)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.SIEM_OFFENSE_NOTES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_offense_notes tool.

        Args:
            arguments: Must contain 'offense_id' (integer)
                      Optional: filter, fields, start, limit

        Returns:
            MCP response with notes array or error
        """
        offense_id = arguments.get("offense_id")

        if offense_id is None:
            return self.create_error_response("Error: offense_id is required")

        if not validate_offense_id(offense_id):
            return self.create_error_response(
                f"Error: Invalid offense_id '{offense_id}'. Must be a non-negative integer"
            )

        # Build query parameters
        params = {}
        if arguments.get("filter"):
            params["filter"] = arguments["filter"]
        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        # Build headers with pagination
        start = arguments.get("start", 0)
        limit = arguments.get("limit", 50)
        headers = build_headers(start=start, end=start + limit - 1)

        # Make API request
        response = await self.client.get(
            self.endpoint.format(offense_id=offense_id),
            params=params,
            headers=headers
        )

        response.raise_for_status()
        notes = response.json()
        result = {
            "offense_id": offense_id,
            "total_notes": len(notes),
            "notes": notes
        }

        return self.create_success_response(json.dumps(result, indent=2))
