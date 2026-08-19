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
Get Reference Table Tool

Retrieves a specific reference data table by name from QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params, build_headers, parse_range_from_limit_offset
from qradar_mcp.tools import endpoints


class GetReferenceTable(MCPTool):
    """Tool for retrieving a specific QRadar reference table by name."""

    @property
    def name(self) -> str:
        return "get_reference_table"

    @property
    def description(self) -> str:
        return """Get reference table metadata and 2D data by name from QRadar SIEM.

Returns table configuration, element and key types, element count,
expiry settings, and stored outer-key and inner-key data."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("name")
                .description("The name of the reference table to retrieve")
                .required()
            .string("namespace")
                .description("Optional namespace: SHARED or TENANT (default: SHARED)")
                .enum(["SHARED", "TENANT"])
            .string("filter")
                .description("Optional AQL filter to restrict table entries")
            .integer("limit")
                .description("Maximum number of entries to return (default: 50)")
                .minimum(1)
                .maximum(10000)
            .integer("offset")
                .description("Number of entries to skip for pagination (default: 0)")
                .minimum(0)
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_TABLE

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_reference_table tool.

        Args:
            arguments: Must contain 'name', optional namespace, filter, limit, offset, fields

        Returns:
            MCP response with reference table data or error
        """
        name = arguments.get("name")

        if not name:
            return self.create_error_response("Error: name is required")

        # Build request parameters
        params = self._build_params(arguments)
        headers = self._build_headers(arguments)

        # Make API request
        response = await self.client.get(
            self.endpoint.format(name=name),
            headers=headers,
            params=params
        )
        response.raise_for_status()
        table_data = response.json()

        # Format response
        formatted_output = json.dumps(table_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build query parameters from arguments."""
        params = build_query_params(
            filter_expr=arguments.get("filter"),
            fields=[f.strip() for f in arguments["fields"].split(",")] if arguments.get("fields") else None
        )

        # Add namespace if provided
        if arguments.get("namespace"):
            params["namespace"] = arguments["namespace"]

        return params

    def _build_headers(self, arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build headers with pagination from arguments."""
        if arguments.get("limit") is not None or arguments.get("offset") is not None:
            start, end = parse_range_from_limit_offset(
                limit=arguments.get("limit", 50),
                offset=arguments.get("offset", 0)
            )
            return build_headers(start=start, end=end)
        return {}
