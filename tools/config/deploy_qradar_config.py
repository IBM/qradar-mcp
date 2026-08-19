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
Deploy QRadar Config Tool

Starts a QRadar staged configuration deploy.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class DeployQrConfigTool(MCPTool):
    """Tool for starting a QRadar staged configuration deploy."""

    @property
    def name(self) -> str:
        return "deploy_qradar_config"

    @property
    def description(self) -> str:
        return """Execute a QRadar staged configuration deploy.

Before calling this tool, use get_deploy_status to verify there is not already
an active deployment in progress. After starting the deploy, use
get_deploy_status to monitor progress until completion.

Deploy types:
  - INCREMENTAL: Deploy only staged changes
  - FULL: Run a full configuration deployment"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("type")
                .description("Deploy type: INCREMENTAL or FULL")
                .enum(["INCREMENTAL", "FULL"])
                .required()
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    @property
    def endpoint(self) -> str:
        return endpoints.STAGED_CONFIG_DEPLOY_STATUS

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the deploy_qradar_config tool."""
        deploy_type = arguments.get("type")

        if not deploy_type:
            return self.create_error_response("Error: type is required")

        response = await self.client.post(
            self.endpoint,
            data={"type": deploy_type},
        )
        response.raise_for_status()

        deploy_status = response.json()
        return self.create_success_response(json.dumps(deploy_status, indent=2))
