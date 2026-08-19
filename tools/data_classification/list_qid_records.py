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
from qradar_mcp.tools import endpoints
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
and severity levels. Each event received by QRadar is resolved to a QID record."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional filter expression.")
            .string("fields")
                .description("Optional comma-separated list of fields to return.")
            .integer("limit")
                .description("Maximum number of QID records to return (default: 10, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(10)
            .integer("offset")
                .description("Number of QID records to skip for pagination (default: 0)")
                .minimum(0)
                .default(0)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.DATA_CLASS_QID_RECORDS

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
            self.endpoint,
            params=params,
            headers=headers
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
