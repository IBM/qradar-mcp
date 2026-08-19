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
Add Staged Network Tool

Adds a single new network entry to the staged network hierarchy.
"""

from typing import Any, Dict
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class AddStagedNetworkTool(MCPTool):
    """Tool for adding a single network entry to the staged hierarchy."""

    @property
    def name(self) -> str:
        return "add_staged_network"

    @property
    def description(self) -> str:
        return """Add a single new network entry to the staged network hierarchy.

Fetches the current staged hierarchy, appends the new entry, and writes the
complete updated list back. Only the fields you provide are set on the new
entry; a server-assigned id will be returned after the change is deployed.

Use cases:
  - Add a new CIDR range to an existing network group
  - Define a new network segment before deployment
  - Extend the network topology with a new subnet

Changes are staged only; use get_deploy_status and deploy_qradar_config to
apply them."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("group")
                .description(
                    "Network group (e.g. 'Internal', 'DMZ', 'External')")
                .required()
            .string("name")
                .description("Name of the new network entry")
                .required()
            .string("cidr")
                .description(
                    "CIDR range for the network (e.g. '192.168.1.0/24')")
                .required()
            .string("description")
                .description("Optional description of the network entry")
            .integer("domain_id")
                .description(
                    "Domain ID for the network entry (use 0 for default "
                    "domain; required if QRadar is domain-aware)")
                .minimum(0)
            .string("country_code")
                .description(
                    "Optional ISO country code (e.g. 'US', 'CA')")
            .build())

    @property
    def http_verb(self) -> str:
        return "PUT"

    @property
    def endpoint(self) -> str:
        return endpoints.CONFIG_STAGED_NETWORKS

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the add_staged_network tool."""
        group = arguments.get("group")
        name = arguments.get("name")
        cidr = arguments.get("cidr")

        if not group:
            return self.create_error_response("Error: group is required")
        if not name:
            return self.create_error_response("Error: name is required")
        if not cidr:
            return self.create_error_response("Error: cidr is required")

        get_response = await self.client.get(
            self.endpoint, params={})
        get_response.raise_for_status()
        networks = get_response.json()

        new_entry = {"group": group, "name": name, "cidr": cidr}
        optional_fields = ["description", "domain_id", "country_code"]
        for field in optional_fields:
            if arguments.get(field) is not None:
                new_entry[field] = arguments[field]

        networks.append(new_entry)

        put_response = await self.client.put(
            self.endpoint,
            data=networks,
        )
        put_response.raise_for_status()

        result = put_response.json()
        return self.create_success_response(json.dumps(result, indent=2))
