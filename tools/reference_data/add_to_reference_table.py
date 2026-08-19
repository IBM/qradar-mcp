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
Add to Reference Table Tool

Adds or updates a cell in a reference data table.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class AddToReferenceTable(MCPTool):
    """Tool for adding or updating cells in a QRadar reference table."""

    @property
    def name(self) -> str:
        return "add_to_reference_table"

    @property
    def description(self) -> str:
        return """Add or update a cell in a reference data table.

Use cases:
  - Add IP × Port → Service mapping
  - Update user × asset access level
  - Enrich multi-dimensional IOC data
  - Maintain 2D threat intelligence

Required parameters:
  - name: Table name
  - outer_key: Outer key (e.g., IP address)
  - inner_key: Inner key (e.g., port number)
  - value: Cell value

Optional parameters:
  - namespace: SHARED or TENANT (default: SHARED)
  - domain_id: Domain ID for multi-tenancy
  - source: Source of the data
  - fields: Response field selection

Note: If the cell already exists, its value will be updated."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("name")
                .description("The name of the reference table")
                .required()
            .string("outer_key")
                .description("The outer key (e.g., IP address)")
                .required()
            .string("inner_key")
                .description("The inner key (e.g., port number)")
                .required()
            .string("value")
                .description("The value to store in the cell")
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
        return endpoints.REFERENCE_DATA_TABLE

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the add_to_reference_table tool.

        Args:
            arguments: Must contain 'name', 'outer_key', 'inner_key', 'value', optional others

        Returns:
            MCP response with updated reference table metadata or error
        """
        name = arguments.get("name")
        outer_key = arguments.get("outer_key")
        inner_key = arguments.get("inner_key")
        value = arguments.get("value")

        if not name:
            return self.create_error_response("Error: name is required")
        if not outer_key:
            return self.create_error_response("Error: outer_key is required")
        if not inner_key:
            return self.create_error_response("Error: inner_key is required")
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
        table_data = response.json()

        formatted_output = json.dumps(table_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "outer_key": arguments["outer_key"],
            "inner_key": arguments["inner_key"],
            "value": arguments["value"]
        }

        # Add optional fields
        optional_fields = ["namespace", "domain_id", "source", "fields"]

        for field in optional_fields:
            if field in arguments and arguments[field] is not None:
                params[field] = arguments[field]

        return params
