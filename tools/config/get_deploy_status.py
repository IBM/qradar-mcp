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
Get Deploy Status Tool

Retrieves the current QRadar staged configuration deploy status.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools import endpoints


class GetDeployStatusTool(MCPTool):
    """Tool for retrieving QRadar staged configuration deploy status."""

    @property
    def name(self) -> str:
        return "get_deploy_status"

    @property
    def description(self) -> str:
        return """Retrieve the current QRadar staged configuration deploy status.

Use this before deploy_qradar_config to check whether a deployment is already
running and after deploy_qradar_config to monitor progress.
"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.STAGED_CONFIG_DEPLOY_STATUS

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the get_deploy_status tool."""
        response = await self.client.get(self.endpoint, params={})
        response.raise_for_status()

        deploy_status = response.json()
        return self.create_success_response(json.dumps(deploy_status, indent=2))
