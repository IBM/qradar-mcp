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
List High Level Categories Tool

Retrieves a list of high level event categories from QRadar.
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


class ListHighLevelCategoriesTool(MCPTool):
    """Tool for listing QRadar high level event categories."""

    @property
    def name(self) -> str:
        return "list_high_level_categories"

    @property
    def description(self) -> str:
        return """Retrieve a list of high level event categories from QRadar.

High level categories are the top-level groupings used to classify events in QRadar.
Each low level category belongs to a high level category.

Each high level category contains:
  - id: The category ID (e.g., 19000 for Audit, 20000 for Risk)
  - name: The category name (e.g., "Audit", "Risk", "Recon")
  - description: A description of the category

Examples:
  - List all categories: (no parameters)
  - Filter by name: filter="name='Audit'"
  - Sort by name: sort="+name"
  - Sort by ID: sort="+id"

Note: Sorting is only supported on "id" or "name" fields."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description('Optional filter expression. Examples: "name=\'Audit\'", "id=19000"')
            .string("sort")
                .description('Sort expression. Sorting only supported on "id" or "name". Use +field for ascending, -field for descending.')
            .string("fields")
                .description('Comma-separated list of fields to return. Examples: "id,name", "id,name,description"')
            .integer("limit")
                .description("Maximum number of categories to return (default: 50, max: 10000)")
                .minimum(1)
                .maximum(10000)
                .default(50)
            .integer("offset")
                .description("Number of categories to skip for pagination (default: 0)")
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
        Execute the list_high_level_categories tool.

        Args:
            arguments: Optional parameters for filtering, sorting, and pagination

        Returns:
            MCP response with high level categories data or error
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
            '/data_classification/high_level_categories',
            params=params,
            headers=headers
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
