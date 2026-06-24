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
List Users Tool

Lists QRadar users with access control information.
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


class ListUsersTool(MCPTool):
    """Tool for listing QRadar users."""

    @property
    def name(self) -> str:
        return "list_users"

    @property
    def description(self) -> str:
        return """List QRadar users with access control information.

Retrieves deployed user accounts including username, email, role, security profile,
tenant, and authentication settings. Access control applies: ADMIN users see all
users, SAASADMIN users see non-admin users, other users see only themselves.

Use cases:
  - User auditing and access reviews
  - Compliance reporting and documentation
  - Security analysis of authentication settings
  - User management and role verification
  - Identifying inactive or flagged users

Example:
  list_users()
  list_users(current_user=True)
  list_users(filter='tenant_id=1', sort='+username')
  list_users(fields="username,email,user_role_id", limit=50)

Note: Sensitive fields like passwords are always returned as null. Access control
is enforced based on caller's capabilities (ADMIN, SAASADMIN, or regular user)."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .boolean("current_user")
                .description("Return only the current user's information (default: false)")
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .string("filter")
                .description("Optional filter expression (e.g., 'tenant_id=1')")
            .string("sort")
                .description("Optional sort expression (e.g., '+username,-email')")
            .integer("limit")
                .description("Maximum number of users to return (1-100)")
                .minimum(1)
                .maximum(100)
            .integer("offset")
                .description("Number of users to skip for pagination")
                .minimum(0)
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
        Execute the list_users tool.

        Args:
            arguments: Optional parameters for filtering, sorting, pagination

        Returns:
            MCP response with user list or error
        """

        # Build query parameters
        fields = arguments.get("fields")
        params = build_query_params(
            fields=fields.split(",") if fields else None,
            filter_expr=arguments.get("filter")
        )

        # Add current_user parameter if specified
        if arguments.get("current_user") is not None:
            params["current_user"] = str(arguments.get("current_user")).lower()

        # Add sort parameter if specified
        if arguments.get("sort"):
            params["sort"] = arguments.get("sort")

        # Build headers with Range for pagination
        headers = {}
        if arguments.get("limit") is not None or arguments.get("offset") is not None:
            start, end = parse_range_from_limit_offset(
                arguments.get("limit"), arguments.get("offset"))
            headers = build_headers(start=start, end=end)

        # Make API call
        response = await self.client.get('/config/access/users', params=params, headers=headers)
        response.raise_for_status()

        users = response.json()

        return self.create_success_response(json.dumps(users, indent=2))
