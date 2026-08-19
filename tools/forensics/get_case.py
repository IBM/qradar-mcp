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
Get Case Tool

Retrieves forensic case details by ID.
Requires QRadar Incident Forensics module.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetCaseTool(MCPTool):
    """Tool for retrieving forensic case details by ID."""

    @property
    def name(self) -> str:
        return "get_case"

    @property
    def description(self) -> str:
        return """Get detailed information about a forensic case.

Returns case details including:
  - Case ID and name
  - Assigned users
  - Case metadata

Use cases:
  - Retrieve case details
  - Verify case assignments
  - Get investigation context

Requirements:
  - QRadar Incident Forensics module
  - FORENSICS role or case assignment

Note: Only accessible if user has FORENSICS role or is assigned to the case."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("case_id")
                .description("The ID of the case to retrieve")
                .minimum(1)
                .required()
            .string("fields")
                .description("Specific fields to return (e.g., 'id,name,assigned_to')")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.FORENSICS_CASE

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_case tool.

        Args:
            arguments: Must contain 'case_id' (integer), optional 'fields'

        Returns:
            MCP response with case details or error
        """
        case_id = arguments.get("case_id")

        if case_id is None:
            return self.create_error_response("Error: case_id is required")

        # Build query parameters
        params = {}

        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        # Make API call
        response = await self.client.get(self.endpoint.format(case_id=int(case_id)),
                            params=params)
        response.raise_for_status()

        case_data = response.json()

        return self.create_success_response(json.dumps(case_data, indent=2))
