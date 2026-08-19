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
List Vulnerabilities Tool

Lists vulnerabilities from QRadar Vulnerability Manager.
Requires QVM module license.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class ListVulnerabilitiesTool(MCPTool):
    """Tool for listing vulnerabilities from QVM scans."""

    @property
    def name(self) -> str:
        return "list_vulnerabilities"

    @property
    def description(self) -> str:
        return """List vulnerabilities discovered by QRadar Vulnerability Manager (QVM).

Returns vulnerability data from QVM scans, including:
  - Vulnerability details and severity
  - Affected assets
  - CVE information
  - Risk scores

Use cases:
  - Vulnerability tracking and assessment
  - Risk prioritization
  - Correlation with security offenses
  - Patch management support
  - Compliance reporting

Requires an active licensed QVM (QRadar Vulnerability Manager) module.

Note: Returns empty list if QVM not available."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("saved_search_id")
                .description("ID of saved QVM search to execute")
            .string("saved_search_name")
                .description("Name of saved QVM search to execute")
            .string("filters")
                .description('JSON array of filter objects ')
                .description('(e.g., [{"parameter":"IP Address","operator":"Equals","value":"10.0.0.1"}])')
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.QVM_VULNS

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_vulnerabilities tool.

        Args:
            arguments: Optional saved_search_id, saved_search_name, or filters

        Returns:
            MCP response with vulnerabilities list or error
        """

        # Build query parameters
        params = {}

        if arguments.get("saved_search_id"):
            params["savedSearchId"] = arguments["saved_search_id"]

        if arguments.get("saved_search_name"):
            params["savedSearchName"] = arguments["saved_search_name"]

        if arguments.get("filters"):
            params["filters"] = arguments["filters"]

        # Make API call
        response = await self.client.get(self.endpoint, params=params)
        response.raise_for_status()

        vulnerabilities = response.json()

        return self.create_success_response(json.dumps(vulnerabilities, indent=2))
