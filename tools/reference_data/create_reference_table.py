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
Create Reference Table Tool

Creates a new reference data table in QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class CreateReferenceTable(MCPTool):
    """Tool for creating a new QRadar reference table."""

    @property
    def name(self) -> str:
        return "create_reference_table"

    @property
    def description(self) -> str:
        return """Create a new reference data table in QRadar SIEM.

Use cases:
  - Create IP × Port service tables
  - Build user × asset access matrices
  - Establish multi-dimensional IOC tracking
  - Store 2D threat intelligence data

Required parameters:
  - name: Unique name for the table
  - element_type: Default type for values (IP, ALN, NUM, PORT, ALNIC, DATE, CIDR)

Optional parameters:
  - outer_key_label: Label for outer keys (e.g., "IP Address")
  - key_name_types: Array defining inner key names and types
    Example: [{"key_name": "port", "element_type": "PORT"}]
  - description: Human-readable description
  - timeout_type: UNKNOWN, FIRST_SEEN, or LAST_SEEN
  - time_to_live: TTL interval (e.g., "1 month", "5 minutes")

Element types:
  - IP: IPv4/IPv6 addresses
  - ALN: Alphanumeric strings
  - ALNIC: Alphanumeric case-insensitive
  - NUM: Numeric values
  - PORT: Port numbers
  - DATE: Date/time values (milliseconds since epoch)
  - CIDR: CIDR notation networks"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("name")
                .description("Unique name for the reference table")
                .required()
            .string("element_type")
                .description("Default type for values: IP, ALN, ALNIC, NUM, PORT, DATE, CIDR")
                .enum(["IP", "ALN", "ALNIC", "NUM", "PORT", "DATE", "CIDR"])
                .required()
            .string("outer_key_label")
                .description("Optional label for outer keys (e.g., 'IP Address')")
            .string("key_name_types")
                .description("Optional JSON array defining inner keys: "
                           "[{\"key_name\": \"port\", \"element_type\": \"PORT\"}]")
            .string("description")
                .description("Optional description of the reference table")
            .string("timeout_type")
                .description("Expiry type: UNKNOWN, FIRST_SEEN, or LAST_SEEN")
                .enum(["UNKNOWN", "FIRST_SEEN", "LAST_SEEN"])
            .string("time_to_live")
                .description("Time to live interval (e.g., '1 month', '5 minutes')")
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_TABLES

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the create_reference_table tool.

        Args:
            arguments: Must contain 'name' and 'element_type', optional other parameters

        Returns:
            MCP response with created reference table data or error
        """
        name = arguments.get("name")
        element_type = arguments.get("element_type")

        if not name:
            return self.create_error_response("Error: name is required")
        if not element_type:
            return self.create_error_response("Error: element_type is required")


        # Build request parameters
        params = self._build_params(arguments)

        # Make API request
        response = await self.client.post(
            self.endpoint,
            params=params
        )
        response.raise_for_status()
        table_data = response.json()

        formatted_output = json.dumps(table_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "name": arguments["name"],
            "element_type": arguments["element_type"]
        }

        # Add optional fields
        optional_fields = [
            "outer_key_label",
            "key_name_types",
            "description",
            "timeout_type",
            "time_to_live",
            "fields"
        ]

        for field in optional_fields:
            if field in arguments and arguments[field] is not None:
                params[field] = arguments[field]

        return params
