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
List Offense Closing Reasons Tool

Retrieves valid offense closing reasons from QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class ListOffenseClosingReasonsTool(MCPTool):
    """Tool for listing valid offense closing reasons."""

    @property
    def name(self) -> str:
        return "list_offense_closing_reasons"

    @property
    def description(self) -> str:
        return """List valid offense closing reasons.

CRITICAL: Use this tool to get valid closing_reason_id values before calling
update_offense to close an offense.

Use cases:
  - Get valid closing reason IDs for offense closure workflow
  - Display available closing reasons to analysts
  - Filter out deleted or reserved reasons
  - Audit available closing reasons

By default, excludes deleted and reserved closing reasons (most common use case).
Use include_deleted=true or include_reserved=true to see all reasons.

Note: Deleted and reserved closing reasons cannot be used to close offenses."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .boolean("include_reserved")
                .description("Include reserved closing reasons (default: false). "
                           "Reserved reasons cannot be used to close offenses.")
            .boolean("include_deleted")
                .description("Include deleted closing reasons (default: false). "
                           "Deleted reasons cannot be used to close offenses.")
            .string("filter")
                .description("Optional AQL filter expression to restrict results")
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
        Execute the list_offense_closing_reasons tool.

        Args:
            arguments: Dict containing optional parameters:
                - include_reserved: Include reserved reasons (default: false)
                - include_deleted: Include deleted reasons (default: false)
                - filter: AQL filter expression
                - fields: Field selection

        Returns:
            MCP response with closing reasons list or error
        """

        # Build query parameters
        params = {}

        # Boolean flags
        if arguments.get("include_reserved"):
            params["include_reserved"] = "true"

        if arguments.get("include_deleted"):
            params["include_deleted"] = "true"

        # Optional filter
        if arguments.get("filter"):
            params["filter"] = arguments["filter"]

        # Optional field selection
        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        response = await self.client.get('/siem/offense_closing_reasons', params=params)
        response.raise_for_status()

        closing_reasons = response.json()

        return self.create_success_response(json.dumps(closing_reasons, indent=2))
