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
Get Low Level Category Tool

Retrieves a single low level event category by ID from QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class GetLowLevelCategoryTool(MCPTool):
    """Tool for retrieving a single QRadar low level event category by ID."""

    @property
    def name(self) -> str:
        return "get_low_level_category"

    @property
    def description(self) -> str:
        return """Retrieve a low level event category by ID from QRadar.

Low level categories are specific event sub-types that belong to a high level category.
They are used to classify events at a granular level in QRadar.

Returns:
  - id: The category ID (e.g., 19001)
  - name: The category name (e.g., "General Audit Event")
  - description: A description of the category
  - severity: The default severity (0-10) for events in this category
  - high_level_category_id: The parent high level category ID"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("low_level_category_id")
                .description("The ID of the low level category to retrieve (must be a positive integer)")
                .minimum(1)
                .required()
            .string("fields")
                .description('Optional comma-separated list of fields to return. Examples: "id,name,severity,high_level_category_id"')
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
        Execute the get_low_level_category tool.

        Args:
            arguments: Must contain 'low_level_category_id' (integer)

        Returns:
            MCP response with low level category data or error
        """
        low_level_category_id = arguments.get("low_level_category_id")
        fields = arguments.get("fields")

        if low_level_category_id is None:
            return self.create_error_response("Error: low_level_category_id is required")

        params = {}
        if fields:
            params['fields'] = fields

        response = await self.client.get(
            f'/data_classification/low_level_categories/{int(low_level_category_id)}',
            params=params if params else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
