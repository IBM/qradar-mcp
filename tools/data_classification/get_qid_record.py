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
Get QID Record Tool

Retrieves a single QID record by ID from QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class GetQidRecordTool(MCPTool):
    """Tool for retrieving a single QRadar QID record by ID."""

    @property
    def name(self) -> str:
        return "get_qid_record"

    @property
    def description(self) -> str:
        return """Retrieve a QID record by ID from QRadar.

QID (QRadar Identifier) records define event types in QRadar, mapping to categories
and severity levels. Each event received by QRadar is resolved to a QID record.

Returns:
  - id: The QID record ID
  - qid: The numeric QRadar Identifier
  - name: The human-readable name of the event type
  - description: A description of the event type
  - severity: The severity level (0-10)
  - low_level_category_id: The low level category this QID belongs to
  - log_source_type_id: The log source type (null for most system QIDs)
  - uuid: The UUID of the QID record"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("qid_record_id")
                .description("The ID of the QID record to retrieve (must be a positive integer)")
                .minimum(1)
                .required()
            .string("fields")
                .description('Optional comma-separated list of fields to return. Examples: "id,qid,name,severity"')
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
        Execute the get_qid_record tool.

        Args:
            arguments: Must contain 'qid_record_id' (integer)

        Returns:
            MCP response with QID record data or error
        """
        qid_record_id = arguments.get("qid_record_id")
        fields = arguments.get("fields")

        if qid_record_id is None:
            return self.create_error_response("Error: qid_record_id is required")

        params = {}
        if fields:
            params['fields'] = fields

        response = await self.client.get(
            f'/data_classification/qid_records/{int(qid_record_id)}',
            params=params if params else None
        )
        response.raise_for_status()

        return self.create_success_response(json.dumps(response.json(), indent=2))
