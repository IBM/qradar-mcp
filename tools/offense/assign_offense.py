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
Assign Offense Tool

Assigns a QRadar offense to a user.
"""

from typing import Dict, Any, Optional
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints
from qradar_mcp.utils.validators import validate_offense_id


class AssignOffenseTool(MCPTool):
    """Tool for assigning a QRadar offense to a user."""

    @property
    def name(self) -> str:
        return "assign_offense"

    @property
    def description(self) -> str:
        return """Assign a QRadar offense to a user. Use this tool to change offense ownership for triage and investigation.
"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("offense_id")
                .description("The ID of the offense to assign")
                .minimum(0)
                .required()
            .string("assigned_to")
                .description("Username to assign the offense to")
                .required()
            .string("fields")
                .description("Comma-separated list of fields to return in response")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.SIEM_OFFENSE

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the assign_offense tool.

        Args:
            arguments: Dictionary containing offense_id, assigned_to,
                and optional fields

        Returns:
            MCP response with updated offense data or error
        """
        validation_result = self._validate_arguments(arguments)
        if validation_result:
            return validation_result

        offense_id = arguments["offense_id"]
        params = self._build_request_params(arguments)
        updated_offense = await self._update_offense(offense_id, params)

        return self.create_success_response(json.dumps(updated_offense, indent=2))

    def _validate_arguments(
        self, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Validate input arguments. Returns error response if invalid."""
        offense_id = arguments.get("offense_id")
        assigned_to = arguments.get("assigned_to")

        if offense_id is None:
            return self.create_error_response("offense_id is required")

        if not validate_offense_id(offense_id):
            return self.create_error_response(f"Invalid offense_id: {offense_id}")

        if not assigned_to:
            return self.create_error_response("assigned_to is required")

        return None

    def _build_request_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "assigned_to": arguments["assigned_to"]
        }

        if arguments.get("fields") is not None:
            params["fields"] = arguments["fields"]

        return params

    async def _update_offense(
        self, offense_id: int, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update the offense via QRadar API."""
        response = await self.client.post(
            api_path=self.endpoint.format(offense_id=offense_id),
            params=params
        )
        response.raise_for_status()
        return response.json()
