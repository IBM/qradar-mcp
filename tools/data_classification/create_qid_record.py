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
Create QID Record Tool

Creates a new QID record in QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class CreateQidRecordTool(MCPTool):
    """Tool for creating a new QRadar QID record."""

    @property
    def name(self) -> str:
        return "create_qid_record"

    @property
    def description(self) -> str:
        return """Create a new QID record in QRadar.

QID records define custom event types in QRadar. Creating a QID record allows custom
events from log sources to be classified with a specific name, category, and severity.

Required parameters:
  - log_source_type_id: The log source type ID this QID is created for
  - name: The human-readable name for the event type
  - low_level_category_id: The low level category ID to classify this event

Optional parameters:
  - description: A description of the event type
  - severity: Override severity (0-10); defaults to the low level category's severity if omitted

Returns the newly created QID record including its assigned id and qid."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("log_source_type_id")
                .description("The ID of the log source type this QID record is created for")
                .minimum(0)
                .required()
            .string("name")
                .description("The human-readable name for the event type")
                .required()
            .integer("low_level_category_id")
                .description("The low level category ID to classify this event type")
                .minimum(0)
                .required()
            .string("description")
                .description("Optional description of the event type")
            .integer("severity")
                .description("Optional severity override (0-10). Defaults to the low level category's severity.")
                .minimum(0)
                .maximum(10)
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
        Execute the create_qid_record tool.

        Args:
            arguments: Must contain log_source_type_id, name, and low_level_category_id

        Returns:
            MCP response with the newly created QID record or error
        """
        log_source_type_id = arguments.get("log_source_type_id")
        name = arguments.get("name")
        low_level_category_id = arguments.get("low_level_category_id")

        if log_source_type_id is None:
            return self.create_error_response("Error: log_source_type_id is required")
        if not name:
            return self.create_error_response("Error: name is required")
        if low_level_category_id is None:
            return self.create_error_response("Error: low_level_category_id is required")

        body = {
            "log_source_type_id": int(log_source_type_id),
            "name": name,
            "low_level_category_id": int(low_level_category_id)
        }

        description = arguments.get("description")
        if description:
            body["description"] = description

        severity = arguments.get("severity")
        if severity is not None:
            body["severity"] = int(severity)

        headers = {}
        fields = arguments.get("fields")
        if fields:
            headers["fields"] = fields

        response = await self.client.post(
            '/data_classification/qid_records',
            data=body,
            headers=headers if headers else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
