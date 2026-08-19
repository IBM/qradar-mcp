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
Create Reference Map Tool

Creates a new reference data map in QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class CreateReferenceMap(MCPTool):
    """Tool for creating a new QRadar reference map."""

    @property
    def name(self) -> str:
        return "create_reference_map"

    @property
    def description(self) -> str:
        return """Create a new reference data map in QRadar SIEM.

Use cases:
  - Create IP geolocation maps
  - Build threat actor profile maps
  - Establish IOC context mappings
  - Store key-value threat intelligence

Required parameters:
  - name: Unique name for the map
  - element_type: Type of values (IP, ALN, NUM, PORT, ALNIC, DATE, CIDR)

Optional parameters:
  - key_label: Label describing the keys (e.g., "IP Address")
  - value_label: Label describing the values (e.g., "Country")
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
                .description("Unique name for the reference map")
                .required()
            .string("element_type")
                .description("Type of values: IP, ALN, ALNIC, NUM, PORT, DATE, CIDR")
                .enum(["IP", "ALN", "ALNIC", "NUM", "PORT", "DATE", "CIDR"])
                .required()
            .string("key_label")
                .description("Optional label for keys (e.g., 'IP Address')")
            .string("value_label")
                .description("Optional label for values (e.g., 'Country')")
            .string("description")
                .description("Optional description of the reference map")
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
        return endpoints.REFERENCE_DATA_MAPS

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the create_reference_map tool.

        Args:
            arguments: Must contain 'name' and 'element_type', optional other parameters

        Returns:
            MCP response with created reference map data or error
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
        map_data = response.json()

        formatted_output = json.dumps(map_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "name": arguments["name"],
            "element_type": arguments["element_type"]
        }

        # Add optional fields
        optional_fields = [
            "key_label",
            "value_label",
            "description",
            "timeout_type",
            "time_to_live",
            "fields"
        ]

        for field in optional_fields:
            if field in arguments and arguments[field] is not None:
                params[field] = arguments[field]

        return params
