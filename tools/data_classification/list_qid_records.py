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
List QID Records Tool

Retrieves a list of QID records from QRadar with optional filtering and pagination.
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


class ListQidRecordsTool(MCPTool):
    """Tool for listing QRadar QID records."""

    @property
    def name(self) -> str:
        return "list_qid_records"

    @property
    def description(self) -> str:
        return """Retrieve a list of QID records from QRadar.

QID (QRadar Identifier) records define event types in QRadar, mapping to categories
and severity levels. Each event received by QRadar is resolved to a QID record.

Each QID record contains:
  - id: The QID record ID
  - qid: The numeric QRadar Identifier
  - name: The human-readable name of the event type
  - description: A description of the event type
  - severity: The severity level (0-10)
  - low_level_category_id: The low level category this QID belongs to
  - log_source_type_id: The log source type (null for most system QIDs)
  - uuid: The UUID of the QID record

Examples:
  - List all QID records: (no parameters)
  - Filter by name: filter="name LIKE '%portscan%'"
  - Filter by severity: filter="severity>=7"
  - Filter by category: filter="low_level_category_id=1008"
  - Get first 100 records: limit=100, offset=0"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description('Optional filter expression. Examples: "severity>=7", "low_level_category_id=1008", "name LIKE \'%scan%\'"')
            .string("fields")
                .description('Comma-separated list of fields to return. Examples: "id,qid,name,severity", "id,name,low_level_category_id"')
            .integer("limit")
                .description("Maximum number of QID records to return (default: 50, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(50)
            .integer("offset")
                .description("Number of QID records to skip for pagination (default: 0)")
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
        Execute the list_qid_records tool.

        Args:
            arguments: Optional parameters for filtering and pagination

        Returns:
            MCP response with QID records data or error
        """
        filter_expr = arguments.get("filter")
        fields_str = arguments.get("fields")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        fields_list = [f.strip() for f in fields_str.split(",")] if fields_str else None
        params = build_query_params(
            filter_expr=filter_expr,
            fields=fields_list
        )

        start, end = parse_range_from_limit_offset(limit, offset)
        headers = build_headers(start=start, end=end)

        response = await self.client.get(
            '/data_classification/qid_records',
            params=params,
            headers=headers
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
