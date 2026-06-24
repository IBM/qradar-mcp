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
List Building Blocks Tool

Lists building block rules from QRadar SIEM with filtering, and pagination.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_query_params, build_headers, parse_range_from_limit_offset


class ListBuildingBlocksTool(MCPTool):
    """Tool for listing QRadar building block rules with filtering and pagination."""

    @property
    def name(self) -> str:
        return "list_building_blocks"

    @property
    def description(self) -> str:
        return """List building block rules from QRadar SIEM with optional filtering and pagination.

Building blocks are reusable rule components that can be referenced by other rules and building blocks.

Examples:
  - List all building blocks: (no parameters)
  - Filter by enabled: filter="enabled=true"
  - Filter by type: filter="type='EVENT'"
  - Filter by origin: filter="origin='USER'"
  - Get first 20: limit=20, offset=0

Building block types:
  - EVENT: Individual event-based building blocks
  - FLOW: Network flow-based building blocks
  - COMMON: Shared building blocks
  - OFFENSE: Offense-generating building blocks

Building block origins:
  - SYSTEM: Built-in QRadar building blocks
  - OVERRIDE: Modified system building blocks
  - USER: Custom user-created building blocks"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional AQL-style filter expression. Examples: \"enabled=true\", "
                           "\"type='EVENT'\", \"origin='USER'\"")
            .string("fields")
                .description("Optional comma-separated list of fields to include. "
                           "Examples: \"id,name,type\", \"id,enabled,owner\"")
            .integer("limit")
                .description("Maximum number of building blocks to return (default: 50, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(50)
            .integer("offset")
                .description("Number of building blocks to skip for pagination (default: 0)")
                .minimum(0)
                .default(0)
            .boolean("format_output")
                .description("Format output as human-readable table (default: false)")
                .default(False)
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
        Execute the list_building_blocks tool.

        Args:
            arguments: Optional 'filter', 'fields', 'limit', 'offset', 'format_output'

        Returns:
            MCP response with building blocks data or error
        """

        # Build request parameters
        params, headers = self._build_request_params(arguments)

        # Make API request
        response = await self.client.get('/analytics/building_blocks', params=params, headers=headers)
        response.raise_for_status()

        building_blocks = response.json()

        # Format output
        format_output = arguments.get("format_output", True)
        if format_output:
            formatted_output = self._format_building_blocks(building_blocks)
            return self.create_success_response(formatted_output)

        return self.create_success_response(json.dumps(building_blocks, indent=2))

    def _build_request_params(self, arguments: Dict[str, Any]) -> tuple:
        """Build query parameters and headers from arguments."""
        filter_expr = arguments.get("filter")
        fields_str = arguments.get("fields")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        # Build query parameters
        fields_list = [f.strip() for f in fields_str.split(",")] if fields_str else None
        params = build_query_params(
            filter_expr=filter_expr,
            sort_fields=None,
            fields=fields_list
        )

        # Build headers with Range for pagination
        start, end = parse_range_from_limit_offset(limit, offset)
        headers = build_headers(start=start, end=end)

        return params, headers

    def _format_building_blocks(self, building_blocks: list) -> str:
        """
        Format building blocks list for display.

        Args:
            building_blocks: List of building block dictionaries

        Returns:
            Formatted string representation
        """
        if not building_blocks:
            return "No building blocks found"

        lines = []
        lines.append("=" * 80)
        lines.append(f"Building Blocks ({len(building_blocks)} found)")
        lines.append("=" * 80)

        for bb in building_blocks:
            lines.append(self._format_single_building_block(bb))

        return "\n".join(lines)

    def _format_single_building_block(self, bb: Dict[str, Any]) -> str:
        """Format a single building block."""
        lines = []

        # Header
        lines.append(f"\nBuilding Block ID: {bb.get('id')}")
        lines.append(f"Name: {bb.get('name', 'N/A')}")

        # Basic info
        bb_type = bb.get('type', 'N/A')
        origin = bb.get('origin', 'N/A')
        lines.append(f"Type: {bb_type} | Origin: {origin}")

        enabled = bb.get('enabled', False)
        status = "✓ Enabled" if enabled else "✗ Disabled"
        lines.append(f"Status: {status}")

        owner = bb.get('owner')
        if owner:
            lines.append(f"Owner: {owner}")

        # Capacity metrics
        self._add_capacity_metrics(lines, bb)

        # Identifiers
        self._add_identifiers(lines, bb)

        # Timestamps
        self._add_timestamps(lines, bb)

        lines.append("-" * 80)

        return "\n".join(lines)

    def _add_capacity_metrics(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add capacity metrics to formatted output."""
        avg_capacity = bb.get('average_capacity')
        base_capacity = bb.get('base_capacity')

        if avg_capacity is not None or base_capacity is not None:
            capacity_parts = []
            if avg_capacity is not None:
                capacity_parts.append(f"Avg: {avg_capacity} EPS")
            if base_capacity is not None:
                capacity_parts.append(f"Base: {base_capacity} EPS")
            lines.append(f"Capacity: {', '.join(capacity_parts)}")

    def _add_identifiers(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add identifiers to formatted output."""
        identifier = bb.get('identifier')
        if identifier:
            lines.append(f"Identifier: {identifier}")

        linked_identifier = bb.get('linked_rule_identifier')
        if linked_identifier:
            lines.append(f"Linked Rule: {linked_identifier}")

    def _add_timestamps(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add timestamps to formatted output."""
        creation_date = bb.get('creation_date')
        modification_date = bb.get('modification_date')

        if creation_date or modification_date:
            timestamp_parts = []
            if creation_date:
                timestamp_parts.append(f"Created: {creation_date}")
            if modification_date:
                timestamp_parts.append(f"Modified: {modification_date}")
            lines.append(f"Timestamps: {', '.join(timestamp_parts)}")
