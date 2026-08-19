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
Base MCP Tool Class

Provides the abstract base class that all MCP tools must inherit from.
Includes production-ready features: structured logging, input sanitization, and audit logging.
"""

import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

import httpx

from qradar_mcp.utils.structured_logger import log_structured
from qradar_mcp.utils.audit_logger import AuditLogger
from qradar_mcp.utils.error_handler import extract_qradar_error
from qradar_mcp.client.qradar_rest_client import QRadarRestClient


class MCPTool(ABC):
    """
    Abstract base class for MCP tools.

    All tools must inherit from this class and implement the required methods.
    """

    # Class-level shared QRadarRestClient instance
    _shared_qradar_client: Optional[QRadarRestClient] = None

    @classmethod
    def set_qradar_client(cls, client: QRadarRestClient):
        """
        Set the shared QRadarRestClient instance for all tools.

        Args:
            client: The QRadarRestClient instance to use
        """
        cls._shared_qradar_client = client

    @property
    def client(self) -> QRadarRestClient:
        """
        Get the shared QRadarRestClient instance.

        Returns:
            The shared QRadarRestClient instance

        Raises:
            RuntimeError: If no client has been set
        """
        if self._shared_qradar_client is None:
            raise RuntimeError("QRadarRestClient not initialized. Call MCPTool.set_qradar_client() first.")
        return self._shared_qradar_client

    @client.setter
    def client(self, value: QRadarRestClient):
        """
        Set the QRadarRestClient instance for this tool instance.

        This setter allows tests to inject mock clients on a per-instance basis.

        Args:
            value: The QRadarRestClient instance (or mock) to use
        """
        self._shared_qradar_client = value

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name (must be unique)."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does."""

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        Return the JSON Schema for the tool's input parameters.

        Example:
            {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of param1"
                    }
                },
                "required": ["param1"]
            }
        """

    @property
    @abstractmethod
    def http_verb(self) -> str:
        """
        Return the HTTP verb used by this tool.

        Must be one of: GET, POST, DELETE, PUT, PATCH

        Returns:
            str: HTTP verb in uppercase
        """

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """
        Return the QRadar API endpoint path for this tool (without /api/ prefix).

        For collection endpoints use the bare path, e.g. "siem/offenses".
        For single-resource endpoints use a template with placeholders,
        e.g. "siem/offenses/{offense_id}".
        """

    @property
    def tool_group(self) -> str:
        """
        Auto-detect tool group from module path.

        Extracts the directory name from the tool's module path.
        For example: qradar_mcp.tools.ariel.get_offense -> "ariel"

        Returns:
            str: Tool group name
        """
        module_path = self.__class__.__module__
        parts = module_path.split('.')

        # Expected format: qradar_mcp.tools.<group>.<tool_name>
        if len(parts) >= 3 and parts[0] == 'qradar_mcp' and parts[1] == 'tools':
            return parts[2]

        # Fallback for tools not in standard structure
        return "unknown"

    @property
    def approval_required(self) -> bool:
        """
        Indicates whether this tool requires user approval before execution.

        By default, all tools require approval for safety. Tools that only
        retrieve or list data (GET operations) should override this to return False.

        Returns:
            bool: True if approval is required (default), False otherwise
        """
        return True

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given arguments.

        This method automatically includes:
        - Structured logging with context
        - Input sanitization
        - Comprehensive audit logging
        - Error handling

        Note: Feature toggle filtering happens during tool registration,
        so this method will only be called for enabled tools.

        Args:
            arguments: Dictionary of input parameters

        Returns:
            Dictionary with MCP response format:
            {
                "content": [
                    {
                        "type": "text",
                        "text": "result text"
                    }
                ],
                "isError": False  # Optional, set to True for errors
            }
        """
        return await self.execute_with_enhancements(arguments)

    @abstractmethod
    async def _execute_impl(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal implementation of tool execution.

        Subclasses must implement this method instead of execute().
        This method receives sanitized arguments and should focus on
        the core tool logic.

        Args:
            arguments: Dictionary of sanitized input parameters

        Returns:
            Dictionary with MCP response format
        """

    async def execute_with_enhancements(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with production enhancements (logging, sanitization, audit).
        This is an opt-in wrapper that tools can use by calling super().execute_with_enhancements()

        Tools that want to use the enhanced execution should:
        1. Rename their execute() method to _execute_impl()
        2. Call super().execute_with_enhancements(arguments) from their execute() method

        Args:
            arguments: Dictionary of input parameters

        Returns:
            Dictionary with MCP response format
        """
        start_time = time.time()

        # Log tool execution start
        log_structured(
            f"Tool execution started: {self.name}",
            level='INFO',
            tool_name=self.name,
            arguments=self._sanitize_log_arguments(arguments)
        )

        try:
            # Sanitize input arguments
            sanitized_args = self._sanitize_arguments(arguments)

            # Execute the actual tool implementation
            result = await self._execute_impl(sanitized_args)

            # Calculate execution time
            duration = time.time() - start_time

            # Log successful execution
            log_structured(
                f"Tool execution completed: {self.name}",
                level='INFO',
                tool_name=self.name,
                duration_seconds=duration
            )

            # Audit log the execution
            AuditLogger.log_tool_execution(
                tool_name=self.name,
                arguments=sanitized_args,
                result=result,
                duration_seconds=duration
            )

            return result

        except httpx.HTTPStatusError as e:
            # Calculate execution time
            duration = time.time() - start_time

            # Extract detailed QRadar error message
            error_msg = extract_qradar_error(e, f"executing {self.name}")

            # Log error
            log_structured(
                f"Tool execution failed: {self.name}",
                level='ERROR',
                tool_name=self.name,
                error=error_msg,
                status_code=e.response.status_code if e.response else None,
                duration_seconds=duration
            )

            # Return error response
            return self.create_error_response(error_msg)

        except (ValueError, KeyError, TypeError, RuntimeError) as e:
            # Calculate execution time
            duration = time.time() - start_time

            # Log error
            log_structured(
                f"Tool execution failed: {self.name}",
                level='ERROR',
                tool_name=self.name,
                error=str(e),
                duration_seconds=duration
            )

            # Audit log the failure
            AuditLogger.log_tool_execution(
                tool_name=self.name,
                arguments=arguments,
                result={'error': str(e)},
                duration_seconds=duration
            )

            # Return error response
            return self.create_error_response(f"Tool execution failed: {str(e)}")


    def to_mcp_tool_definition(self) -> Dict[str, Any]:
        """Convert tool to MCP tool definition format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }

    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize input arguments based on the tool's input schema.
        Override this method in subclasses for custom sanitization logic.

        Args:
            arguments: Raw input arguments

        Returns:
            Sanitized arguments dictionary
        """
        # Default implementation: pass through arguments unchanged
        # Tools can override this method for custom sanitization
        return arguments

    def _sanitize_log_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize arguments for logging (remove sensitive data).
        Override this method in subclasses to customize what gets logged.

        Args:
            arguments: Input arguments

        Returns:
            Sanitized arguments safe for logging
        """
        # Create a copy to avoid modifying original
        sanitized = arguments.copy()

        # Remove common sensitive fields
        sensitive_fields = ['password', 'token', 'secret', 'api_key', 'credential']
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***REDACTED***'

        return sanitized

    def create_success_response(self, text: str) -> Dict[str, Any]:
        """Helper to create a successful response."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }

    def create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Helper to create an error response."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_message
                }
            ],
            "isError": True
        }
