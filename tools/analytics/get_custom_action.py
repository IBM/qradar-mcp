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
Get Custom Action Tool

Retrieves detailed information about a specific custom action.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params
from qradar_mcp.tools import endpoints


class GetCustomActionTool(MCPTool):
    """Tool for retrieving custom action details."""

    @property
    def name(self) -> str:
        return "get_custom_action"

    @property
    def description(self) -> str:
        return """Retrieve detailed information about a specific custom action.

Use cases:
  - Review action configuration before execution
  - Verify required parameters are configured correctly
  - Extract action details for investigation runbooks
  - Troubleshoot action execution failures
  - Get parameter details for SOAR integration

Parameter types explained:
  - Fixed parameters: Static values (e.g., timeout=3600, api_endpoint="https://...")
  - Dynamic parameters: Values from events/flows (e.g., sourceip, username, file_hash)
  - Encrypted parameters: Sensitive values (e.g., API keys, passwords) - masked in response

Custom actions are triggered by:
  - Offense rules (execute when offense created)
  - Event rules (execute on specific event patterns)
  - Flow rules (execute on network flow patterns)
  - Manual execution (analyst triggers from UI)

Note: Returns 404 if action doesn't exist or user lacks permission.
Encrypted parameter values are masked (********) in the response."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("action_id")
                .description("ID of the custom action to retrieve")
                .minimum(1)
                .required()
            .string("fields")
                .description("Comma-separated fields (e.g., 'id,name,parameters')")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.ANALYTICS_CUSTOM_ACTION

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_custom_action tool.

        Args:
            arguments: Must contain:
                - action_id: ID of the custom action (required)
                - fields: Comma-separated fields (optional)

        Returns:
            MCP response with custom action details or error
        """
        action_id = arguments.get("action_id")

        if action_id is None:
            return self.create_error_response("Error: action_id is required")


        # Build query parameters
        fields = arguments.get("fields")
        params = build_query_params(
            fields=fields.split(",") if fields else None
        )

        # Make API call
        response = await self.client.get(self.endpoint.format(action_id=int(action_id)),
                            params=params)
        response.raise_for_status()

        data = response.json()

        return self.create_success_response(json.dumps(data, indent=2))
