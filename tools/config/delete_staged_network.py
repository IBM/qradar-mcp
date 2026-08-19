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
Delete Staged Network Tool

Removes a single entry from the staged network hierarchy by its id.
"""

from typing import Any, Dict
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class DeleteStagedNetworkTool(MCPTool):
    """Tool for removing a single entry from the staged network hierarchy."""

    @property
    def name(self) -> str:
        return "delete_staged_network"

    @property
    def description(self) -> str:
        return """Remove a single entry from the staged network hierarchy by its id.

Fetches the current staged hierarchy, removes the entry with the matching id,
and writes the reduced list back. Returns an error if the id is not found.

Use cases:
  - Remove a decommissioned network segment from the staged hierarchy
  - Delete an incorrectly added network entry before deployment
  - Clean up obsolete CIDR ranges

Changes are staged only; use get_deploy_status and deploy_qradar_config to
apply them."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("network_id")
                .description(
                    "The id of the network entry to remove (from "
                    "get_staged_network_hierarchy)")
                .minimum(0)
                .required()
            .build())

    @property
    def http_verb(self) -> str:
        return "PUT"

    @property
    def endpoint(self) -> str:
        return endpoints.CONFIG_STAGED_NETWORKS

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the delete_staged_network tool."""
        network_id = arguments.get("network_id")

        if network_id is None:
            return self.create_error_response("Error: network_id is required")

        get_response = await self.client.get(
            self.endpoint, params={})
        get_response.raise_for_status()
        networks = get_response.json()

        filtered = [net for net in networks if net.get("id") != network_id]

        if len(filtered) == len(networks):
            return self.create_error_response(
                f"Error: network entry with id {network_id} not found "
                "in staged hierarchy"
            )

        put_response = await self.client.put(
            self.endpoint,
            data=filtered,
        )
        put_response.raise_for_status()

        return self.create_success_response(
            f"Network entry {network_id} removed from staged hierarchy"
        )
