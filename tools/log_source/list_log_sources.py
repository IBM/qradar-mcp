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
List Log Sources Tool

Retrieves a list of log sources from QRadar SIEM with optional filtering,
sorting, and pagination.
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


class ListLogSourcesTool(MCPTool):
    """Tool for listing QRadar log sources with filtering and pagination."""

    @property
    def name(self) -> str:
        return "list_log_sources"

    @property
    def description(self) -> str:
        return """List log sources from QRadar SIEM with optional filtering, sorting, and pagination.

Log sources are the systems that send event data to QRadar for processing and analysis.

Filterable Fields:
  - id, name, description (text fields)
  - type_id, protocol_type_id (numeric IDs)
  - enabled, internal, gateway, auto_discovered (boolean)
  - credibility (0-10)
  - average_eps (numeric, events per second)
  - last_event_time, creation_date, modified_date (epoch milliseconds)

Examples:
  - List all log sources: (no parameters)
  - Filter by name: filter="name LIKE 'firewall%'"
  - Filter by type: filter="type_id=42"
  - Filter by enabled status: filter="enabled=true"
  - Filter by credibility: filter="credibility >= 8"
  - Sort by name: sort="+name"
  - Get first 20 sources: limit=20
"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description('Optional AQL-style filter expression. Examples: "name LIKE \'firewall%\'", "enabled=true", "type_id=42"')
            .string("fields")
                .description('Comma-separated list of fields to include. Examples: "id,name,type_id", "id,name,enabled,status"')
            .string("sort")
                .description('Optional sort expression. Use +field for ascending, -field for descending. Examples: "+name", "-modified_date", "+type_id,-name"')
            .integer("limit")
                .description("Maximum number of log sources to return (default: 50, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(50)
            .integer("offset")
                .description("Number of log sources to skip for pagination (default: 0)")
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
        Execute the list_log_sources tool.

        Args:
            arguments: Optional parameters for filtering, sorting, and pagination

        Returns:
            MCP response with log source data or error
        """
        # Extract and prepare parameters
        params, headers = self._prepare_request_params(arguments)

        # Make API request
        log_sources = await self._fetch_log_sources(params, headers)

        # Format and return response
        format_output = arguments.get("format_output", True)
        if format_output:
            formatted_output = self._format_log_sources(log_sources)
            return self.create_success_response(formatted_output)

        return self.create_success_response(json.dumps(log_sources, indent=2))

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
        sort_expr = arguments.get("sort")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        # Build query parameters
        fields_list = [f.strip() for f in fields_str.split(",")] if fields_str else None
        params = build_query_params(
            filter_expr=filter_expr,
            sort_fields=[sort_expr] if sort_expr else None,
            fields=fields_list
        )

        # Build Range header for pagination
        start, end = parse_range_from_limit_offset(limit, offset)
        headers = build_headers(start=start, end=end)

        return params, headers

    async def _fetch_log_sources(self, params: Dict[str, Any], headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Fetch log sources from QRadar API.

        Args:
            params: Query parameters
            headers: Request headers

        Returns:
            List of log source dictionaries
        """
        response = await self.client.get(
            '/config/event_sources/log_source_management/log_sources',
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def _format_log_sources(self, log_sources: List[Dict[str, Any]]) -> str:
        """
        Format log sources as human-readable text.

        Args:
            log_sources: List of log source dictionaries

        Returns:
            Formatted string representation
        """
        if not log_sources:
            return "No log sources found"

        output_lines = [
            f"Found {len(log_sources)} log source(s)\n",
            "=" * 80
        ]

        for source in log_sources:
            output_lines.extend(self._format_single_log_source(source))
            output_lines.append("-" * 80)

        return "\n".join(output_lines)

    def _format_single_log_source(self, source: Dict[str, Any]) -> List[str]:
        """
        Format a single log source entry.

        Args:
            source: Log source dictionary

        Returns:
            List of formatted lines
        """
        lines = [
            f"\nLog Source ID: {source.get('id', 'N/A')}",
            f"Name: {source.get('name', 'N/A')}"
        ]

        # Add optional fields
        self._add_description(lines, source)
        self._add_type_info(lines, source)
        self._add_status_flags(lines, source)
        self._add_metrics(lines, source)
        self._add_status_details(lines, source)
        self._add_deployment_info(lines, source)

        return lines

    def _add_description(self, lines: List[str], source: Dict[str, Any]) -> None:
        """Add description if present."""
        description = source.get('description')
        if description:
            lines.append(f"Description: {description}")

    def _add_type_info(self, lines: List[str], source: Dict[str, Any]) -> None:
        """Add type and protocol information."""
        lines.extend([
            f"Type ID: {source.get('type_id', 'N/A')}",
            f"Protocol Type ID: {source.get('protocol_type_id', 'N/A')}"
        ])

    def _add_status_flags(self, lines: List[str], source: Dict[str, Any]) -> None:
        """Add status flags (enabled, gateway, internal)."""
        enabled = source.get('enabled', False)
        lines.append(f"Enabled: {'Yes' if enabled else 'No'}")

        if source.get('gateway', False):
            lines.append("Gateway: Yes")

        if source.get('internal', False):
            lines.append("Internal: Yes")

    def _add_metrics(self, lines: List[str], source: Dict[str, Any]) -> None:
        """Add metrics (credibility, EPS, last event time)."""
        credibility = source.get('credibility')
        if credibility is not None:
            lines.append(f"Credibility: {credibility}/10")

        average_eps = source.get('average_eps')
        if average_eps is not None:
            lines.append(f"Average EPS: {average_eps}")

        last_event_time = source.get('last_event_time')
        if last_event_time:
            lines.append(f"Last Event Time: {last_event_time}")

    def _add_status_details(self, lines: List[str], source: Dict[str, Any]) -> None:
        """Add detailed status information."""
        status = source.get('status')
        if not status:
            return

        status_str = status.get('status', 'N/A')
        lines.append(f"Status: {status_str}")

        messages = status.get('messages', [])
        if messages:
            lines.append("Status Messages:")
            for msg in messages[:3]:  # Show first 3 messages
                severity = msg.get('severity', 'INFO')
                text = msg.get('text', '')
                lines.append(f"  [{severity}] {text}")

    def _add_deployment_info(self, lines: List[str], source: Dict[str, Any]) -> None:
        """Add deployment-related information."""
        target_collector = source.get('target_event_collector_id')
        if target_collector:
            lines.append(f"Target Event Collector ID: {target_collector}")

        if source.get('requires_deploy', False):
            lines.append("⚠️  Requires Deploy: Yes")
