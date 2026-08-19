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
List Low Level Categories Tool

Retrieves a list of low level event categories from QRadar.
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


class ListLowLevelCategoriesTool(MCPTool):
    """Tool for listing QRadar low level event categories."""

    @property
    def name(self) -> str:
        return "list_low_level_categories"

    @property
    def description(self) -> str:
        return """Retrieve a list of low level event categories from QRadar.

Low level categories are specific event sub-types that belong to a high level category.
They are used to classify events at a granular level in QRadar.

=== FIELDS REFERENCE ===

id: Number
name: String
description: String
high_level_category_id: Number
severity: Number

"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description('Optional filter expression.')
            .string("sort")
                .description('Optional sort expression.')
            .string("fields")
                .description('Comma-separated list of fields to return.')
            .integer("limit")
                .description("Maximum number of categories to return (default: 10, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(10)
            .integer("offset")
                .description("Number of categories to skip for pagination (default: 0)")
                .minimum(0)
                .default(0)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.DATA_CLASS_LOW_LEVEL_CATEGORIES

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_low_level_categories tool.

        Args:
            arguments: Optional parameters for filtering, sorting, and pagination

        Returns:
            MCP response with low level categories data or error
        """
        filter_expr = arguments.get("filter")
        fields_str = arguments.get("fields")
        sort_expr = arguments.get("sort")
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

        response = await self.client.get(
            self.endpoint,
            params=params,
            headers=headers
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
