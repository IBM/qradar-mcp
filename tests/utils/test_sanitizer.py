"""
Tests for input sanitization utilities
"""

import pytest
from unittest.mock import patch

from qradar_mcp.utils.sanitizer import InputSanitizer


class TestSanitizeString:
    """Test sanitize_string method"""

    def test_sanitize_valid_string(self):
        """Test sanitizing a valid string"""
        result = InputSanitizer.sanitize_string("Hello World")
        assert result == "Hello World"

    def test_sanitize_none_returns_empty(self):
        """Test that None returns empty string"""
        result = InputSanitizer.sanitize_string(None)
        assert result == ""

    def test_sanitize_converts_to_string(self):
        """Test that non-string values are converted"""
        result = InputSanitizer.sanitize_string(123)
        assert result == "123"

        result = InputSanitizer.sanitize_string(45.67)
        assert result == "45.67"

    @patch('qradar_mcp.utils.sanitizer.log_mcp')
    def test_sanitize_truncates_long_string(self, mock_log_mcp):
        """Test that strings exceeding max length are truncated"""
        long_string = "a" * 15000
        result = InputSanitizer.sanitize_string(long_string, max_length=10000)

        assert len(result) == 10000
        assert mock_log_mcp.called
        assert "truncating" in str(mock_log_mcp.call_args[0][0]).lower()

    def test_sanitize_removes_control_characters(self):
        """Test that control characters are removed"""
        # ASCII control characters (0-31) except \n, \r, \t
        text_with_control = "Hello\x00\x01\x02World"
        result = InputSanitizer.sanitize_string(text_with_control)
        assert result == "HelloWorld"

    def test_sanitize_preserves_newlines_tabs(self):
        """Test that newlines and tabs are preserved"""
        text = "Hello\nWorld\tTest\r\n"
        result = InputSanitizer.sanitize_string(text)
        assert "\n" in result
        assert "\t" in result
        assert "\r" in result

    def test_sanitize_with_special_chars_allowed(self):
        """Test sanitization with special characters allowed"""
        text = "Hello! @#$%^&*() World"
        result = InputSanitizer.sanitize_string(text, allow_special_chars=True)
        assert result == text

    def test_sanitize_with_special_chars_disallowed_valid(self):
        """Test sanitization with special chars disallowed but valid input"""
        text = "Hello World 123"
        result = InputSanitizer.sanitize_string(text, allow_special_chars=False)
        assert result == text

    def test_sanitize_with_special_chars_disallowed_invalid(self):
        """Test that invalid chars raise error when special chars disallowed"""
        # Use a character not in SAFE_STRING_PATTERN (e.g., emoji or special unicode)
        text = "Hello 😀 World"
        with pytest.raises(ValueError, match="invalid characters"):
            InputSanitizer.sanitize_string(text, allow_special_chars=False)

    def test_sanitize_custom_max_length(self):
        """Test sanitization with custom max length"""
        text = "Hello World"
        result = InputSanitizer.sanitize_string(text, max_length=5)
        assert len(result) <= 5


class TestSanitizeInteger:
    """Test sanitize_integer method"""

    def test_sanitize_valid_integer(self):
        """Test sanitizing a valid integer"""
        result = InputSanitizer.sanitize_integer(42)
        assert result == 42

    def test_sanitize_string_to_integer(self):
        """Test converting string to integer"""
        result = InputSanitizer.sanitize_integer("123")
        assert result == 123

    def test_sanitize_float_to_integer(self):
        """Test converting float to integer"""
        result = InputSanitizer.sanitize_integer(42.7)
        assert result == 42

    def test_sanitize_invalid_integer(self):
        """Test that invalid values raise ValueError"""
        with pytest.raises(ValueError, match="Invalid integer value"):
            InputSanitizer.sanitize_integer("not a number")

    def test_sanitize_none_raises_error(self):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError, match="Invalid integer value"):
            InputSanitizer.sanitize_integer(None)

    def test_sanitize_with_min_value(self):
        """Test integer with minimum value constraint"""
        result = InputSanitizer.sanitize_integer(10, min_val=5)
        assert result == 10

    def test_sanitize_below_min_value(self):
        """Test that value below minimum raises error"""
        with pytest.raises(ValueError, match="less than minimum"):
            InputSanitizer.sanitize_integer(3, min_val=5)

    def test_sanitize_with_max_value(self):
        """Test integer with maximum value constraint"""
        result = InputSanitizer.sanitize_integer(10, max_val=20)
        assert result == 10

    def test_sanitize_above_max_value(self):
        """Test that value above maximum raises error"""
        with pytest.raises(ValueError, match="greater than maximum"):
            InputSanitizer.sanitize_integer(25, max_val=20)

    def test_sanitize_with_min_and_max(self):
        """Test integer with both min and max constraints"""
        result = InputSanitizer.sanitize_integer(15, min_val=10, max_val=20)
        assert result == 15

    def test_sanitize_negative_integer(self):
        """Test sanitizing negative integers"""
        result = InputSanitizer.sanitize_integer(-42)
        assert result == -42


class TestSanitizeBoolean:
    """Test sanitize_boolean method"""

    def test_sanitize_true_boolean(self):
        """Test sanitizing True boolean"""
        result = InputSanitizer.sanitize_boolean(True)
        assert result is True

    def test_sanitize_false_boolean(self):
        """Test sanitizing False boolean"""
        result = InputSanitizer.sanitize_boolean(False)
        assert result is False

    def test_sanitize_string_true_variations(self):
        """Test various string representations of true"""
        for value in ['true', 'True', 'TRUE', '1', 'yes', 'YES', 'on', 'ON']:
            result = InputSanitizer.sanitize_boolean(value)
            assert result is True, f"Failed for value: {value}"

    def test_sanitize_string_false_variations(self):
        """Test various string representations of false"""
        for value in ['false', 'False', 'FALSE', '0', 'no', 'NO', 'off', 'OFF']:
            result = InputSanitizer.sanitize_boolean(value)
            assert result is False, f"Failed for value: {value}"

    def test_sanitize_integer_to_boolean(self):
        """Test converting integers to boolean"""
        assert InputSanitizer.sanitize_boolean(1) is True
        assert InputSanitizer.sanitize_boolean(0) is False
        assert InputSanitizer.sanitize_boolean(42) is True

    def test_sanitize_none_to_boolean(self):
        """Test converting None to boolean"""
        result = InputSanitizer.sanitize_boolean(None)
        assert result is False

    def test_sanitize_empty_string_to_boolean(self):
        """Test converting empty string to boolean"""
        result = InputSanitizer.sanitize_boolean("")
        assert result is False


class TestSanitizeIpAddress:
    """Test sanitize_ip_address method"""

    def test_sanitize_valid_ipv4(self):
        """Test sanitizing valid IPv4 addresses"""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "255.255.255.255",
            "0.0.0.0"
        ]
        for ip in valid_ips:
            result = InputSanitizer.sanitize_ip_address(ip)
            assert result == ip, f"Failed for IP: {ip}"

    def test_sanitize_empty_ip(self):
        """Test that empty IP raises error"""
        with pytest.raises(ValueError, match="cannot be empty"):
            InputSanitizer.sanitize_ip_address("")

    def test_sanitize_none_ip(self):
        """Test that None IP raises error"""
        with pytest.raises((ValueError, AttributeError)):
            InputSanitizer.sanitize_ip_address(None)  # type: ignore

    def test_sanitize_invalid_ip_format(self):
        """Test that invalid IP format raises error"""
        invalid_ips = [
            "256.1.1.1",  # Octet > 255
            "192.168.1",  # Missing octet
            "192.168.1.1.1",  # Too many octets
            "abc.def.ghi.jkl",  # Non-numeric
            "192.168.-1.1",  # Negative octet
        ]
        for ip in invalid_ips:
            with pytest.raises(ValueError, match="Invalid IP address"):
                InputSanitizer.sanitize_ip_address(ip)

    def test_sanitize_valid_ipv6(self):
        """Test sanitizing valid IPv6 addresses"""
        valid_ipv6 = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:db8:85a3::8a2e:370:7334",  # Compressed
            "::1",  # Loopback
            "::",  # All zeros
            "fe80::1",  # Link-local
            "::ffff:192.0.2.1",  # IPv4-mapped IPv6
        ]
        for ip in valid_ipv6:
            result = InputSanitizer.sanitize_ip_address(ip)
            # Result may be normalized (e.g., compressed form)
            assert result is not None, f"Failed for IPv6: {ip}"

    def test_sanitize_invalid_ipv6_format(self):
        """Test that invalid IPv6 format raises error"""
        invalid_ipv6 = [
            "2001:0db8:85a3::8a2e:370g:7334",  # Invalid hex character 'g'
            "2001:0db8:85a3::8a2e::7334",  # Double compression
            "gggg::1",  # Invalid hex
            "2001:db8:85a3:0:0:8a2e:370:7334:extra",  # Too many groups
        ]
        for ip in invalid_ipv6:
            with pytest.raises(ValueError, match="Invalid IP address"):
                InputSanitizer.sanitize_ip_address(ip)


class TestSanitizeAqlQuery:
    """Test sanitize_aql_query method"""

    def test_sanitize_valid_query(self):
        """Test sanitizing a valid AQL query"""
        query = "SELECT sourceip FROM events LAST 1 HOURS"
        result = InputSanitizer.sanitize_aql_query(query)
        assert result == query

    def test_sanitize_empty_query(self):
        """Test that empty query raises error"""
        with pytest.raises(ValueError, match="cannot be empty"):
            InputSanitizer.sanitize_aql_query("")

    def test_sanitize_whitespace_only_query(self):
        """Test that whitespace-only query raises error"""
        with pytest.raises(ValueError, match="cannot be empty"):
            InputSanitizer.sanitize_aql_query("   \n\t   ")

    def test_sanitize_query_too_long(self):
        """Test that query exceeding max length raises error"""
        long_query = "SELECT * FROM events WHERE " + "a" * 60000
        with pytest.raises(ValueError, match="exceeds maximum length"):
            InputSanitizer.sanitize_aql_query(long_query)

    def test_sanitize_query_removes_control_chars(self):
        """Test that control characters are removed from query"""
        query = "SELECT\x00 sourceip\x01 FROM events"
        result = InputSanitizer.sanitize_aql_query(query)
        assert "\x00" not in result
        assert "\x01" not in result

    def test_sanitize_query_preserves_newlines(self):
        """Test that newlines and tabs are preserved"""
        query = "SELECT sourceip\nFROM events\nWHERE sourceip='1.2.3.4'"
        result = InputSanitizer.sanitize_aql_query(query)
        assert "\n" in result

    def test_sanitize_query_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped"""
        query = "  SELECT sourceip FROM events  \n"
        result = InputSanitizer.sanitize_aql_query(query)
        assert result == "SELECT sourceip FROM events"

    @patch('qradar_mcp.utils.sanitizer.log_mcp')
    def test_sanitize_query_logs_dangerous_patterns(self, mock_log_mcp):
        """Test that dangerous patterns are logged"""
        dangerous_queries = [
            "SELECT * FROM events; DROP TABLE users",
            "SELECT * FROM events; DELETE FROM logs",
            "SELECT * FROM events; UPDATE users SET admin=1",
            "SELECT * FROM events; INSERT INTO logs VALUES (1)",
            "SELECT * FROM events -- comment",
            "SELECT * FROM events /* comment */",
        ]

        for query in dangerous_queries:
            result = InputSanitizer.sanitize_aql_query(query)
            # Should not raise error, but should log
            assert result is not None

        # Check that logging was called
        assert mock_log_mcp.called


class TestSanitizeDict:
    """Test sanitize_dict method"""

    def test_sanitize_dict_with_string_field(self):
        """Test sanitizing dict with string field"""
        schema = {
            'name': {'type': 'string', 'max_length': 100}
        }
        data = {'name': 'Test Name'}

        result = InputSanitizer.sanitize_dict(data, schema)
        assert result['name'] == 'Test Name'

    def test_sanitize_dict_with_integer_field(self):
        """Test sanitizing dict with integer field"""
        schema = {
            'offense_id': {'type': 'integer', 'min': 0}
        }
        data = {'offense_id': '42'}

        result = InputSanitizer.sanitize_dict(data, schema)
        assert result['offense_id'] == 42

    def test_sanitize_dict_with_boolean_field(self):
        """Test sanitizing dict with boolean field"""
        schema = {
            'enabled': {'type': 'boolean'}
        }
        data = {'enabled': 'true'}

        result = InputSanitizer.sanitize_dict(data, schema)
        assert result['enabled'] is True

    def test_sanitize_dict_with_ip_field(self):
        """Test sanitizing dict with IP address field"""
        schema = {
            'source_ip': {'type': 'ip'}
        }
        data = {'source_ip': '192.168.1.1'}

        result = InputSanitizer.sanitize_dict(data, schema)
        assert result['source_ip'] == '192.168.1.1'

    def test_sanitize_dict_with_enum(self):
        """Test sanitizing dict with enum constraint"""
        schema = {
            'status': {'type': 'string', 'enum': ['OPEN', 'CLOSED']}
        }
        data = {'status': 'OPEN'}

        result = InputSanitizer.sanitize_dict(data, schema)
        assert result['status'] == 'OPEN'

    def test_sanitize_dict_with_invalid_enum(self):
        """Test that invalid enum value raises error"""
        schema = {
            'status': {'type': 'string', 'enum': ['OPEN', 'CLOSED']}
        }
        data = {'status': 'INVALID'}

        with pytest.raises(ValueError, match="Invalid value"):
            InputSanitizer.sanitize_dict(data, schema)

    def test_sanitize_dict_missing_required_field(self):
        """Test that missing required field raises error"""
        schema = {
            'offense_id': {'type': 'integer', 'required': True}
        }
        data = {}

        with pytest.raises(ValueError, match="Required field"):
            InputSanitizer.sanitize_dict(data, schema)

    def test_sanitize_dict_missing_optional_field(self):
        """Test that missing optional field is skipped"""
        schema = {
            'note': {'type': 'string', 'required': False}
        }
        data = {}

        result = InputSanitizer.sanitize_dict(data, schema)
        assert 'note' not in result

    def test_sanitize_dict_multiple_fields(self):
        """Test sanitizing dict with multiple fields"""
        schema = {
            'offense_id': {'type': 'integer', 'min': 0},
            'note_text': {'type': 'string', 'max_length': 1000},
            'status': {'type': 'string', 'enum': ['OPEN', 'CLOSED']},
            'enabled': {'type': 'boolean'}
        }
        data = {
            'offense_id': '123',
            'note_text': 'Test note',
            'status': 'OPEN',
            'enabled': 'true'
        }

        result = InputSanitizer.sanitize_dict(data, schema)
        assert result['offense_id'] == 123
        assert result['note_text'] == 'Test note'
        assert result['status'] == 'OPEN'
        assert result['enabled'] is True

    def test_sanitize_dict_with_constraints(self):
        """Test sanitizing dict with min/max constraints"""
        schema = {
            'count': {'type': 'integer', 'min': 1, 'max': 100}
        }
        data = {'count': '50'}

        result = InputSanitizer.sanitize_dict(data, schema)
        assert result['count'] == 50


class TestInputSanitizerConstants:
    """Test InputSanitizer class constants"""

    def test_max_lengths_defined(self):
        """Test that max length constants are defined"""
        assert InputSanitizer.MAX_STRING_LENGTH == 10000
        assert InputSanitizer.MAX_QUERY_LENGTH == 50000
        assert InputSanitizer.MAX_NOTE_LENGTH == 10000
        assert InputSanitizer.MAX_NAME_LENGTH == 255

    def test_patterns_defined(self):
        """Test that regex patterns are defined"""
        assert InputSanitizer.SAFE_STRING_PATTERN is not None
        assert InputSanitizer.IP_PATTERN is not None
        assert InputSanitizer.DOMAIN_PATTERN is not None