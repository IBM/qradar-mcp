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
Get QID Record by QID Tool

Looks up a QID record by its numeric QID value (not the record ID) from QRadar.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class GetQidRecordByQidTool(MCPTool):
    """Tool for retrieving a QRadar QID record by its QID value."""

    @property
    def name(self) -> str:
        return "get_qid_record_by_qid"

    @property
    def description(self) -> str:
        return """Retrieve a QID record by its numeric QID value from QRadar.

QID records have two different numeric identifiers:
  - id: the internal QID record database ID (used by get_qid_record)
  - qid: the QRadar Identifier — the well-known numeric event identifier (e.g., 2500001)

Use this tool when you know the QID value (e.g., from an event payload) and need the
full record including name, description, severity, and category.

Returns the matching QID record, or an error if no record is found for that QID.

Example:
  - Look up QID 2500001: qid=2500001"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("qid")
                .description("The numeric QRadar Identifier (QID) to look up (e.g., 2500001)")
                .minimum(0)
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
        Execute the get_qid_record_by_qid tool.

        Queries the list endpoint with filter="qid=<value>" and returns the
        single matching record, or an error if not found.

        Args:
            arguments: Must contain 'qid' (integer)

        Returns:
            MCP response with QID record data or error
        """
        qid = arguments.get("qid")
        fields = arguments.get("fields")

        if qid is None:
            return self.create_error_response("Error: qid is required")

        params = {"filter": f"qid={int(qid)}"}
        if fields:
            params["fields"] = fields

        response = await self.client.get(
            '/data_classification/qid_records',
            params=params
        )
        response.raise_for_status()

        records = response.json()

        if not records:
            return self.create_error_response(f"Error: no QID record found for qid={qid}")

        return self.create_success_response(json.dumps(records[0], indent=2))
