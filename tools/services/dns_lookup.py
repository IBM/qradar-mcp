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
DNS Lookup Tool

Initiates DNS resolution for IP addresses (reverse lookup).
"""

from typing import Dict, Any
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class DnsLookupTool(MCPTool):
    """Tool for initiating DNS lookups (reverse DNS resolution)."""

    @property
    def name(self) -> str:
        return "dns_lookup"

    @property
    def description(self) -> str:
        return """Initiate DNS resolution for an IP address (reverse lookup).

Returns a task ID for an asynchronous lookup.

Use cases:
  - Resolve suspicious IPs to hostnames
  - Identify infrastructure ownership
  - Correlate IPs across investigations
  - Build threat actor profiles

Use get_dns_result with the returned task ID to check status and retrieve
results."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("ip_address")
                .description("IP address to resolve (IPv4)")
                .required()
            .string("fields")
                .description("Comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.SERVICES_DNS_LOOKUPS

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the dns_lookup tool.

        Args:
            arguments: Must contain 'ip_address' (string)

        Returns:
            MCP response with task ID and status or error
        """
        ip_address = arguments.get("ip_address")

        if not ip_address:
            return self.create_error_response("Error: ip_address is required")

        # Build query parameters
        params = {"IP": ip_address}

        # Add fields if provided
        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        # Make POST request to initiate lookup
        response = await self.client.post(self.endpoint, params=params)
        response.raise_for_status()

        task_data = response.json()

        # Format the response
        formatted = self._format_task_initiated(task_data)

        return self.create_success_response(formatted)

    def _format_task_initiated(self, task_data: Dict[str, Any]) -> str:
        """Format task initiation response."""
        task_id = task_data.get("id", "Unknown")
        ip_addr = task_data.get("ip", "Unknown")
        status = task_data.get("status", "Unknown")

        lines = [
            "DNS Lookup Initiated",
            "",
            f"Task ID: {task_id}",
            f"Status: {status}",
            f"IP Address: {ip_addr}",
            "",
            f"Use get_dns_result tool with task_id={task_id} to retrieve results.",
            f"Status URL: /services/dns_lookups/{task_id}"
        ]

        return "\n".join(lines)
