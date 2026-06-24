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
Get High Level Category Tool

Retrieves a single high level event category by ID from QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class GetHighLevelCategoryTool(MCPTool):
    """Tool for retrieving a single QRadar high level event category by ID."""

    @property
    def name(self) -> str:
        return "get_high_level_category"

    @property
    def description(self) -> str:
        return """Retrieve a high level event category by ID from QRadar.

High level categories are top-level groupings used to classify events in QRadar.
Each low level category belongs to a high level category.

Returns:
  - id: The category ID (e.g., 19000)
  - name: The category name (e.g., "Audit")
  - description: A description of the category"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("high_level_category_id")
                .description("The ID of the high level category to retrieve (must be a positive integer)")
                .minimum(1)
                .required()
            .string("fields")
                .description('Optional comma-separated list of fields to return. Examples: "id,name,description"')
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
        Execute the get_high_level_category tool.

        Args:
            arguments: Must contain 'high_level_category_id' (integer)

        Returns:
            MCP response with high level category data or error
        """
        high_level_category_id = arguments.get("high_level_category_id")
        fields = arguments.get("fields")

        if high_level_category_id is None:
            return self.create_error_response("Error: high_level_category_id is required")

        params = {}
        if fields:
            params['fields'] = fields

        response = await self.client.get(
            f'/data_classification/high_level_categories/{int(high_level_category_id)}',
            params=params if params else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
