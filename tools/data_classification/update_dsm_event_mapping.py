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
Update DSM Event Mapping Tool

Updates an existing custom DSM event mapping in QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class UpdateDsmEventMappingTool(MCPTool):
    """Tool for updating an existing custom QRadar DSM event mapping."""

    @property
    def name(self) -> str:
        return "update_dsm_event_mapping"

    @property
    def description(self) -> str:
        return """Update an existing custom DSM event mapping in QRadar.

Only user-provided (custom_event=true) DSM event mappings can be updated.
Currently only the qid_record_id field can be updated.

Required parameters:
  - dsm_event_mapping_id: The ID of the mapping to update
  - qid_record_id: The new QID record ID to map the event to"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("dsm_event_mapping_id")
                .description("The ID of the DSM event mapping to update. Get this from list_dsm_event_mappings or get_dsm_event_mapping")
                .minimum(0)
                .required()
            .integer("qid_record_id")
                .description("The new ID of the QID record to map matching events to. Get this from list_qid_records, get_qid_record, or get_qid_record_by_qid")
                .minimum(0)
                .required()
            .string("fields")
                .description("Optional comma-separated list of fields to return in the response")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.DATA_CLASS_DSM_EVENT_MAPPING

    @property
    def approval_required(self) -> bool:
        """POST (update) operation - requires approval."""
        return True

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the update_dsm_event_mapping tool.

        Args:
            arguments: Must contain 'dsm_event_mapping_id' and 'qid_record_id'

        Returns:
            MCP response with the updated DSM event mapping or error
        """
        dsm_event_mapping_id = arguments.get("dsm_event_mapping_id")
        qid_record_id = arguments.get("qid_record_id")

        if dsm_event_mapping_id is None:
            return self.create_error_response("Error: dsm_event_mapping_id is required")
        if qid_record_id is None:
            return self.create_error_response("Error: qid_record_id is required")

        body = {"qid_record_id": int(qid_record_id)}

        headers = {}
        fields = arguments.get("fields")
        if fields:
            headers["fields"] = fields

        response = await self.client.post(
            self.endpoint.format(dsm_event_mapping_id=int(dsm_event_mapping_id)),
            data=body,
            headers=headers if headers else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
