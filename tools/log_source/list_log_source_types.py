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
List Log Source Types Tool

Lists available log source types in QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints
from qradar_mcp.utils.parameters import build_range_header, parse_range_from_limit_offset


class ListLogSourceTypesTool(MCPTool):
    """Tool for listing available log source types."""

    @property
    def name(self) -> str:
        return "list_log_source_types"

    @property
    def description(self) -> str:
        return """List available log source types in QRadar.

Returns log source types that can be configured, including:
  - Type ID and name
  - Internal vs. external types
  - Supported languages
  - Protocol types
  - Version information

Use cases:
  - Discover supported log sources
  - Validate log source configurations
  - Troubleshoot collection issues
  - Plan log source deployments
  - Verify DSM availability

Note: Internal types (System Notification, SIM Audit, etc.) cannot have log sources created.

=== FIELDS REFERENCE ===

custom: Boolean
default_protocol_id: Number
id: Number
internal: Boolean
latest_version: String
log_source_extension_id: Number
name: String
protocol_types: Array<Object>
  protocol_types(documented): Boolean
  protocol_types(protocol_id): Number
supported_language_ids: Array<Number>
uuid: String
version: String

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional filter expression.")
            .string("fields")
                .description("Optional comma-separated list of fields to return.")
            .integer("limit")
                .description("Maximum number of types to return (default: 10)")
                .minimum(1)
                .default(10)
            .integer("offset")
                .description("Starting index for pagination (0-based)")
                .minimum(0)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.CONFIG_LOG_SOURCE_TYPES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_log_source_types tool.

        Args:
            arguments: Optional filter, fields, limit, offset parameters

        Returns:
            MCP response with log source types or error
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
        response = await self.client.get(self.endpoint,
                            params=params, headers=headers)
        response.raise_for_status()

        log_source_types = response.json()

        return self.create_success_response(json.dumps(log_source_types, indent=2))
