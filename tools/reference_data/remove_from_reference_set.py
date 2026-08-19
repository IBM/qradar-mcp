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
Remove from Reference Set Tool

Removes entries from a QRadar reference data set by entry ID.
"""

from typing import Dict, Any
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class RemoveFromReferenceSetTool(MCPTool):
    """Tool for removing entries from QRadar reference data sets."""

    @property
    def name(self) -> str:
        return "remove_from_reference_set"

    @property
    def description(self) -> str:
        return """Remove an entry from a QRadar reference data set by entry ID.

Use cases:
  - Remove false positive IOCs
  - Clean up expired or invalid entries
  - Remove entries that are no longer relevant
  - Maintain reference set accuracy

Note: This operation is permanent and cannot be undone. The entry ID can be obtained
from list_reference_sets (with entry details) or when adding entries to a set."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("entry_id")
                .description("The ID of the entry to remove from the reference set. Get this from list_reference_sets or a prior add_to_reference_set result")
                .minimum(0)
                .required()
            .build())

    @property
    def http_verb(self) -> str:
        return "DELETE"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_COLLECTIONS_SET_ENTRY

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the remove_from_reference_set tool.

        Args:
            arguments: Must contain 'entry_id' (integer)

        Returns:
            MCP response with success message or error
        """
        entry_id = arguments.get("entry_id")

        if entry_id is None:
            return self.create_error_response("Error: entry_id is required")

        response = await self.client.delete(self.endpoint.format(entry_id=entry_id))

        response.raise_for_status()
        message = f"Entry {entry_id} removed successfully from reference set"
        return self.create_success_response(message)
