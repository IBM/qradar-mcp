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
List Assets Tool

Lists assets from QRadar asset model with filtering, sorting, and pagination.
"""

from typing import Dict, Any
import json
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.utils.parameters import (
    build_query_params,
    build_headers,
    parse_range_from_limit_offset
)
from qradar_mcp.tools import endpoints


class ListAssetsTool(MCPTool):
    """Tool for listing QRadar assets with filtering and pagination."""

    @property
    def name(self) -> str:
        return "list_assets"

    @property
    def description(self) -> str:
        return """List assets from QRadar asset model with optional filtering, sorting, and pagination.

=== FIELDS REFERENCE ===

domain_id: Number
hostnames: Array<Object>
  hostnames(created): Number
  hostnames(first_seen_profiler): Number
  hostnames(first_seen_scanner): Number
  hostnames(id): Number
  hostnames(last_seen_profiler): Number
  hostnames(last_seen_scanner): Number
  hostnames(name): String
  hostnames(type): String
id: Number
interfaces: Array<Object>
  interfaces(created): Number
  interfaces(first_seen_profiler): Number
  interfaces(first_seen_scanner): Number
  interfaces(id): Number
  interfaces(ip_addresses): Array<Object>
    interfaces(ip_addresses)(created): Number
    interfaces(ip_addresses)(first_seen_profiler): Number
    interfaces(ip_addresses)(first_seen_scanner): Number
    interfaces(ip_addresses)(id): Number
    interfaces(ip_addresses)(last_seen_profiler): Number
    interfaces(ip_addresses)(last_seen_scanner): Number
    interfaces(ip_addresses)(network_id): Number
    interfaces(ip_addresses)(type): String
    interfaces(ip_addresses)(value): String
  interfaces(last_seen_profiler): Number
  interfaces(last_seen_scanner): Number
  interfaces(mac_address): String
products: Array<Object>
  products(first_seen_profiler): Number
  products(first_seen_scanner): Number
  products(id): Number
  products(last_scanned_for): Number
  products(last_seen_profiler): Number
  products(last_seen_scanner): Number
  products(name): String
  products(product_variant_id): Number
  products(vendor): String
  products(version): String
properties: Array<Object>
  properties(id): Number
  properties(last_reported): Number
  properties(last_reported_by): String
  properties(name): String
  properties(type_id): Number
  properties(value): String
risk_score_sum: Number
users: Array<Object>
  users(first_seen_profiler): Number
  users(first_seen_scanner): Number
  users(id): Number
  users(last_seen_profiler): Number
  users(last_seen_scanner): Number
  users(username): String
vulnerability_count: Number
"""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("filter")
                .description("Optional filter expression.")
            .string("fields")
                .description("Optional comma-separated list of fields to return.")
            .string("sort")
                .description("Optional sort expression.")
            .integer("limit")
                .description("Maximum number of assets to return (default: 50, max: 10000)")
                .minimum(1)
                .maximum(10000)
            .integer("offset")
                .description("Number of assets to skip for pagination (default: 0)")
                .minimum(0)
            .boolean("format_output")
                .description("Format output as human-readable table (default: false)")
                .default(False)
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.ASSET_MODEL_ASSETS

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the list_assets tool.

        Args:
            arguments: Optional parameters for filtering, sorting, and pagination

        Returns:
            MCP response with asset list or error
        """
        filter_expr = arguments.get("filter")
        sort_expr = arguments.get("sort")
        fields_str = arguments.get("fields")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)

        # Build query parameters
        fields_list = [f.strip() for f in fields_str.split(",")] if fields_str else None
        params = build_query_params(
            filter_expr=filter_expr,
            sort_fields=[sort_expr] if sort_expr else None,
            fields=fields_list
        )

        # Build headers (Range for pagination)
        start, end = parse_range_from_limit_offset(limit, offset)
        headers = build_headers(start=start, end=end)

        response = await self.client.get(self.endpoint, params=params, headers=headers)
        response.raise_for_status()

        assets = response.json()

        # Format output if requested (default: true)
        format_output = arguments.get('format_output', True)
        if format_output and assets:
            formatted = self._format_assets(assets)
            return self.create_success_response(formatted)

        return self.create_success_response(json.dumps(assets, indent=2))

    def _format_assets(self, assets: list) -> str:
        """Format assets as human-readable output."""
        if not assets:
            return "No assets found"

        lines = [f"Found {len(assets)} asset(s):\n"]

        for asset in assets:
            lines.append(f"Asset ID: {asset.get('id', 'N/A')}")

            # Hostnames
            hostnames = asset.get('hostnames', [])
            if hostnames:
                hostname_list = [h.get('name', 'N/A') for h in hostnames]
                lines.append(f"  Hostnames: {', '.join(hostname_list)}")

            # IP Addresses
            interfaces = asset.get('interfaces', [])
            if interfaces:
                ips = []
                for iface in interfaces:
                    ip_addrs = iface.get('ip_addresses', [])
                    ips.extend([ip.get('value', 'N/A') for ip in ip_addrs])
                if ips:
                    lines.append(f"  IP Addresses: {', '.join(ips)}")

            # Risk and vulnerabilities
            risk_score = asset.get('risk_score_sum', 0)
            vuln_count = asset.get('vulnerability_count', 0)
            lines.append(f"  Risk Score: {risk_score}, Vulnerabilities: {vuln_count}")

            # Domain
            domain_id = asset.get('domain_id', 'N/A')
            lines.append(f"  Domain ID: {domain_id}")

            lines.append("")  # Blank line between assets

        return "\n".join(lines)
