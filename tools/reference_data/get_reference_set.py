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
Get Reference Set Tool

Retrieves a specific reference data set by ID from QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetReferenceSetTool(MCPTool):
    """Tool for retrieving a specific QRadar reference set by ID."""

    @property
    def name(self) -> str:
        return "get_reference_set"

    @property
    def description(self) -> str:
        return """Get reference set metadata by ID from QRadar SIEM.

Returns the set name, description, entry type, entry count, TTL and
expiry settings, and namespace details."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("set_id")
                .description("The ID of the reference set to retrieve")
                .minimum(0)
                .required()
            .string("fields")
                .description("Optional comma-separated list of fields to return "
                           "(e.g., 'id,name,entry_type,number_of_entries')")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_COLLECTIONS_SET

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_reference_set tool.

        Args:
            arguments: Must contain 'set_id' (integer), optional 'fields' (string)

        Returns:
            MCP response with reference set data or error
        """
        set_id = arguments.get("set_id")

        if set_id is None:
            return self.create_error_response("Error: set_id is required")

        # Build query parameters
        params = self._build_params(arguments)

        # Make API request
        response = await self.client.get(
            self.endpoint.format(name=set_id),
            params=params
        )

        response.raise_for_status()
        set_data = response.json()

        # Format response
        formatted_output = json.dumps(set_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build query parameters for the API request."""
        params = {}

        # Add fields parameter if provided
        fields = arguments.get("fields")
        if fields:
            params["fields"] = fields

        return params
