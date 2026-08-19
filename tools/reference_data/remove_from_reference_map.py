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
Remove from Reference Map Tool

Removes a specific key-value pair from a reference data map.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class RemoveFromReferenceMap(MCPTool):
    """Tool for removing entries from a QRadar reference map."""

    @property
    def name(self) -> str:
        return "remove_from_reference_map"

    @property
    def description(self) -> str:
        return """Remove a specific key-value pair from a reference data map.

Use cases:
  - Remove false positive from threat list
  - Delete outdated mapping
  - Clean up specific entries
  - Maintain data accuracy

Required parameters:
  - name: Map name
  - key: The key to remove
  - value: The value to remove

Optional parameters:
  - namespace: SHARED or TENANT (default: SHARED)
  - domain_id: Domain ID for multi-tenancy
  - fields: Response field selection

Note: Both key and value must match for removal."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("name")
                .description("The name of the reference map")
                .required()
            .string("key")
                .description("The key to remove")
                .required()
            .string("value")
                .description("The value to remove (must match existing value)")
                .required()
            .string("namespace")
                .description("Optional namespace: SHARED or TENANT")
                .enum(["SHARED", "TENANT"])
            .integer("domain_id")
                .description("Optional domain ID for multi-tenancy")
                .minimum(0)
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "DELETE"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_MAP_ENTRY

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the remove_from_reference_map tool.

        Args:
            arguments: Must contain 'name', 'key', 'value', optional other parameters

        Returns:
            MCP response with updated reference map metadata or error
        """
        name = arguments.get("name")
        key = arguments.get("key")
        value = arguments.get("value")

        if not name:
            return self.create_error_response("Error: name is required")
        if not key:
            return self.create_error_response("Error: key is required")
        if not value:
            return self.create_error_response("Error: value is required")

        # Build request parameters
        params = self._build_params(arguments)

        # Make API request
        response = await self.client.delete(
            self.endpoint.format(name=name, key=key),
            params=params
        )
        response.raise_for_status()
        map_data = response.json()

        formatted_output = json.dumps(map_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "value": arguments["value"]
        }

        # Add optional fields
        optional_fields = ["namespace", "domain_id", "fields"]

        for field in optional_fields:
            if field in arguments and arguments[field] is not None:
                params[field] = arguments[field]

        return params
