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
Update Reference Set Tool

Updates properties of an existing reference data set in QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class UpdateReferenceSetTool(MCPTool):
    """Tool for updating QRadar reference set properties."""

    @property
    def name(self) -> str:
        return "update_reference_set"

    @property
    def description(self) -> str:
        return """Update properties of an existing reference data set in QRadar SIEM.

Use cases:
  - Modify TTL and expiry settings
  - Update set description
  - Change logging options for expired entries
  - Clear all entries from a set (delete_entries=true)

Updatable properties:
  - description: Human-readable description
  - time_to_live: TTL in seconds for entries
  - expiry_type: FIRST_SEEN, LAST_SEEN, or NO_EXPIRY
  - expired_log_option: LOG_NONE, LOG_EACH, or LOG_BATCH
  - delete_entries: Set to true to remove all entries

Note: Cannot change name, entry_type, or namespace after creation.
Only the properties specified will be updated; others remain unchanged."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("set_id")
                .description("The ID of the reference set to update")
                .minimum(0)
                .required()
            .string("description")
                .description("Optional updated description of the reference set")
            .integer("time_to_live")
                .description("Time to live in seconds for entries (optional)")
                .minimum(0)
            .string("expiry_type")
                .description("Expiry type: FIRST_SEEN, LAST_SEEN, or NO_EXPIRY")
                .enum(["FIRST_SEEN", "LAST_SEEN", "NO_EXPIRY"])
            .string("expired_log_option")
                .description("Logging option for expired entries: LOG_NONE, LOG_EACH, LOG_BATCH")
                .enum(["LOG_NONE", "LOG_EACH", "LOG_BATCH"])
            .boolean("delete_entries")
                .description("Set to true to delete all entries from the set")
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_COLLECTIONS_SET

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the update_reference_set tool.

        Args:
            arguments: Must contain 'set_id', optional update parameters

        Returns:
            MCP response with updated reference set data or error
        """
        set_id = arguments.get("set_id")

        if set_id is None:
            return self.create_error_response("Error: set_id is required")

        # Check if at least one update parameter is provided
        update_params = [
            "description", "time_to_live", "expiry_type",
            "expired_log_option", "delete_entries"
        ]
        has_updates = any(param in arguments for param in update_params)

        if not has_updates:
            return self.create_error_response(
                "Error: At least one update parameter must be provided "
                "(description, time_to_live, expiry_type, expired_log_option, delete_entries)"
            )


        # Build request body and headers
        body = self._build_body(arguments)
        headers = self._build_headers(arguments)

        # Make API request
        response = await self.client.post(
            self.endpoint.format(name=set_id),
            data=body,
            headers=headers
        )

        response.raise_for_status()
        set_data = response.json()

        formatted_output = json.dumps(set_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_body(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build request body for the API request."""
        body = {}

        # Add optional update fields
        optional_fields = [
            "description",
            "time_to_live",
            "expiry_type",
            "expired_log_option",
            "delete_entries"
        ]

        for field in optional_fields:
            if field in arguments and arguments[field] is not None:
                body[field] = arguments[field]

        return body

    def _build_headers(self, arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build headers for the API request."""
        headers = {}

        # Add fields header if provided
        fields = arguments.get("fields")
        if fields:
            headers["fields"] = fields

        return headers
