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
Tests for server.py

Tests the FastMCP server initialization, factory methods, and resource functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from qradar_mcp.server import mcp, app
from qradar_mcp.utils.feature_toggle_manager import FeatureToggleManager

class TestMCPServerInitialization:
    """Test FastMCP server initialization."""

    def test_mcp_server_exists(self):
        """Test that MCP server is initialized."""
        assert mcp is not None
        assert hasattr(mcp, 'name')
        assert mcp.name == "qradar-mcp"

    def test_mcp_server_version(self):
        """Test that MCP server has correct version."""
        assert hasattr(mcp, 'version')
        assert mcp.version == "1.0.0"

    def test_app_has_middleware(self):
        """Test that app is created with middleware."""
        assert app is not None
        # App should be an ASGI application
        assert callable(app)


class TestResourceRegistration:
    """Test the register_resources function and resource registration logic."""

    @patch('qradar_mcp.server.log_structured')
    @patch('qradar_mcp.server.AQLEventsFieldsResource')
    @patch('qradar_mcp.server.AQLFlowsFieldsResource')
    @patch('qradar_mcp.server.AQLFunctionsResource')
    @patch('qradar_mcp.server.AQLGenerationGuideResource')
    def test_register_resources_with_mixed_toggles(
        self,
        mock_guide_resource,
        mock_functions_resource,
        mock_flows_resource,
        mock_events_resource,
        mock_log_structured
    ):
        """Test that register_resources respects feature toggles."""
        # Create a mock toggle manager with mixed settings
        mock_toggle_manager = Mock(spec=FeatureToggleManager)
        mock_toggle_manager.resource_toggles = {
            'aql_events_fields': True,
            'aql_flows_fields': False,
            'aql_functions': True,
            'aql_generation_guide': False,
            'api_query_syntax': False,
        }

        # Mock the resource read methods
        for mock_resource_class in [mock_events_resource, mock_flows_resource,
                                     mock_functions_resource, mock_guide_resource]:
            mock_instance = Mock()
            mock_instance.read.return_value = {"contents": [{"text": "test"}]}
            mock_resource_class.return_value = mock_instance

        # Create a mock MCP server
        mock_mcp = MagicMock()

        # Import and execute register_resources logic
        from qradar_mcp.server import register_resources

        # Patch the toggle_manager and mcp in the server module
        with patch('qradar_mcp.server.toggle_manager', mock_toggle_manager), \
             patch('qradar_mcp.server.mcp', mock_mcp):
            register_resources()

        # Verify log_structured was called with summary
        summary_calls = [
            call for call in mock_log_structured.call_args_list
            if len(call[0]) > 0 and call[0][0] == "Resource Registration Summary"
        ]

        assert len(summary_calls) == 1, "Should log resource registration summary"
        summary_kwargs = summary_calls[0][1]

        assert summary_kwargs['total_resources'] == 5
        assert summary_kwargs['registered_count'] == 2
        assert summary_kwargs['skipped_count'] == 3
        assert 'aql_events_fields' in summary_kwargs['registered']
        assert 'aql_functions' in summary_kwargs['registered']
        assert 'aql_flows_fields' in summary_kwargs['skipped']
        assert 'aql_generation_guide' in summary_kwargs['skipped']
        assert 'api_query_syntax' in summary_kwargs['skipped']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
