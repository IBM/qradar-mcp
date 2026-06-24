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
Get Rule Tool

Retrieves a specific analytics rule from QRadar SIEM by ID.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class GetRuleTool(MCPTool):
    """Tool for retrieving a specific QRadar analytics rule by ID."""

    @property
    def name(self) -> str:
        return "get_rule"

    @property
    def description(self) -> str:
        return """Get analytics rule details by ID from QRadar SIEM.

Use cases:
  - View rule configuration and properties
  - Check rule status (enabled/disabled)
  - Review rule capacity metrics
  - Understand rule type and origin
  - Verify rule identifiers and relationships

Returns detailed information including:
  - Rule ID, name, and description
  - Type (EVENT, FLOW, COMMON, OFFENSE)
  - Origin (SYSTEM, OVERRIDE, USER)
  - Enabled status
  - Owner information
  - Capacity metrics (base, average, timestamp)
  - Identifiers (rule ID, linked rule ID)
  - Timestamps (creation, modification)"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("rule_id")
                .description("The ID of the analytics rule to retrieve")
                .minimum(0)
                .required()
            .string("fields")
                .description("Optional comma-separated list of fields to return (e.g., 'id,name,type,enabled')")
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
        Execute the get_rule tool.

        Args:
            arguments: Must contain 'rule_id' (integer), optional 'fields' (string)

        Returns:
            MCP response with rule data or error
        """
        rule_id = arguments.get("rule_id")
        fields_str = arguments.get("fields")

        if rule_id is None:
            return self.create_error_response("Error: rule_id is required")


        # Build query parameters
        params = {}
        if fields_str:
            params['fields'] = fields_str

        # Make API request
        response = await self.client.get(f'/analytics/rules/{rule_id}', params=params)
        response.raise_for_status()

        rule_data = response.json()

        # Format the response
        formatted_output = self._format_rule(rule_data)

        return self.create_success_response(formatted_output)

    def _format_rule(self, rule: Dict[str, Any]) -> str:
        """
        Format rule data for display.

        Args:
            rule: Rule data dictionary

        Returns:
            Formatted string representation
        """
        lines = []

        # Header
        self._add_header(lines, rule)

        # Basic information
        self._add_basic_info(lines, rule)

        # Capacity metrics
        self._add_capacity_info(lines, rule)

        # Identifiers
        self._add_identifiers(lines, rule)

        # Timestamps
        self._add_timestamps(lines, rule)

        lines.append("\n" + "=" * 80)

        # Add JSON representation
        lines.append("\nFull JSON:")
        lines.append(json.dumps(rule, indent=2))

        return "\n".join(lines)

    def _add_header(self, lines: list, rule: Dict[str, Any]) -> None:
        """Add header section to formatted output."""
        lines.append("=" * 80)
        lines.append(f"Rule ID: {rule.get('id')}")
        lines.append(f"Name: {rule.get('name', 'N/A')}")
        lines.append("=" * 80)

    def _add_basic_info(self, lines: list, rule: Dict[str, Any]) -> None:
        """Add basic information section to formatted output."""
        rule_type = rule.get('type', 'N/A')
        origin = rule.get('origin', 'N/A')
        lines.append(f"\nType: {rule_type} | Origin: {origin}")

        enabled = rule.get('enabled', False)
        status = "✓ Enabled" if enabled else "✗ Disabled"
        lines.append(f"Status: {status}")

        owner = rule.get('owner')
        if owner:
            lines.append(f"Owner: {owner}")

    def _add_capacity_info(self, lines: list, rule: Dict[str, Any]) -> None:
        """Add capacity metrics section to formatted output."""
        avg_capacity = rule.get('average_capacity')
        base_capacity = rule.get('base_capacity')

        if avg_capacity is not None or base_capacity is not None:
            lines.append("\nCapacity:")
            if avg_capacity is not None:
                lines.append(f"  Avg: {avg_capacity} EPS")
            if base_capacity is not None:
                lines.append(f"  Base: {base_capacity} EPS")

            base_host_id = rule.get('base_host_id')
            if base_host_id is not None:
                lines.append(f"  Base Host ID: {base_host_id}")

            capacity_ts = rule.get('capacity_timestamp')
            if capacity_ts:
                lines.append(f"  Last Updated: {capacity_ts}")

    def _add_identifiers(self, lines: list, rule: Dict[str, Any]) -> None:
        """Add identifiers section to formatted output."""
        identifier = rule.get('identifier')
        if identifier:
            lines.append(f"\nIdentifier: {identifier}")

        linked_identifier = rule.get('linked_rule_identifier')
        if linked_identifier:
            lines.append(f"Linked Rule: {linked_identifier}")

    def _add_timestamps(self, lines: list, rule: Dict[str, Any]) -> None:
        """Add timestamps section to formatted output."""
        creation_date = rule.get('creation_date')
        modification_date = rule.get('modification_date')

        if creation_date or modification_date:
            lines.append("\nTimestamps:")
            if creation_date:
                lines.append(f"  Created: {creation_date}")
            if modification_date:
                lines.append(f"  Modified: {modification_date}")
