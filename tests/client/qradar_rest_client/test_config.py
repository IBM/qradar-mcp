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
Unit tests for QRadarRestClient configuration loading.
"""

import os
from unittest.mock import patch, mock_open
from qradar_mcp.client.qradar_rest_client import load_config
import qradar_mcp.client.qradar_rest_client as _mod


class TestLoadConfig:
    """Tests for load_config function."""

    @patch('builtins.open', new_callable=mock_open, read_data='{"qradar": {"host": "test.com"}}')
    @patch('os.path.exists')
    def test_load_config_file_exists(self, mock_exists, mock_file):
        """Test loading config when file exists."""
        mock_exists.return_value = True

        config = load_config()

        assert config is not None
        assert "qradar" in config
        assert config["qradar"]["host"] == "test.com"

    @patch('os.path.exists')
    def test_load_config_file_not_exists(self, mock_exists):
        """Test loading config when file doesn't exist."""
        mock_exists.return_value = False

        config = load_config()

        assert config is None

    @patch('os.path.exists')
    def test_load_config_resolves_to_project_root(self, mock_exists):
        """load_config must look for config.json at the project root (two levels up from client/)."""
        mock_exists.return_value = False

        load_config()

        checked_path = mock_exists.call_args[0][0]
        client_dir = os.path.dirname(os.path.abspath(_mod.__file__))
        project_root = os.path.dirname(client_dir)
        expected_path = os.path.join(project_root, 'config.json')
        assert checked_path == expected_path