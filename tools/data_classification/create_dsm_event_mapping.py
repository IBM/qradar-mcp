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
Create DSM Event Mapping Tool

Creates a new custom DSM event mapping in QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class CreateDsmEventMappingTool(MCPTool):
    """Tool for creating a new custom QRadar DSM event mapping."""

    @property
    def name(self) -> str:
        return "create_dsm_event_mapping"

    @property
    def description(self) -> str:
        return """Create a new custom DSM event mapping in QRadar.

DSM event mappings link raw log source event identifiers to QID records so that
QRadar can classify incoming events. This creates a user-provided (custom) mapping.

Required parameters:
  - log_source_type_id: The ID of the log source type
  - log_source_event_id: The primary event identifier to match (e.g., event type string)
  - log_source_event_category: The secondary event identifier to match
  - qid_record_id: The QID record ID to map the event to

Note: A 409 error is returned if a mapping with the same log_source_type_id,
log_source_event_id and log_source_event_category already exists."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("log_source_type_id")
                .description("The ID of the log source type this mapping is associated with")
                .minimum(0)
                .required()
            .string("log_source_event_id")
                .description("The primary identifying value parsed from an event (e.g., event type string)")
                .required()
            .string("log_source_event_category")
                .description("The secondary identifying value parsed from an event")
                .required()
            .integer("qid_record_id")
                .description("The ID of the QID record to map matching events to")
                .minimum(0)
                .required()
            .string("fields")
                .description("Optional comma-separated list of fields to return in the response")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def approval_required(self) -> bool:
        """POST operation - requires approval."""
        return True

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the create_dsm_event_mapping tool.

        Args:
            arguments: Must contain log_source_type_id, log_source_event_id,
                       log_source_event_category, and qid_record_id

        Returns:
            MCP response with the newly created DSM event mapping or error
        """
        log_source_type_id = arguments.get("log_source_type_id")
        log_source_event_id = arguments.get("log_source_event_id")
        log_source_event_category = arguments.get("log_source_event_category")
        qid_record_id = arguments.get("qid_record_id")

        if log_source_type_id is None:
            return self.create_error_response("Error: log_source_type_id is required")
        if not log_source_event_id:
            return self.create_error_response("Error: log_source_event_id is required")
        if log_source_event_category is None:
            return self.create_error_response("Error: log_source_event_category is required")
        if qid_record_id is None:
            return self.create_error_response("Error: qid_record_id is required")

        body = {
            "log_source_type_id": int(log_source_type_id),
            "log_source_event_id": log_source_event_id,
            "log_source_event_category": log_source_event_category,
            "qid_record_id": int(qid_record_id)
        }

        headers = {}
        fields = arguments.get("fields")
        if fields:
            headers["fields"] = fields

        response = await self.client.post(
            '/data_classification/dsm_event_mappings',
            data=body,
            headers=headers if headers else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
