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
Get Log Source Tool

Retrieves log source details from QRadar SIEM by log source ID.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetLogSourceTool(MCPTool):
    """Tool for retrieving QRadar log source details by ID."""

    @property
    def name(self) -> str:
        return "get_log_source"

    @property
    def description(self) -> str:
        return """Get log source details by ID from QRadar SIEM.

Returns configuration, type and protocol details, health and status
fields, event collection statistics, and deployment information."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("log_source_id")
                .description("The ID of the log source to retrieve")
                .minimum(0)
                .required()
            .string("fields")
                .description('Optional comma-separated list of fields to return (e.g., "id,name,enabled,status")')
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.CONFIG_LOG_SOURCE

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_log_source tool.

        Args:
            arguments: Must contain 'log_source_id' (integer), optional 'fields' (string)

        Returns:
            MCP response with log source data or error
        """
        log_source_id = arguments.get("log_source_id")
        fields = arguments.get("fields")

        if log_source_id is None:
            return self.create_error_response("Error: log_source_id is required")

        # Build query parameters
        params = {}
        if fields:
            params['fields'] = fields

        # Make API request
        response = await self.client.get(
            self.endpoint.format(log_source_id=int(log_source_id)),
            params=params if params else None
        )
        response.raise_for_status()

        log_source_data = response.json()
        return self.create_success_response(json.dumps(log_source_data, indent=2))
