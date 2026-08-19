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
Add to Reference Set Tool

Adds entries (IOCs) to a QRadar reference data set.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class AddToReferenceSetTool(MCPTool):
    """Tool for adding entries to QRadar reference data sets."""

    @property
    def name(self) -> str:
        return "add_to_reference_set"

    @property
    def description(self) -> str:
        return """Add IOC entries (IPs, domains, hashes, etc.) to a QRadar reference data set.

Use cases:
  - Add threat indicators from external feeds
  - Add suspicious IPs discovered during investigation
  - Add malicious domains or hashes
  - Bulk import IOCs from threat intelligence

The entry will be created with the current timestamp. If the entry already exists,
it will be updated with the new timestamp and optional notes/source."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("set_name")
                .description("Name of the reference set to add the entry to")
                .required()
            .string("value")
                .description("The value to add (IP, domain, hash, etc.). Must match the set's entry_type")
                .required()
            .string("source")
                .description("Optional source of the entry (e.g., 'threat_feed', 'manual_investigation')")
            .string("notes")
                .description("Optional notes about this entry (max 10000 characters)")
            .string("fields")
                .description("Optional comma-separated list of fields to return (e.g., 'id,value,first_seen')")
            .build())
    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_COLLECTIONS_SET_ENTRIES

    _SETS_ENDPOINT = "reference_data_collections/sets"

    def _build_body(self, arguments: Dict[str, Any], set_id: int) -> Dict[str, Any]:
        """Build the request body for adding an entry."""
        body = {
            "collection_id": set_id,
            "value": arguments["value"]
        }

        # Add optional fields if provided
        if "source" in arguments:
            body["source"] = arguments["source"]
        if "notes" in arguments:
            body["notes"] = arguments["notes"]

        return body

    def _build_headers(self, arguments: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers including optional fields parameter."""
        headers = {}
        if "fields" in arguments:
            headers["fields"] = arguments["fields"]
        return headers

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the add_to_reference_set tool.

        Args:
            arguments: Must contain 'set_name' and 'value'.
                      Optional: 'source', 'notes', 'fields'

        Returns:
            MCP response with created/updated entry data or error
        """
        set_name = arguments.get("set_name")
        value = arguments.get("value")

        if not set_name:
            return self.create_error_response("Error: set_name is required")
        if not value:
            return self.create_error_response("Error: value is required")

        # First, look up the reference set by name to get its ID
        list_response = await self.client.get(
            self._SETS_ENDPOINT,
            params={"filter": f"name='{set_name}'"}
        )
        sets = list_response.json()

        if not sets or len(sets) == 0:
            return self.create_error_response(f"Error: Reference set '{set_name}' not found")

        # Add entry to the reference set
        response = await self.client.post(
            self.endpoint,
            data=self._build_body(arguments, sets[0]["id"]),
            headers=self._build_headers(arguments)
        )

        response.raise_for_status()
        result = response.json()

        # 201 = created, 200 = updated existing entry
        message = (f"Entry {'added' if response.status_code == 201 else 'updated'} "
                  f"successfully {'to' if response.status_code == 201 else 'in'} "
                  f"reference set '{set_name}'")

        return self.create_success_response(
            f"{message}\n\n{json.dumps(result, indent=2)}"
        )
