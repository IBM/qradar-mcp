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
List QVM Assets Tool

Lists assets with vulnerability context from QVM.
Requires QVM module license.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class ListQvmAssetsTool(MCPTool):
    """Tool for listing assets with vulnerability context from QVM."""

    @property
    def name(self) -> str:
        return "list_qvm_assets"

    @property
    def description(self) -> str:
        return """List assets with vulnerability information from QVM.

Returns asset data enriched with vulnerability context:
  - Asset identification
  - Vulnerability counts and severity
  - Risk scores
  - Scan status

Use cases:
  - Asset vulnerability status
  - Risk-based asset prioritization
  - Vulnerability coverage analysis
  - Identify high-risk assets

Requirements:
  - QVM (QRadar Vulnerability Manager) module
  - QVM license active

Note: Returns empty list if QVM module not installed."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("saved_search_id")
                .description("ID of saved QVM asset search to execute")
            .string("saved_search_name")
                .description("Name of saved QVM asset search to execute")
            .string("filters")
                .description('JSON array of filter objects for QVM queries ')
                .description('(e.g., [{"parameter":"Severity","operator":"GreaterThan","value":"7"}])')
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
        Execute the list_qvm_assets tool.

        Args:
            arguments: Optional saved_search_id, saved_search_name, or filters

        Returns:
            MCP response with QVM assets list or error
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
        response = await self.client.get('/qvm/assets', params=params)
        response.raise_for_status()

        assets = response.json()

        return self.create_success_response(json.dumps(assets, indent=2))
