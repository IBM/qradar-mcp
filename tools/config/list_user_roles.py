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
List User Roles Tool

Lists available QRadar user roles and their capabilities.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import (
    build_query_params,
    build_headers,
    parse_range_from_limit_offset
)
from qradar_mcp.tools import endpoints


class ListUserRolesTool(MCPTool):
    """Tool for listing QRadar user roles."""

    @property
    def name(self) -> str:
        return "list_user_roles"

    @property
    def description(self) -> str:
        return """List available QRadar user roles and their capabilities.

Use this to review role names, IDs, and capabilities. Access control is
applied: ADMIN users see all roles, SAASADMIN users see non-admin roles, and
other users see only their own role unless current_user_role is used.

=== FIELDS REFERENCE ===

capabilities: Array<Object>
  capabilities(application_id): Number
  capabilities(description): String
  capabilities(name): String
id: Number
name: String

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .boolean("current_user_role")
                .description("Return only the current user's role (default: false)")
            .string("contains")
                .description("Filter roles containing this capability")
                .enum(["ADMIN", "SAAS_ADMIN", "ADMIN_MANAGER", "LOCAL_ONLY"])
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .string("filter")
                .description("Optional filter expression")
            .integer("limit")
                .description("Maximum number of roles to return (1-100)")
                .minimum(1)
                .maximum(100)
            .integer("offset")
                .description("Number of roles to skip for pagination")
                .minimum(0)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.CONFIG_ACCESS_USER_ROLES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_user_roles tool.

        Args:
            arguments: Optional parameters for filtering, pagination

        Returns:
            MCP response with user role list or error
        """

        # Build query parameters
        fields = arguments.get("fields")
        params = build_query_params(
            fields=fields.split(",") if fields else None,
            filter_expr=arguments.get("filter")
        )

        # Add current_user_role parameter if specified
        if arguments.get("current_user_role") is not None:
            params["current_user_role"] = str(arguments.get("current_user_role")).lower()

        # Add contains parameter if specified
        if arguments.get("contains"):
            params["contains"] = arguments.get("contains")

        # Build headers with Range for pagination
        headers = {}
        if arguments.get("limit") is not None or arguments.get("offset") is not None:
            start, end = parse_range_from_limit_offset(
                arguments.get("limit"), arguments.get("offset"))
            headers = build_headers(start=start, end=end)

        # Make API call
        response = await self.client.get(self.endpoint, params=params, headers=headers)
        response.raise_for_status()

        roles = response.json()

        return self.create_success_response(json.dumps(roles, indent=2))
