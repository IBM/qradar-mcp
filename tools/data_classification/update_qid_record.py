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
Update QID Record Tool

Updates an existing QID record in QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class UpdateQidRecordTool(MCPTool):
    """Tool for updating an existing QRadar QID record."""

    @property
    def name(self) -> str:
        return "update_qid_record"

    @property
    def description(self) -> str:
        return """Update an existing QID record in QRadar.

Only user-created QID records can be updated. System-provided QIDs will return a 409 error.

Required parameters:
  - qid_record_id: The ID of the QID record to update

Updatable fields (at least one must be provided):
  - name: New name for the event type
  - description: New description
  - severity: New severity (0-10)
  - low_level_category_id: New low level category ID"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("qid_record_id")
                .description("The ID of the QID record to update")
                .minimum(1)
                .required()
            .string("name")
                .description("Optional new name for the event type")
            .string("description")
                .description("Optional new description for the event type")
            .integer("severity")
                .description("Optional new severity level (0-10)")
                .minimum(0)
                .maximum(10)
            .integer("low_level_category_id")
                .description("Optional new low level category ID")
                .minimum(0)
            .string("fields")
                .description("Optional comma-separated list of fields to return in the response")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def approval_required(self) -> bool:
        """POST (update) operation - requires approval."""
        return True

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the update_qid_record tool.

        Args:
            arguments: Must contain 'qid_record_id'; optional update fields

        Returns:
            MCP response with the updated QID record or error
        """
        qid_record_id = arguments.get("qid_record_id")

        if qid_record_id is None:
            return self.create_error_response("Error: qid_record_id is required")

        body = {}
        for field in ("name", "description"):
            value = arguments.get(field)
            if value is not None:
                body[field] = value

        for field in ("severity", "low_level_category_id"):
            value = arguments.get(field)
            if value is not None:
                body[field] = int(value)

        if not body:
            return self.create_error_response(
                "Error: at least one updatable field (name, description, severity, low_level_category_id) must be provided"
            )

        headers = {}
        fields = arguments.get("fields")
        if fields:
            headers["fields"] = fields

        response = await self.client.post(
            f'/data_classification/qid_records/{int(qid_record_id)}',
            data=body,
            headers=headers if headers else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
