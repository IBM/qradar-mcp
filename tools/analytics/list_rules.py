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
List Rules Tool

Retrieves a list of analytics rules from QRadar SIEM with optional filtering and pagination.
"""

from typing import Dict, Any, List
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import (
    build_query_params,
    parse_range_from_limit_offset,
    build_headers
)
from qradar_mcp.tools import endpoints


class ListRulesTool(MCPTool):
    """Tool for listing QRadar analytics rules with filtering and pagination."""

    @property
    def name(self) -> str:
        return "list_rules"

    @property
    def description(self) -> str:
        return """List analytics rules from QRadar SIEM with optional filtering and pagination.

Analytics rules are the core detection logic in QRadar that generate offenses and events.

Rule Types:
  - EVENT: Rules that process individual events
  - FLOW: Rules that process network flows
  - COMMON: Shared rules used by other rules
  - OFFENSE: Rules that create offenses

Rule Origins:
  - SYSTEM: Built-in QRadar rules
  - OVERRIDE: Modified system rules
  - USER: Custom user-created rules

=== FIELDS REFERENCE ===

average_capacity: Number
base_capacity: Number
base_host_id: Number
capacity_timestamp: Number
creation_date: Number
enabled: Boolean
id: Number
identifier: String
linked_rule_identifier: String
modification_date: Number
name: String
origin: String
owner: String
type: String

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional filter expression.")
            .string("fields")
                .description("Optional comma-separated list of fields to include.")
            .integer("limit")
                .description("Maximum number of rules to return (default: 10, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(10)
            .integer("offset")
                .description("Number of rules to skip for pagination (default: 0)")
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
    def endpoint(self) -> str:
        return endpoints.ANALYTICS_RULES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_rules tool.

        Args:
            arguments: Optional parameters for filtering, sorting, and pagination

        Returns:
            MCP response with rules data or error
        """
        # Extract and prepare parameters
        params, headers = self._prepare_request_params(arguments)

        # Make API request
        rules = await self._fetch_rules(params, headers)

        # Format and return response
        format_output = arguments.get("format_output", True)
        if format_output:
            formatted_output = self._format_rules(rules)
            return self.create_success_response(formatted_output)

        return self.create_success_response(json.dumps(rules, indent=2))

    def _prepare_request_params(self, arguments: Dict[str, Any]) -> tuple:
        """
        Prepare request parameters and headers.

        Args:
            arguments: Tool arguments

        Returns:
            Tuple of (params dict, headers dict)
        """
        filter_expr = arguments.get("filter")
        fields_str = arguments.get("fields")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        # Build query parameters
        fields_list = [f.strip() for f in fields_str.split(",")] if fields_str else None
        params = build_query_params(
            filter_expr=filter_expr,
            fields=fields_list
        )

        # Build Range header for pagination
        start, end = parse_range_from_limit_offset(limit, offset)
        headers = build_headers(start=start, end=end)

        return params, headers

    async def _fetch_rules(self, params: Dict[str, Any], headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Fetch rules from QRadar API.

        Args:
            params: Query parameters
            headers: Request headers

        Returns:
            List of rule dictionaries
        """
        response = await self.client.get(
            self.endpoint,
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def _format_rules(self, rules: List[Dict[str, Any]]) -> str:
        """
        Format rules as human-readable text.

        Args:
            rules: List of rule dictionaries

        Returns:
            Formatted string representation
        """
        if not rules:
            return "No rules found"

        output_lines = [
            f"Found {len(rules)} rule(s)\n",
            "=" * 80
        ]

        for rule in rules:
            output_lines.extend(self._format_single_rule(rule))
            output_lines.append("-" * 80)

        return "\n".join(output_lines)

    def _format_single_rule(self, rule: Dict[str, Any]) -> List[str]:
        """
        Format a single rule entry.

        Args:
            rule: Rule dictionary

        Returns:
            List of formatted lines
        """
        lines = [
            f"\nRule ID: {rule.get('id', 'N/A')}",
            f"Name: {rule.get('name', 'N/A')}"
        ]

        # Type and origin
        rule_type = rule.get('type', 'N/A')
        origin = rule.get('origin', 'N/A')
        lines.append(f"Type: {rule_type} | Origin: {origin}")

        # Status
        enabled = rule.get('enabled', False)
        status_str = "✓ Enabled" if enabled else "✗ Disabled"
        lines.append(f"Status: {status_str}")

        # Owner
        owner = rule.get('owner')
        if owner:
            lines.append(f"Owner: {owner}")

        # Capacity metrics
        self._add_capacity_metrics(lines, rule)

        # Identifiers
        self._add_identifiers(lines, rule)

        # Timestamps
        self._add_timestamps(lines, rule)

        return lines

    def _add_capacity_metrics(self, lines: List[str], rule: Dict[str, Any]) -> None:
        """Add capacity metrics if available."""
        average_capacity = rule.get('average_capacity')
        base_capacity = rule.get('base_capacity')

        if average_capacity is not None or base_capacity is not None:
            capacity_parts = []
            if average_capacity is not None:
                capacity_parts.append(f"Avg: {average_capacity} EPS")
            if base_capacity is not None:
                capacity_parts.append(f"Base: {base_capacity} EPS")
            if capacity_parts:
                lines.append(f"Capacity: {', '.join(capacity_parts)}")

    def _add_identifiers(self, lines: List[str], rule: Dict[str, Any]) -> None:
        """Add rule identifiers if available."""
        identifier = rule.get('identifier')
        if identifier:
            lines.append(f"Identifier: {identifier}")

        linked_identifier = rule.get('linked_rule_identifier')
        if linked_identifier:
            lines.append(f"Linked Rule: {linked_identifier}")

    def _add_timestamps(self, lines: List[str], rule: Dict[str, Any]) -> None:
        """Add timestamp information if available."""
        creation_date = rule.get('creation_date')
        modification_date = rule.get('modification_date')

        if creation_date:
            lines.append(f"Created: {creation_date}")
        if modification_date:
            lines.append(f"Modified: {modification_date}")
