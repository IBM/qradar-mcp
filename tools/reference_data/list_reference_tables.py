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
List Reference Tables Tool

Lists reference data tables from QRadar SIEM with filtering, sorting, and pagination.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params, build_headers, parse_range_from_limit_offset
from qradar_mcp.utils.formatters import format_reference_sets_table
from qradar_mcp.tools import endpoints


class ListReferenceTables(MCPTool):
    """Tool for listing QRadar reference data tables."""

    @property
    def name(self) -> str:
        return "list_reference_tables"

    @property
    def description(self) -> str:
        return """List reference data tables from QRadar SIEM with optional filtering, sorting, and pagination.

Reference tables store two-dimensional data such as IP-to-port service mappings, user-to-asset access matrices, or other multi-key enrichment data.

=== FIELDS REFERENCE ===

collection_id: Number
creation_time: Number
description: String
element_type: String
key_label: String
key_name_types: Object
  key_name_types(String): String
name: String
namespace: String
number_of_elements: Number
time_to_live: String
timeout_type: String

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional AQL-style filter expression.")
            .string("sort")
                .description("Optional sort expression.")
            .integer("limit")
                .description("Maximum number of tables to return (default: 50, max: 10000)")
                .minimum(1)
                .maximum(10000)
            .integer("offset")
                .description("Number of tables to skip for pagination (default: 0)")
                .minimum(0)
            .string("fields")
                .description("Optional comma-separated list of fields to return.")
            .boolean("format_output")
                .description("Format output as human-readable table (default: false)")
                .default(False)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_TABLES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_reference_tables tool.

        Args:
            arguments: Optional filter, sort, limit, offset, fields, format_output

        Returns:
            MCP response with reference tables list or error
        """

        # Build request parameters
        params = self._build_params(arguments)
        headers = self._build_headers(arguments)

        # Make API request
        response = await self.client.get(
            self.endpoint,
            headers=headers,
            params=params
        )
        response.raise_for_status()
        tables_data = response.json()

        # Format and return response
        return self._format_response(tables_data, arguments.get("format_output", True))

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build query parameters from arguments."""
        sort_expr = arguments.get("sort")
        fields_str = arguments.get("fields")

        return build_query_params(
            filter_expr=arguments.get("filter"),
            sort_fields=[sort_expr] if sort_expr else None,
            fields=[f.strip() for f in fields_str.split(",")] if fields_str else None
        )

    def _build_headers(self, arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build headers with pagination from arguments."""
        start, end = parse_range_from_limit_offset(
            limit=arguments.get("limit", 50),
            offset=arguments.get("offset", 0)
        )
        return build_headers(start=start, end=end)

    def _format_response(self, tables_data: Any, format_output: bool) -> Dict[str, Any]:
        """Format the response based on format_output flag."""
        if format_output and isinstance(tables_data, list):
            return self.create_success_response(format_reference_sets_table(tables_data))
        return self.create_success_response(json.dumps(tables_data, indent=2))
