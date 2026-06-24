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
List Asset Properties Tool

Lists available asset property types in QRadar.
"""
from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_range_header, parse_range_from_limit_offset


class ListAssetPropertiesTool(MCPTool):
    """Tool for listing available asset property types."""

    @property
    def name(self) -> str:
        return "list_asset_properties"

    @property
    def description(self) -> str:
        return """List available asset property types in QRadar.

Returns property types that can be used with assets, including:
  - Standard QRadar properties
  - Custom properties defined by administrators
  - Property data types and display settings

Use cases:
  - Discover available asset properties
  - Validate property names for queries
  - Understand asset model structure
  - Build dynamic asset filters

Note: Custom properties are organization-specific."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Filter properties (e.g., 'custom=true' for custom properties only)")
            .string("fields")
                .description("Specific fields to return (e.g., 'id,name,data_type')")
            .integer("limit")
                .description("Maximum number of properties to return (1-100)")
                .minimum(1)
                .maximum(100)
            .integer("offset")
                .description("Starting index for pagination (0-based)")
                .minimum(0)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_asset_properties tool.

        Args:
            arguments: Optional filter, fields, limit, offset parameters

        Returns:
            MCP response with asset property types or error
        """

        # Build query parameters
        params = {}

        if arguments.get("filter"):
            params["filter"] = arguments["filter"]

        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        # Build headers with Range if limit/offset provided
        limit = arguments.get("limit")
        offset = arguments.get("offset", 0)

        start, end = parse_range_from_limit_offset(limit, offset)
        headers = build_range_header(start, end)

        # Make API call
        response = await self.client.get('/asset_model/properties', params=params, headers=headers)
        response.raise_for_status()

        properties = response.json()

        return self.create_success_response(json.dumps(properties, indent=2))
