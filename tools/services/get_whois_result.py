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
Get WHOIS Result Tool

Retrieves WHOIS lookup results by task ID.
"""

from typing import Dict, Any
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GetWhoisResultTool(MCPTool):
    """Tool for retrieving WHOIS lookup results by task ID."""

    @property
    def name(self) -> str:
        return "get_whois_result"

    @property
    def description(self) -> str:
        return """Retrieve WHOIS lookup results by task ID.

Use this after whois_lookup to check status and retrieve results.

Returns:
  - Task status (QUEUED, PROCESSING, COMPLETED, EXCEPTION)
  - WHOIS data (when status is COMPLETED)
  - Error message (when status is EXCEPTION)

If status is PROCESSING or QUEUED, retry after a few seconds."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("task_id")
                .description("WHOIS lookup task ID from whois_lookup tool")
                .minimum(1)
                .required()
            .string("fields")
                .description("Comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.SERVICES_WHOIS_LOOKUP

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the get_whois_result tool.

        Args:
            arguments: Must contain 'task_id' (integer)

        Returns:
            MCP response with WHOIS results or status
        """
        task_id = arguments.get("task_id")

        if task_id is None:
            return self.create_error_response("Error: task_id is required")


        # Build query parameters
        params = {}
        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        # Make GET request
        response = await self.client.get(self.endpoint.format(task_id=int(task_id)), params=params)
        response.raise_for_status()

        task_data = response.json()
        status = task_data.get("status", "Unknown")

        # Format based on status
        if status == "COMPLETED":
            formatted = self._format_completed(task_data)
        elif status in ["QUEUED", "PROCESSING", "INITIALIZING"]:
            formatted = self._format_in_progress(task_data)
        else:
            formatted = self._format_failed(task_data)

        return self.create_success_response(formatted)

    def _format_completed(self, task_data: Dict[str, Any]) -> str:
        """Format completed task results."""
        task_id = task_data.get("id", "Unknown")
        ip_addr = task_data.get("ip", "Unknown")
        whois_data = task_data.get("message", "No WHOIS data available")

        lines = [
            "WHOIS Lookup Results",
            "",
            f"Task ID: {task_id}",
            f"IP Address: {ip_addr}",
            "Status: COMPLETED",
            "",
            "WHOIS Data:",
            whois_data
        ]

        return "\n".join(lines)


    def _format_in_progress(self, task_data: Dict[str, Any]) -> str:
        """Format in-progress task status."""
        task_id = task_data.get("id", "Unknown")
        ip_addr = task_data.get("ip", "Unknown")
        status = task_data.get("status", "Unknown")

        lines = [
            "WHOIS Lookup Status",
            "",
            f"Task ID: {task_id}",
            f"IP Address: {ip_addr}",
            f"Status: {status}",
            "",
            "The WHOIS lookup is still in progress. Please retry in a few seconds."
        ]

        return "\n".join(lines)

    def _format_failed(self, task_data: Dict[str, Any]) -> str:
        """Format failed task status."""
        task_id = task_data.get("id", "Unknown")
        ip_addr = task_data.get("ip", "Unknown")
        status = task_data.get("status", "Unknown")
        message = task_data.get("message", "No error message available")

        lines = [
            "WHOIS Lookup Failed",
            "",
            f"Task ID: {task_id}",
            f"IP Address: {ip_addr}",
            f"Status: {status}",
            "",
            f"Error: {message}"
        ]

        return "\n".join(lines)
