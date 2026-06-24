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
AQL Functions Resource

Provides dynamic access to QRadar AQL function definitions.
"""

import json
from typing import Dict, Any

from qradar_mcp.utils.mcp_logger import log_mcp
from qradar_mcp.client.qradar_rest_client import QRadarRestClient

from .base import MCPResource


class AQLFunctionsResource(MCPResource):
    """Resource providing AQL function definitions."""

    def __init__(self):
        self.rest_client = QRadarRestClient()

    @property
    def uri(self) -> str:
        return "qradar://aql/functions"

    @property
    def name(self) -> str:
        return "AQL Functions"

    @property
    def description(self) -> str:
        return "Available AQL functions for data retrieval, aggregation, and transformation. Use these functions to enrich queries and perform calculations."

    @property
    def mime_type(self) -> str:
        return "application/json"

    async def read(self) -> Dict[str, Any]:
        """
        Fetch AQL functions from QRadar API.

        Returns:
            Dict with function definitions in MCP format
        """
        try:
            log_mcp("Fetching AQL functions from /ariel/functions", level='DEBUG')
            response = await self.rest_client.get('ariel/functions')

            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch AQL functions: {response.status_code} - {response.text}"
                )

            data = response.json()

            # Extract and format function information
            functions = []
            if isinstance(data, list):
                for func in data:
                    func_info = {
                        "name": func.get('name', ''),
                        "description": func.get('description', ''),
                        "return_data_type": func.get('return_data_type', ''),
                        "argument_types": func.get('argument_types', []),
                        "database_type": func.get('database_type', '')
                    }
                    functions.append(func_info)

            # Categorize functions
            data_retrieval = [f for f in functions if f.get('database_type') == 'COMMON']
            aggregation = [f for f in functions if f['name'].upper() in
                          ['AVG', 'MAX', 'MIN', 'SUM', 'COUNT', 'DISTINCTCOUNT', 'UNIQUECOUNT', 'FIRST', 'LAST']]
            other = [f for f in functions if f not in data_retrieval and f not in aggregation]

            # Format as MCP resource content
            content = {
                "total_functions": len(functions),
                "categories": {
                    "data_retrieval": {
                        "description": "Functions for enriching data (e.g., LOGSOURCENAME, CATEGORYNAME, QIDDESCRIPTION)",
                        "count": len(data_retrieval),
                        "functions": data_retrieval
                    },
                    "aggregation": {
                        "description": "Functions for aggregating data (e.g., COUNT, SUM, AVG, UNIQUECOUNT)",
                        "count": len(aggregation),
                        "functions": aggregation
                    },
                    "other": {
                        "description": "Other utility functions",
                        "count": len(other),
                        "functions": other
                    }
                },
                "usage": "Use these functions in SELECT clauses, WHERE conditions, and GROUP BY/HAVING clauses to enrich and transform query results."
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
            log_mcp(f"Error reading AQL functions resource: {str(e)}", level='ERROR')
            raise
