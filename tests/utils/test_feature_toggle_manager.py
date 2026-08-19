"""
Unit tests for FeatureToggleManager.

Tests the three-level feature toggle mechanism including:
- Configuration loading and validation
- Toggle resolution logic (verb, group, per-tool)
- Tool state summary generation
- Edge cases and error handling
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from qradar_mcp.utils.feature_toggle_manager import (
    FeatureToggleManager,
    FeatureToggleConfigError,
    get_feature_toggle_manager,
    set_feature_toggle_manager
)


@pytest.fixture
def valid_config():
    """Valid feature toggle configuration."""
    return {
        "verb_toggles": {
            "GET": True,
            "POST": True,
            "DELETE": False
        },
        "group_toggles": {
            "offense": True,
            "ariel": False,
            "reference_data": True
        },
        "per_tool_toggles": {
            "GetOffenseTool": True,
            "CreateArielSearchTool": True,
            "DeleteReferenceSe Tool": False
        }
    }


@pytest.fixture
def config_file(valid_config):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)


@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    tool = Mock()
    tool.__class__.__name__ = "GetOffenseTool"
    tool.http_verb = "GET"
    tool.tool_group = "offense"
    return tool


class TestFeatureToggleManagerInit:
    """Test FeatureToggleManager initialization and configuration loading."""
    
    def test_load_valid_config(self, config_file):
        """Test loading a valid configuration file."""
        manager = FeatureToggleManager(config_file)
        
        assert manager.verb_toggles is not None
        assert manager.group_toggles is not None
        assert manager.per_tool_toggles is not None
        assert isinstance(manager.verb_toggles, dict)
        assert isinstance(manager.group_toggles, dict)
        assert isinstance(manager.per_tool_toggles, dict)
    
    def test_missing_config_file(self):
        """Test error when configuration file is missing."""
        with pytest.raises(FeatureToggleConfigError, match="not found"):
            FeatureToggleManager("/nonexistent/path/config.json")
    
    def test_invalid_json(self):
        """Test error when configuration file contains invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            config_path = f.name
        
        try:
            with pytest.raises(FeatureToggleConfigError, match="Invalid JSON"):
                FeatureToggleManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_missing_verb_toggles(self):
        """Test error when verb_toggles key is missing."""
        config = {
            "group_toggles": {"offense": True},
            "per_tool_toggles": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            with pytest.raises(FeatureToggleConfigError, match="verb_toggles"):
                FeatureToggleManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_missing_group_toggles(self):
        """Test error when group_toggles key is missing."""
        config = {
            "verb_toggles": {"GET": True},
            "per_tool_toggles": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            with pytest.raises(FeatureToggleConfigError, match="group_toggles"):
                FeatureToggleManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_missing_per_tool_toggles(self):
        """Test that per_tool_toggles is optional and defaults to empty dict."""
        config = {
            "verb_toggles": {"GET": True},
            "group_toggles": {"offense": True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            manager = FeatureToggleManager(config_path)
            assert manager.per_tool_toggles == {}
        finally:
            os.unlink(config_path)


class TestToggleResolutionLogic:
    """Test the three-level toggle resolution logic."""
    
    def test_verb_enabled_group_enabled_no_override(self, config_file):
        """Test: verb=true, group=true, override=null → enabled."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "GetOffenseTool"
        tool.http_verb = "GET"
        tool.tool_group = "offense"
        
        assert manager.is_tool_enabled(tool) is True
    
    def test_verb_disabled_group_enabled_no_override(self, config_file):
        """Test: verb=false, group=true, override=null → disabled."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "DeleteOffenseTool"
        tool.http_verb = "DELETE"
        tool.tool_group = "offense"
        
        assert manager.is_tool_enabled(tool) is False
    
    def test_verb_enabled_group_disabled_no_override(self, config_file):
        """Test: verb=true, group=false, override=null → disabled."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "GetArielSearchTool"
        tool.http_verb = "GET"
        tool.tool_group = "ariel"
        
        assert manager.is_tool_enabled(tool) is False
    
    def test_verb_disabled_group_disabled_no_override(self, config_file):
        """Test: verb=false, group=false, override=null → disabled."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "DeleteArielSearchTool"
        tool.http_verb = "DELETE"
        tool.tool_group = "ariel"
        
        assert manager.is_tool_enabled(tool) is False
    
    def test_override_enabled_verb_disabled_group_disabled(self, config_file):
        """Test: override=true → enabled (regardless of verb/group)."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "CreateArielSearchTool"
        tool.http_verb = "POST"
        tool.tool_group = "ariel"
        
        # Both verb (POST=true) and group (ariel=false) would normally disable
        # But override=true should enable
        assert manager.is_tool_enabled(tool) is True
    
    def test_override_disabled_verb_enabled_group_enabled(self, config_file):
        """Test: override=false → disabled (regardless of verb/group)."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "DeleteReferenceSetTool"
        tool.http_verb = "DELETE"
        tool.tool_group = "reference_data"
        
        # Verb (DELETE=false) would disable, but group (reference_data=true) is enabled
        # Override=false should disable
        assert manager.is_tool_enabled(tool) is False
    
    def test_unknown_verb(self, config_file):
        """Test tool with unknown HTTP verb defaults to disabled."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "UnknownVerbTool"
        tool.http_verb = "PATCH"
        tool.tool_group = "offense"
        
        assert manager.is_tool_enabled(tool) is False
    
    def test_unknown_group(self, config_file):
        """Test tool with unknown group defaults to disabled."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock()
        tool.__class__.__name__ = "UnknownGroupTool"
        tool.http_verb = "GET"
        tool.tool_group = "unknown_group"
        
        assert manager.is_tool_enabled(tool) is False


class TestToolStateSummary:
    """Test tool state summary generation."""
    
    def test_summary_structure(self, config_file):
        """Test that summary has correct structure."""
        manager = FeatureToggleManager(config_file)
        
        # Create mock tools
        tools = [
            Mock(__class__=type('GetOffenseTool', (), {}), name="get_offense", http_verb="GET", tool_group="offense"),
            Mock(__class__=type('CreateArielSearchTool', (), {}), name="create_ariel_search", http_verb="POST", tool_group="ariel"),
        ]
        
        summary = manager.get_tool_state_summary(tools)
        
        assert "total" in summary
        assert "enabled" in summary
        assert "disabled" in summary
        assert "enabled_tools" in summary
        assert "disabled_tools" in summary
    
    def test_summary_counts(self, config_file):
        """Test tool counts in summary."""
        manager = FeatureToggleManager(config_file)
        
        # Create mock tools
        tools = [
            Mock(__class__=type('GetOffenseTool', (), {}), name="get_offense", http_verb="GET", tool_group="offense"),
            Mock(__class__=type('DeleteOffenseTool', (), {}), name="delete_offense", http_verb="DELETE", tool_group="offense"),
        ]
        
        summary = manager.get_tool_state_summary(tools)
        
        assert summary["total"] == 2
        assert summary["enabled"] == 1  # GET+offense=enabled
        assert summary["disabled"] == 1  # DELETE+offense=disabled
    
    def test_summary_tool_details(self, config_file):
        """Test tool details in summary."""
        manager = FeatureToggleManager(config_file)
        
        # Create mock tool with proper name attribute
        tool = Mock(http_verb="GET", tool_group="offense")
        tool.__class__ = type('GetOffenseTool', (), {})
        tool.name = "get_offense"  # Set name as attribute, not in Mock constructor
        
        summary = manager.get_tool_state_summary([tool])
        
        assert len(summary["enabled_tools"]) == 1
        tool_info = summary["enabled_tools"][0]
        assert tool_info["name"] == "get_offense"
        assert tool_info["class_name"] == "GetOffenseTool"
        assert tool_info["group"] == "offense"
        assert tool_info["verb"] == "GET"
        assert tool_info["enabled"] is True


class TestSingletonPattern:
    """Test the singleton pattern for global feature toggle manager."""
    
    def test_set_and_get_manager(self, config_file):
        """Test setting and getting the global manager."""
        manager = FeatureToggleManager(config_file)
        set_feature_toggle_manager(manager)
        
        retrieved = get_feature_toggle_manager()
        assert retrieved is manager
    
    def test_get_manager_before_set(self):
        """Test getting manager before it's set returns None."""
        # Reset the global manager
        set_feature_toggle_manager(None)
        
        retrieved = get_feature_toggle_manager()
        assert retrieved is None


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_tool_without_http_verb(self, config_file):
        """Test tool without http_verb property."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock(spec=[])  # Empty spec means no attributes
        tool.__class__ = type('BrokenTool', (), {})
        tool.tool_group = "offense"
        
        # Should handle gracefully and return False
        with pytest.raises(AttributeError):
            manager.is_tool_enabled(tool)
    
    def test_tool_without_tool_group(self, config_file):
        """Test tool without tool_group property."""
        manager = FeatureToggleManager(config_file)
        
        tool = Mock(spec=[])  # Empty spec means no attributes
        tool.__class__ = type('BrokenTool', (), {})
        tool.http_verb = "GET"
        
        # Should handle gracefully and return False
        with pytest.raises(AttributeError):
            manager.is_tool_enabled(tool)
    
    def test_empty_per_tool_toggles(self):
        """Test configuration with empty per_tool_toggles."""
        config = {
            "verb_toggles": {"GET": True, "POST": True, "DELETE": True},
            "group_toggles": {"offense": True},
            "per_tool_toggles": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            manager = FeatureToggleManager(config_path)
            
            tool = Mock()
            tool.__class__.__name__ = "GetOffenseTool"
            tool.http_verb = "GET"
            tool.tool_group = "offense"
            
            # Should use verb AND group logic
            assert manager.is_tool_enabled(tool) is True
        finally:
            os.unlink(config_path)
    
    def test_null_override_value(self):
        """Test per-tool toggle with null value uses verb AND group logic."""
        config = {
            "verb_toggles": {"GET": True, "POST": True, "DELETE": True},
            "group_toggles": {"offense": True},
            "per_tool_toggles": {"GetOffenseTool": None}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            manager = FeatureToggleManager(config_path)
            
            tool = Mock(http_verb="GET", tool_group="offense")
            tool.__class__ = type('GetOffenseTool', (), {})
            
            # Null override should skip to verb AND group logic
            # GET=true AND offense=true = enabled
            assert manager.is_tool_enabled(tool) is True
        finally:
            os.unlink(config_path)
