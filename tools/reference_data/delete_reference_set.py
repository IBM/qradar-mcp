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
Delete Reference Set Tool

Deletes a reference data set from QRadar SIEM.
"""

from typing import Dict, Any
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class DeleteReferenceSetTool(MCPTool):
    """Tool for deleting QRadar reference sets."""

    @property
    def name(self) -> str:
        return "delete_reference_set"

    @property
    def description(self) -> str:
        return """Delete a reference data set from QRadar SIEM.

Use cases:
  - Remove obsolete threat intelligence lists
  - Clean up test or temporary sets
  - Remove sets that are no longer needed

WARNING: This operation is permanent and cannot be undone. All entries in the set will be deleted along with the set itself.

Note: You cannot delete a reference set that is currently being used by active rules or building blocks."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("set_id")
                .description("The ID of the reference set to delete")
                .minimum(0)
                .required()
            .build())

    @property
    def http_verb(self) -> str:
        return "DELETE"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_COLLECTIONS_SET

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the delete_reference_set tool.

        Args:
            arguments: Must contain 'set_id'

        Returns:
            MCP response confirming deletion or error
        """
        set_id = arguments.get("set_id")

        if set_id is None:
            return self.create_error_response("Error: set_id is required")


        # Make API request
        response = await self.client.delete(self.endpoint.format(name=set_id))

        response.raise_for_status()
        success_msg = f"Reference set {set_id} deleted successfully"
        return self.create_success_response(success_msg)
