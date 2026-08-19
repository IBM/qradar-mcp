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
Get DSM Event Mapping Tool

Retrieves a single DSM event mapping by ID from QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetDsmEventMappingTool(MCPTool):
    """Tool for retrieving a single QRadar DSM event mapping by ID."""

    @property
    def name(self) -> str:
        return "get_dsm_event_mapping"

    @property
    def description(self) -> str:
        return """Retrieve a DSM event mapping by ID from QRadar.

A DSM event mapping links a raw log source event identifier to a QID record,
enabling QRadar to classify and categorize the incoming event.

Returns:
  - id: The mapping ID
  - log_source_type_id: The log source type this mapping is associated with
  - log_source_event_id: The primary event identifier parsed from the raw event
  - log_source_event_category: The secondary event identifier parsed from the raw event
  - custom_event: Whether this is a user-provided mapping (true) or system-provided (false)
  - qid_record_id: The QID record this mapping resolves to
  - uuid: The UUID of the mapping"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("dsm_event_mapping_id")
                .description("The ID of the DSM event mapping to retrieve")
                .minimum(0)
                .required()
            .string("fields")
                .description('Optional comma-separated list of fields to return. Examples: "id,log_source_type_id,qid_record_id"')
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.DATA_CLASS_DSM_EVENT_MAPPING

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_dsm_event_mapping tool.

        Args:
            arguments: Must contain 'dsm_event_mapping_id' (integer)

        Returns:
            MCP response with DSM event mapping data or error
        """
        dsm_event_mapping_id = arguments.get("dsm_event_mapping_id")
        fields = arguments.get("fields")

        if dsm_event_mapping_id is None:
            return self.create_error_response("Error: dsm_event_mapping_id is required")

        params = {}
        if fields:
            params['fields'] = fields

        response = await self.client.get(
            self.endpoint.format(dsm_event_mapping_id=int(dsm_event_mapping_id)),
            params=params if params else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
