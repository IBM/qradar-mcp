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
Input Validators

Utilities for validating input parameters before making API calls.
"""

import ipaddress
import re
from typing import Optional, List, Any


def validate_offense_id(offense_id: Any) -> bool:
    """
    Validate offense ID is a positive integer.

    Args:
        offense_id: The offense ID to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        id_int = int(offense_id)
        return id_int >= 0
    except (ValueError, TypeError):
        return False


def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 or IPv6 address format.

    Args:
        ip: IP address string to validate

    Returns:
        True if valid IPv4 or IPv6, False otherwise
    """
    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, ip):
        # Check each octet is 0-255
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)

    # IPv6 pattern (simplified)
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'
    if re.match(ipv6_pattern, ip):
        return True

    # IPv6 with :: compression
    if '::' in ip:
        parts = ip.split('::')
        if len(parts) == 2:
            return True

    return False


def validate_path_segment(value: str, param_name: str) -> str:
    """
    Validate that a string value is safe to interpolate into a URL path segment.

    Rejects values containing path traversal sequences (`..`), forward slashes
    (`/`), or backslashes (`\\`) so that user-supplied parameters cannot escape
    their intended API path prefix.

    Args:
        value: The string to validate.
        param_name: Name of the parameter (used in the error message).

    Returns:
        The original `value` unchanged if it is safe.

    Raises:
        ValueError: If `value` contains a disallowed character or sequence.
    """
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(
            f"Invalid value for '{param_name}': path traversal characters are not allowed"
        )
    return value


def validate_cidr(cidr: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a string is a well-formed CIDR network notation.

    Accepts both IPv4 (e.g. 192.168.1.0/24) and IPv6 (e.g. 2001:db8::/32)
    notation. Uses `strict=False` so host bits being set (e.g. 192.168.1.5/24)
    is accepted rather than rejected — QRadar normalises these on import.

    Args:
        cidr: The CIDR string to validate.

    Returns:
        Tuple of (is_valid, error_message). error_message is None when valid.
    """
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True, None
    except ValueError:
        return False, f"Invalid CIDR notation: '{cidr}'"


def validate_aql_query(query: str) -> tuple[bool, Optional[str]]:
    """
    Perform basic validation of AQL query syntax.

    Args:
        query: AQL query string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"

    query_lower = query.lower().strip()

    # Must start with SELECT
    if not query_lower.startswith('select'):
        return False, "Query must start with SELECT"

    # Must contain FROM
    if ' from ' not in query_lower:
        return False, "Query must contain FROM clause"

    # Check for balanced parentheses
    if query.count('(') != query.count(')'):
        return False, "Unbalanced parentheses in query"

    # Check for balanced quotes
    single_quotes = query.count("'")
    if single_quotes % 2 != 0:
        return False, "Unbalanced single quotes in query"

    return True, None


def validate_status(status: str) -> bool:
    """
    Validate offense status value.

    Args:
        status: Status string to validate

    Returns:
        True if valid status, False otherwise
    """
    valid_statuses = ['OPEN', 'HIDDEN', 'CLOSED']
    return status.upper() in valid_statuses


def validate_severity(severity: Any) -> bool:
    """
    Validate severity value (1-10).

    Args:
        severity: Severity value to validate

    Returns:
        True if valid severity, False otherwise
    """
    try:
        sev_int = int(severity)
        return 1 <= sev_int <= 10
    except (ValueError, TypeError):
        return False


def validate_range(start: int, end: int) -> tuple[bool, Optional[str]]:
    """
    Validate range parameters for pagination.

    Args:
        start: Starting index
        end: Ending index

    Returns:
        Tuple of (is_valid, error_message)
    """
    if start < 0:
        return False, "Start index must be non-negative"

    if end < start:
        return False, "End index must be greater than or equal to start index"

    if end - start > 10000:
        return False, "Range too large (max 10000 items)"

    return True, None


def validate_element_type(element_type: str) -> bool:
    """
    Validate reference data element type.

    Args:
        element_type: Element type string to validate

    Returns:
        True if valid element type, False otherwise
    """
    valid_types = [
        'ALN',  # Alphanumeric
        'NUM',  # Numeric
        'IP',   # IP Address
        'PORT', # Port
        'DATE'  # Date
    ]
    return element_type.upper() in valid_types


def validate_timeout_type(timeout_type: str) -> bool:
    """
    Validate reference data timeout type.

    Args:
        timeout_type: Timeout type string to validate

    Returns:
        True if valid timeout type, False otherwise
    """
    valid_types = [
        'UNKNOWN',
        'FIRST_SEEN',
        'LAST_SEEN'
    ]
    return timeout_type.upper() in valid_types


def validate_field_name(field_name: str, allowed_fields: Optional[List[str]] = None) -> bool:
    """
    Validate field name format and optionally check against allowed list.

    Args:
        field_name: Field name to validate
        allowed_fields: Optional list of allowed field names

    Returns:
        True if valid field name, False otherwise
    """
    # Basic format check - alphanumeric and underscores
    if not re.match(r'^[a-zA-Z_]\w*$', field_name):
        return False

    # Check against allowed list if provided
    if allowed_fields is not None:
        return field_name in allowed_fields

    return True


def validate_filter_expression(filter_expr: str) -> tuple[bool, Optional[str]]:
    """
    Perform basic validation of AQL filter expression.

    Args:
        filter_expr: Filter expression to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filter_expr or not filter_expr.strip():
        return False, "Filter expression cannot be empty"

    # Check for balanced parentheses
    if filter_expr.count('(') != filter_expr.count(')'):
        return False, "Unbalanced parentheses in filter"

    # Check for balanced quotes
    single_quotes = filter_expr.count("'")
    if single_quotes % 2 != 0:
        return False, "Unbalanced single quotes in filter"

    double_quotes = filter_expr.count('"')
    if double_quotes % 2 != 0:
        return False, "Unbalanced double quotes in filter"

    return True, None


def validate_sort_expression(sort_expr: str) -> tuple[bool, Optional[str]]:
    """
    Validate sort expression format.

    Args:
        sort_expr: Sort expression to validate (e.g., "+field1,-field2")

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not sort_expr or not sort_expr.strip():
        return False, "Sort expression cannot be empty"

    # Split by comma
    fields = [f.strip() for f in sort_expr.split(',')]

    for field in fields:
        # Check if starts with + or -
        if field[0] in ['+', '-']:
            field_name = field[1:]
        else:
            field_name = field

        # Validate field name format
        if not re.match(r'^[a-zA-Z_]\w*(\([\w,]+\))?$', field_name):
            return False, f"Invalid field name in sort expression: {field}"

    return True, None


def validate_note_text(note_text: str, max_length: int = 10000) -> tuple[bool, Optional[str]]:
    """
    Validate offense note text.

    Args:
        note_text: Note text to validate
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not note_text or not note_text.strip():
        return False, "Note text cannot be empty"

    if len(note_text) > max_length:
        return False, f"Note text exceeds maximum length of {max_length} characters"

    return True, None


def validate_search_id(search_id: str) -> bool:
    """
    Validate Ariel search ID format.

    Args:
        search_id: Search ID to validate

    Returns:
        True if valid format, False otherwise
    """
    # Search IDs typically start with 's' followed by numbers
    # or can be UUIDs
    if re.match(r'^s\d+$', search_id):
        return True

    # UUID format
    uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    if re.match(uuid_pattern, search_id):
        return True

    return False


def escape_filter_value(value: str, delimiter: str = "'") -> str:
    """
    Escape a user-supplied string for safe interpolation into a QRadar API
    filter expression.

    QRadar filter expressions delimit string literals with single quotes (default)
    or double quotes. An unescaped quote matching the delimiter terminates the
    literal early, allowing arbitrary filter logic to be injected. This function
    escapes every occurrence of the delimiter with a backslash so the value is
    treated as a literal string by the API.

    Args:
        value: The raw user-supplied string to embed in the filter.
        delimiter: The quote character used to delimit the filter value
            (`'` or `"`). Defaults to `'`.

    Returns:
        The value with all occurrences of `delimiter` backslash-escaped.
    """
    return value.replace(delimiter, f"\\{delimiter}")
