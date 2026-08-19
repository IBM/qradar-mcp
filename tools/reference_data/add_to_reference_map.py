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
Add to Reference Map Tool

Adds or updates a key-value pair in a reference data map.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class AddToReferenceMap(MCPTool):
    """Tool for adding or updating entries in a QRadar reference map."""

    @property
    def name(self) -> str:
        return "add_to_reference_map"

    @property
    def description(self) -> str:
        return """Add or update a key-value pair in a reference data map.

Use cases:
  - Add IP-to-country mapping
  - Update threat actor attribute
  - Enrich IOC with context
  - Maintain threat intelligence data

Required parameters:
  - name: Map name
  - key: The key to add/update
  - value: The value to associate with the key

Optional parameters:
  - namespace: SHARED or TENANT (default: SHARED)
  - domain_id: Domain ID for multi-tenancy
  - source: Source of the data
  - fields: Response field selection

Note: If the key already exists, its value will be updated."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("name")
                .description("The name of the reference map")
                .required()
            .string("key")
                .description("The key to add or update")
                .required()
            .string("value")
                .description("The value to associate with the key")
                .required()
            .string("namespace")
                .description("Optional namespace: SHARED or TENANT")
                .enum(["SHARED", "TENANT"])
            .integer("domain_id")
                .description("Optional domain ID for multi-tenancy")
                .minimum(0)
            .string("source")
                .description("Optional source of the data")
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_MAP

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the add_to_reference_map tool.

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
        response = await self.client.post(
            self.endpoint.format(name=name),
            params=params
        )
        response.raise_for_status()
        map_data = response.json()

        formatted_output = json.dumps(map_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "key": arguments["key"],
            "value": arguments["value"]
        }

        # Add optional fields
        optional_fields = ["namespace", "domain_id", "source", "fields"]

        for field in optional_fields:
            if field in arguments and arguments[field] is not None:
                params[field] = arguments[field]

        return params
