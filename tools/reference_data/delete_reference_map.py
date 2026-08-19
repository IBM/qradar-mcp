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
Delete Reference Map Tool

Deletes a reference data map or purges its contents.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class DeleteReferenceMap(MCPTool):
    """Tool for deleting or purging a QRadar reference map."""

    @property
    def name(self) -> str:
        return "delete_reference_map"

    @property
    def description(self) -> str:
        return """Delete a reference data map or purge its contents.

Required parameters:
  - name: Map name to delete or purge

Optional parameters:
  - purge_only: If true, keep structure but clear all data (default: false)
  - namespace: SHARED or TENANT (default: SHARED)
  - fields: Response field selection

Returns an async task status object for deletion progress."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("name")
                .description("The name of the reference map to delete or purge")
                .required()
            .boolean("purge_only")
                .description("If true, keep structure but clear data (default: false)")
            .string("namespace")
                .description("Optional namespace: SHARED or TENANT")
                .enum(["SHARED", "TENANT"])
            .string("fields")
                .description("Optional comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "DELETE"

    @property
    def endpoint(self) -> str:
        return endpoints.REFERENCE_DATA_MAP

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the delete_reference_map tool.

        Args:
            arguments: Must contain 'name', optional purge_only, namespace, fields

        Returns:
            MCP response with task status or error
        """
        name = arguments.get("name")

        if not name:
            return self.create_error_response("Error: name is required")

        # Build request parameters
        params = self._build_params(arguments)

        # Make API request
        response = await self.client.delete(
            self.endpoint.format(name=name),
            params=params
        )
        response.raise_for_status()
        task_data = response.json()

        formatted_output = json.dumps(task_data, indent=2)
        return self.create_success_response(formatted_output)

    def _build_params(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build query parameters for the API request."""
        params = {}

        # Add optional fields
        if arguments.get("purge_only") is not None:
            params["purge_only"] = str(arguments["purge_only"]).lower()

        if arguments.get("namespace"):
            params["namespace"] = arguments["namespace"]

        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        return params
