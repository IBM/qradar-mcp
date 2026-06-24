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
AQL Fields Resources

Provides dynamic access to QRadar AQL field definitions for events and flows tables.
"""

import json
from typing import Dict, Any

from qradar_mcp.utils.mcp_logger import log_mcp
from qradar_mcp.client.qradar_rest_client import QRadarRestClient

from .base import MCPResource


class AQLEventsFieldsResource(MCPResource):
    """Resource providing AQL events table field definitions."""

    def __init__(self):
        self.rest_client = QRadarRestClient()

    @property
    def uri(self) -> str:
        return "qradar://aql/fields/events"

    @property
    def name(self) -> str:
        return "AQL Events Fields"

    @property
    def description(self) -> str:
        return "Field definitions for the QRadar AQL 'events' table. ALWAYS read this resource before generating AQL queries against event data to ensure you use valid field names for this QRadar deployment."

    @property
    def mime_type(self) -> str:
        return "application/json"

    async def read(self) -> Dict[str, Any]:
        """
        Fetch events table fields from QRadar API.

        Returns:
            Dict with field definitions in MCP format
        """
        try:
            log_mcp("Fetching events fields from /ariel/databases/events", level='DEBUG')
            response = await self.rest_client.get('ariel/databases/events')

            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch events fields: {response.status_code} - {response.text}"
                )

            data = response.json()

            # Extract and format field information
            fields = []
            if 'columns' in data:
                for column in data['columns']:
                    field_info = {
                        "name": column.get('name', ''),
                        "type": column.get('type', ''),
                        "description": column.get('description', ''),
                        "argument_type": column.get('argument_type')
                    }
                    fields.append(field_info)

            # Format as MCP resource content
            content = {
                "table": "events",
                "field_count": len(fields),
                "fields": fields,
                "usage": "Use these field names in SELECT, WHERE, GROUP BY, and ORDER BY clauses when querying the events table."
            }

            return {
                "contents": [
                    {
                        "uri": self.uri,
                        "mimeType": self.mime_type,
                        "text": json.dumps(content, indent=2)
                    }
                ]
            }

        except Exception as e:
            log_mcp(f"Error reading events fields resource: {str(e)}", level='ERROR')
            raise


class AQLFlowsFieldsResource(MCPResource):
    """Resource providing AQL flows table field definitions."""

    def __init__(self):
        self.rest_client = QRadarRestClient()

    @property
    def uri(self) -> str:
        return "qradar://aql/fields/flows"

    @property
    def name(self) -> str:
        return "AQL Flows Fields"

    @property
    def description(self) -> str:
        return "Field definitions for the QRadar AQL 'flows' table. ALWAYS read this resource before generating AQL queries against network flow data to ensure you use valid field names for this QRadar deployment."

    @property
    def mime_type(self) -> str:
        return "application/json"

    async def read(self) -> Dict[str, Any]:
        """
        Fetch flows table fields from QRadar API.

        Returns:
            Dict with field definitions in MCP format
        """
        try:
            log_mcp("Fetching flows fields from /ariel/databases/flows", level='DEBUG')
            response = await self.rest_client.get('ariel/databases/flows')

            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch flows fields: {response.status_code} - {response.text}"
                )

            data = response.json()

            # Extract and format field information
            fields = []
            if 'columns' in data:
                for column in data['columns']:
                    field_info = {
                        "name": column.get('name', ''),
                        "type": column.get('type', ''),
                        "description": column.get('description', ''),
                        "argument_type": column.get('argument_type')
                    }
                    fields.append(field_info)

            # Format as MCP resource content
            content = {
                "table": "flows",
                "field_count": len(fields),
                "fields": fields,
                "usage": "Use these field names in SELECT, WHERE, GROUP BY, and ORDER BY clauses when querying the flows table."
            }

            return {
                "contents": [
                    {
                        "uri": self.uri,
                        "mimeType": self.mime_type,
                        "text": json.dumps(content, indent=2)
                    }
                ]
            }

        except Exception as e:
            log_mcp(f"Error reading flows fields resource: {str(e)}", level='ERROR')
            raise
