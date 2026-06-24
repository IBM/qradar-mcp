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
List DSM Event Mappings Tool

Retrieves a list of DSM event mappings from QRadar with optional filtering and pagination.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import (
    build_query_params,
    parse_range_from_limit_offset,
    build_headers
)


class ListDsmEventMappingsTool(MCPTool):
    """Tool for listing QRadar DSM event mappings."""

    @property
    def name(self) -> str:
        return "list_dsm_event_mappings"

    @property
    def description(self) -> str:
        return """Retrieve a list of DSM event mappings from QRadar.

DSM event mappings link raw log source event identifiers to QID records, enabling
QRadar to classify and categorize incoming events.

Each DSM event mapping contains:
  - id: The mapping ID
  - log_source_type_id: The log source type this mapping is associated with
  - log_source_event_id: The primary event identifier parsed from the raw event
  - log_source_event_category: The secondary event identifier parsed from the raw event
  - custom_event: Whether this is a user-provided mapping (true) or system-provided (false)
  - qid_record_id: The QID record this mapping resolves to
  - uuid: The UUID of the mapping

Examples:
  - List all mappings: (no parameters)
  - Filter by log source type: filter="log_source_type_id=123"
  - Filter by custom events: filter="custom_event=true"
  - Filter by QID record: filter="qid_record_id=64280"
  - Get first 50 mappings: limit=50, offset=0"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description('Optional filter expression. Examples: "log_source_type_id=123", "custom_event=true"')
            .string("fields")
                .description('Comma-separated list of fields to return. Examples: "id,log_source_type_id,qid_record_id"')
            .integer("limit")
                .description("Maximum number of mappings to return (default: 50, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(50)
            .integer("offset")
                .description("Number of mappings to skip for pagination (default: 0)")
                .minimum(0)
                .default(0)
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
        Execute the list_dsm_event_mappings tool.

        Args:
            arguments: Optional parameters for filtering and pagination

        Returns:
            MCP response with DSM event mappings data or error
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

        response = await self.client.get(
            '/data_classification/dsm_event_mappings',
            params=params,
            headers=headers
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
