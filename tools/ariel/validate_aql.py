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
Validate AQL Tool

Validates AQL query syntax using QRadar's validation endpoint.
"""

from typing import Dict, Any

from qradar_mcp.tools.base import MCPTool
from qradar_mcp.tools.schema import schema


class ValidateAQLTool(MCPTool):
    """Tool for validating AQL query syntax."""

    @property
    def name(self) -> str:
        return "validate_aql"

    @property
    def description(self) -> str:
        return """Validate AQL (Ariel Query Language) query syntax before execution.

REQUIRED WORKFLOW: Always use this tool to validate AQL queries BEFORE using create_ariel_search.

Use cases:
  - Verify AQL syntax is correct before creating a search
  - Check for common AQL errors and get helpful error messages
  - Validate queries generated from natural language
  - Ensure queries will execute successfully

This tool uses QRadar's built-in AQL validator to check query syntax without executing the query.
Validation prevents wasted searches and provides helpful error messages with suggestions."""

    @property
    def input_schema(self) -> Dict[str, Any]:
        return (schema()
            .string("query_expression")
                .description("The AQL query to validate (e.g., 'SELECT sourceip FROM events LAST 1 HOURS')")
                .required()
            .build())

    @property
    def http_verb(self) -> str:
        return "POST"

    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an AQL query.

        Args:
            arguments: Dict containing:
                - query_expression: The AQL query to validate

        Returns:
            Dict with validation results
        """
        query_expression = arguments.get('query_expression')

        if not query_expression:
            return self._create_error_response("Error: query_expression is required")

        # Call QRadar AQL validation endpoint with query parameters
        response = await self.client.post(
            'ariel/validators/aql',
            params={'query_expression': query_expression}
        )

        if response.status_code == 200:
            return self._handle_success_response(response.json(), query_expression)

        if response.status_code == 422:
            return self._handle_422_error(response.json(), query_expression)

        # Unexpected error
        return self._create_error_response(
            f"Error validating AQL query: {response.status_code} - {response.text}"
        )

    def _create_error_response(self, text: str) -> Dict[str, Any]:
        """Create a standard error response."""
        return {
            "content": [{"type": "text", "text": text}],
            "isError": True
        }

    def _handle_success_response(self, result: Dict[str, Any], query_expression: str) -> Dict[str, Any]:
        """Handle successful validation response (status 200)."""
        error_messages = result.get('error_messages', [])

        if error_messages:
            return self._handle_validation_errors(error_messages, query_expression)

        # Query is valid - check for warnings
        return self._create_success_response(result.get('warnings', []), query_expression)

    def _handle_validation_errors(self, error_messages: list, query_expression: str) -> Dict[str, Any]:
        """Handle validation errors from QRadar (200 status with error_messages)."""
        error_details = [
            f"[{error.get('severity', 'ERROR')}] {error.get('message', 'Unknown error')}"
            for error in error_messages
        ]

        error_text = "✗ AQL validation failed:\n\n" + "\n\n".join(error_details)
        guidance = self._get_recovery_guidance()

        return self._create_error_response(
            f"{error_text}\n\nQuery: {query_expression}{guidance}"
        )

    def _create_success_response(self, warnings: list, query_expression: str) -> Dict[str, Any]:
        """Create a success response with optional warnings."""
        warning_text = ""
        if warnings:
            warning_text = "\n\nWarnings:\n" + "\n".join(f"- {w}" for w in warnings)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"✓ AQL query is valid{warning_text}\n\nQuery: {query_expression}"
                }
            ]
        }

    def _handle_422_error(self, error_data: Dict[str, Any], query_expression: str) -> Dict[str, Any]:
        """Handle 422 validation error response."""
        error_message = error_data.get('message', 'Unknown validation error')
        error_text = f"✗ AQL validation failed:\n\n{error_message}"

        details = error_data.get('details', {})
        if details:
            error_text += f"\n\nDetails: {details}"

        return self._create_error_response(f"{error_text}\n\nQuery: {query_expression}")

    @staticmethod
    def _get_recovery_guidance() -> str:
        """Get guidance text for LLM to recover from validation errors."""
        return (
            "\n\nNEXT STEPS:\n"
            "1. Review the error messages above carefully\n"
            "2. Refer to the AQL guide (qradar://aql/guide) you loaded earlier for syntax rules\n"
            "3. Check the field and function names against the AQL field and functions resources you should have in context\n"
            "4. Generate the query following the correct AQL construction steps\n"
            "5. Validate the corrected query again before executing\n"
            "\nIf you haven't loaded the AQL resources yet, do so now before regenerating the query.\n"
        )
