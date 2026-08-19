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
Get Building Block Tool

Retrieves a specific building block rule from QRadar SIEM by ID.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetBuildingBlockTool(MCPTool):
    """Tool for retrieving a specific QRadar building block rule by ID."""

    @property
    def name(self) -> str:
        return "get_building_block"

    @property
    def description(self) -> str:
        return """Get building block rule details by ID from QRadar SIEM.

Building blocks are reusable rule components that can be referenced by other rules and building blocks.

Use cases:
  - View building block configuration and properties
  - Check building block status (enabled/disabled)
  - Review building block capacity metrics
  - Understand building block type and origin
  - Verify building block identifiers and relationships

Returns detailed information including:
  - Building block ID, name, and description
  - Type (EVENT, FLOW, COMMON, OFFENSE)
  - Origin (SYSTEM, OVERRIDE, USER)
  - Enabled status
  - Owner information
  - Capacity metrics (base, average, timestamp)
  - Identifiers (building block ID, linked rule ID)
  - Timestamps (creation, modification)"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("building_block_id")
                .description("The ID of the building block rule to retrieve")
                .minimum(0)
                .required()
            .string("fields")
                .description("Optional comma-separated list of fields to return "
                           "(e.g., 'id,name,type,enabled')")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.ANALYTICS_BUILDING_BLOCK

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_building_block tool.

        Args:
            arguments: Must contain 'building_block_id' (integer), optional 'fields' (string)

        Returns:
            MCP response with building block data or error
        """
        building_block_id = arguments.get("building_block_id")
        fields_str = arguments.get("fields")

        if building_block_id is None:
            return self.create_error_response("Error: building_block_id is required")

        # Build query parameters
        params = {}
        if fields_str:
            params['fields'] = fields_str

        # Make API request
        response = await self.client.get(self.endpoint.format(building_block_id=building_block_id),
                            params=params)
        response.raise_for_status()

        building_block_data = response.json()

        # Format the response
        formatted_output = self._format_building_block(building_block_data)

        return self.create_success_response(formatted_output)

    def _format_building_block(self, bb: Dict[str, Any]) -> str:
        """
        Format building block data for display.

        Args:
            bb: Building block data dictionary

        Returns:
            Formatted string representation
        """
        lines = []

        # Header
        self._add_header(lines, bb)

        # Basic information
        self._add_basic_info(lines, bb)

        # Capacity metrics
        self._add_capacity_info(lines, bb)

        # Identifiers
        self._add_identifiers(lines, bb)

        # Timestamps
        self._add_timestamps(lines, bb)

        lines.append("\n" + "=" * 80)

        # Add JSON representation
        lines.append("\nFull JSON:")
        lines.append(json.dumps(bb, indent=2))

        return "\n".join(lines)

    def _add_header(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add header section to formatted output."""
        lines.append("=" * 80)
        lines.append(f"Building Block ID: {bb.get('id')}")
        lines.append(f"Name: {bb.get('name', 'N/A')}")
        lines.append("=" * 80)

    def _add_basic_info(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add basic information section to formatted output."""
        bb_type = bb.get('type', 'N/A')
        origin = bb.get('origin', 'N/A')
        lines.append(f"\nType: {bb_type} | Origin: {origin}")

        enabled = bb.get('enabled', False)
        status = "✓ Enabled" if enabled else "✗ Disabled"
        lines.append(f"Status: {status}")

        owner = bb.get('owner')
        if owner:
            lines.append(f"Owner: {owner}")

    def _add_capacity_info(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add capacity metrics section to formatted output."""
        avg_capacity = bb.get('average_capacity')
        base_capacity = bb.get('base_capacity')

        if avg_capacity is not None or base_capacity is not None:
            lines.append("\nCapacity:")
            if avg_capacity is not None:
                lines.append(f"  Avg: {avg_capacity} EPS")
            if base_capacity is not None:
                lines.append(f"  Base: {base_capacity} EPS")

            base_host_id = bb.get('base_host_id')
            if base_host_id is not None:
                lines.append(f"  Base Host ID: {base_host_id}")

            capacity_ts = bb.get('capacity_timestamp')
            if capacity_ts:
                lines.append(f"  Last Updated: {capacity_ts}")

    def _add_identifiers(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add identifiers section to formatted output."""
        identifier = bb.get('identifier')
        if identifier:
            lines.append(f"\nIdentifier: {identifier}")

        linked_identifier = bb.get('linked_rule_identifier')
        if linked_identifier:
            lines.append(f"Linked Rule: {linked_identifier}")

    def _add_timestamps(self, lines: list, bb: Dict[str, Any]) -> None:
        """Add timestamps section to formatted output."""
        creation_date = bb.get('creation_date')
        modification_date = bb.get('modification_date')

        if creation_date or modification_date:
            lines.append("\nTimestamps:")
            if creation_date:
                lines.append(f"  Created: {creation_date}")
            if modification_date:
                lines.append(f"  Modified: {modification_date}")
