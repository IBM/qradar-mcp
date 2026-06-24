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
List Cases Tool

Lists forensic investigation cases in QRadar.
Requires QRadar Incident Forensics module.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import build_range_header, parse_range_from_limit_offset


class ListCasesTool(MCPTool):
    """Tool for listing forensic investigation cases."""

    @property
    def name(self) -> str:
        return "list_cases"

    @property
    def description(self) -> str:
        return """List forensic investigation cases in QRadar.

Returns cases created for formal forensic investigations, including:
  - Case ID and name
  - Assigned users (FORENSICS role required)
  - Case status and metadata

Use cases:
  - Track active forensic investigations
  - Case management and coordination
  - Team workload visibility
  - Investigation status tracking

Requirements:
  - QRadar Incident Forensics module
  - FORENSICS role for case access

Note: Only returns cases accessible to the current user."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Filter cases (e.g., 'name contains \"incident\"')")
            .string("fields")
                .description("Specific fields to return (e.g., 'id,name,assigned_to')")
            .integer("limit")
                .description("Maximum number of cases to return (1-100)")
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
        Execute the list_cases tool.

        Args:
            arguments: Optional filter, fields, limit, offset parameters

        Returns:
            MCP response with cases list or error
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
        response = await self.client.get('/forensics/case_management/cases',
                            params=params, headers=headers)
        response.raise_for_status()

        cases = response.json()

        return self.create_success_response(json.dumps(cases, indent=2))
