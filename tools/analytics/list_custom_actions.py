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
List Custom Actions Tool

Lists all custom actions available in the QRadar deployment.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params, build_headers, parse_range_from_limit_offset
from qradar_mcp.tools import endpoints


class ListCustomActionsTool(MCPTool):
    """Tool for listing custom actions."""

    @property
    def name(self) -> str:
        return "list_custom_actions"

    @property
    def description(self) -> str:
        return """List all custom actions available in the QRadar deployment.

Custom actions enable automated responses to security events.

Use cases:
  - Discover available automated response actions
  - Identify actions for SOAR integration and orchestration
  - Understand automation capabilities in the deployment
  - Audit custom actions for compliance and security

=== FIELDS REFERENCE ===

description: String
id: Number
interpreter: Number
name: String
parameters: Array<Object>
  parameters(encrypted): Boolean
  parameters(name): String
  parameters(parameter_type): String
  parameters(value): String
script: Number

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("fields")
                .description("Comma-separated fields.")
            .string("filter")
                .description("Optional filter expression.")
            .integer("limit")
                .description("Maximum number of results to return (1-100)")
                .minimum(1)
                .maximum(100)
            .integer("offset")
                .description("Starting position for pagination (0-based)")
                .minimum(0)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.ANALYTICS_CUSTOM_ACTIONS

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_custom_actions tool.

        Args:
            arguments: Optional parameters:
                - fields: Comma-separated list of fields
                - filter: AQL-style filter expression
                - limit: Maximum results (1-100)
                - offset: Starting position

        Returns:
            MCP response with custom actions array or error
        """

        # Build query parameters
        fields = arguments.get("fields")
        params = build_query_params(
            fields=fields.split(",") if fields else None,
            filter_expr=arguments.get("filter")
        )

        # Build headers with pagination
        headers = {}
        if arguments.get("limit") is not None:
            start, end = parse_range_from_limit_offset(
                arguments.get("limit"),
                arguments.get("offset", 0)
            )
            headers = build_headers(start=start, end=end)

        # Make API call
        response = await self.client.get(self.endpoint,
                            params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        return self.create_success_response(json.dumps(data, indent=2))
