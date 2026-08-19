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
Get Offense Tool

Retrieves offense details from QRadar SIEM by offense ID.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetOffenseTool(MCPTool):
    """Tool for retrieving QRadar offense details by ID."""

    @property
    def name(self) -> str:
        return "get_offense"

    @property
    def description(self) -> str:
        return "Get offense data by ID from QRadar SIEM"

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("offense_id")
                .description("The ID of the offense to retrieve")
                .minimum(0)
                .required()
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.SIEM_OFFENSE

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_offense tool.

        Args:
            arguments: Must contain 'offense_id' (integer)

        Returns:
            MCP response with offense data or error
        """
        offense_id = arguments.get("offense_id")

        if offense_id is None:
            return self.create_error_response("Error: offense_id is required")

        response = await self.client.get(self.endpoint.format(offense_id=int(offense_id)))
        response.raise_for_status()

        offense_data = response.json()

        return self.create_success_response(json.dumps(offense_data, indent=2))
