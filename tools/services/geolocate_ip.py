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
Geolocate IP Tool

Retrieves MaxMind GeoIP location data for IP addresses.
"""

from typing import Dict, Any
from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema
from qradar_mcp.tools import endpoints


class GeolocateIpTool(MCPTool):
    """Tool for retrieving IP geolocation data from MaxMind GeoIP database."""

    @property
    def name(self) -> str:
        return "geolocate_ip"

    @property
    def description(self) -> str:
        return """Get geographic location data for an IP address using MaxMind GeoIP.

IMPORTANT: Only PUBLIC IP addresses can be geolocated. Private/RFC1918 addresses will fail:

Returns comprehensive location information including:
  - City, country, continent
  - Latitude/longitude coordinates
  - ISP and organization details
  - Timezone information
  - Network details (ASN, domain)

Use cases:
  - Identify geographic origin of attacks from external IPs
  - Detect anomalous login locations
  - Map threat actor infrastructure
  - Enrich offense data with location context

Note: Data sourced from MaxMind GeoIP2 database maintained by QRadar."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("ip_address")
                .description("IP address to geolocate (IPv4 or IPv6)")
                .required()
            .string("fields")
                .description("Comma-separated list of fields to return")
            .build())

    @property
    def http_verb(self) -> str:
        return "GET"

    @property
    def endpoint(self) -> str:
        return endpoints.SERVICES_GEOLOCATIONS

    @property
    def approval_required(self) -> bool:
        """GET operation - does not require approval."""
        return False

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the geolocate_ip tool.

        Args:
            arguments: Must contain 'ip_address' (string)

        Returns:
            MCP response with geolocation data or error
        """
        ip_address = arguments.get("ip_address")

        if not ip_address:
            return self.create_error_response("Error: ip_address is required")


        # Build filter parameter
        filter_expr = f'ip_address = "{ip_address}"'
        params = {"filter": filter_expr}

        # Add fields if provided
        if arguments.get("fields"):
            params["fields"] = arguments["fields"]

        # Make API request
        response = await self.client.get(self.endpoint, params=params)
        response.raise_for_status()

        data = response.json()

        # Check if we got results
        if not data or len(data) == 0:
            return self.create_error_response(
                f"No geolocation data found for IP address: {ip_address}"
            )

        # Extract first result (filter returns array)
        location = data[0]

        # Format the response
        formatted = self._format_geolocation(location)

        return self.create_success_response(formatted)

    def _format_geolocation(self, location: Dict[str, Any]) -> str:
        """Format geolocation data for display."""
        ip_addr = location.get("ip_address", "Unknown")
        is_local = location.get("is_local", False)

        lines = [f"IP Geolocation: {ip_addr}", ""]

        # Add location information
        self._add_location_info(lines, location)

        # Add network information
        self._add_network_info(lines, location)

        # Add local network status
        self._add_status_info(lines, location, is_local)

        return "\n".join(lines)

    def _add_location_info(self, lines: list, location: Dict[str, Any]) -> None:
        """Add location information to output lines."""
        city = location.get("city", {})
        country = location.get("physical_country", {})
        continent = location.get("continent", {})
        loc = location.get("location", {})

        if not (city or country or continent):
            return

        lines.append("Location:")

        # Add city with subdivision if available
        if city.get("name"):
            subdivisions = location.get("subdivisions", [])
            if subdivisions and subdivisions[0].get("name"):
                lines.append(f"  City: {city['name']}, {subdivisions[0]['name']}")
            else:
                lines.append(f"  City: {city['name']}")

        # Add country
        if country.get("name"):
            iso = country.get("iso_code", "")
            lines.append(f"  Country: {country['name']} ({iso})")

        # Add continent
        if continent.get("name"):
            lines.append(f"  Continent: {continent['name']}")

        # Add coordinates
        if loc.get("latitude") is not None and loc.get("longitude") is not None:
            lines.append(f"  Coordinates: {loc['latitude']}, {loc['longitude']}")

        # Add timezone
        if loc.get("timezone"):
            lines.append(f"  Timezone: {loc['timezone']}")

        lines.append("")

    def _add_network_info(self, lines: list, location: Dict[str, Any]) -> None:
        """Add network information to output lines."""
        traits = location.get("traits", {})
        if not traits:
            return

        lines.append("Network:")

        if traits.get("internet_service_provider"):
            lines.append(f"  ISP: {traits['internet_service_provider']}")
        if traits.get("autonomous_system_number"):
            lines.append(f"  ASN: AS{traits['autonomous_system_number']}")
        if traits.get("organization"):
            lines.append(f"  Organization: {traits['organization']}")
        if traits.get("domain"):
            lines.append(f"  Domain: {traits['domain']}")

        lines.append("")

    def _add_status_info(self, lines: list, location: Dict[str, Any],
                        is_local: bool) -> None:
        """Add status information to output lines."""
        if is_local:
            network = location.get("network", "Unknown")
            domain_id = location.get("domain_id", "Unknown")
            lines.append(f"Status: Local IP (Network: {network}, Domain: {domain_id})")
        else:
            lines.append("Status: External IP (not in local network)")
