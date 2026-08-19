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
List Offenses Tool

Retrieves a list of offenses from QRadar SIEM with filtering, sorting, and pagination.
"""

from typing import Dict, Any, Optional, List
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints
from qradar_mcp.utils.parameters import (
    build_query_params,
    build_headers,
    parse_range_from_limit_offset
)
from qradar_mcp.utils.formatters import format_offense_list
from qradar_mcp.utils.validators import validate_filter_expression, validate_sort_expression


class ListOffensesTool(MCPTool):
    """Tool for listing QRadar offenses with filtering and pagination."""

    @property
    def name(self) -> str:
        return "list_offenses"

    @property
    def description(self) -> str:
        return """List offenses from QRadar SIEM with optional filtering, sorting, and pagination.

An offense is a correlated security incident created when one or more rules fire.
Use this tool to triage active threats, review recent activity, or scope an investigation.

Offense Status:
  - OPEN: Active, unresolved offenses
  - CLOSED: Resolved offenses
  - HIDDEN: Suppressed offenses

Examples:
  - List 50 open offenses: filter with `status="OPEN"`, use `limit=50` and ` offset=0`
  - High severity open offenses: filter="status="OPEN" and severity > 7"
  - Sort by most recent offenses: sort with -start_time
  - Sort offenses severity descending: sort with -severity

=== FIELDS REFERENCE ===

last_persisted_time: Number
username_count: Number
description: String
rules: Array<Object>
  rules(id): Number
  rules(type): String
event_count: Number
flow_count: Number
assigned_to: String
security_category_count: Number
follow_up: Boolean
source_address_ids: Array<Number>
source_count: Number
inactive: Boolean
protected: Boolean
closing_user: String
destination_networks: Array<String>
source_network: String
category_count: Number
close_time: Number
remote_destination_count: Number
start_time: Number
magnitude: Number
last_updated_time: Number
credibility: Number
id: Number
categories: Array<String>
severity: Number
policy_category_count: Number
log_sources: Array<Object>
  log_sources(type_name): String
  log_sources(type_id): Number
  log_sources(name): String
  log_sources(id): Number
closing_reason_id: Number
device_count: Number
first_persisted_time: Number
offense_type: Number
relevance: Number
domain_id: Number
offense_source: String
local_destination_address_ids: Array<Number>
local_destination_count: Number
status: String

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description('Optional filter expression."')
            .string("sort")
                .description('Sort expression.')
            .string("fields")
                .description('Comma-separated list of fields to include.')
            .integer("limit")
                .description("Maximum number of offenses to return (default: 10, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(10)
            .integer("offset")
                .description("Number of offenses to skip for pagination (default: 0)")
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
        return endpoints.SIEM_OFFENSES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_offenses tool.

        Args:
            arguments: Dictionary containing optional parameters

        Returns:
            MCP response with offense list or error
        """
        # Validate and extract parameters
        validation_result = self._validate_arguments(arguments)
        if validation_result:
            return validation_result

        params, headers = self._build_request_params(arguments)

        # Make API request
        offenses, total_count = await self._fetch_offenses(params, headers)

        # Format and return response
        return self._format_response(offenses, total_count, arguments.get("format_output", True))

    def _validate_arguments(self, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate input arguments. Returns error response if invalid, None if valid."""
        filter_expr = arguments.get("filter")
        if filter_expr:
            is_valid, error_msg = validate_filter_expression(filter_expr)
            if not is_valid:
                return self.create_error_response(f"Invalid filter expression: {error_msg}")

        sort_expr = arguments.get("sort")
        if sort_expr:
            is_valid, error_msg = validate_sort_expression(sort_expr)
            if not is_valid:
                return self.create_error_response(f"Invalid sort expression: {error_msg}")

        return None

    def _build_request_params(self, arguments: Dict[str, Any]) -> tuple:
        """Build query parameters and headers for API request."""
        filter_expr = arguments.get("filter")
        sort_expr = arguments.get("sort")
        fields_str = arguments.get("fields")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        fields_list = [f.strip() for f in fields_str.split(",")] if fields_str else None
        params = build_query_params(
            filter_expr=filter_expr,
            sort_fields=[sort_expr] if sort_expr else None,
            fields=fields_list
        )

        start, end = parse_range_from_limit_offset(limit, offset)
        headers = build_headers(start=start, end=end)

        return params, headers

    async def _fetch_offenses(self, params: Dict[str, Any], headers: Dict[str, str]) -> tuple:
        """Fetch offenses from QRadar API."""
        response = await self.client.get(
            api_path=self.endpoint,
            params=params,
            headers=headers
        )
        response.raise_for_status()

        offenses = response.json()
        total_count = self._extract_total_count(response)

        return offenses, total_count

    def _extract_total_count(self, response) -> Optional[int]:
        """Extract total count from Content-Range header."""
        content_range = response.headers.get('Content-Range')
        if content_range:
            return int(content_range.split('/')[-1])
        return None

    def _format_response(self, offenses: List[Dict[str, Any]],
                        total_count: Optional[int], format_output: bool) -> Dict[str, Any]:
        """Format the response based on format_output flag."""
        if format_output:
            formatted_output = format_offense_list(offenses, total_count)
            return self.create_success_response(formatted_output)

        # Return raw JSON
        result = {
            "offenses": offenses,
            "count": len(offenses)
        }
        if total_count:
            result["total_count"] = total_count
        return self.create_success_response(json.dumps(result, indent=2))
