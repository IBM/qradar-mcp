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
Update Staged Network Tool

Updates fields on a single existing entry in the staged network hierarchy.
"""

from typing import Any, Dict
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


_UPDATABLE_FIELDS = [
    "group", "name", "cidr", "description", "domain_id", "country_code"
]


class UpdateStagedNetworkTool(MCPTool):
    """Tool for updating a single entry in the staged network hierarchy."""

    @property
    def name(self) -> str:
        return "update_staged_network"

    @property
    def description(self) -> str:
        return """Update fields on a single existing entry in the staged network hierarchy.

Fetches the current staged hierarchy, finds the entry by its numeric id,
merges only the fields you provide over the existing values, and writes
the complete updated list back. Fields you do not supply are preserved
unchanged.

Use cases:
  - Rename a network entry
  - Update the CIDR range for an existing network
  - Change the group or description of a network entry
  - Assign a domain or country code to an existing entry

Changes are staged only; use get_deploy_status and deploy_qradar_config to
apply them."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .integer("network_id")
                .description(
                    "The id of the network entry to update (from "
                    "get_staged_network_hierarchy)")
                .minimum(0)
                .required()
            .string("group")
                .description(
                    "Updated network group (e.g. 'Internal', 'DMZ')")
            .string("name")
                .description("Updated name of the network entry")
            .string("cidr")
                .description(
                    "Updated CIDR range (e.g. '192.168.1.0/24')")
            .string("description")
                .description("Updated description of the network entry")
            .integer("domain_id")
                .description("Updated domain ID (use 0 for default domain)")
                .minimum(0)
            .string("country_code")
                .description("Updated ISO country code (e.g. 'US', 'CA')")
            .build())

    @property
    def http_verb(self) -> str:
        return "PUT"

    @property
    def endpoint(self) -> str:
        return endpoints.CONFIG_STAGED_NETWORKS

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the update_staged_network tool."""
        network_id = arguments.get("network_id")

        if network_id is None:
            return self.create_error_response("Error: network_id is required")

        updates = {
            f: arguments[f]
            for f in _UPDATABLE_FIELDS
            if arguments.get(f) is not None
        }
        if not updates:
            return self.create_error_response(
                "Error: at least one update field must be provided "
                "(group, name, cidr, description, domain_id, country_code)"
            )

        get_response = await self.client.get(
            self.endpoint, params={})
        get_response.raise_for_status()
        networks = get_response.json()

        target_index = next(
            (idx for idx, net in enumerate(networks)
             if net.get("id") == network_id),
            None
        )
        if target_index is None:
            return self.create_error_response(
                f"Error: network entry with id {network_id} not found "
                "in staged hierarchy"
            )

        updated_entry = dict(networks[target_index])
        updated_entry.update(updates)
        networks[target_index] = updated_entry

        put_response = await self.client.put(
            self.endpoint,
            data=networks,
        )
        put_response.raise_for_status()

        result = put_response.json()
        return self.create_success_response(json.dumps(result, indent=2))
