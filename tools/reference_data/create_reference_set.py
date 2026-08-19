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
Create Reference Set Tool

Creates a new reference data set in QRadar SIEM.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class CreateReferenceSetTool(MCPTool):
    """Tool for creating a new QRadar reference set."""

    @property
    def name(self) -> str:
        return "create_reference_set"

    @property
    def description(self) -> str:
        return """Create a new reference data set in QRadar SIEM.

Use cases:
  - Create custom threat intelligence lists
  - Build watchlists for malicious IPs/domains
  - Maintain allowlists for trusted entities
  - Track indicators of compromise (IOCs)

Required parameters:
  - name: Unique name for the set
  - entry_type: Type of data (IP, ALN, NUM, PORT, DATE, CIDR)

Optional parameters:
  - description: Human-readable description
  - namespace: PRIVATE, SHARED, or TENANT (default: PRIVATE)
  - time_to_live: TTL in seconds for entries
  - expiry_type: FIRST_SEEN, LAST_SEEN, or NO_EXPIRY
  - expired_log_option: LOG_NONE, LOG_EACH, or LOG_BATCH
  - tenant_id: Required if namespace is TENANT

Entry types:
  - IP: IPv4/IPv6 addresses
  - ALN: Alphanumeric strings
  - ALNIC: Alphanumeric case-insensitive
  - NUM: Numeric values
  - PORT: Port numbers
  - DATE: Date/time values
  - CIDR: CIDR notation networks"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("name")
                .description("Unique name for the reference set")
                .required()
            .string("entry_type")
                .description("Type of entries: IP, ALN, ALNIC, NUM, PORT, DATE, CIDR")
                .enum(["IP", "ALN", "ALNIC", "NUM", "PORT", "DATE", "CIDR"])
                .required()
            .string("description")
                .description("Optional description of the reference set")
            .string("namespace")
                .description("Namespace: PRIVATE, SHARED, or TENANT (default: PRIVATE)")
                .enum(["PRIVATE", "SHARED", "TENANT"])
            .integer("time_to_live")
                .description("Time to live in seconds for entries (optional)")
                .minimum(0)
            .string("expiry_type")
                .description("Expiry type: FIRST_SEEN, LAST_SEEN, or NO_EXPIRY")
                .enum(["FIRST_SEEN", "LAST_SEEN", "NO_EXPIRY"])
            .string("expired_log_option")
                .description("Logging option for expired entries: LOG_NONE, LOG_EACH, LOG_BATCH")
                .enum(["LOG_NONE", "LOG_EACH", "LOG_BATCH"])
            .integer("tenant_id")
                .description("Tenant ID (required if namespace is TENANT)")
                .minimum(0)
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_COLLECTIONS_SETS

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the create_reference_set tool.

        Args:
            arguments: Must contain 'name' and 'entry_type', optional other parameters

        Returns:
            MCP response with created reference set data or error
        """
        name = arguments.get("name")
        entry_type = arguments.get("entry_type")

        if not name:
            return self.create_error_response("Error: name is required")
        if not entry_type:
            return self.create_error_response("Error: entry_type is required")


        # Build request body and headers
        body = self._build_body(arguments)
        headers = self._build_headers(arguments)

        # Make API request
        response = await self.client.post(
            self.endpoint,
            data=body,
            headers=headers
        )

        response.raise_for_status()
        set_data = response.json()

        formatted_output = json.dumps(set_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_body(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build request body for the API request."""
        body = {
            "name": arguments["name"],
            "entry_type": arguments["entry_type"]
        }

        # Add optional fields
        optional_fields = [
            "description",
            "namespace",
            "time_to_live",
            "expiry_type",
            "expired_log_option",
            "tenant_id"
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
