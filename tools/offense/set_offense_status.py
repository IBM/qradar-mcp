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
Set Offense Status Tool

Sets the status of a QRadar offense.
"""

from typing import Dict, Any, Optional
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints
from qradar_mcp.utils.validators import validate_offense_id


class SetOffenseStatusTool(MCPTool):
    """Tool for setting QRadar offense status."""

    @property
    def name(self) -> str:
        return "set_offense_status"

    @property
    def description(self) -> str:
        return """Set the status of a QRadar offense.

Use this to reopen, hide, or close an offense. When setting status to
CLOSED, provide a closing_reason_id from list_offense_closing_reasons.
"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("offense_id")
                .description("The ID of the offense to update")
                .minimum(0)
                .required()
            .string("status")
                .description("New status: OPEN, HIDDEN, or CLOSED")
                .enum(["OPEN", "HIDDEN", "CLOSED"])
                .required()
            .integer("closing_reason_id")
                .description("Closing reason ID from list_offense_closing_reasons (required when status=CLOSED)")
                .minimum(1)
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
        Execute the set_offense_status tool.

        Args:
            arguments: Dictionary containing offense_id, status,
                and optional closing_reason_id and fields

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
        status = arguments.get("status")
        closing_reason_id = arguments.get("closing_reason_id")

        if offense_id is None:
            return self.create_error_response("offense_id is required")

        if not validate_offense_id(offense_id):
            return self.create_error_response(f"Invalid offense_id: {offense_id}")

        if status is None:
            return self.create_error_response("status is required")

        if status == "CLOSED" and closing_reason_id is None:
            return self.create_error_response(
                "closing_reason_id is required when status is CLOSED"
            )

        return None

    def _build_request_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "status": arguments["status"]
        }

        if arguments.get("closing_reason_id") is not None:
            params["closing_reason_id"] = arguments["closing_reason_id"]

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
