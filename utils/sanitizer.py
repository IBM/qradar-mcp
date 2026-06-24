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
Input Sanitization Utilities

Provides centralized input validation and sanitization for security.
"""

import re
import ipaddress
from typing import Any, Optional
from .mcp_logger import log_mcp


class InputSanitizer:
    """
    Centralized input sanitization for security and data validation.
    """

    # Maximum lengths for various input types
    MAX_STRING_LENGTH = 10000
    MAX_QUERY_LENGTH = 50000
    MAX_NOTE_LENGTH = 10000
    MAX_NAME_LENGTH = 255

    # Patterns for validation
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?@#$%&*()\[\]{}:;\'\"+=<>/\\|~`]+$')
    IP_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    DOMAIN_PATTERN = re.compile(
        r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
        r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    )

    @staticmethod
    def sanitize_string(value: Any, max_length: int = MAX_STRING_LENGTH,
                       allow_special_chars: bool = True) -> str:
        """
        Sanitize a string input.

        Args:
            value: Input value to sanitize
            max_length: Maximum allowed length
            allow_special_chars: Whether to allow special characters

        Returns:
            Sanitized string

        Raises:
            ValueError: If input is invalid
        """
        if value is None:
            return ""

        # Convert to string
        str_value = str(value)

        # Check length
        if len(str_value) > max_length:
            log_mcp(
                f"String exceeds maximum length {max_length}, truncating",
                level='WARNING'
            )
            str_value = str_value[:max_length]

        # Remove control characters
        str_value = ''.join(
            char for char in str_value
            if ord(char) >= 32 or char in '\n\r\t'
        )

        # Check for dangerous patterns if not allowing special chars
        if not allow_special_chars:
            if not InputSanitizer.SAFE_STRING_PATTERN.match(str_value):
                raise ValueError("String contains invalid characters")

        return str_value

    @staticmethod
    def sanitize_integer(value: Any, min_val: Optional[int] = None,
                        max_val: Optional[int] = None) -> int:
        """
        Sanitize an integer input.

        Args:
            value: Input value to sanitize
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Sanitized integer

        Raises:
            ValueError: If input is invalid
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid integer value: {value}") from e

        if min_val is not None and int_value < min_val:
            raise ValueError(f"Value {int_value} is less than minimum {min_val}")

        if max_val is not None and int_value > max_val:
            raise ValueError(f"Value {int_value} is greater than maximum {max_val}")

        return int_value

    @staticmethod
    def sanitize_boolean(value: Any) -> bool:
        """
        Sanitize a boolean input.

        Args:
            value: Input value to sanitize

        Returns:
            Sanitized boolean
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')

        return bool(value)

    @staticmethod
    def sanitize_ip_address(value: str) -> str:
        """
        Sanitize and validate an IP address (IPv4 or IPv6).

        Args:
            value: IP address string

        Returns:
            Sanitized IP address

        Raises:
            ValueError: If IP address is invalid
        """
        if not value:
            raise ValueError("IP address cannot be empty")

        # Use ipaddress module for comprehensive IPv4 and IPv6 validation
        try:
            # This validates both IPv4 and IPv6 addresses
            ip_obj = ipaddress.ip_address(value)
            return str(ip_obj)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {value}") from e

    @staticmethod
    def sanitize_aql_query(query: str) -> str:
        """
        Sanitize an AQL query.

        Args:
            query: AQL query string

        Returns:
            Sanitized query

        Raises:
            ValueError: If query is invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Check length
        if len(query) > InputSanitizer.MAX_QUERY_LENGTH:
            raise ValueError(
                f"Query exceeds maximum length of {InputSanitizer.MAX_QUERY_LENGTH}"
            )

        # Remove control characters except newlines and tabs
        query = ''.join(
            char for char in query
            if ord(char) >= 32 or char in '\n\r\t'
        )

        # Basic SQL injection prevention (AQL is SQL-like)
        dangerous_patterns = [
            r';\s*DROP\s+',
            r';\s*DELETE\s+',
            r';\s*UPDATE\s+',
            r';\s*INSERT\s+',
            r'--',  # SQL comments
            r'/\*',  # Multi-line comments
        ]

        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper):
                log_mcp(
                    f"Potentially dangerous pattern detected in query: {pattern}",
                    level='WARNING'
                )
                # Don't reject, but log for audit

        return query.strip()

    @staticmethod
    def _sanitize_string_field(key: str, value: Any, constraints: dict) -> str:
        max_length = constraints.get(
            'max_length',
            InputSanitizer.MAX_STRING_LENGTH
        )
        sanitized_value = InputSanitizer.sanitize_string(value, max_length)

        # Check enum constraint
        if 'enum' in constraints:
            if sanitized_value not in constraints['enum']:
                raise ValueError(
                    f"Invalid value for {key}: {sanitized_value}"
                )

        return sanitized_value

    @staticmethod
    def _sanitize_integer_field(key: str, value: Any, constraints: dict) -> int:
        min_val = constraints.get('min')
        max_val = constraints.get('max')
        try:
            return InputSanitizer.sanitize_integer(value, min_val, max_val)
        except ValueError as e:
            raise ValueError(f"Invalid value for {key}: {e}") from e

    @staticmethod
    def sanitize_dict(data: dict, schema: dict) -> dict:
        """
        Sanitize a dictionary based on a schema.

        Args:
            data: Input dictionary
            schema: Schema defining expected types and constraints

        Returns:
            Sanitized dictionary

        Example schema:
            {
                'offense_id': {'type': 'integer', 'min': 0},
                'note_text': {'type': 'string', 'max_length': 1000},
                'status': {'type': 'string', 'enum': ['OPEN', 'CLOSED']}
            }
        """
        sanitized = {}

        for key, constraints in schema.items():
            if key not in data:
                if constraints.get('required', False):
                    raise ValueError(f"Required field '{key}' is missing")
                continue

            value = data[key]
            field_type = constraints.get('type', 'string')

            if field_type == 'string':
                sanitized[key] = InputSanitizer._sanitize_string_field(
                    key, value, constraints
                )

            elif field_type == 'integer':
                sanitized[key] = InputSanitizer._sanitize_integer_field(
                    key, value, constraints
                )

            elif field_type == 'boolean':
                sanitized[key] = InputSanitizer.sanitize_boolean(value)

            elif field_type == 'ip':
                sanitized[key] = InputSanitizer.sanitize_ip_address(value)

        return sanitized
